"""
Advanced Legal Text Enhancement Engine
واحد پردازش و بهبود خودکار متون حقوقی فارسی
پشتیبانی از:
- نرمال‌سازی پیشرفته
- اصلاح املایی غیرتهاجمی
- تشخیص و فرمت‌بندی ساختار قانونی
- استخراج خودکار metadata
- محاسبه fingerprint برای تشخیص duplicate
"""

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)

# Persian Unicode Ranges
PERSIAN_ALPHA_RANGE = (0x0600, 0x06FF)
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "0123456789"

# Arabic to Persian character mapping
ARABIC_TO_PERSIAN_MAP = {
    "ي": "ی",
    "ك": "ک",
    "ؤ": "و",
    "إ": "ا",
    "أ": "ا",
    "آ": "آ",
    "ة": "ه",
    "ۀ": "ه",
    "ـ": "",  # Tatweel (کشیده)
}

# Legal Structure Patterns
LEGAL_PATTERNS = {
    "article": r"ماده\s*(\d+)\s*[:\-]?",
    "note": r"تبصره\s*(\d*)\s*[:\-]?",
    "clause": r"[الف-ی][)٫]?",
    "paragraph": r"بند\s*([الف-ی]|\d+)\s*[:\-]?",
    "chapter": r"فصل\s*(\d*)\s*[:\-]?",
    "section": r"بخش\s*(\d*)\s*[:\-]?",
}

# Common Persian Legal Typos
LEGAL_TYPO_CORRECTIONS = {
    "مادهه": "ماده",
    "تبصرهه": "تبصره",
    "بندد": "بند",
    "قانونن": "قانون",
    "مقرراتت": "مقررات",
    "آیین‌نامه": "آیین‌نامه",
    "آیین نامه": "آیین‌نامه",
    "تصویب‌نامه": "تصویب‌نامه",
    "تصویب نامه": "تصویب‌نامه",
}

# High-risk legal keywords (for risk assessment)
HIGH_RISK_KEYWORDS = {"نسخ", "اصلاح", "ابطال", "تخصیص", "تقیید", "لغو", "تغییر", "سقوط"}

@dataclass
class TextChange:
    """Represents a single change in text transformation"""
    line_number: int
    original: str
    corrected: str
    change_type: str  # 'normalization', 'typo', 'formatting'
    reason: str

@dataclass
class StructuredText:
    """Result of structure detection and formatting"""
    text: str
    changes: List[TextChange] = field(default_factory=list)
    detected_articles: List[int] = field(default_factory=list)
    detected_notes: List[int] = field(default_factory=list)
    detected_clauses: List[str] = field(default_factory=list)

@dataclass
class ExtractedMetadata:
    """Auto-extracted metadata from legal text"""
    article_count: int = 0
    note_count: int = 0
    clause_count: int = 0
    keywords: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    approval_date: Optional[str] = None
    legal_entities: List[str] = field(default_factory=list)
    risk_level: str = "LOW"
    detected_document_type: Optional[str] = None

@dataclass
class EnhancedText:
    """Complete result of text enhancement pipeline"""
    original: str
    enhanced: str
    metadata: ExtractedMetadata
    fingerprint: str
    content_hash: str
    changes: List[TextChange]
    quality_score: float
    enhancement_timestamp: str

