"""
Legal Structure Formatter Service
فرمت‌بندی ساختار حقوقی: ماده، تبصره، بند، فصل، بخش
"""

import re
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class LegalStructure:
    """Represents a structured legal document element."""
    element_type: str  # 'article', 'note', 'clause', 'chapter', 'section'
    number: str
    text: str
    level: int  # Hierarchy level (1=article, 2=note, 3=clause)


class LegalStructureFormatter:
    """
    Formats and structures legal text with proper article/note/clause hierarchy.
    Handles Persian legal document conventions.
    """

    # Patterns for legal structure elements
    ARTICLE_PATTERN = re.compile(
        r'(?:ماده|ماده\s*)(\d+)\s*[:\-]?\s*',
        re.IGNORECASE
    )
    NOTE_PATTERN = re.compile(
        r'(?:تبصره|تبصره\s*)(\d+)\s*[:\-]?\s*',
        re.IGNORECASE
    )
    CLAUSE_PATTERN = re.compile(
        r'(?:بند|بند\s*)(\d+)\s*[:\-]?\s*',
        re.IGNORECASE
    )
    CHAPTER_PATTERN = re.compile(
        r'(?:فصل|فصل\s*)(\d+)\s*[:\-]?\s*',
        re.IGNORECASE
    )
    SECTION_PATTERN = re.compile(
        r'(?:بخش|بخش\s*)(\d+)\s*[:\-]?\s*',
        re.IGNORECASE
    )

    # Amendment/Repeal patterns
    AMENDMENT_PATTERN = re.compile(
        r'(?:اصلاحیه|متمم|تغییرات|الحاقیه)\s*(?:ماده\s*)?(\d+)?',
        re.IGNORECASE
    )
    REPEAL_PATTERN = re.compile(
        r'(?:نسخ|لغو|ابطال)\s*(?:ماده\s*)?(\d+)?',
        re.IGNORECASE
    )

    def __init__(self):
        self._compiled_patterns = {
            'article': self.ARTICLE_PATTERN,
            'note': self.NOTE_PATTERN,
            'clause': self.CLAUSE_PATTERN,
            'chapter': self.CHAPTER_PATTERN,
            'section': self.SECTION_PATTERN,
        }

    def format(self, text: str) -> str:
        """
        Apply consistent formatting to legal structure elements.
        
        Args:
            text: Raw legal text
            
        Returns:
            Formatted text with consistent structure markers
        """
        if not text:
            return ""
        
        # Normalize article references
        text = self._format_articles(text)
        # Normalize notes
        text = self._format_notes(text)
        # Normalize clauses
        text = self._format_clauses(text)
        # Normalize chapters
        text = self._format_chapters(text)
        # Normalize sections
        text = self._format_sections(text)
        
        return text

    def _format_articles(self, text: str) -> str:
        """Format article references consistently."""
        def repl(match):
            num = match.group(1)
            return f"ماده {num}: "
        return self.ARTICLE_PATTERN.sub(repl, text)

    def _format_notes(self, text: str) -> str:
        """Format note references consistently."""
        def repl(match):
            num = match.group(1)
            return f"تبصره {num}: "
        return self.NOTE_PATTERN.sub(repl, text)

    def _format_clauses(self, text: str) -> str:
        """Format clause references consistently."""
        def repl(match):
            num = match.group(1)
            return f"بند {num}: "
        return self.CLAUSE_PATTERN.sub(repl, text)

    def _format_chapters(self, text: str) -> str:
        """Format chapter references consistently."""
        def repl(match):
            num = match.group(1)
            return f"فصل {num}: "
        return self.CHAPTER_PATTERN.sub(repl, text)

    def _format_sections(self, text: str) -> str:
        """Format section references consistently."""
        def repl(match):
            num = match.group(1)
            return f"بخش {num}: "
        return self.SECTION_PATTERN.sub(repl, text)

    def extract_structure(self, text: str) -> List[LegalStructure]:
        """
        Extract all legal structure elements from text.
        
        Returns:
            List of LegalStructure elements in document order
        """
        structures = []
        
        # Find all matches with positions
        matches = []
        for pattern, elem_type, level in [
            (self.CHAPTER_PATTERN, 'chapter', 0),
            (self.SECTION_PATTERN, 'section', 0),
            (self.ARTICLE_PATTERN, 'article', 1),
            (self.NOTE_PATTERN, 'note', 2),
            (self.CLAUSE_PATTERN, 'clause', 3),
        ]:
            for match in pattern.finditer(text):
                matches.append({
                    'type': elem_type,
                    'number': match.group(1),
                    'start': match.start(),
                    'end': match.end(),
                    'level': level
                })
        
        # Sort by position
        matches.sort(key=lambda x: x['start'])
        
        # Extract text for each element
        for i, match in enumerate(matches):
            start = match['end']
            end = matches[i + 1]['start'] if i + 1 < len(matches) else len(text)
            element_text = text[start:end].strip()
            
            structures.append(LegalStructure(
                element_type=match['type'],
                number=match['number'],
                text=element_text,
                level=match['level']
            ))
        
        return structures

    def extract_article_numbers(self, text: str) -> List[int]:
        """Extract all article numbers as integers."""
        numbers = []
        for match in self.ARTICLE_PATTERN.finditer(text):
            try:
                numbers.append(int(match.group(1)))
            except ValueError:
                pass
        return sorted(set(numbers))

    def extract_note_numbers(self, text: str) -> List[int]:
        """Extract all note numbers as integers."""
        numbers = []
        for match in self.NOTE_PATTERN.finditer(text):
            try:
                numbers.append(int(match.group(1)))
            except ValueError:
                pass
        return sorted(set(numbers))

    def extract_clause_numbers(self, text: str) -> List[int]:
        """Extract all clause numbers as integers."""
        numbers = []
        for match in self.CLAUSE_PATTERN.finditer(text):
            try:
                numbers.append(int(match.group(1)))
            except ValueError:
                pass
        return sorted(set(numbers))

    def detect_amendment(self, text: str) -> Optional[str]:
        """Detect if text contains amendment reference."""
        match = self.AMENDMENT_PATTERN.search(text)
        if match:
            return match.group(1) if match.group(1) else "general"
        return None

    def detect_repeal(self, text: str) -> Optional[str]:
        """Detect if text contains repeal reference."""
        match = self.REPEAL_PATTERN.search(text)
        if match:
            return match.group(1) if match.group(1) else "general"
        return None

    def get_document_type_hint(self, text: str) -> str:
        """Guess document type from structure."""
        has_articles = bool(self.ARTICLE_PATTERN.search(text))
        has_notes = bool(self.NOTE_PATTERN.search(text))
        has_chapters = bool(self.CHAPTER_PATTERN.search(text))
        
        if has_chapters:
            return "law"
        elif has_articles and has_notes:
            return "regulation"
        elif has_articles:
            return "bylaw"
        return "document"