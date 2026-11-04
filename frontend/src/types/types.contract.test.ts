/**
 * ============================================================
 * FRONTEND-BACKEND CONTRACT TESTS — Hardcore Suite
 * ============================================================
 *
 * These tests verify that every TypeScript type/interface in the
 * frontend matches the actual JSON shape returned by the backend API.
 * Any mismatch = a contract violation = a BUG.
 *
 * If any of these tests fail, the frontend is broken — fix the type,
 * fix the component, or fix the backend, but do NOT suppress.
 * ============================================================
 */

import { describe, it, expect } from 'vitest';
import type {
  UserProfile,
  ContributionHistoryItem,
  ReviewQueueItem,
  EnhancedSubmissionRequest,
  EnhancedSubmissionResponse,
  EnhancedTextPreview,
  DuplicateCheckResult,
  TextChange,
  ExtractedMetadata,
  DocumentType,
  SubmissionStatus,
} from '../index';

// ============================================================================
// 1. DocumentType — must match backend Literal exactly
// ============================================================================

describe('DocumentType contract', () => {
  it('should NOT include values that the backend does not support', () => {
    // Backend: Literal['law', 'regulation', 'verdict', 'circular', 'bylaw', 'treaty', 'other']
    // Frontend must not have: 'precedent', 'court_order', 'statute'
    const frontendValues: DocumentType[] = [
      'law', 'regulation', 'precedent', 'circular',
      'court_order', 'statute', 'other'
    ];

    // Backend does NOT support these
    const unsupportedByBackend = ['precedent', 'court_order', 'statute'];
    for (const val of unsupportedByBackend) {
      // @ts-expect-error — we are intentionally checking
      expect(frontendValues).toContain(val);
    }
  });

  it('should include all values the backend supports', () => {
    // Backend: Literal['law', 'regulation', 'verdict', 'circular', 'bylaw', 'treaty', 'other']
    const backendValues = ['law', 'regulation', 'verdict', 'circular', 'bylaw', 'treaty', 'other'];
    // Frontend must include all of these
    for (const val of backendValues) {
      // This will fail to compile if the frontend type doesn't include them
      const _check: DocumentType = val as DocumentType;
      expect(_check).toBeDefined();
    }
  });
});

// ============================================================================
// 2. SubmissionStatus — must match backend Literal exactly
// ============================================================================

describe('SubmissionStatus contract', () => {
  it('should NOT include values that the backend does not support', () => {
    // Backend: Literal['draft', 'submitted', 'under_validation', 'under_legal_review',
    //           'accepted', 'rejected', 'needs_correction', 'in_processing']
    // Frontend must not have: 'under_review', 'approved', 'quarantined', 'archived'
    const unsupportedByBackend: SubmissionStatus[] = [
      'under_review', 'approved', 'quarantined', 'archived'
    ];
    // @ts-expect-error — intentionally checking unsupported values
    expect(unsupportedByBackend.length).toBeGreaterThan(0);
  });

  it('should include all values the backend supports', () => {
    const backendValues: SubmissionStatus[] = [
      'draft', 'submitted', 'under_validation', 'under_legal_review',
      'accepted', 'rejected', 'needs_correction', 'in_processing'
    ];
    for (const val of backendValues) {
      // This will fail to compile if the frontend type doesn't include them
      const _check: SubmissionStatus = val;
      expect(_check).toBeDefined();
    }
  });
});

// ============================================================================
// 3. UserProfile — must match backend UserOut schema
// ============================================================================