class PersianTextNormalizer:
    """
    Advanced Persian text normalizer for legal documents
    Handles Unicode normalization, character conversion, spacing
    """

    @staticmethod
    def normalize_arabic_to_persian(text: str) -> str:
        """Convert Arabic characters to Persian equivalents"""
        for arabic, persian in ARABIC_TO_PERSIAN_MAP.items():
            text = text.replace(arabic, persian)
        return text

    @staticmethod
    def normalize_digits_to_persian(text: str) -> str:
        """Convert all digits to Persian (۰-۹)"""
        result = []
        for char in text:
            if char in ARABIC_DIGITS:
                result.append(PERSIAN_DIGITS[int(char)])
            else:
                result.append(char)
        return ''.join(result)

    @staticmethod
    def normalize_zwnj(text: str) -> str:
        """
        Normalize Zero-Width Non-Joiner (نیم‌فاصله)
        - Remove excessive ZWNJ
        - Ensure proper placement
        """
        # Replace multiple ZWNJ with single
        text = re.sub(r'\u200c{2,}', '\u200c', text)

        # Remove ZWNJ at beginning/end of words
        text = re.sub(r'(?<=\s)\u200c', '', text)
        text = re.sub(r'\u200c(?=\s)', '', text)

        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize all whitespace characters
        - Replace multiple spaces with single
        - Normalize line breaks
        - Remove trailing/leading whitespace per line
        """
        # Normalize line breaks to \n
        text = re.sub(r'\r\n|\r', '\n', text)

        # Remove excessive blank lines (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Normalize spaces (no multiple spaces)
        text = re.sub(r' {2,}', ' ', text)

        # Trim each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        return text.strip()

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """Normalize Persian punctuation marks"""
        # Normalize Persian/Arabic comma
        text = text.replace('،،', '،')
        text = text.replace(',,', '،')

        # Normalize Persian semicolon
        text = text.replace('؛؛', '؛')

        # Ensure space after punctuation
        text = re.sub(r'([،؛:])([^\s\d])', r'\1 \2', text)

        # Remove space before punctuation
        text = re.sub(r'\s+([،؛:\.])', r'\1', text)

        return text

    def full_normalize(self, text: str) -> str:
        """Apply all normalization steps"""
        text = self.normalize_arabic_to_persian(text)
        text = self.normalize_digits_to_persian(text)
        text = self.normalize_zwnj(text)
        text = self.normalize_whitespace(text)
        text = self.normalize_punctuation(text)

        # Unicode NFC normalization
        text = unicodedata.normalize('NFC', text)

        return text

class LegalStructureFormatter:
    """
    Detects and formats legal document structure
    Articles, notes, clauses, paragraphs
    """

    def detect_articles(self, text: str) -> List[int]:
        """Extract all article numbers from text"""
        articles = []
        matches = re.finditer(LEGAL_PATTERNS['article'], text)
        for match in matches:
            try:
                article_num = int(match.group(1))
                articles.append(article_num)
            except (ValueError, IndexError):
                continue
        return sorted(set(articles))

    def detect_notes(self, text: str) -> List[int]:
        """Extract all note (تبصره) numbers from text"""
        notes = []
        matches = re.finditer(LEGAL_PATTERNS['note'], text)
        for match in matches:
            try:
                note_num = int(match.group(1)) if match.group(1) else 0
                notes.append(note_num)
            except (ValueError, IndexError):
                continue
        return sorted(set(notes))

    def detect_clauses(self, text: str) -> List[str]:
        """Extract all clause letters (الف، ب، ...) from text"""
        clauses = []
        matches = re.finditer(LEGAL_PATTERNS['clause'], text)
        for match in matches:
            clauses.append(match.group(0))
        return list(set(clauses))

    def format_article_headers(self, text: str) -> Tuple[str, List[TextChange]]:
        """Standardize article header formatting"""
        changes = []
        lines = text.split('\n')
        formatted_lines = []

        for i, line in enumerate(lines, 1):
            original_line = line

            # Standardize article format: "ماده X:" or "ماده X -"
            match = re.match(r'^(ماده)\s*(\d+)\s*[:\-]?\s*(.*)$', line)
            if match:
                article_num = match.group(2)
                rest = match.group(3)
                line = f"ماده {article_num}: {rest}"

                if line != original_line:
                    changes.append(TextChange(
                        line_number=i,
                        original=original_line,
                        corrected=line,
                        change_type='formatting',
                        reason='استانداردسازی سرتیتر ماده'
                    ))

            formatted_lines.append(line)

        return '\n'.join(formatted_lines), changes

    def format_note_headers(self, text: str) -> Tuple[str, List[TextChange]]:
        """Standardize note (تبصره) header formatting"""
        changes = []
        lines = text.split('\n')
        formatted_lines = []

        for i, line in enumerate(lines, 1):
            original_line = line

            # Standardize note format
            match = re.match(r'^(تبصره)\s*(\d*)\s*[:\-]?\s*(.*)$', line)
            if match:
                note_num = match.group(2) if match.group(2) else ""
                rest = match.group(3)
                if note_num:
                    line = f"تبصره {note_num}: {rest}"
                else:
                    line = f"تبصره: {rest}"

                if line != original_line:
                    changes.append(TextChange(
                        line_number=i,
                        original=original_line,
                        corrected=line,
                        change_type='formatting',
                        reason='استانداردسازی سرتیتر تبصره'
                    ))

            formatted_lines.append(line)

        return '\n'.join(formatted_lines), changes

    def full_format(self, text: str) -> StructuredText:
        """Apply all structure detection and formatting"""
        all_changes = []

        # Format articles
        text, changes = self.format_article_headers(text)
        all_changes.extend(changes)

        # Format notes
        text, changes = self.format_note_headers(text)
        all_changes.extend(changes)

        # Detect structure
        articles = self.detect_articles(text)
        notes = self.detect_notes(text)
        clauses = self.detect_clauses(text)

        return StructuredText(
            text=text,
            changes=all_changes,
            detected_articles=articles,
            detected_notes=notes,
            detected_clauses=clauses
        )

class LegalTypoCorrector:
    """
    Non-invasive typo correction for Persian legal text
    Only corrects obvious, unambiguous typos
    """

    def __init__(self):
        self.corrections = LEGAL_TYPO_CORRECTIONS.copy()

    def correct_typos(self, text: str) -> Tuple[str, List[TextChange]]:
        """Apply typo corrections"""
        changes = []
        lines = text.split('\n')
        corrected_lines = []

        for i, line in enumerate(lines, 1):
            original_line = line

            for typo, correct in self.corrections.items():
                if typo in line:
                    line = line.replace(typo, correct)

            if line != original_line:
                changes.append(TextChange(
                    line_number=i,
                    original=original_line,
                    corrected=line,
                    change_type='typo',
                    reason='اصلاح غلط املایی رایج'
                ))

            corrected_lines.append(line)

        return '\n'.join(corrected_lines), changes

    def add_custom_correction(self, typo: str, correct: str):
        """Add custom typo correction"""
        self.corrections[typo] = correct

class LegalMetadataExtractor:
    """
    Extracts metadata from legal text:
    - Keywords
    - Cross-references
    - Dates
    - Legal entities
    - Risk level
    """

    # Common legal keywords in Persian law
    LEGAL_KEYWORDS = {
        "ماده", "تبصره", "بند", "قانون", "آیین‌نامه", "تصویب‌نامه",
        "بخشنامه", "رأی", "دادنامه", "شعبه", "دیوان", "دادگاه",
        "هیأت", "مجلس", "مصوب", "شورای نگهبان", "مجمع تشخیص",
        "ابلاغ", "اجرا", "نافذ", "لازم‌الاجرا", "تاریخ"
    }

    # Date patterns in Persian text
    DATE_PATTERNS = [
        r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})',  # 12/05/1402
        r'(\d{1,2})\s*(فروردین|اردیبهشت|خرداد|تیر|مرداد|شهریور|مهر|آبان|آذر|دی|بهمن|اسفند)\s*(\d{2,4})',  # 12 فروردین 1402
    ]

    def extract_keywords(self, text: str) -> List[str]:
        """Extract legal keywords present in text"""
        found = []
        text_lower = text.lower()

        for keyword in self.LEGAL_KEYWORDS:
            if keyword in text:
                found.append(keyword)

        return sorted(set(found))

    def extract_cross_references(self, text: str) -> List[str]:
        """
        Extract cross-references to other laws/articles
        Examples: "قانون مدنی", "ماده ۵ قانون مجازات اسلامی"
        """
        references = []

        # Pattern: "ماده X قانون Y"
        pattern1 = r'ماده\s*\d+\s*قانون\s+[آ-ی\s]+'
        matches1 = re.findall(pattern1, text)
        references.extend(matches1)

        # Pattern: "قانون X"
        pattern2 = r'قانون\s+[آ-ی\s]+'
        matches2 = re.findall(pattern2, text)
        references.extend(matches2)

        # Clean and deduplicate
        references = [ref.strip() for ref in references]
        return sorted(set(references))

    def extract_dates(self, text: str) -> Optional[str]:
        """Extract approval/publication dates from text"""
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def assess_risk_level(self, text: str, document_type: str = None) -> str:
        """
        Assess risk level based on content and document type
        HIGH: Contains repeal/amendment keywords or is a law/treaty
        LOW: Otherwise
        """
        text_lower = text.lower()

        # Check for high-risk keywords
        for keyword in HIGH_RISK_KEYWORDS:
            if keyword in text:
                return "HIGH"

        # Check document type
        if document_type and document_type.lower() in ["law", "treaty", "قانون", "معاهده"]:
            return "HIGH"

        return "LOW"

    def detect_document_type(self, text: str, title: str = None) -> Optional[str]:
        """
        Auto-detect document type from content
        Returns: 'law', 'regulation', 'bylaw', 'verdict', 'circular', or None
        """
        text_lower = text.lower()
        title_lower = (title or "").lower()

        if "قانون" in title_lower or "قانون" in text_lower[:200]:
            return "law"
        elif "آیین‌نامه" in title_lower or "آیین‌نامه" in text_lower[:200]:
            return "bylaw"
        elif "تصویب‌نامه" in title_lower or "تصویب‌نامه" in text_lower[:200]:
            return "regulation"
        elif "بخشنامه" in title_lower or "بخشنامه" in text_lower[:200]:
            return "circular"
        elif "رأی" in title_lower or "دادنامه" in title_lower:
            return "verdict"

        return None

    def full_extract(
        self,
        text: str,
        title: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> ExtractedMetadata:
        """Extract all metadata from text"""

        # Structure detection
        articles = re.findall(LEGAL_PATTERNS['article'], text)
        notes = re.findall(LEGAL_PATTERNS['note'], text)
        clauses = re.findall(LEGAL_PATTERNS['clause'], text)

        # Content analysis
        keywords = self.extract_keywords(text)
        references = self.extract_cross_references(text)
        date = self.extract_dates(text)
        risk = self.assess_risk_level(text, document_type)

        # Document type detection
        if not document_type:
            document_type = self.detect_document_type(text, title)

        return ExtractedMetadata(
            article_count=len(articles),
            note_count=len(notes),
            clause_count=len(clauses),
            keywords=keywords,
            references=references,
            approval_date=date,
            legal_entities=[],  # Would require NER model
            risk_level=risk,
            detected_document_type=document_type
        )

class TextFingerprinter:
    """
    Computes fingerprints for duplicate detection
    Uses SimHash-like approach for near-duplicate detection
    """

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Compute SHA-256 hash of text"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_simhash_features(text: str) -> List[str]:
        """
        Extract features for SimHash computation
        - Shingles (n-grams)
        - Words
        - Structural markers
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text.lower().strip())

        # Word-level features
        words = text.split()

        # 3-word shingles
        shingles = []
        for i in range(len(words) - 2):
            shingle = ' '.join(words[i:i+3])
            shingles.append(shingle)

        # Add structural markers
        if re.search(r'ماده\s*\d+', text):
            shingles.append('STRUCTURE:ARTICLE')

        if re.search(r'تبصره', text):
            shingles.append('STRUCTURE:NOTE')

        return shingles

    @staticmethod
    def compute_simhash(text: str) -> str:
        """
        Compute SimHash fingerprint for near-duplicate detection
        Based on: Charikar, M. (2002). "Similarity estimation techniques from rounding algorithms"
        """
        features = TextFingerprinter.compute_simhash_features(text)

        if not features:
            return "0" * 64

        # Initialize 64-bit vector
        v = [0] * 64

        for feature in features:
            # Hash each feature
            feature_hash = int(hashlib.md5(feature.encode('utf-8')).hexdigest(), 16)

            # Update bit vector
            for i in range(64):
                bit = (feature_hash >> i) & 1
                if bit:
                    v[i] += 1
                else:
                    v[i] -= 1

        # Generate final fingerprint
        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return format(fingerprint, '064b')

    @staticmethod
    def hamming_distance(fp1: str, fp2: str) -> int:
        """Calculate Hamming distance between two fingerprints"""
        if len(fp1) != len(fp2):
            return 64

        return sum(c1 != c2 for c1, c2 in zip(fp1, fp2))

    @staticmethod
    def similarity(fp1: str, fp2: str) -> float:
        """Calculate similarity (0-1) from two fingerprints"""
        distance = TextFingerprinter.hamming_distance(fp1, fp2)
        return 1.0 - (distance / 64.0)

