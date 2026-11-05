/**
 * ============================================================
 * COMPONENT BRUTAL TESTS — Hardcore Suite
 * ============================================================
 *
 * These tests verify that each component:
 * 1. Renders without crashing
 * 2. Calls the correct API methods
 * 3. Handles loading/error/success states correctly
 * 4. Does NOT reference undefined properties on types
 * 5. Sends correct data to the API
 *
 * If any test fails, there is a real bug in the component.
 * ============================================================
 */

import React from 'react';
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { apiClient } from '../api/client';

// Mock the apiClient
vi.mock('../api/client', () => ({
  apiClient: {
    setToken: vi.fn(),
    getToken: vi.fn(() => null),
    logout: vi.fn(),
    login: vi.fn(),
    getMe: vi.fn(),
    submitEnhanced: vi.fn(),
    getMyHistory: vi.fn(),
    getReviewQueue: vi.fn(),
    submitReview: vi.fn(),
    uploadDocument: vi.fn(),
    validateUrl: vi.fn().mockResolvedValue({ valid: true, authority: 'روزنامه رسمی جمهوری اسلامی ایران' }),
  },
}));

import { Header } from './Header';
import { Footer } from './Footer';
import { ContributionForm } from './ContributionForm';
import { ContributionHistory } from './ContributionHistory';
import { ReviewerQueue } from './ReviewerQueue';
import { TextEnhancementPreviewModal } from './TextEnhancementPreviewModal';
import { LoginModal } from './LoginModal';
import type { UserProfile } from '../types';

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ============================================================================
// 1. Header component
// ============================================================================

describe('Header component', () => {
  const mockSetTab = vi.fn();
  const mockLoginClick = vi.fn();
  const mockLogoutClick = vi.fn();

  it('should render MAHOUNN brand', () => {
    render(
      <Header
        user={null}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );
    expect(screen.getByText('MAHOUNN')).toBeInTheDocument();
  });

  it('should show login button when user is null', () => {
    render(
      <Header
        user={null}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );
    expect(screen.getByText('ورود / ثبت‌نام')).toBeInTheDocument();
  });

  it('should show user email and total_credits when user is logged in', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'contributor',
      total_credits: 42,
    };

    render(
      <Header
        user={user}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );

    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    // The Header should display total_credits, NOT mcc_credits
    // If the component uses user.mcc_credits, this test will expose the bug
    // by checking that the MCC value is rendered correctly
    expect(screen.getByText(/42/)).toBeInTheDocument();
  });

  it('should NOT crash when user has total_credits (not mcc_credits)', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'test@example.com',
      role: 'contributor',
      total_credits: 10,
    };

    // This will crash if Header.tsx uses user.mcc_credits
    expect(() => {
      render(
        <Header
          user={user}
          activeTab="submit"
          setActiveTab={mockSetTab}
          onLoginClick={mockLoginClick}
          onLogoutClick={mockLogoutClick}
        />
      );
    }).not.toThrow();
  });

  it('should show reviewer tab for reviewer role', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'reviewer@example.com',
      role: 'reviewer',
      total_credits: 0,
    };

    render(
      <Header
        user={user}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );

    expect(screen.getByText('میزکار داوری')).toBeInTheDocument();
  });

  it('should show reviewer tab for admin role', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'admin@example.com',
      role: 'admin',
      total_credits: 0,
    };

    render(
      <Header
        user={user}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );

    expect(screen.getByText('میزکار داوری')).toBeInTheDocument();
  });

  it('should NOT show reviewer tab for contributor role', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'contrib@example.com',
      role: 'contributor',
      total_credits: 0,
    };

    render(
      <Header
        user={user}
        activeTab="submit"
        setActiveTab={mockSetTab}
        onLoginClick={mockLoginClick}
        onLogoutClick={mockLogoutClick}
      />
    );

    expect(screen.queryByText('میزکار داوری')).not.toBeInTheDocument();
  });
});

// ============================================================================
// 2. Footer component
// ============================================================================

