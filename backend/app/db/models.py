import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "staging_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="contributor", nullable=False)  # contributor, reviewer, admin
    is_active = Column(Boolean, default=True, nullable=False)
    total_credits = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    submissions = relationship("Submission", back_populates="submitter")
    reviews = relationship("Review", back_populates="reviewer")

class UploadedFile(Base):
    __tablename__ = "staging_uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submitter_id = Column(String(36), ForeignKey("staging_users.id"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    detected_mime = Column(String(100), nullable=False)
    quarantine_status = Column(String(50), default="quarantined_verified", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    submission = relationship("Submission", back_populates="uploaded_file", uselist=False)

class Submission(Base):
    __tablename__ = "staging_submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submitter_id = Column(String(36), ForeignKey("staging_users.id"), nullable=False)
    source_title = Column(String(500), nullable=False)
    legal_document_name = Column(String(500), nullable=False)
    raw_legal_text = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=False)
    source_domain = Column(String(100), nullable=False)
    document_type = Column(String(50), default="law", nullable=False)
    issuing_authority = Column(String(255), nullable=False)
    publication_info = Column(String(500), nullable=True)
    contributor_notes = Column(Text, nullable=True)
    file_upload_id = Column(String(36), ForeignKey("staging_uploaded_files.id"), nullable=True)
    
    # Quality & Credit metrics
    quality_score = Column(Integer, default=0, nullable=False)
    awarded_credits = Column(Integer, default=0, nullable=False)

    # Risk & Multi-Reviewer Quorum (Phase 2 Roadmap)
    required_reviewers = Column(Integer, default=1, nullable=False)
    current_approvals = Column(Integer, default=0, nullable=False)
    provenance_stamp = Column(Text, nullable=True)

    # Advanced Text Enhancement & Duplicate Detection (Phase 3)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for exact duplicate detection
    content_fingerprint = Column(String(64), nullable=True, index=True)  # SimHash for near-duplicate detection
    auto_extracted_metadata = Column(Text, nullable=True)  # JSON: article_count, keywords, references, etc.
    enhancement_changes = Column(Text, nullable=True)  # JSON: list of TextChange objects
    text_quality_score = Column(Integer, nullable=True)  # 0-100 computed by QualityScorer
    detected_risk_level = Column(String(10), nullable=True)  # HIGH, LOW (auto-detected)

    # Finite State Machine status
    status = Column(String(50), default="submitted", index=True, nullable=False)
    
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    submitter = relationship("User", back_populates="submissions")
    uploaded_file = relationship("UploadedFile", back_populates="submission")
    reviews = relationship("Review", back_populates="submission", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "staging_reviews"
    __table_args__ = (
        UniqueConstraint("submission_id", "reviewer_id", name="uq_submission_reviewer"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("staging_submissions.id"), nullable=False)
    reviewer_id = Column(String(36), ForeignKey("staging_users.id"), nullable=False)
    decision = Column(String(50), nullable=False)  # approve, reject, request_correction
    reviewer_notes = Column(Text, nullable=True)
    validation_result = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    submission = relationship("Submission", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

class AuditLog(Base):
    __tablename__ = "staging_audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action = Column(String(100), nullable=False)
    actor_id = Column(String(36), nullable=False)
    target_id = Column(String(36), nullable=False)
    details = Column(Text, nullable=True)
    previous_hash = Column(String(64), nullable=False, default="0000000000000000000000000000000000000000000000000000000000000000")
    record_hash = Column(String(64), nullable=False, default="")
    timestamp = Column(DateTime, default=utc_now, nullable=False)