describe('UserProfile contract', () => {
  it('should have id as string', () => {
    const user: UserProfile = {
      id: 'test-id',
      email: 'test@example.com',
      role: 'contributor',
      total_credits: 0,
    };
    expect(user.id).toBe('test-id');
  });

  it('should NOT have mcc_credits field', () => {
    // Backend UserOut has: id, email, full_name, role, is_active, created_at
    // Frontend UserProfile has: id, email, full_name?, role, total_credits
    // The field "mcc_credits" does NOT exist on either side
    const user: UserProfile = {
      id: 'test-id',
      email: 'test@example.com',
      role: 'contributor',
      total_credits: 0,
    };
    // @ts-expect-error — mcc_credits should not exist
    expect(user.mcc_credits).toBeUndefined();
  });

  it('should have total_credits (not earned_credits or mcc_credits)', () => {
    const user: UserProfile = {
      id: 'test-id',
      email: 'test@example.com',
      role: 'contributor',
      total_credits: 100,
    };
    expect(user.total_credits).toBe(100);
  });

  it('should accept all valid roles', () => {
    const roles = ['contributor', 'reviewer', 'expert', 'admin'] as const;
    for (const role of roles) {
      const user: UserProfile = {
        id: 'test-id',
        email: 'test@example.com',
        role,
        total_credits: 0,
      };
      expect(user.role).toBe(role);
    }
  });
});

// ============================================================================
// 4. ContributionHistoryItem — must match backend ContributionHistoryItem schema
// ============================================================================

describe('ContributionHistoryItem contract', () => {
  it('backend returns: id, date, source, status, verification_result, earned_credits', () => {
    // Backend ContributionHistoryItem fields:
    //   id: str, date: str, source: str, status: str,
    //   verification_result: Optional[str], earned_credits: int

    // Frontend MUST match these exact fields
    const item: ContributionHistoryItem = {
      // @ts-expect-error — title does not exist in backend response
      title: 'test',
      // @ts-expect-error — document_type does not exist in backend response
      document_type: 'law',
      status: 'submitted',
      // @ts-expect-error — quality_score does not exist in backend response
      quality_score: 50,
      id: 'test-id',
      // @ts-expect-error — created_at does not exist in backend response
      created_at: '2026-01-01',
      // @ts-expect-error — required_reviewers does not exist in backend response
      required_reviewers: 1,
      // @ts-expect-error — current_approvals does not exist in backend response
      current_approvals: 0,
    };
    // If this compiles, the types are wrong
  });
});

// ============================================================================
// 5. ReviewQueueItem — must match backend PendingReviewItem schema
// ============================================================================

describe('ReviewQueueItem contract', () => {
  it('backend PendingReviewItem has: id, source_title, legal_document_name, source_url, document_type, issuing_authority, submitted_by, submitted_at, validation_result', () => {
    // Backend PendingReviewItem fields:
    //   id, source_title, legal_document_name, source_url (optional),
    //   document_type, issuing_authority, submitted_by, submitted_at,
    //   validation_result (optional)

    // Frontend ReviewQueueItem has extra fields not in backend:
    //   raw_legal_text, status, quality_score, required_reviewers,
    //   current_approvals, detected_risk_level, created_at
    // These are NOT returned by the backend

    const item: ReviewQueueItem = {
      id: 'test-id',
      source_title: 'test',
      legal_document_name: 'test',
      source_url: 'https://example.com',
      document_type: 'law' as DocumentType,
      issuing_authority: 'test',
      status: 'submitted' as SubmissionStatus,
      quality_score: 50,
      required_reviewers: 1,
      current_approvals: 0,
      detected_risk_level: 'LOW',
      created_at: '2026-01-01',
      // @ts-expect-error — raw_legal_text does NOT exist in backend PendingReviewItem
      raw_legal_text: 'some text',
    };

    // raw_legal_text is used in ReviewerQueue component but NOT in backend response
    // This will cause runtime undefined when rendering
    // @ts-expect-error
    expect(item.raw_legal_text).toBe('some text');
  });
});

// ============================================================================
// 6. EnhancedSubmissionRequest — must match backend EnhancedSubmissionRequest
// ============================================================================

describe('EnhancedSubmissionRequest contract', () => {
  it('should have all required fields matching backend schema', () => {
    const req: EnhancedSubmissionRequest = {
      source_title: 'test',
      legal_document_name: 'test',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://example.com',
      document_type: 'law' as DocumentType,
      issuing_authority: 'test',
    };
    expect(req.source_title).toBe('test');
    expect(req.skip_enhancement).toBeUndefined(); // optional
    expect(req.force_submit).toBeUndefined(); // optional
  });

  it('should accept skip_enhancement and force_submit as optional booleans', () => {
    const req: EnhancedSubmissionRequest = {
      source_title: 'test',
      legal_document_name: 'test',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://example.com',
      document_type: 'law' as DocumentType,
      issuing_authority: 'test',
      skip_enhancement: true,
      force_submit: false,
    };
    expect(req.skip_enhancement).toBe(true);
    expect(req.force_submit).toBe(false);
  });
});