describe('Footer component', () => {
  it('should render without crashing', () => {
    render(<Footer />);
    // Footer contains "MAHOUNN" in multiple places — use getAllByText
    expect(screen.getAllByText(/MAHOUNN/).length).toBeGreaterThan(0);
  });
});

// ============================================================================
// 3. ContributionForm component
// ============================================================================

describe('ContributionForm component', () => {
  it('should render form with all required fields', () => {
    render(<ContributionForm onSuccess={vi.fn()} />);

    expect(screen.getByPlaceholderText(/قانون شوراهای حل اختلاف/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/https:\/\/rc.majlis.ir/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/متن کامل ماده/)).toBeInTheDocument();
  });

  it('should show error when text is less than 20 characters', async () => {
    render(<ContributionForm onSuccess={vi.fn()} />);

    // Fill required fields
    fireEvent.change(screen.getByPlaceholderText(/قانون شوراهای حل اختلاف/), { target: { value: 'قانون تستی' } });
    fireEvent.change(screen.getByPlaceholderText(/مثال: مجلس/), { target: { value: 'مجلس شورای اسلامی' } });
    fireEvent.change(screen.getByPlaceholderText(/https:\/\/rc.majlis.ir/), { target: { value: 'https://rc.majlis.ir/fa/law/show/1' } });
    fireEvent.change(screen.getByPlaceholderText(/متن کامل ماده/), { target: { value: 'کوتاه' } });

    const form = screen.getByPlaceholderText(/متن کامل ماده/).closest('form')!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/حداقل ۲۰ کاراکتر/)).toBeInTheDocument();
    });
  });

  it('should call apiClient.submitEnhanced with correct payload on submit', async () => {
    const mockSubmit = vi.mocked(apiClient.submitEnhanced);
    mockSubmit.mockResolvedValue({
      status: 'submitted',
      submission_id: 'sub-1',
      message: 'ثبت شد',
    });

    render(<ContributionForm onSuccess={vi.fn()} />);

    // Fill required fields using fireEvent for reliability
    fireEvent.change(screen.getByPlaceholderText(/قانون شوراهای حل اختلاف/), { target: { value: 'قانون تستی' } });
    fireEvent.change(screen.getByPlaceholderText(/مثال: مجلس/), { target: { value: 'مجلس شورای اسلامی' } });
    fireEvent.change(screen.getByPlaceholderText(/https:\/\/rc.majlis.ir/), { target: { value: 'https://rc.majlis.ir/fa/law/show/1' } });
    fireEvent.change(screen.getByPlaceholderText(/متن کامل ماده/), { target: { value: 'این یک متن تستی برای قانون است که حداقل بیست کاراکتر دارد' } });

    const form = screen.getByPlaceholderText(/متن کامل ماده/).closest('form')!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1);
    });

    const callArgs = mockSubmit.mock.calls[0][0];
    expect(callArgs.source_title).toBe('قانون تستی');
    expect(callArgs.source_url).toBe('https://rc.majlis.ir/fa/law/show/1');
    expect(callArgs.force_submit).toBe(false); // initial submit is NOT force
  });

  it('should show success message on submitted status', async () => {
    const mockSubmit = vi.mocked(apiClient.submitEnhanced);
    mockSubmit.mockResolvedValue({
      status: 'submitted',
      submission_id: 'sub-1',
      message: 'ثبت شد: sub-1',
    });

    render(<ContributionForm onSuccess={vi.fn()} />);

    fireEvent.change(screen.getByPlaceholderText(/قانون شوراهای حل اختلاف/), { target: { value: 'قانون تستی' } });
    fireEvent.change(screen.getByPlaceholderText(/مثال: مجلس/), { target: { value: 'مجلس' } });
    fireEvent.change(screen.getByPlaceholderText(/https:\/\/rc.majlis.ir/), { target: { value: 'https://rc.majlis.ir/fa/law/show/1' } });
    fireEvent.change(screen.getByPlaceholderText(/متن کامل ماده/), { target: { value: 'این یک متن تستی برای قانون است که حداقل بیست کاراکتر دارد' } });

    const form = screen.getByPlaceholderText(/متن کامل ماده/).closest('form')!;
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText(/مشارکت شما با موفقیت ثبت شد/)).toBeInTheDocument();
    });
  });
});

