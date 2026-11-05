import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ContributionForm } from './ContributionForm';
import { AdminPanel } from './AdminPanel';
import { apiClient } from '../api/client';
import { UserProfile } from '../types';

describe('Frontend Hardcore Adversarial & Boundary Test Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('safely escapes XSS injection vectors in legal text and title fields', () => {
    const onSuccess = vi.fn();
    render(<ContributionForm onSuccess={onSuccess} />);

    const xssPayload = '<script>alert("PWNED_DOM")</script><img src=x onerror=alert(1)>';
    
    // Inject into document title
    const titleInput = screen.getByPlaceholderText(/قانون شوراهای حل اختلاف/);
    fireEvent.change(titleInput, { target: { value: xssPayload } });

    // Inject into legal raw text
    const textarea = screen.getByPlaceholderText(/متن کامل ماده، تبصره‌ها و مفاد قانونی را در این قسمت وارد کنید\.\.\./);
    fireEvent.change(textarea, { target: { value: xssPayload.repeat(2) } });

    // Assert that the input values contain the raw string safely without HTML rendering or execution
    expect(titleInput).toHaveValue(xssPayload);
    expect(textarea).toHaveValue(xssPayload.repeat(2));
    expect(document.querySelector('script')).toBeNull();
  });

  it('cancels in-flight requests and debounces rapid-fire URL flooding', async () => {
    const validateMock = vi.spyOn(apiClient, 'validateUrl').mockResolvedValue({
      valid: true,
      authority: 'مرکز پژوهش‌های مجلس شورای اسلامی',
      error: null,
    });

    render(<ContributionForm onSuccess={vi.fn()} />);
    const urlInput = screen.getByPlaceholderText(/https:\/\/rrk\.ir\/laws\/show\//);

    // Rapidly change URL 10 times in a burst
    for (let i = 0; i < 10; i++) {
      fireEvent.change(urlInput, { target: { value: `https://rc.majlis.ir/law/burst_${i}` } });
    }

    // Wait for the debounce timer (450ms) to settle
    await waitFor(() => {
      // Despite 10 rapid keystrokes, validateUrl should only be called for the final settled value!
      expect(validateMock).toHaveBeenCalledTimes(1);
      expect(validateMock).toHaveBeenCalledWith('https://rc.majlis.ir/law/burst_9');
    });
  });

  it('enforces character boundary warning when text exceeds maximum threshold', () => {
    render(<ContributionForm onSuccess={vi.fn()} />);

    const textarea = screen.getByPlaceholderText(/متن کامل ماده، تبصره‌ها و مفاد قانونی را در این قسمت وارد کنید\.\.\./);
    
    // 10,001 characters payload
    const oversizedText = 'الف'.repeat(10001);
    fireEvent.change(textarea, { target: { value: oversizedText } });

    // Counter shows over-limit state with warning message
    expect(screen.getByText('متن حقوقی نباید بیشتر از ۱۰٬۰۰۰ نویسه باشد.')).toBeInTheDocument();
  });

  it('strictly blocks non-admin users from accessing AdminPanel (Access Control)', () => {
    const contributorUser: UserProfile = {
      id: 'user-contributor-1',
      email: 'contributor@example.com',
      role: 'contributor',
      total_credits: 100,
    };

    render(<AdminPanel currentUser={contributorUser} />);

    expect(screen.getByText('دسترسی غیرمجاز')).toBeInTheDocument();
    expect(screen.getByText(/تنها مدیران ارشد سیستم دارای مجوز مشاهده/)).toBeInTheDocument();
  });

  it('handles server network errors gracefully in AdminPanel for authorized admin', async () => {
    const adminUser: UserProfile = {
      id: 'admin-1',
      email: 'admin@mahoun.ir',
      role: 'admin',
      total_credits: 500,
    };

    vi.spyOn(apiClient, 'getAdminUsers').mockRejectedValue(new Error('خطای بحرانی سرور دیتابیس'));
    vi.spyOn(apiClient, 'getAdminStats').mockResolvedValue({
      total_users: 10,
      total_submissions: 5,
      pending_reviews: 2,
      accepted_submissions: 3,
      rejected_submissions: 0,
      total_credits_awarded: 50,
      quarantine_files_count: 5,
    });
    vi.spyOn(apiClient, 'getAdminExportOverview').mockResolvedValue({
      total_export_ready: 3,
      schema_version: 'mahoun-1.0',
      isolation_verified: true,
      export_token_configured: true,
    });

    render(<AdminPanel currentUser={adminUser} />);

    await waitFor(() => {
      expect(screen.getByText('خطای بحرانی سرور دیتابیس')).toBeInTheDocument();
    });
  });
});
