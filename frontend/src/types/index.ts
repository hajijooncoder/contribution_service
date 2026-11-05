export type DocumentType =
  | 'law'
  | 'regulation'
  | 'precedent'
  | 'circular'
  | 'court_order'
  | 'statute'
  | 'other';

export type SubmissionStatus =
  | 'submitted'
  | 'under_review'
  | 'under_legal_review'
  | 'needs_correction'
  | 'in_processing'
  | 'approved'
  | 'accepted'
  | 'rejected'
  | 'quarantined'
  | 'archived';

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  role: 'contributor' | 'reviewer' | 'expert' | 'admin';
  total_credits: number;
}

export interface TextChange {
  line_number: number;
  original: string;
  corrected: string;
  change_type: string;
  reason: string;
}

export interface ExtractedMetadata {
  article_count: number;
  note_count: number;
  clause_count: number;
  keywords: string[];
  references: string[];
  approval_date?: string;
  legal_entities: string[];
  risk_level: string;
  detected_document_type?: string;
}

export interface EnhancedTextPreview {
  original_length: number;
  enhanced_length: number;
  changes_count: number;
  changes: TextChange[];
  metadata: ExtractedMetadata;
  quality_score: number;
  fingerprint: string;
  content_hash: string;
  suggested_improvements: string[];
}

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  level: string;
  similarity: number;
  existing_id?: string;
  message: string;
  overlapping_submissions: Array<{
    submission_id: string;
    overlapping_articles: string[];
    overlap_percentage: number;
  }>;
  related_versions: Array<{
    submission_id: string;
    version_type: string;
    confidence: number;
  }>;
}

export interface EnhancedSubmissionRequest {
  source_title: string;
  legal_document_name: string;
  raw_legal_text: string;
  source_url: string;
  document_type: DocumentType;
  issuing_authority: string;
  publication_info?: string;
  contributor_notes?: string;
  skip_enhancement?: boolean;
  force_submit?: boolean;
}

export interface EnhancedSubmissionResponse {
  status: 'preview' | 'duplicate_detected' | 'submitted';
  submission_id?: string;
  enhanced_preview?: EnhancedTextPreview;
  duplicate_check?: DuplicateCheckResult;
  message: string;
}

export interface ContributionHistoryItem {
  id: string;
  title: string;
  document_type: DocumentType;
  status: SubmissionStatus;
  quality_score: number;
  created_at: string;
  required_reviewers: number;
  current_approvals: number;
}

export interface ReviewQueueItem {
  id: string;
  source_title: string;
  legal_document_name: string;
  raw_legal_text: string;
  source_url: string;
  document_type: DocumentType;
  issuing_authority: string;
  status: SubmissionStatus;
  quality_score: number;
  required_reviewers: number;
  current_approvals: number;
  detected_risk_level: string;
  created_at: string;
}

export interface RecentActivityItem {
  id: string;
  title: string;
  status: SubmissionStatus;
  date: string;
  awarded_credits?: number;
}

export interface PlatformStats {
  total_submissions: number;
  pending_submissions: number;
  accepted_submissions: number;
  rejected_submissions: number;
  contribution_credits: number;
}

export interface UrlValidationResponse {
  valid: boolean;
  authority?: string | null;
  error?: string | null;
}
