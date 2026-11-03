import re

def sanitize_input_text(text: str, max_length: int = 50000) -> str:
    """
    Sanitizes user input text to eliminate transport vulnerabilities
    (null bytes, control characters, script tags) while strictly PRESERVING
    all Persian legal syntax, numbers, punctuation, and article references.
    """
    if not text:
        return ""

    # 1. Remove dangerous binary control characters (preserve normal newlines and tabs)
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 2. Prevent HTML script execution
    clean = re.sub(r"(?i)<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", clean)

    # 3. Trim length boundary
    return clean[:max_length].strip()

def validate_legal_title(title: str) -> bool:
    """Validates that a title is a meaningful legal document reference."""
    if not title or len(title.strip()) < 3:
        return False
    return True