class QualityScorer:
    """
    Computes quality score for legal text (0-100)
    Based on:
    - Text length
    - Structure presence
    - Keyword density
    - Formatting quality
    """

    @staticmethod
    def score_text_length(text: str) -> int:
        """Score based on text length (0-25 points)"""
        length = len(text.strip())

        if length >= 1000:
            return 25
        elif length >= 500:
            return 20
        elif length >= 200:
            return 15
        elif length >= 100:
            return 10
        elif length >= 50:
            return 5
        else:
            return 0

    @staticmethod
    def score_structure(metadata: ExtractedMetadata) -> int:
        """Score based on legal structure presence (0-35 points)"""
        score = 0

        # Articles
        if metadata.article_count > 0:
            score += min(15, metadata.article_count * 3)

        # Notes
        if metadata.note_count > 0:
            score += min(10, metadata.note_count * 2)

        # Clauses
        if metadata.clause_count > 0:
            score += min(10, metadata.clause_count * 2)

        return min(35, score)

    @staticmethod
    def score_keywords(metadata: ExtractedMetadata) -> int:
        """Score based on keyword density (0-25 points)"""
        count = len(metadata.keywords)

        if count >= 10:
            return 25
        elif count >= 7:
            return 20
        elif count >= 5:
            return 15
        elif count >= 3:
            return 10
        elif count >= 1:
            return 5
        else:
            return 0

    @staticmethod
    def score_formatting(text: str) -> int:
        """Score based on formatting quality (0-15 points)"""
        score = 0

        # Check for proper article formatting
        if re.search(r'ماده\s*\d+:', text):
            score += 5

        # Check for proper line breaks
        if '\n\n' in text:
            score += 5

        # Check for absence of excessive whitespace
        if not re.search(r' {3,}', text):
            score += 5

        return score

    def compute_score(self, text: str, metadata: ExtractedMetadata) -> float:
        """Compute overall quality score (0-100)"""
        length_score = self.score_text_length(text)
        structure_score = self.score_structure(metadata)
        keyword_score = self.score_keywords(metadata)
        formatting_score = self.score_formatting(text)

        total = length_score + structure_score + keyword_score + formatting_score

        return min(100.0, float(total))

