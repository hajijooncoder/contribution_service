"""
Advanced Duplicate Detection System
تشخیص هوشمند اسناد تکراری و هم‌پوشانی

سطوح تشخیص:
1. Exact Match (SHA-256)
2. Near Duplicate (SimHash)
3. Partial Overlap (Article-level)
4. Version Detection (Amendment relationships)
"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import logging

logger = logging.getLogger(__name__)

class DuplicateLevel(str, Enum):
    """Level of duplication detected"""
    EXACT = "exact"  # 100% identical
    NEAR_DUPLICATE = "near_duplicate"  # 95%+ similarity
    PARTIAL_OVERLAP = "partial_overlap"  # Some articles overlap
    VERSION = "version"  # Same law, different version/amendment
    UNIQUE = "unique"  # No duplication

@dataclass
class OverlapInfo:
    """Information about partial overlap with another submission"""
    submission_id: str
    overlapping_articles: List[int]
    overlap_percentage: float
    total_articles_in_other: int

@dataclass
class VersionInfo:
    """Information about version relationship"""
    submission_id: str
    version_type: str  # 'original', 'amendment', 'repealed'
    confidence: float
    date_comparison: Optional[str]

@dataclass
class DuplicateReport:
    """Complete duplicate detection report"""
    is_duplicate: bool
    level: DuplicateLevel
    similarity: float
    existing_id: Optional[str] = None
    overlapping_submissions: List[OverlapInfo] = field(default_factory=list)
    related_versions: List[VersionInfo] = field(default_factory=list)
    message: str = ""

class ExactDuplicateDetector:
    """Detects 100% identical submissions using SHA-256"""

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def check(text: str, db: Session, Submission) -> Optional[str]:
        """
        Check for exact duplicate in database

        Returns:
            submission_id if duplicate found, None otherwise
        """
        content_hash = ExactDuplicateDetector.compute_hash(text)

        existing = db.query(Submission).filter(
            Submission.content_hash == content_hash
        ).first()

        return existing.id if existing else None

class NearDuplicateDetector:
    """
    Detects near-duplicates using SimHash
    Based on: Charikar, M. (2002)

    Can detect ~95%+ similar documents efficiently
    """

    @staticmethod
    def compute_simhash(text: str) -> str:
        """
        Compute SimHash fingerprint

        Implementation matches text_enhancement.TextFingerprinter
        """
        from .text_enhancement import TextFingerprinter
        return TextFingerprinter.compute_simhash(text)

    @staticmethod
    def hamming_distance(fp1: str, fp2: str) -> int:
        """Calculate Hamming distance between fingerprints"""
        return sum(c1 != c2 for c1, c2 in zip(fp1, fp2))

    @staticmethod
    def similarity(fp1: str, fp2: str) -> float:
        """Calculate similarity percentage from fingerprints"""
        distance = NearDuplicateDetector.hamming_distance(fp1, fp2)
        return 1.0 - (distance / 64.0)

    @staticmethod
    def check(
        text: str,
        db: Session,
        Submission,
        threshold: float = 0.95
    ) -> Optional[Tuple[str, float]]:
        """
        Check for near-duplicate in database

        Args:
            text: Text to check
            db: Database session
            Submission: Submission model class
            threshold: Minimum similarity to consider as duplicate (0.95 = 95%)

        Returns:
            (submission_id, similarity) if found, None otherwise
        """
        query_fp = NearDuplicateDetector.compute_simhash(text)

        # Fetch all submissions with fingerprints
        # In production, this would use an efficient index (e.g., Redis bitmap)
        candidates = db.query(Submission).filter(
            Submission.content_fingerprint.isnot(None)
        ).limit(1000).all()  # Limit for performance

        best_match = None
        best_similarity = 0.0

        for candidate in candidates:
            if not candidate.content_fingerprint:
                continue

            similarity = NearDuplicateDetector.similarity(
                query_fp,
                candidate.content_fingerprint
            )

            if similarity >= threshold and similarity > best_similarity:
                best_match = candidate
                best_similarity = similarity

        if best_match:
            return (best_match.id, best_similarity)

        return None

class PartialOverlapDetector:
    """
    Detects partial overlaps at article level

    Example:
        Submission A: Articles 1-10 of Law X
        Submission B: Articles 1-20 of Law X
        → 50% overlap detected
    """

    @staticmethod
    def extract_article_numbers(text: str) -> Set[int]:
        """Extract all article numbers from text"""
        pattern = r'ماده\s*(\d+)'
        matches = re.findall(pattern, text)

        articles = set()
        for m in matches:
            try:
                articles.add(int(m))
            except ValueError:
                continue

        return articles

    @staticmethod
    def check(
        text: str,
        metadata: dict,
        db: Session,
        Submission
    ) -> List[OverlapInfo]:
        """
        Check for partial overlaps with existing submissions

        Args:
            text: Text to check
            metadata: Extracted metadata (contains title)
            db: Database session
            Submission: Submission model class

        Returns:
            List of overlapping submissions with details
        """
        overlaps = []

        # Extract articles from submitted text
        query_articles = PartialOverlapDetector.extract_article_numbers(text)

        if not query_articles:
            return overlaps

        # Find submissions with similar titles
        title = metadata.get('title', '')
        if not title or len(title) < 5:
            return overlaps

        # Search for similar document names
        similar_submissions = db.query(Submission).filter(
            or_(
                Submission.legal_document_name.ilike(f"%{title[:50]}%"),
                Submission.source_title.ilike(f"%{title[:50]}%")
            )
        ).limit(100).all()

        for candidate in similar_submissions:
            # Extract articles from candidate
            candidate_articles = PartialOverlapDetector.extract_article_numbers(
                candidate.raw_legal_text
            )

            if not candidate_articles:
                continue

            # Calculate overlap
            common_articles = query_articles & candidate_articles

            if not common_articles:
                continue

            overlap_percentage = len(common_articles) / len(query_articles)

            # Only report significant overlaps (>30%)
            if overlap_percentage > 0.3:
                overlaps.append(OverlapInfo(
                    submission_id=candidate.id,
                    overlapping_articles=sorted(list(common_articles)),
                    overlap_percentage=overlap_percentage,
                    total_articles_in_other=len(candidate_articles)
                ))

        # Sort by overlap percentage
        overlaps.sort(key=lambda x: x.overlap_percentage, reverse=True)

        return overlaps

class VersionDetector:
    """
    Detects version relationships (original, amendment, repeal)

    Example:
        - "قانون مدنی" (original, 1307)
        - "قانون مدنی (اصلاحیه 1376)" (amendment)
        - "قانون نسخ قسمتی از قانون مدنی" (repeal)
    """

    # Patterns indicating version relationship
    AMENDMENT_PATTERNS = [
        r'اصلاحیه',
        r'متمم',
        r'تغییرات',
        r'الحاقیہ',
    ]

    REPEAL_PATTERNS = [
        r'نسخ',
        r'لغو',
        r'ابطال',
    ]

    @staticmethod
    def extract_year(text: str, title: str = None) -> Optional[int]:
        """Extract year (Shamsi) from text or title"""
        combined = f"{title or ''} {text}"

        # Pattern: سال ۱۴۰۲ or 1402
        pattern1 = r'سال\s*[۱۲]\d{3}'
        pattern2 = r'[۱۲]\d{3}'

        match = re.search(pattern1, combined)
        if match:
            year_str = re.sub(r'سال\s*', '', match.group(0))
            # Convert Persian digits
            year = int(year_str.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
            return year

        match = re.search(pattern2, combined)
        if match:
            year_str = match.group(0)
            # Check if Persian or Arabic digits
            if year_str[0] in '۱۲':
                year = int(year_str.translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
            else:
                year = int(year_str)
            return year if 1300 <= year <= 1500 else None

        return None

    @staticmethod
    def detect_version_type(title: str, text: str) -> Tuple[str, float]:
        """
        Detect if document is amendment/repeal/original

        Returns:
            (version_type, confidence)
        """
        combined = f"{title or ''} {text[:500]}".lower()

        # Check for amendment patterns
        for pattern in VersionDetector.AMENDMENT_PATTERNS:
            if re.search(pattern, combined):
                return ('amendment', 0.85)

        # Check for repeal patterns
        for pattern in VersionDetector.REPEAL_PATTERNS:
            if re.search(pattern, combined):
                return ('repealed', 0.80)

        return ('original', 0.70)

    @staticmethod
    def check(
        text: str,
        title: str,
        db: Session,
        Submission
    ) -> List[VersionInfo]:
        """
        Check for version relationships with existing submissions

        Returns:
            List of related versions
        """
        versions = []

        # Detect current document's version type
        version_type, confidence = VersionDetector.detect_version_type(title, text)
        current_year = VersionDetector.extract_year(text, title)

        # Find related documents by title similarity
        # Remove version-related words from title for matching
        clean_title = re.sub(
            r'(اصلاحیه|متمم|تغییرات|الحاقیه|نسخ|لغو)\s*(\(\d*\))?',
            '',
            title or ''
        ).strip()

        if len(clean_title) < 5:
            return versions

        similar = db.query(Submission).filter(
            Submission.legal_document_name.ilike(f"%{clean_title[:50]}%")
        ).limit(50).all()

        for candidate in similar:
            cand_type, cand_conf = VersionDetector.detect_version_type(
                candidate.legal_document_name,
                candidate.raw_legal_text
            )
            cand_year = VersionDetector.extract_year(
                candidate.raw_legal_text,
                candidate.legal_document_name
            )

            # Determine relationship
            date_comparison = None
            if current_year and cand_year:
                if current_year > cand_year:
                    date_comparison = "newer"
                elif current_year < cand_year:
                    date_comparison = "older"
                else:
                    date_comparison = "same_year"

            versions.append(VersionInfo(
                submission_id=candidate.id,
                version_type=cand_type,
                confidence=cand_conf,
                date_comparison=date_comparison
            ))

        return versions

class SmartDuplicateDetector:
    """
    Main orchestrator for multi-level duplicate detection
    """

    def __init__(self, db: Session, Submission):
        self.db = db
        self.Submission = Submission

    def check_all_levels(
        self,
        text: str,
        metadata: dict,
        title: Optional[str] = None
    ) -> DuplicateReport:
        """
        Perform comprehensive duplicate check across all levels

        Order of checks (fastest to slowest):
        1. Exact hash match
        2. SimHash near-duplicate
        3. Article-level partial overlap
        4. Version relationship detection

        Returns:
            Complete DuplicateReport
        """

        # Level 1: Exact duplicate check (fastest)
        exact_match = ExactDuplicateDetector.check(text, self.db, self.Submission)
        if exact_match:
            return DuplicateReport(
                is_duplicate=True,
                level=DuplicateLevel.EXACT,
                similarity=1.0,
                existing_id=exact_match,
                message="این متن دقیقاً قبلاً ثبت شده است"
            )

        # Level 2: Near-duplicate check (fast)
        near_dup = NearDuplicateDetector.check(text, self.db, self.Submission, threshold=0.95)
        if near_dup:
            return DuplicateReport(
                is_duplicate=True,
                level=DuplicateLevel.NEAR_DUPLICATE,
                similarity=near_dup[1],
                existing_id=near_dup[0],
                message=f"متن مشابه با میزان تشابه {near_dup[1]*100:.1f}% یافت شد"
            )

        # Level 3: Partial overlap check (medium)
        overlaps = PartialOverlapDetector.check(text, metadata, self.db, self.Submission)
        if overlaps and overlaps[0].overlap_percentage > 0.5:
            return DuplicateReport(
                is_duplicate=False,
                level=DuplicateLevel.PARTIAL_OVERLAP,
                similarity=overlaps[0].overlap_percentage,
                overlapping_submissions=overlaps,
                message="بخشی از این متن در اسناد دیگر موجود است"
            )

        # Level 4: Version detection (slower)
        versions = VersionDetector.check(text, title or "", self.db, self.Submission)
        if versions:
            return DuplicateReport(
                is_duplicate=False,
                level=DuplicateLevel.VERSION,
                similarity=0.0,
                related_versions=versions,
                message="نسخه‌های دیگر این سند در سیستم موجود است"
            )

        # No duplication detected
        return DuplicateReport(
            is_duplicate=False,
            level=DuplicateLevel.UNIQUE,
            similarity=0.0,
            message="متن جدید و منحصر به فرد است"
        )

# Convenience function
def check_duplicate(
    text: str,
    db: Session,
    Submission,
    metadata: Optional[dict] = None,
    title: Optional[str] = None
) -> DuplicateReport:
    """
    Convenience function for duplicate detection

    Usage:
        report = check_duplicate(text, db, Submission, metadata, title)
        if report.is_duplicate:
            print(f"Duplicate detected: {report.level}")
    """
    detector = SmartDuplicateDetector(db, Submission)
    return detector.check_all_levels(text, metadata or {}, title)
