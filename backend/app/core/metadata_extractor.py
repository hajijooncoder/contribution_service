"""
Legal Metadata Extractor Service
استخراج متادیتای حقوقی: کلیدواژه‌ها، مراجع، تاریخ‌ها، موجودات قانونی
"""

import re
from datetime import datetime
from typing import List, Optional, Set
from dataclasses import dataclass, field

@dataclass
class ExtractedMetadata:
    """Extracted metadata from legal text."""
    article_count: int = 0
    note_count: int = 0
    clause_count: int = 0
    keywords: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    approval_date: Optional[str] = None
    legal_entities: List[str] = field(default_factory=list)
    risk_level: str = "LOW"
    detected_document_type: str = "unknown"


class LegalMetadataExtractor:
    """
    Extracts structured metadata from Persian legal texts.
    Identifies articles, notes, keywords, references, dates, and legal entities.
    """

    # Legal keyword dictionary (high-value terms for search/analysis)
    LEGAL_KEYWORDS = {
        # Constitutional
        'قانون اساسی', 'ماده', 'تبصره', 'بند', 'فصل', 'بخش',
        # Legislative
        'قانون', 'مقررات', 'آئین‌نامه', 'دستورالعمل', 'مرسوم', 'الزام',
        # Executive
        'وزیر', 'وزارت', 'سازمان', 'شرکت', 'مؤسسه', 'دولت',
        # Judicial
        'دادگاه', 'قاضی', 'دادستان', 'وکیل', 'شکایت', 'دعوا', 'حکم', 'رأی',
        # Procedural
        'مرحله', 'مراجع', 'مراجع اداری', 'دادگاه اداری', 'دیوان عدالت اداری',
        # Rights
        'حق', 'وظیفه', 'جرم', 'مجازات', 'حبس', 'جرمیه', 'تحریر', 'امضاء',
        # Financial
        'مالیات', 'عاید', 'بودجه', 'اعتبار', 'پول', 'ریال', 'دلار',
        # Temporal
        'مهلت', 'تاریخ', 'شروع', 'انقضا', 'تمدید', 'لغو', 'نسخ', 'ابطال',
    }

    # Legal entity patterns (organizations, courts, ministries)
    LEGAL_ENTITY_PATTERNS = [
        r'مجلس\s+شورای\s+اسلامی',
        r'مجلس\s+خبرگان',
        r'شورای\s+نگهبان',
        r'دیوان\s+عدالت\s+اداری',
        r'دادگاه\s+عالی\s+کشور',
        r'قوه\s+قضاییه',
        r'وزارت\s+\w+',
        r'سازمان\s+\w+',
        r'شرکت\s+\w+',
        r'بانک\s+\w+',
        r'بیمه\s+\w+',
    ]

    # Reference patterns (legal citations)
    REFERENCE_PATTERNS = [
        r'قانون\s+\w+(?:\s+\w+)*',
        r'مقررات\s+\w+(?:\s+\w+)*',
        r'آئین‌نامه\s+\w+(?:\s+\w+)*',
        r'دستورالعمل\s+\w+(?:\s+\w+)*',
        r'مرسوم\s+\w+(?:\s+\w+)*',
    ]

    # Date patterns (Persian/Shamsi dates)
    DATE_PATTERNS = [
        r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})',  # DD/MM/YYYY
        r'(\d{4})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})',  # YYYY/MM/DD
        r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # DD Month YYYY
        r'(?:تاریخ|تاریخ\s+)\s*(\d{1,2})/(\d{1,2})/(\d{4})',
        r'(?:تأیید\s+|مصوب\s+|ابلاغ\s+)\s*(\d{1,2})/(\d{1,2})/(\d{4})',
    ]

    # Risk keywords
    HIGH_RISK_KEYWORDS = [
        'نسخ', 'لغو', 'ابطال', 'تخصیص', 'تقیید', 'جرم', 'مجازات',
        'حبس', 'جرمیه', 'اعدام', 'تفریق', 'انحلال', 'باطله',
    ]

    def __init__(self):
        self._compiled_entities = [re.compile(p, re.IGNORECASE) for p in self.LEGAL_ENTITY_PATTERNS]
        self._compiled_refs = [re.compile(p, re.IGNORECASE) for p in self.REFERENCE_PATTERNS]
        self._compiled_dates = [re.compile(p) for p in self.DATE_PATTERNS]

    def extract(self, text: str, structure_formatter=None) -> ExtractedMetadata:
        """
        Extract all metadata from legal text.
        
        Args:
            text: Legal text to analyze
            structure_formatter: Optional LegalStructureFormatter for structure analysis
            
        Returns:
            ExtractedMetadata with all extracted information
        """
        if not text:
            return ExtractedMetadata()
        
        metadata = ExtractedMetadata()
        
        # 1. Extract structure counts
        if structure_formatter:
            metadata.article_count = len(structure_formatter.extract_article_numbers(text))
            metadata.note_count = len(structure_formatter.extract_note_numbers(text))
            metadata.clause_count = len(structure_formatter.extract_clause_numbers(text))
            metadata.detected_document_type = structure_formatter.get_document_type_hint(text)
        else:
            metadata.article_count = len(re.findall(r'ماده\s*\d+', text))
            metadata.note_count = len(re.findall(r'تبصره\s*\d+', text))
            metadata.clause_count = len(re.findall(r'بند\s*\d+', text))
        
        # 2. Extract keywords
        metadata.keywords = self._extract_keywords(text)
        
        # 3. Extract legal references
        metadata.references = self._extract_references(text)
        
        # 4. Extract dates
        metadata.approval_date = self._extract_approval_date(text)
        
        # 5. Extract legal entities
        metadata.legal_entities = self._extract_legal_entities(text)
        
        # 6. Assess risk level
        metadata.risk_level = self._assess_risk(text)
        
        return metadata

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract legal keywords from text."""
        found = set()
        text_lower = text.lower()
        for keyword in self.LEGAL_KEYWORDS:
            if keyword.lower() in text_lower:
                found.add(keyword)
        return sorted(found)

    def _extract_references(self, text: str) -> List[str]:
        """Extract legal references (law names, regulations)."""
        refs = set()
        for pattern in self._compiled_refs:
            for match in pattern.finditer(text):
                ref = match.group(0).strip()
                if len(ref) > 3:
                    refs.add(ref)
        return sorted(refs)[:20]  # Limit to top 20

    def _extract_approval_date(self, text: str) -> Optional[str]:
        """Extract approval/enactment date."""
        for pattern in self._compiled_dates:
            match = pattern.search(text)
            if match:
                # Normalize to YYYY/MM/DD
                groups = match.groups()
                if len(groups) == 3:
                    try:
                        if len(groups[0]) == 4:  # YYYY/MM/DD
                            return f"{groups[0]}/{int(groups[1]):02d}/{int(groups[2]):02d}"
                        else:  # DD/MM/YYYY
                            return f"{groups[2]}/{int(groups[1]):02d}/{int(groups[0]):02d}"
                    except ValueError:
                        pass
        return None

    def _extract_legal_entities(self, text: str) -> List[str]:
        """Extract legal entities (organizations, courts, ministries)."""
        entities = set()
        for pattern in self._compiled_entities:
            for match in pattern.finditer(text):
                entity = match.group(0).strip()
                if len(entity) > 2:
                    entities.add(entity)
        return sorted(entities)

    def _assess_risk(self, text: str) -> str:
        """Assess risk level based on content."""
        text_lower = text.lower()
        high_risk_count = sum(1 for kw in self.HIGH_RISK_KEYWORDS if kw in text_lower)
        
        if high_risk_count >= 3:
            return "CRITICAL"
        elif high_risk_count >= 1:
            return "HIGH"
        elif any(kw in text_lower for kw in ['ماده', 'قانون', 'مقررات']):
            return "MEDIUM"
        return "LOW"

    def get_risk_explanation(self, metadata: ExtractedMetadata) -> str:
        """Get human-readable risk explanation."""
        if metadata.risk_level == "CRITICAL":
            return "متن شامل کلمات کلیدی با ریسک بسیار بالا (نسخ، مجازات، ابطال) است"
        elif metadata.risk_level == "HIGH":
            return "متن شامل کلمات کلیدی با ریسک بالا است"
        elif metadata.risk_level == "MEDIUM":
            return "متن حقوقی استاندارد با ریسک متوسط"
        return "ریسک پایین - احتمالاً متن اداری/مرجع"