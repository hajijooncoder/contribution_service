from datetime import datetime
from typing import Optional, Literal, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

SubmissionStatusType = Literal[
    'draft',
    'submitted',
    'under_validation',
    'under_legal_review',
    'accepted',
    'rejected',
    'needs_correction',
    'in_processing'
]

DocumentType = Literal[
    'law', 'regulation', 'verdict', 'circular', 'bylaw', 'treaty', 'other'
]

class SubmissionCreate(BaseModel):
    source_title: str = Field(..., min_length=3, max_length=500)
    legal_document_name: str = Field(..., min_length=3, max_length=500)
    raw_legal_text: str = Field(..., min_length=20, max_length=500000, description="متن کامل ماده قانونی، مقرره یا رأی قضایی کپی‌شده از منبع رسمی")
    source_url: str = Field(..., min_length=10, max_length=1000, description="آدرس اینترنتی مرجع رسمی کشور (روزنامه رسمی، مرکز پژوهش‌ها، قوانین، داتیک یا سامانه آرای قضایی)")
    document_type: DocumentType = 'law'
    issuing_authority: str = Field(..., min_length=2, max_length=255)
    publication_info: Optional[str] = Field(None, max_length=500)
    contributor_notes: Optional[str] = Field(None, max_length=10000)
    file_upload_id: Optional[str] = None

class ContributionSubmissionOut(BaseModel):
    id: str
    source_title: str
    legal_document_name: str
    raw_legal_text: str
    source_url: str
    source_domain: str
    document_type: str
    issuing_authority: str
    publication_info: Optional[str] = None
    contributor_notes: Optional[str] = None
    file_upload_id: Optional[str] = None
    quality_score: int
    awarded_credits: int
    required_reviewers: int = 1
    current_approvals: int = 0
    provenance_stamp: Optional[str] = None
    
    # Advanced text enhancement fields
    content_hash: Optional[str] = None
    content_fingerprint: Optional[str] = None
    auto_extracted_metadata: Optional[str] = None
    enhancement_changes: Optional[str] = None
    text_quality_score: Optional[int] = None
    detected_risk_level: Optional[str] = None
    
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecentActivityItem(BaseModel):
    id: str
    title: str
    status: str
    date: str
    awarded_credits: int = 0


class UrlValidationRequest(BaseModel):
    """درخواست اعتبارسنجی در لحظه آدرس منبع حقوقی"""
    url: str = Field(..., max_length=2048, description="نشانی اینترنتی منبع قانونی")


class UrlValidationResponse(BaseModel):
    """پاسخ اعتبارسنجی منبع حقوقی همراه با نام مرجع رسمی"""
    valid: bool
    authority: Optional[str] = None
    error: Optional[str] = None

class ContributionStats(BaseModel):
    total_submissions: int
    pending_submissions: int
    accepted_submissions: int
    rejected_submissions: int
    contribution_credits: int = 0

class ContributionHistoryItem(BaseModel):
    id: str
    date: str
    source: str
    status: str
    verification_result: Optional[str] = None
    earned_credits: int = 0

class ContributionSearchItem(BaseModel):
    id: str
    date: str
    legal_document_name: str
    source_title: Optional[str] = None
    document_type: str
    issuing_authority: str
    status: str
    quality_score: float = 0.0
    awarded_credits: int = 0
    submitter_id: Optional[str] = None

class ContributionSearchResponse(BaseModel):
    items: List[ContributionSearchItem]
    total: int
    skip: int
    limit: int

class FileUploadResponse(BaseModel):
    file_id: str
    original_filename: str
    file_size: int
    sha256_hash: str
    detected_mime: str


# Advanced text enhancement schemas

class TextChangeSchema(BaseModel):
    """Represents a change made during text enhancement"""
    line_number: int
    original: str
    corrected: str
    change_type: str
    reason: str


class ExtractedMetadataSchema(BaseModel):
    """Auto-extracted metadata from legal text"""
    article_count: int = 0
    note_count: int = 0
    clause_count: int = 0
    keywords: List[str] = []
    references: List[str] = []
    approval_date: Optional[str] = None
    legal_entities: List[str] = []
    risk_level: str = "LOW"
    detected_document_type: Optional[str] = None


class EnhancedTextPreview(BaseModel):
    """Preview of enhanced text before final submission"""
    original_length: int
    enhanced_length: int
    changes_count: int
    changes: List[TextChangeSchema]
    metadata: ExtractedMetadataSchema
    quality_score: float
    fingerprint: str
    content_hash: str
    suggested_improvements: List[str] = []


class DuplicateCheckResult(BaseModel):
    """Result of duplicate detection check"""
    is_duplicate: bool
    level: str  # exact, near_duplicate, partial_overlap, version, unique
    similarity: float
    existing_id: Optional[str] = None
    message: str
    overlapping_submissions: List[Dict[str, Any]] = []
    related_versions: List[Dict[str, Any]] = []


class EnhancedSubmissionRequest(BaseModel):
    """Request for text enhancement and duplicate check"""
    source_title: str = Field(..., min_length=3, max_length=500)
    legal_document_name: str = Field(..., min_length=3, max_length=500)
    raw_legal_text: str = Field(..., min_length=20, max_length=500000)
    source_url: str = Field(..., min_length=10, max_length=1000)
    document_type: DocumentType = 'law'
    issuing_authority: str = Field(..., min_length=2, max_length=255)
    publication_info: Optional[str] = None
    contributor_notes: Optional[str] = None
    
    # Option to skip enhancement (use raw text as-is)
    skip_enhancement: bool = False
    
    # Option to force submit even if duplicate detected
    force_submit: bool = False


class EnhancedSubmissionResponse(BaseModel):
    """Response with enhancement preview or duplicate warning"""
    status: str  # 'preview', 'duplicate_detected', 'submitted'
    submission_id: Optional[str] = None
    enhanced_preview: Optional[EnhancedTextPreview] = None
    duplicate_check: Optional[DuplicateCheckResult] = None
    message: str
