"""
Persian Text Normalization Service
نرمال‌سازی متن فارسی: یونیکد، نیم‌فاصله، ارقام، حذف استگانوگرافی
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Persian/Arabic character mappings
PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'
ARABIC_DIGITS = '٠١٢٣٤٥٦٧٨٩'
ENGLISH_DIGITS = '0123456789'

# Translation tables
TO_ENGLISH_DIGITS = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS, ENGLISH_DIGITS * 2)
TO_PERSIAN_DIGITS = str.maketrans(ENGLISH_DIGITS, PERSIAN_DIGITS)

# Zero-width characters to remove (steganography defense)
ZERO_WIDTH_CHARS = [
    '\u200b',  # ZERO WIDTH SPACE
    '\u200c',  # ZERO WIDTH NON-JOINER (ZWNJ) - keep for Persian but normalize
    '\u200d',  # ZERO WIDTH JOINER (ZWJ)
    '\u200e',  # LEFT-TO-RIGHT MARK
    '\u200f',  # RIGHT-TO-LEFT MARK
    '\u202a',  # LEFT-TO-RIGHT EMBEDDING
    '\u202b',  # RIGHT-TO-LEFT EMBEDDING
    '\u202c',  # POP DIRECTIONAL FORMATTING
    '\u202d',  # LEFT-TO-RIGHT OVERRIDE
    '\u202e',  # RIGHT-TO-LEFT OVERRIDE
    '\u2060',  # WORD JOINER
    '\u2061',  # FUNCTION APPLICATION
    '\u2062',  # INVISIBLE TIMES
    '\u2063',  # INVISIBLE SEPARATOR
    '\u2064',  # INVISIBLE PLUS
    '\ufeff',  # ZERO WIDTH NO-BREAK SPACE (BOM)
]

# Characters that should be normalized to ZWNJ
ZWNJ_NORMALIZE = ['\u200c']  # Keep ZWNJ but ensure consistent usage

# Arabic to Persian character mapping (for backward compatibility)
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


class PersianTextNormalizer:
    """
    Normalizes Persian legal text for consistent processing.
    Handles: Unicode normalization, digit conversion, ZWNJ management,
    invisible character removal, bidirectional override defense.
    """

    def __init__(self, preserve_zwj: bool = False):
        self.preserve_zwj = preserve_zwj

    def normalize(self, text: str) -> str:
        """
        Full normalization pipeline for Persian legal text.
        
        Args:
            text: Raw input text
            
        Returns:
            Normalized text safe for legal processing
        """
        if not text:
            return ""
        
        # 1. Unicode NFC normalization (canonical composition)
        text = unicodedata.normalize('NFC', text)
        
        # 2. Remove dangerous bidirectional override characters (BiDi attack defense)
        text = self._remove_bidi_overrides(text)
        
        # 3. Remove zero-width steganography characters (except ZWNJ)
        text = self._remove_zero_width_chars(text)
        
        # 4. Normalize ZWNJ usage (consistent Persian half-space)
        text = self._normalize_zwj(text)
        
        # 5. Convert all digits to English (for internal processing)
        text = text.translate(TO_ENGLISH_DIGITS)
        
        # 6. Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # 7. Fix common Persian character variations
        text = self._fix_persian_chars(text)
        
        return text.strip()

    def normalize_arabic_to_persian(self, text: str) -> str:
        """Convert Arabic characters to Persian equivalents (backward compatibility)."""
        for arabic, persian in ARABIC_TO_PERSIAN_MAP.items():
            text = text.replace(arabic, persian)
        return text

    def _remove_bidi_overrides(self, text: str) -> str:
        """Remove bidirectional override characters that can cause BiDi attacks."""
        bidi_chars = [
            '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
            '\u2066', '\u2067', '\u2068', '\u2069',  # Isolate characters
        ]
        for char in bidi_chars:
            text = text.replace(char, '')
        return text

    def _remove_zero_width_chars(self, text: str) -> str:
        """Remove zero-width characters used for steganography, preserve ZWNJ."""
        for char in ZERO_WIDTH_CHARS:
            if char != '\u200c':  # Preserve ZWNJ for Persian
                text = text.replace(char, '')
        return text

    def _normalize_zwj(self, text: str) -> str:
        """Normalize Zero Width Non-Joiner usage for consistent Persian text."""
        # Replace multiple consecutive ZWNJ with single
        text = re.sub(r'(\u200c){2,}', '\u200c', text)
        # Ensure ZWNJ not at start/end of words
        text = re.sub(r'^\u200c+|\u200c+$', '', text)
        # Fix ZWNJ around punctuation
        text = re.sub(r'(\u200c)([،؛:.!?])', r'\2', text)
        text = re.sub(r'([\(\[<])\u200c', r'\1', text)
        text = re.sub(r'\u200c([\)\]>])', r'\1', text)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace: tabs, multiple spaces, newlines."""
        # Replace tabs and other whitespace with single space
        text = re.sub(r'[\t\v\f\r]+', ' ', text)
        # Normalize multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        # Normalize newlines (max 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    def _fix_persian_chars(self, text: str) -> str:
        """Fix common Persian character variations."""
        # Arabic yeh -> Persian yeh
        text = text.replace('\u064a', '\u06cc')  # ی
        # Arabic kaf -> Persian kaf
        text = text.replace('\u0643', '\u06a9')  # ک
        # Arabic teh marbuta -> Persian heh
        text = text.replace('\u0629', '\u0647')  # ه
        # Fix hamza variations
        text = text.replace('\u0624', '\u0648\u0654')  # ؤ -> وْ
        text = text.replace('\u0626', '\u06cc\u0654')  # ئ -> یْ
        return text

    def to_persian_digits(self, text: str) -> str:
        """Convert English digits to Persian for display."""
        return text.translate(TO_PERSIAN_DIGITS)

    def extract_persian_digits(self, text: str) -> list[int]:
        """Extract all Persian/Arabic digits as integers."""
        digits = re.findall(r'[۰-۹٠-٩]', text)
        return [int(d.translate(TO_ENGLISH_DIGITS)) for d in digits]

    # Backward compatibility static methods
    @staticmethod
    def normalize_digits_to_persian(text: str) -> str:
        """Convert all digits to Persian (۰-۹) - handles English, Arabic-Indic, and Persian digits."""
        result = []
        for char in text:
            if char in ARABIC_DIGITS:
                result.append(PERSIAN_DIGITS[int(char)])
            elif char in ENGLISH_DIGITS:
                result.append(PERSIAN_DIGITS[int(char)])
            else:
                result.append(char)
        return ''.join(result)

    @staticmethod
    def normalize_zwnj(text: str) -> str:
        """Normalize Zero-Width Non-Joiner (نیم‌فاصله)"""
        # Replace multiple ZWNJ with single
        text = re.sub(r'\u200c{2,}', '\u200c', text)
        # Remove ZWNJ at beginning/end of words
        text = re.sub(r'(?<=\s)\u200c', '', text)
        text = re.sub(r'\u200c(?=\s)', '', text)
        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize all whitespace characters"""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def normalize_punctuation(text: str) -> str:
        """Normalize punctuation marks"""
        # Normalize double Persian punctuation
        text = re.sub(r'،{2,}', '،', text)
        text = re.sub(r'؛{2,}', '؛', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'،\s*،', '،', text)
        text = re.sub(r'؛\s*؛', '؛', text)
        
        # Normalize Persian punctuation
        text = text.replace('،', '،').replace('؛', '؛')
        text = text.replace('؟', '؟').replace('۔', '؟')
        return text

    def full_normalize(self, text: str) -> str:
        """Apply all normalization steps (backward compatibility)."""
        text = self.normalize_arabic_to_persian(text)
        text = self.normalize_digits_to_persian(text)
        text = self.normalize_zwnj(text)
        text = self.normalize_whitespace(text)
        text = self.normalize_punctuation(text)

        # Unicode NFC normalization
        text = unicodedata.normalize('NFC', text)

        return text