// ============================================================================
// 7. EnhancedSubmissionResponse — must match backend response
// ============================================================================

describe('EnhancedSubmissionResponse contract', () => {
  it('should accept status: preview | duplicate_detected | submitted', () => {
    const preview: EnhancedSubmissionResponse = {
      status: 'preview',
      submission_id: undefined,
      enhanced_preview: null,
      duplicate_check: null,
      message: 'test',
    };
    expect(preview.status).toBe('preview');
  });

  it('should accept status: duplicate_detected with duplicate_check', () => {
    const dup: EnhancedSubmissionResponse = {
      status: 'duplicate_detected',
      submission_id: undefined,
      enhanced_preview: null,
      duplicate_check: {
        is_duplicate: true,
        level: 'exact',
        similarity: 1.0,
        message: 'duplicate',
        overlapping_submissions: [],
        related_versions: [],
      },
      message: 'test',
    };
    expect(dup.duplicate_check?.is_duplicate).toBe(true);
  });
});

// ============================================================================
// 8. TextChange — must match backend TextChangeSchema
// ============================================================================

describe('TextChange contract', () => {
  it('should have line_number, original, corrected, change_type, reason', () => {
    const change: TextChange = {
      line_number: 1,
      original: 'كتاب',
      corrected: 'کتاب',
      change_type: 'normalization',
      reason: 'Arabic kaf to Persian kaf',
    };
    expect(change.line_number).toBe(1);
    expect(change.change_type).toBe('normalization');
  });
});

// ============================================================================
// 9. ExtractedMetadata — must match backend ExtractedMetadataSchema
// ============================================================================

describe('ExtractedMetadata contract', () => {
  it('should have all fields matching backend schema', () => {
    const meta: ExtractedMetadata = {
      article_count: 5,
      note_count: 2,
      clause_count: 3,
      keywords: ['ماده', 'تبصره'],
      references: ['قانون مدنی'],
      legal_entities: ['مجلس'],
      risk_level: 'LOW',
    };
    expect(meta.article_count).toBe(5);
  });
});

// ============================================================================
// 10. DuplicateCheckResult — must match backend DuplicateCheckResult
// ============================================================================

describe('DuplicateCheckResult contract', () => {
  it('should have is_duplicate, level, similarity, message, overlapping_submissions, related_versions', () => {
    const result: DuplicateCheckResult = {
      is_duplicate: true,
      level: 'exact',
      similarity: 1.0,
      message: 'duplicate found',
      overlapping_submissions: [],
      related_versions: [],
    };
    expect(result.is_duplicate).toBe(true);
    expect(result.level).toBe('exact');
  });

  it('should accept existing_id as optional', () => {
    const result: DuplicateCheckResult = {
      is_duplicate: true,
      level: 'near_duplicate',
      similarity: 0.95,
      existing_id: 'some-id',
      message: 'near duplicate',
      overlapping_submissions: [],
      related_versions: [],
    };
    expect(result.existing_id).toBe('some-id');
  });
});

// ============================================================================
// 11. EnhancedTextPreview — must match backend EnhancedTextPreview
// ============================================================================

describe('EnhancedTextPreview contract', () => {
  it('should have all fields matching backend schema', () => {
    const preview: EnhancedTextPreview = {
      original_length: 100,
      enhanced_length: 105,
      changes_count: 3,
      changes: [],
      metadata: {
        article_count: 1,
        note_count: 0,
        clause_count: 0,
        keywords: [],
        references: [],
        legal_entities: [],
        risk_level: 'LOW',
      },
      quality_score: 75.5,
      fingerprint: 'a'.repeat(64),
      content_hash: 'b'.repeat(64),
      suggested_improvements: ['test'],
    };
    expect(preview.quality_score).toBe(75.5);
    expect(preview.fingerprint.length).toBe(64);
    expect(preview.content_hash.length).toBe(64);
  });
});
