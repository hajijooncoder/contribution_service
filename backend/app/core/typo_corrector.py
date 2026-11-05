"""
Legal Typo Corrector Service
اصلاح املایی متون حقوقی فارسی
"""

import re
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class TypoCorrection:
    """Represents a single typo correction."""
    original: str
    corrected: str
    position: int
    confidence: float
    rule_id: str


class LegalTypoCorrector:
    """
    Corrects common Persian legal typos and OCR errors.
    Uses rule-based corrections with confidence scoring.
    """

    # Common legal typo corrections (Persian legal terminology)
    CORRECTION_RULES = [
        # Legal terminology fixes
        (r'\bقانون\s+اساسی\b', 'قانون اساسی', 'constitution_spelling', 0.95),
        (r'\bماده\s+(\d+)\s+قانون\s+اساسی\b', r'ماده \1 قانون اساسی', 'constitution_article', 0.95),
        (r'\bقوانین\s+اساسی\b', 'قوانین اساسی', 'constitution_plural', 0.90),
        
        # Common OCR errors in legal texts
        (r'\bماده\s+(\d+)\s+تبصره\s+(\d+)\b', r'ماده \1 تبصره \2', 'article_note_format', 0.95),
        (r'\bتبصره\s+(\d+)\s+ماده\s+(\d+)\b', r'تبصره \1 ماده \2', 'note_article_format', 0.95),
        
        # Arabic/Persian character fixes
        (r'ی', 'ی', 'arabic_yeh_to_persian', 0.99),  # Will be handled by normalizer
        (r'ک', 'ک', 'arabic_kaf_to_persian', 0.99),  # Will be handled by normalizer
        
        # Legal prepositions
        (r'\bاز\s+طریق\s+([^\s]+)\b', r'از طریق \1', 'preposition_fix', 0.85),
        (r'\bبه\s+منظور\s+([^\s]+)\b', r'به منظور \1', 'preposition_fix2', 0.85),
        (r'\bطبق\s+([^\s]+)\b', r'طبق \1', 'preposition_fix3', 0.85),
        (r'\bمطابق\s+([^\s]+)\b', r'مطابق \1', 'preposition_fix4', 0.85),
        
        # Common verb forms in legal texts
        (r'\bمصوب\s+شده\b', 'مصوب شده', 'passive_verb', 0.90),
        (r'\تأیید\s+شده\b', 'تأیید شده', 'passive_verb2', 0.90),
        (r'\ابلاغ\s+شده\b', 'ابلاغ شده', 'passive_verb3', 0.90),
        
        # Number formatting
        (r'(\d+)\s*(\.)\s*(\d+)', r'\1.\3', 'decimal_format', 0.80),
        
        # Punctuation fixes
        (r'\s+([،؛:.!?])', r'\1', 'punctuation_space', 0.95),
        (r'([،؛:.!?])\s*([،؛:.!?])', r'\1 ', 'double_punctuation', 0.90),
        
        # Common legal abbreviations
        (r'\bم\.\s*(\d+)', r'ماده \1', 'article_abbrev', 0.90),
        (r'\تب\.\s*(\d+)', r'تبصره \1', 'note_abbrev', 0.90),
        (r'\ب\.\s*(\d+)', r'بند \1', 'clause_abbrev', 0.90),
        
        # "واژه" corrections
        (r'\bنامه\s+رسمی\b', 'نامه رسمی', 'official_letter', 0.95),
        (r'\bروزنامه\s+رسمی\b', 'روزنامه رسمی', 'official_gazette', 0.95),
        (r'\بمهلت\s+قانونی\b', 'مهلت قانونی', 'legal_deadline', 0.95),
    ]

    def __init__(self, custom_rules: List[Tuple[str, str, str, float]] = None):
        """
        Initialize with built-in rules and optional custom rules.
        
        Args:
            custom_rules: List of (pattern, replacement, rule_id, confidence)
        """
        self.rules = self.CORRECTION_RULES.copy()
        if custom_rules:
            self.rules.extend(custom_rules)
        
        # Compile patterns
        self._compiled_rules = [
            (re.compile(pattern, re.IGNORECASE), replacement, rule_id, confidence)
            for pattern, replacement, rule_id, confidence in self.rules
        ]

    def correct(self, text: str) -> Tuple[str, List[TypoCorrection]]:
        """
        Apply all typo corrections to text.
        
        Returns:
            Tuple of (corrected_text, list_of_corrections)
        """
        if not text:
            return "", []
        
        corrections = []
        corrected = text
        
        # Apply each rule
        for pattern, replacement, rule_id, confidence in self._compiled_rules:
            for match in pattern.finditer(corrected):
                original = match.group(0)
                # Apply replacement
                new_text = pattern.sub(replacement, corrected, count=1)
                if new_text != corrected:
                    corrections.append(TypoCorrection(
                        original=original,
                        corrected=replacement if not callable(replacement) else replacement(match),
                        position=match.start(),
                        confidence=confidence,
                        rule_id=rule_id
                    ))
                    corrected = new_text
        
        # Sort corrections by position
        corrections.sort(key=lambda c: c.position)
        
        return corrected, corrections

    def get_correction_stats(self, corrections: List[TypoCorrection]) -> dict:
        """Get statistics about applied corrections."""
        if not corrections:
            return {"total": 0, "by_rule": {}, "avg_confidence": 0.0}
        
        by_rule = {}
        for c in corrections:
            by_rule[c.rule_id] = by_rule.get(c.rule_id, 0) + 1
        
        return {
            "total": len(corrections),
            "by_rule": by_rule,
            "avg_confidence": sum(c.confidence for c in corrections) / len(corrections)
        }