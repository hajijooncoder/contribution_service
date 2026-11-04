import {
  EnhancedSubmissionRequest,
  EnhancedSubmissionResponse,
  ContributionHistoryItem,
  ReviewQueueItem,
  UserProfile,
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('mahoun_auth_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('mahoun_auth_token', token);
    } else {
      localStorage.removeItem('mahoun_auth_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || errorData.message || `خطای سرور (${response.status})`;
      throw new Error(message);
    }

    return response.json();
  }

  // Auth
  async login(formData: URLSearchParams): Promise<{ access_token: string; token_type: string }> {
    const response = await fetch(`${API_BASE}/auth/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'ورود ناموفق بود.');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // Contributions
  async submitEnhanced(data: EnhancedSubmissionRequest): Promise<EnhancedSubmissionResponse> {
    return this.request<EnhancedSubmissionResponse>('/contribution/submit/enhanced', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMyHistory(): Promise<ContributionHistoryItem[]> {
    return this.request<ContributionHistoryItem[]>('/contribution/history');
  }

  async uploadDocument(file: File): Promise<{ file_id: string; original_name: string; sha256_hash: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}/contribution/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'بارگذاری فایل با خطا مواجه شد.');
    }

    return response.json();
  }

  // Reviewer Workspace
  async getReviewQueue(): Promise<ReviewQueueItem[]> {
    return this.request<ReviewQueueItem[]>('/contribution/review/pending');
  }

  async submitReview(submissionId: string, decision: 'approve' | 'reject' | 'request_correction', notes?: string) {
    return this.request('/contribution/review/decision', {
      method: 'POST',
      body: JSON.stringify({ submission_id: submissionId, decision, reviewer_notes: notes }),
    });
  }
}

export const apiClient = new ApiClient();