// ============================================================================
// 4. ContributionHistory component
// ============================================================================

describe('ContributionHistory component', () => {
  it('should render without crashing', async () => {
    const mockGetHistory = vi.mocked(apiClient.getMyHistory);
    mockGetHistory.mockResolvedValue([]);

    render(<ContributionHistory />);

    await waitFor(() => {
      expect(screen.getByText('تاریخچه مشارکت‌های حقوقی شما')).toBeInTheDocument();
    });
  });

  it('should show empty state when no history exists', async () => {
    const mockGetHistory = vi.mocked(apiClient.getMyHistory);
    mockGetHistory.mockResolvedValue([]);

    render(<ContributionHistory />);

    await waitFor(() => {
      expect(screen.getByText('هنوز مشارکتی ثبت نکرده‌اید')).toBeInTheDocument();
    });
  });

  it('should call apiClient.getMyHistory on mount', async () => {
    const mockGetHistory = vi.mocked(apiClient.getMyHistory);
    mockGetHistory.mockResolvedValue([]);

    render(<ContributionHistory />);

    await waitFor(() => {
      expect(mockGetHistory).toHaveBeenCalledTimes(1);
    });
  });

  it('should show loading state initially', async () => {
    const mockGetHistory = vi.mocked(apiClient.getMyHistory);
    // Never resolve to keep loading state
    mockGetHistory.mockReturnValue(new Promise(() => {}));

    render(<ContributionHistory />);

    expect(screen.getByText('در حال بارگذاری مشارکت‌ها...')).toBeInTheDocument();
  });

  it('should show error message on API failure', async () => {
    const mockGetHistory = vi.mocked(apiClient.getMyHistory);
    mockGetHistory.mockRejectedValue(new Error('خطای شبکه'));

    render(<ContributionHistory />);

    await waitFor(() => {
      expect(screen.getByText('خطای شبکه')).toBeInTheDocument();
    });
  });
});

// ============================================================================
// 5. ReviewerQueue component
// ============================================================================

describe('ReviewerQueue component', () => {
  it('should render without crashing', async () => {
    const mockGetQueue = vi.mocked(apiClient.getReviewQueue);
    mockGetQueue.mockResolvedValue([]);

    render(<ReviewerQueue />);

    await waitFor(() => {
      expect(screen.getByText('میزکار و کارتابل داوری همتا')).toBeInTheDocument();
    });
  });

  it('should call apiClient.getReviewQueue on mount', async () => {
    const mockGetQueue = vi.mocked(apiClient.getReviewQueue);
    mockGetQueue.mockResolvedValue([]);

    render(<ReviewerQueue />);

    await waitFor(() => {
      expect(mockGetQueue).toHaveBeenCalledTimes(1);
    });
  });

  it('should show empty state when queue is empty', async () => {
    const mockGetQueue = vi.mocked(apiClient.getReviewQueue);
    mockGetQueue.mockResolvedValue([]);

    render(<ReviewerQueue />);

    await waitFor(() => {
      expect(screen.getByText('هیچ سندی در انتظار داوری شما نیست')).toBeInTheDocument();
    });
  });

  it('should show error on API failure', async () => {
    const mockGetQueue = vi.mocked(apiClient.getReviewQueue);
    mockGetQueue.mockRejectedValue(new Error('خطای سرور'));

    render(<ReviewerQueue />);

    await waitFor(() => {
      expect(screen.getByText('خطای سرور')).toBeInTheDocument();
    });
  });
});

// ============================================================================
// 6. TextEnhancementPreviewModal component
// ============================================================================

