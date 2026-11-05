"""
Quality Scorer Service
امتیازدهی کیفیت متون حقوقی (0-100)
"""

from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class QualityBreakdown:
    """Detailed quality score breakdown."""
    structure_score: int = 0      # 0-20: Has articles, notes, proper formatting
    metadata_score: int = 0       # 0-20: Has dates, references, entities
    content_score: int = 0        # 0-25: Length, completeness, legal terminology
    source_score: int = 0         # 0-15: Official source URL, authority
    formatting_score: int = 0     # 0-10: Clean formatting, no OCR artifacts
    file_bonus: int = 0           # 0-10: Attached source file
    total: int = 0                # 0-100
    details: List[str] = field(default_factory=list)


class QualityScorer:
    """
    Scores legal text quality from 0-100 based on multiple dimensions.
    Used for contributor credits and review prioritization.
    """

    # Weights for each dimension (must sum to 100)
    WEIGHTS = {
        'structure': 20,
        'metadata': 20,
        'content': 25,
        'source': 15,
        'formatting': 10,
        'file_bonus': 10,
    }

    # Minimum thresholds
    MIN_ARTICLES_FOR_FULL_STRUCTURE = 3
    MIN_WORDS_FOR_CONTENT = 200
    MIN_KEYWORDS_FOR_METADATA = 3

    def __init__(self):
        pass

    def score(self,
              source_url: str = "",
              raw_legal_text: str = "",
              legal_document_name: str = "",
              issuing_authority: str = "",
              publication_info: str = "",
              contributor_notes: str = "",
              has_file_attached: bool = False,
              metadata=None) -> tuple[int, QualityBreakdown]:
        """
        Calculate comprehensive quality score.
        
        Returns:
            Tuple of (total_score, QualityBreakdown)
        """
        breakdown = QualityBreakdown()
        
        # 1. Structure Score (0-20)
        breakdown.structure_score = self._score_structure(raw_legal_text, metadata)
        
        # 2. Metadata Score (0-20)
        breakdown.metadata_score = self._score_metadata(
            raw_legal_text, legal_document_name, issuing_authority, 
            publication_info, contributor_notes, metadata
        )
        
        # 3. Content Score (0-25)
        breakdown.content_score = self._score_content(raw_legal_text)
        
        # 4. Source Score (0-15)
        breakdown.source_score = self._score_source(source_url, issuing_authority)
        
        # 5. Formatting Score (0-10)
        breakdown.formatting_score = self._score_formatting(raw_legal_text)
        
        # 6. File Bonus (0-10)
        breakdown.file_bonus = self.WEIGHTS['file_bonus'] if has_file_attached else 0
        
        # Calculate total
        breakdown.total = (
            breakdown.structure_score +
            breakdown.metadata_score +
            breakdown.content_score +
            breakdown.source_score +
            breakdown.formatting_score +
            breakdown.file_bonus
        )
        
        # Cap at 100
        breakdown.total = min(100, breakdown.total)
        
        return breakdown.total, breakdown

    def _score_structure(self, text: str, metadata) -> int:
        """Score document structure (articles, notes, hierarchy)."""
        if not text:
            return 0
        
        score = 0
        details = []
        
        # Article count
        article_count = metadata.article_count if metadata else len(
            __import__('re').findall(r'ماده\s*\d+', text)
        )
        if article_count >= self.MIN_ARTICLES_FOR_FULL_STRUCTURE:
            score += 10
            details.append(f"{article_count} ماده")
        elif article_count > 0:
            score += 5
            details.append(f"{article_count} ماده")
        
        # Note count
        note_count = metadata.note_count if metadata else len(
            __import__('re').findall(r'تبصره\s*\d+', text)
        )
        if note_count > 0:
            score += 5
            details.append(f"{note_count} تبصره")
        
        # Clause/hierarchy
        clause_count = metadata.clause_count if metadata else len(
            __import__('re').findall(r'بند\s*\d+', text)
        )
        if clause_count > 0:
            score += 3
            details.append(f"{clause_count} بند")
        
        # Chapter/section structure
        if __import__('re').search(r'فصل\s*\d+', text):
            score += 2
            details.append("فصل‌بندی")
        
        breakdown_details = f"ساختار: {', '.join(details)}" if details else "ساختار: ساده"
        return min(20, score)

    def _score_metadata(self, text: str, title: str, authority: str,
                       pub_info: str, notes: str, metadata) -> int:
        """Score metadata completeness."""
        score = 0
        details = []
        
        # Title quality
        if title and len(title.strip()) > 10:
            score += 4
            details.append("عنوان کامل")
        elif title:
            score += 2
        
        # Authority
        if authority and len(authority.strip()) > 5:
            score += 4
            details.append("مرجع صادره")
        
        # Publication info
        if pub_info and len(pub_info.strip()) > 5:
            score += 3
            details.append("اطلاعات انتشار")
        
        # Notes
        if notes and len(notes.strip()) > 20:
            score += 3
            details.append("یادداشت مشارکت‌کننده")
        
        # Keywords from metadata
        if metadata and metadata.keywords:
            kw_count = len(metadata.keywords)
            if kw_count >= self.MIN_KEYWORDS_FOR_METADATA:
                score += 4
                details.append(f"{kw_count} کلیدواژه")
            elif kw_count > 0:
                score += 2
        
        # References
        if metadata and metadata.references:
            score += 3
            details.append(f"{len(metadata.references)} مرجع")
        
        # Date
        if metadata and metadata.approval_date:
            score += 2
            details.append("تاریخ تصویب")
        
        breakdown_details = f"متادیتا: {', '.join(details)}" if details else "متادیتا: ناقص"
        return min(20, score)

    def _score_content(self, text: str) -> int:
        """Score content richness and legal terminology."""
        if not text:
            return 0
        
        score = 0
        word_count = len(text.split())
        details = []
        
        # Length scoring
        if word_count >= 1000:
            score += 10
            details.append("متن بسیار کامل")
        elif word_count >= 500:
            score += 7
            details.append("متن کامل")
        elif word_count >= self.MIN_WORDS_FOR_CONTENT:
            score += 5
            details.append("متن متوسط")
        elif word_count >= 50:
            score += 3
            details.append("متن کوتاه")
        
        # Legal terminology density
        legal_terms = [
            'ماده', 'تبصره', 'بند', 'فصل', 'قانون', 'مقررات',
            'آئین‌نامه', 'دستورالعمل', 'مرسوم', 'وزیر', 'دادگاه',
            'حق', 'وظیفه', 'مجازات', 'جرم', 'مهلت', 'تاریخ'
        ]
        text_lower = text.lower()
        term_count = sum(1 for term in legal_terms if term in text_lower)
        
        if term_count >= 10:
            score += 8
            details.append("ترمینولوژی غنی")
        elif term_count >= 5:
            score += 5
            details.append("ترمینologii متوسط")
        elif term_count >= 2:
            score += 3
        
        # Completeness indicators
        completeness_indicators = [
            'مصوب', 'تأیید', 'ابلاغ', 'اجرای', 'لازم‌الاجراست',
            'تبصره', 'استثنا', 'شرط', 'مشروط', 'بدون'
        ]
        indicator_count = sum(1 for ind in completeness_indicators if ind in text_lower)
        if indicator_count >= 3:
            score += 4
            details.append("مؤشرهای کاملیت")
        elif indicator_count >= 1:
            score += 2
        
        # Persian text ratio (not garbled/OCR)
        persian_chars = len(__import__('re').findall(r'[\u0600-\u06FF]', text))
        total_chars = len(__import__('re').findall(r'\S', text))
        if total_chars > 0 and persian_chars / total_chars > 0.7:
            score += 3
            details.append("متن فارسی صحیح")
        
        return min(25, score)

    def _score_source(self, source_url: str, authority: str) -> int:
        """Score source credibility."""
        score = 0
        
        # Official domains get full score
        official_domains = [
            'rrk.ir', 'dotic.ir', 'rc.majlis.ir', 'qavanin.ir',
            'divan-edalat.ir', 'rooznamehrasmi.ir', 'parliran.ir',
            'president.ir', 'cbi.ir', 'shora-gc.ir'
        ]
        
        if source_url:
            from urllib.parse import urlparse
            try:
                domain = urlparse(source_url).netloc.lower().replace('www.', '')
                if any(official in domain for official in official_domains):
                    score = 15
                elif '.ir' in domain and ('gov' in domain or 'org' in domain):
                    score = 10
                elif '.ir' in domain:
                    score = 5
            except Exception:
                score = 3  # Has URL but parsing failed
        
        # Authority match
        if authority and any(official in authority for official in 
                           ['مجلس', 'وزارت', 'ریاست', 'دیوان', 'دادگاه', 'سازمان']):
            score = max(score, 12)
        
        return min(15, score)

    def _score_formatting(self, text: str) -> int:
        """Score text formatting quality."""
        if not text:
            return 0
        
        score = 10  # Start with full, deduct for issues
        
        # Check for OCR artifacts
        ocr_artifacts = [
            r'\s{3,}',  # Excessive whitespace
            r'[|]{2,}',  # Multiple pipes (table artifacts)
            r'[_]{3,}',  # Underscore lines
            r'[.]{4,}',  # Dot leaders
            r'\d+\s*\n\s*\d+',  # Page numbers
        ]
        
        for pattern in ocr_artifacts:
            if __import__('re').search(pattern, text):
                score -= 2
        
        # Check for proper Persian punctuation
        if __import__('re').search(r'[،؛؟]', text):
            score += 1  # Bonus for proper punctuation
        
        # Check for mixed RTL/LTR issues
        if __import__('re').search(r'[\u200e\u200f]', text):
            score -= 1  # Explicit direction markers (might indicate issues)
        
        return max(0, min(10, score))