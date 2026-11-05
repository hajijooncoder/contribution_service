import {
  EnhancedSubmissionRequest,
  EnhancedSubmissionResponse,
  ContributionHistoryItem,
  ReviewQueueItem,
  UserProfile,
  PlatformStats,
  RecentActivityItem,
  UrlValidationResponse,
  UserAdminItem,
  AdminOverviewStats,
  AdminExportOverview,
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

  async getStats(): Promise<PlatformStats> {
    return this.request<PlatformStats>('/contribution/stats');
  }

  async getRecentActivity(limit = 5): Promise<RecentActivityItem[]> {
    return this.request<RecentActivityItem[]>(`/contribution/recent-activity?limit=${limit}`);
  }

  async validateUrl(url: string): Promise<UrlValidationResponse> {
    return this.request<UrlValidationResponse>('/contribution/validate-url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
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

  // Admin Endpoints
  async getAdminUsers(role?: string, is_active?: boolean, skip = 0, limit = 50): Promise<{ users: UserAdminItem[]; total: number }> {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
    if (role) params.append('role', role);
    if (is_active !== undefined) params.append('is_active', String(is_active));
    return this.request<{ users: UserAdminItem[]; total: number }>(`/admin/users?${params.toString()}`);
  }

  async toggleUserActivation(userId: string, activate: boolean): Promise<{ user_id: string; is_active: boolean; message: string }> {
    return this.request(`/admin/users/${userId}/activate`, {
      method: 'PUT',
      body: JSON.stringify({ activate }),
    });
  }

  async updateUserRole(userId: string, role: string): Promise<{ user_id: string; role: string; message: string }> {
    return this.request(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async getAdminStats(): Promise<AdminOverviewStats> {
    return this.request<AdminOverviewStats>('/admin/stats/overview');
  }

  async getAdminExportOverview(): Promise<AdminExportOverview> {
    return this.request<AdminExportOverview>('/admin/export/overview');
  }

  async downloadDatasetJsonl(token: string): Promise<Blob> {
    const response = await fetch(`${API_BASE}/internal/export/dataset.jsonl`, {
      headers: {
        'X-Gateway-Token': token,
      },
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'خطا در بارگیری بسته داده‌های استخراجی.');
    }
    return response.blob();
  }
}

export const apiClient = new ApiClient();