describe('TextEnhancementPreviewModal component', () => {
  it('should NOT render when isOpen is false', () => {
    const { container } = render(
      <TextEnhancementPreviewModal
        preview={null}
        duplicateCheck={null}
        isOpen={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isSubmitting={false}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render title when isOpen is true', () => {
    render(
      <TextEnhancementPreviewModal
        preview={null}
        duplicateCheck={null}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isSubmitting={false}
      />
    );
    expect(screen.getByText('پیش‌نمایش ارتقای کیفیت و تحلیل متن')).toBeInTheDocument();
  });

  it('should show duplicate warning when duplicateCheck.is_duplicate is true', () => {
    render(
      <TextEnhancementPreviewModal
        preview={null}
        duplicateCheck={{
          is_duplicate: true,
          level: 'exact',
          similarity: 1.0,
          message: 'متن تکراری است',
          overlapping_submissions: [],
          related_versions: [],
        }}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isSubmitting={false}
      />
    );
    expect(screen.getByText('هشدار تشابه یا تکرار سند!')).toBeInTheDocument();
    expect(screen.getByText('متن تکراری است')).toBeInTheDocument();
  });

  it('should show quality score when preview is provided', () => {
    render(
      <TextEnhancementPreviewModal
        preview={{
          original_length: 100,
          enhanced_length: 105,
          changes_count: 3,
          changes: [],
          metadata: {
            article_count: 5,
            note_count: 2,
            clause_count: 1,
            keywords: ['ماده'],
            references: ['قانون'],
            legal_entities: ['مجلس'],
            risk_level: 'LOW',
          },
          quality_score: 75,
          fingerprint: 'a'.repeat(64),
          content_hash: 'b'.repeat(64),
          suggested_improvements: [],
        }}
        duplicateCheck={null}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isSubmitting={false}
      />
    );
    // quality_score.toFixed(0) renders "75" (Latin digit)
    expect(screen.getByText(/75/)).toBeInTheDocument();
    // article_count renders as "5" (Latin digit, not Persian "۵")
    expect(screen.getByText(/5 ماده/)).toBeInTheDocument();
  });

  it('should call onConfirm when confirm button is clicked', async () => {
    const onConfirm = vi.fn();
    render(
      <TextEnhancementPreviewModal
        preview={null}
        duplicateCheck={null}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={onConfirm}
        isSubmitting={false}
      />
    );

    fireEvent.click(screen.getByText('تأیید و ارسال مشارکت'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('should show submitting text when isSubmitting is true', () => {
    render(
      <TextEnhancementPreviewModal
        preview={null}
        duplicateCheck={null}
        isOpen={true}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        isSubmitting={true}
      />
    );
    expect(screen.getByText('در حال ثبت نهایی...')).toBeInTheDocument();
  });
});

// ============================================================================
// 7. LoginModal component
// ============================================================================

describe('LoginModal component', () => {
  it('should NOT render when isOpen is false', () => {
    const { container } = render(
      <LoginModal isOpen={false} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should render login form when isOpen is true', () => {
    render(
      <LoginModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(screen.getByText('ورود به حساب کاربری')).toBeInTheDocument();
  });

  it('should toggle to register mode', async () => {
    render(
      <LoginModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );

    fireEvent.click(screen.getByText('ایجاد حساب مشارکت‌کننده'));
    expect(screen.getByText('ثبت‌نام پژوهشگر جدید')).toBeInTheDocument();
  });

  it('should have email and password inputs', () => {
    render(
      <LoginModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    );
    expect(screen.getByPlaceholderText('contributor@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  });
});

// ============================================================================
// 8. Cross-component integration: Header + UserProfile
// ============================================================================

describe('Header + UserProfile integration', () => {
  it('should render user info correctly with total_credits field', () => {
    const user: UserProfile = {
      id: 'user-1',
      email: 'contributor@example.com',
      full_name: 'علی محمدی',
      role: 'contributor',
      total_credits: 150,
    };

    render(
      <Header
        user={user}
        activeTab="submit"
        setActiveTab={vi.fn()}
        onLoginClick={vi.fn()}
        onLogoutClick={vi.fn()}
      />
    );

    // Email should be displayed
    expect(screen.getByText('contributor@example.com')).toBeInTheDocument();
    // The component should display credits — it must use total_credits, not mcc_credits
    // If the component uses mcc_credits, it would render "undefined MCC" instead of "150 MCC"
    expect(screen.getByText(/150/)).toBeInTheDocument();
  });
});
