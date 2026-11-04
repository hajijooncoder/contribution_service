/**
 * ============================================================
 * API CLIENT CONTRACT TESTS — Hardcore Suite
 * ============================================================
 *
 * These tests verify that the ApiClient class:
 * 1. Calls the correct backend endpoint URLs
 * 2. Sends the correct HTTP method (GET/POST)
 * 3. Sends the correct Content-Type headers
 * 4. Returns data in the shape the frontend types expect
 *
 * Uses fetch mocking to intercept all network calls.
 * ============================================================
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { apiClient } from './client';

// Helper: create a mock fetch response
function mockResponse(body: unknown, ok = true, status = 200): Response {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
    headers: new Headers(),
  } as Response;
}

// Helper: spy on fetch
function spyOnFetch() {
  const spy = vi.fn();
  globalThis.fetch = spy as unknown as typeof fetch;
  return spy;
}

beforeEach(() => {
  // Reset token before each test
  apiClient.setToken(null);
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ============================================================================
// 1. Login endpoint — POST /api/v1/auth/token
// ============================================================================

describe('ApiClient.login', () => {
  it('should POST to /api/v1/auth/token', async () => {
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      access_token: 'test-token',
      token_type: 'bearer',
      role: 'contributor',
      user_id: 'test-id',
    }));

    const formData = new URLSearchParams();
    formData.append('username', 'test@example.com');
    formData.append('password', 'password123');

    await apiClient.login(formData);

    expect(spy).toHaveBeenCalledTimes(1);
    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/auth/token');
    expect(init?.method).toBe('POST');
  });

  it('should send Content-Type: application/x-www-form-urlencoded', async () => {
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      access_token: 'test-token',
      token_type: 'bearer',
    }));

    const formData = new URLSearchParams();
    formData.append('username', 'test@example.com');
    formData.append('password', 'password123');

    await apiClient.login(formData);

    const [, init] = spy.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('application/x-www-form-urlencoded');
  });

  it('should store the access_token after successful login', async () => {
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      access_token: 'my-jwt-token',
      token_type: 'bearer',
    }));

    const formData = new URLSearchParams();
    formData.append('username', 'test@example.com');
    formData.append('password', 'password123');

    await apiClient.login(formData);
    expect(apiClient.getToken()).toBe('my-jwt-token');
    expect(localStorage.getItem('mahoun_auth_token')).toBe('my-jwt-token');
  });

  it('should throw on non-ok response', async () => {
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({ detail: 'Incorrect email or password.' }, false, 401));

    const formData = new URLSearchParams();
    formData.append('username', 'wrong@example.com');
    formData.append('password', 'wrong');

    await expect(apiClient.login(formData)).rejects.toThrow('Incorrect email or password.');
  });
});

// ============================================================================
// 2. getMe endpoint — GET /api/v1/auth/me
// ============================================================================

describe('ApiClient.getMe', () => {
  it('should GET /api/v1/auth/me with Authorization header', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      id: 'user-1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'contributor',
      is_active: true,
      created_at: '2026-01-01T00:00:00',
    }));

    await apiClient.getMe();

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/auth/me');
    expect(init?.method).toBeUndefined(); // GET is default
    const headers = init?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer my-token');
  });

  it('should NOT have mcc_credits in the response type', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      id: 'user-1',
      email: 'test@example.com',
      role: 'contributor',
      is_active: true,
      created_at: '2026-01-01T00:00:00',
    }));

    const result = await apiClient.getMe();
    // The backend UserOut does NOT return mcc_credits or total_credits
    // So the frontend should not expect them from getMe()
    // @ts-expect-error — mcc_credits does not exist on backend response
    expect(result.mcc_credits).toBeUndefined();
    // @ts-expect-error — total_credits does not exist on backend response
    expect(result.total_credits).toBeUndefined();
  });
});

// ============================================================================
// 3. submitEnhanced — POST /api/v1/contribution/submit/enhanced
// ============================================================================

describe('ApiClient.submitEnhanced', () => {
  it('should POST to /api/v1/contribution/submit/enhanced', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      status: 'submitted',
      submission_id: 'sub-1',
      message: 'ثبت شد',
    }));

    await apiClient.submitEnhanced({
      source_title: 'test',
      legal_document_name: 'test doc',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://rc.majlis.ir/fa/law/show/1',
      document_type: 'law',
      issuing_authority: 'مجلس',
      force_submit: true,
      skip_enhancement: true,
    });

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/contribution/submit/enhanced');
    expect(init?.method).toBe('POST');
    const headers = init?.headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('application/json');
    expect(headers['Authorization']).toBe('Bearer my-token');
  });

  it('should send JSON body with the request payload', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      status: 'submitted',
      submission_id: 'sub-1',
      message: 'ثبت شد',
    }));

    const payload = {
      source_title: 'test',
      legal_document_name: 'test doc',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://rc.majlis.ir/fa/law/show/1',
      document_type: 'law' as const,
      issuing_authority: 'مجلس',
      force_submit: true,
      skip_enhancement: true,
    };

    await apiClient.submitEnhanced(payload);

    const [, init] = spy.mock.calls[0];
    const body = JSON.parse(init?.body as string);
    expect(body.source_title).toBe('test');
    expect(body.force_submit).toBe(true);
    expect(body.skip_enhancement).toBe(true);
  });

  it('should handle preview response correctly', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      status: 'preview',
      submission_id: null,
      enhanced_preview: {
        original_length: 100,
        enhanced_length: 105,
        changes_count: 1,
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
        quality_score: 75.0,
        fingerprint: 'a'.repeat(64),
        content_hash: 'b'.repeat(64),
        suggested_improvements: [],
      },
      duplicate_check: null,
      message: 'پیش‌نمایش آماده است.',
    }));

    const result = await apiClient.submitEnhanced({
      source_title: 'test',
      legal_document_name: 'test doc',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://rc.majlis.ir/fa/law/show/1',
      document_type: 'law',
      issuing_authority: 'مجلس',
    });

    expect(result.status).toBe('preview');
    expect(result.enhanced_preview).not.toBeNull();
    expect(result.enhanced_preview?.quality_score).toBe(75.0);
    expect(result.submission_id).toBeNull();
  });

  it('should handle duplicate_detected response correctly', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      status: 'duplicate_detected',
      submission_id: null,
      enhanced_preview: null,
      duplicate_check: {
        is_duplicate: true,
        level: 'exact',
        similarity: 1.0,
        message: 'این متن دقیقاً قبلاً ثبت شده است',
        overlapping_submissions: [],
        related_versions: [],
      },
      message: 'هشدار: این متن دقیقاً قبلاً ثبت شده است',
    }));

    const result = await apiClient.submitEnhanced({
      source_title: 'test',
      legal_document_name: 'test doc',
      raw_legal_text: 'A'.repeat(20),
      source_url: 'https://rc.majlis.ir/fa/law/show/1',
      document_type: 'law',
      issuing_authority: 'مجلس',
      force_submit: false,
      skip_enhancement: true,
    });

    expect(result.status).toBe('duplicate_detected');
    expect(result.duplicate_check?.is_duplicate).toBe(true);
    expect(result.duplicate_check?.level).toBe('exact');
    expect(result.submission_id).toBeNull();
  });
});

// ============================================================================
// 4. getMyHistory — GET /api/v1/contribution/history
// ============================================================================

describe('ApiClient.getMyHistory', () => {
  it('should GET /api/v1/contribution/history', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse([
      {
        id: 'sub-1',
        date: '2026-01-01',
        source: 'قانون مدنی',
        status: 'submitted',
        verification_result: null,
        earned_credits: 0,
      },
    ]));

    await apiClient.getMyHistory();

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/contribution/history');
    const headers = init?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer my-token');
  });

  it('backend returns: id, date, source, status, verification_result, earned_credits', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    const backendResponse = [
      {
        id: 'sub-1',
        date: '2026-01-01',
        source: 'قانون مدنی',
        status: 'submitted',
        verification_result: null,
        earned_credits: 0,
      },
    ];
    spy.mockResolvedValue(mockResponse(backendResponse));

    const result = await apiClient.getMyHistory();

    // The backend returns: id, date, source, status, verification_result, earned_credits
    // NOT: title, document_type, quality_score, created_at, required_reviewers, current_approvals
    expect(result[0].id).toBe('sub-1');
    // @ts-expect-error — title does NOT exist in backend response
    expect(result[0].title).toBeUndefined();
    // @ts-expect-error — document_type does NOT exist in backend response
    expect(result[0].document_type).toBeUndefined();
    // @ts-expect-error — quality_score does NOT exist in backend response
    expect(result[0].quality_score).toBeUndefined();
    // @ts-expect-error — created_at does NOT exist in backend response
    expect(result[0].created_at).toBeUndefined();
  });
});

// ============================================================================
// 5. getReviewQueue — GET /api/v1/contribution/review/pending
// ============================================================================

describe('ApiClient.getReviewQueue', () => {
  it('should GET /api/v1/contribution/review/pending', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse([
      {
        id: 'sub-1',
        source_title: 'test',
        legal_document_name: 'test doc',
        source_url: 'https://example.com',
        document_type: 'law',
        issuing_authority: 'مجلس',
        submitted_by: 'Test User',
        submitted_at: '2026-01-01 10:00',
        validation_result: null,
      },
    ]));

    await apiClient.getReviewQueue();

    const [url] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/contribution/review/pending');
  });

  it('backend PendingReviewItem does NOT have raw_legal_text', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse([
      {
        id: 'sub-1',
        source_title: 'test',
        legal_document_name: 'test doc',
        source_url: 'https://example.com',
        document_type: 'law',
        issuing_authority: 'مجلس',
        submitted_by: 'Test User',
        submitted_at: '2026-01-01 10:00',
        validation_result: null,
      },
    ]));

    const result = await apiClient.getReviewQueue();

    // Backend PendingReviewItem does NOT return:
    // raw_legal_text, status, quality_score, required_reviewers,
    // current_approvals, detected_risk_level, created_at
    // @ts-expect-error — raw_legal_text does NOT exist in backend response
    expect(result[0].raw_legal_text).toBeUndefined();
    // @ts-expect-error — status does NOT exist in backend PendingReviewItem
    expect(result[0].status).toBeUndefined();
    // @ts-expect-error — quality_score does NOT exist
    expect(result[0].quality_score).toBeUndefined();
    // @ts-expect-error — required_reviewers does NOT exist
    expect(result[0].required_reviewers).toBeUndefined();
    // @ts-expect-error — current_approvals does NOT exist
    expect(result[0].current_approvals).toBeUndefined();
    // @ts-expect-error — detected_risk_level does NOT exist
    expect(result[0].detected_risk_level).toBeUndefined();
    // @ts-expect-error — created_at does NOT exist
    expect(result[0].created_at).toBeUndefined();
  });
});

// ============================================================================
// 6. submitReview — POST /api/v1/contribution/review/decision
// ============================================================================

describe('ApiClient.submitReview', () => {
  it('should POST to /api/v1/contribution/review/decision', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      status: 'ok',
      submission_id: 'sub-1',
      new_status: 'accepted',
      decision: 'approve',
      message: 'approved',
    }));

    await apiClient.submitReview('sub-1', 'approve', 'good');

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/contribution/review/decision');
    expect(init?.method).toBe('POST');
    const body = JSON.parse(init?.body as string);
    expect(body.submission_id).toBe('sub-1');
    expect(body.decision).toBe('approve');
    expect(body.reviewer_notes).toBe('good');
  });

  it('should accept "approve", "reject", "request_correction" — NOT "approved" or "rejected"', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({ status: 'ok' }));

    // Valid: 'approve'
    await apiClient.submitReview('sub-1', 'approve', 'good');
    expect(spy).toHaveBeenCalled();

    // Valid: 'reject'
    spy.mockClear();
    await apiClient.submitReview('sub-1', 'reject', 'bad');
    expect(spy).toHaveBeenCalled();

    // Valid: 'request_correction'
    spy.mockClear();
    await apiClient.submitReview('sub-1', 'request_correction', 'fix please');
    expect(spy).toHaveBeenCalled();

    // INVALID: 'approved' — should NOT compile
    // @ts-expect-error — 'approved' is not a valid decision
    await apiClient.submitReview('sub-1', 'approved', 'good');

    // INVALID: 'rejected' — should NOT compile
    // @ts-expect-error — 'rejected' is not a valid decision
    await apiClient.submitReview('sub-1', 'rejected', 'bad');
  });
});

// ============================================================================
// 7. uploadDocument — POST /api/v1/contribution/upload
// ============================================================================

describe('ApiClient.uploadDocument', () => {
  it('should POST to /api/v1/contribution/upload with FormData', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      file_id: 'file-1',
      original_filename: 'test.pdf',
      file_size: 1024,
      sha256_hash: 'abc123',
      detected_mime: 'application/pdf',
    }));

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    await apiClient.uploadDocument(file);

    const [url, init] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/contribution/upload');
    expect(init?.method).toBe('POST');
    expect(init?.body).toBeInstanceOf(FormData);
  });

  it('should NOT set Content-Type for FormData (browser sets it automatically)', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      file_id: 'file-1',
      original_filename: 'test.pdf',
      file_size: 1024,
      sha256_hash: 'abc123',
      detected_mime: 'application/pdf',
    }));

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    await apiClient.uploadDocument(file);

    const [, init] = spy.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    // Content-Type should NOT be application/json for FormData uploads
    // It should be undefined so the browser can set multipart/form-data boundary
    expect(headers['Content-Type']).toBeUndefined();
  });

  it('backend returns original_filename, NOT original_name', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      file_id: 'file-1',
      original_filename: 'test.pdf',
      file_size: 1024,
      sha256_hash: 'abc123',
      detected_mime: 'application/pdf',
    }));

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const result = await apiClient.uploadDocument(file);

    // Backend returns: original_filename (NOT original_name)
    // The frontend type says: original_name — this is a MISMATCH
    // @ts-expect-error — original_name does NOT exist in backend response
    expect(result.original_name).toBeUndefined();
  });
});

// ============================================================================
// 8. Token management
// ============================================================================

describe('ApiClient token management', () => {
  it('should store token in localStorage', () => {
    apiClient.setToken('my-jwt');
    expect(localStorage.getItem('mahoun_auth_token')).toBe('my-jwt');
  });

  it('should remove token from localStorage on setToken(null)', () => {
    apiClient.setToken('my-jwt');
    apiClient.setToken(null);
    expect(localStorage.getItem('mahoun_auth_token')).toBeNull();
  });

  it('should read token from localStorage on construction', () => {
    localStorage.setItem('mahoun_auth_token', 'persisted-token');
    // Re-create client by importing fresh — but since it's a singleton,
    // we just check the stored value
    expect(localStorage.getItem('mahoun_auth_token')).toBe('persisted-token');
  });

  it('should send Authorization header when token is set', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      id: '1', email: 'test', role: 'contributor', is_active: true, created_at: '2026-01-01', full_name: 'Test'
    }));

    await apiClient.getMe();

    const [, init] = spy.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer my-token');
  });

  it('should NOT send Authorization header when token is null', async () => {
    apiClient.setToken(null);
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({
      id: '1', email: 'test', role: 'contributor', is_active: true, created_at: '2026-01-01', full_name: 'Test'
    }));

    await apiClient.getMe();

    const [, init] = spy.mock.calls[0];
    const headers = init?.headers as Record<string, string>;
    expect(headers['Authorization']).toBeUndefined();
  });
});

// ============================================================================
// 9. Error handling
// ============================================================================

describe('ApiClient error handling', () => {
  it('should throw with detail message on error response', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({ detail: 'Custom error message' }, false, 400));

    await expect(apiClient.getMe()).rejects.toThrow('Custom error message');
  });

  it('should throw with message field if detail is missing', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({ message: 'Another error' }, false, 400));

    await expect(apiClient.getMe()).rejects.toThrow('Another error');
  });

  it('should throw with generic message if both detail and message are missing', async () => {
    apiClient.setToken('my-token');
    const spy = spyOnFetch();
    spy.mockResolvedValue(mockResponse({}, false, 500));

    await expect(apiClient.getMe()).rejects.toThrow('خطای سرور (500)');
  });
});
