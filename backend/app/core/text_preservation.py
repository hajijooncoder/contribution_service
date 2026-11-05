import re

# Matches any HTML tag: <b>, </b>, <br/>, <div class="x">, etc.
_HTML_TAG_RE = re.compile(r"<[^>]+>")

def sanitize_input_text(text: str, max_length: int = 50000) -> str:
    """
    Sanitizes user input text to eliminate transport vulnerabilities
    (null bytes, control characters, ALL html tags) while strictly PRESERVING
    all Persian legal syntax, numbers, punctuation, and article references.
    """
    if not text:
        return ""

    # 1. Remove dangerous binary control characters (preserve normal newlines and tabs)
    clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 1b. Strip invisible zero-width steganography characters (ZWSP, ZWJ, BOM), preserving legitimate Persian ZWNJ (\u200c)
    clean = re.sub(r"[\u200b\u200d\ufeff]", "", clean)

    # 2. Strip ALL HTML tags (including <b>, <div>, <script>, etc.)
    #    This must run before the script-content removal so that
    #    <script>alert('xss')</script> → "alert('xss')" → then caught below.
    clean = _HTML_TAG_RE.sub("", clean)

    # 3. Remove any residual JS payloads that were inside stripped tags
    clean = re.sub(r"alert\s*\(.*?\)", "", clean)
    clean = re.sub(r"javascript\s*:", "", clean, flags=re.IGNORECASE)

    # 4. Trim length boundary
    return clean[:max_length].strip()

def validate_legal_title(title: str) -> bool:
    """
    Validates that a title is a meaningful legal document reference.
    Minimum 5 characters after stripping — single words like 'کوت' are rejected.
    """
    if not title or len(title.strip()) < 5:
        return False
    return True