class LegalTextEnhancer:
    """
    Main orchestrator for legal text enhancement
    Coordinates all sub-components
    """

    def __init__(self):
        self.normalizer = PersianTextNormalizer()
        self.formatter = LegalStructureFormatter()
        self.corrector = LegalTypoCorrector()
        self.extractor = LegalMetadataExtractor()
        self.fingerprinter = TextFingerprinter()
        self.scorer = QualityScorer()

    def enhance(
        self,
        raw_text: str,
        title: Optional[str] = None,
        document_type: Optional[str] = None,
        aggressive: bool = False
    ) -> EnhancedText:
        """
        Main enhancement pipeline

        Args:
            raw_text: Original text
            title: Optional document title
            document_type: Optional document type hint
            aggressive: If True, apply more aggressive corrections

        Returns:
            EnhancedText with all processing results
        """
        if not raw_text or not raw_text.strip():
            raise ValueError("Text cannot be empty")

        original = raw_text
        all_changes = []

        # Step 1: Unicode normalization
        text = self.normalizer.full_normalize(raw_text)
        if text != original:
            all_changes.append(TextChange(
                line_number=0,
                original=original,
                corrected=text,
                change_type='normalization',
                reason='نرمال‌سازی یونیکد و فاصله‌ها'
            ))

        # Step 2: Typo correction
        text, changes = self.corrector.correct_typos(text)
        all_changes.extend(changes)

        # Step 3: Structure formatting
        structured = self.formatter.full_format(text)
        text = structured.text
        all_changes.extend(structured.changes)

        # Step 4: Metadata extraction
        metadata = self.extractor.full_extract(text, title, document_type)

        # Step 5: Fingerprinting
        fingerprint = self.fingerprinter.compute_simhash(text)
        content_hash = self.fingerprinter.compute_sha256(text)

        # Step 6: Quality scoring
        quality_score = self.scorer.compute_score(text, metadata)

        return EnhancedText(
            original=original,
            enhanced=text,
            metadata=metadata,
            fingerprint=fingerprint,
            content_hash=content_hash,
            changes=all_changes,
            quality_score=quality_score,
            enhancement_timestamp=datetime.now(timezone.utc).isoformat()
        )

# Convenience function for direct use
def enhance_legal_text(
    text: str,
    title: Optional[str] = None,
    document_type: Optional[str] = None
) -> EnhancedText:
    """
    Convenience function to enhance legal text

    Usage:
        result = enhance_legal_text("ماده ۱: این قانون...")
        print(result.enhanced)
        print(result.quality_score)
    """
    enhancer = LegalTextEnhancer()
    return enhancer.enhance(text, title, document_type)
