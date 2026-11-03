from typing import Dict, Any, Tuple
from app.core.source_validator import validate_official_legal_source_url

LEGAL_KEYWORDS = [
    "ماده", "تبصره", "بند", "قانون", "آیین‌نامه", "آیین نامه", "تصویب‌نامه",
    "تصویب نامه", "بخشنامه", "رأی", "دادنامه", "شعبه", "دیوان", "دادگاه",
    "هیأت", "مجلس", "مصوب", "شورای نگهبان", "مجمع تشخیص", "ابلاغ"
]

def calculate_submission_quality_score(
    source_url: str,
    raw_legal_text: str,
    legal_document_name: str,
    issuing_authority: str,
    publication_info: str = None,
    contributor_notes: str = None,
    has_file_attached: bool = False
) -> Tuple[int, Dict[str, Any]]:
    """
    Computes an objective data quality score (0 to 100) for a legal submission.
    Awards credits based on verifiable authenticity, structural completeness,
    and text depth.
    """
    breakdown = {
        "source_authenticity": 0,
        "text_quality": 0,
        "structural_completeness": 0,
        "context_and_attachment": 0
    }

    # 1. Official Source Verification (30 Points)
    is_valid_source, auth_name, _ = validate_official_legal_source_url(source_url)
    if is_valid_source:
        breakdown["source_authenticity"] = 30

    # 2. Legal Text Quality & Richness (Up to 35 Points)
    text = (raw_legal_text or "").strip()
    text_len = len(text)
    if text_len >= 50:
        # Base text length score
        if text_len >= 500:
            breakdown["text_quality"] += 20
        elif text_len >= 150:
            breakdown["text_quality"] += 15
        else:
            breakdown["text_quality"] += 10

        # Legal keyword density & structure
        keyword_hits = sum(1 for kw in LEGAL_KEYWORDS if kw in text)
        if keyword_hits >= 4:
            breakdown["text_quality"] += 15
        elif keyword_hits >= 2:
            breakdown["text_quality"] += 10
        elif keyword_hits >= 1:
            breakdown["text_quality"] += 5

    # 3. Structural Completeness (Up to 25 Points)
    if legal_document_name and len(legal_document_name.strip()) >= 5:
        breakdown["structural_completeness"] += 10
    if issuing_authority and len(issuing_authority.strip()) >= 3:
        breakdown["structural_completeness"] += 10
    if publication_info and len(publication_info.strip()) >= 3:
        breakdown["structural_completeness"] += 5

    # 4. Context & Attachment (Up to 10 Points)
    if contributor_notes and len(contributor_notes.strip()) >= 10:
        breakdown["context_and_attachment"] += 5
    if has_file_attached:
        breakdown["context_and_attachment"] += 5

    total_score = min(100, sum(breakdown.values()))
    return total_score, breakdown
