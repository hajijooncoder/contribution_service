from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

DecisionType = Literal['approve', 'reject', 'request_correction']

class ReviewDecision(BaseModel):
    submission_id: str
    decision: DecisionType
    reviewer_notes: Optional[str] = Field(None, max_length=5000)
    validation_result: Optional[str] = Field(None, max_length=5000)

class PendingReviewItem(BaseModel):
    id: str
    source_title: str
    legal_document_name: str
    source_url: Optional[str] = None
    document_type: str
    issuing_authority: str
    submitted_by: str
    submitted_at: str
    validation_result: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
