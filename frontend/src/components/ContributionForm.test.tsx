import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ContributionForm } from './ContributionForm';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    validateUrl: vi.fn(),
    submitEnhanced: vi.fn(),
  },
}));

describe('ContributionForm Real-time URL Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('validates URL in real time and displays verified authority badge', async () => {
    vi.mocked(apiClient.validateUrl).mockResolvedValue({
      valid: true,
      authority: 'روزنامه رسمی جمهوری اسلامی ایران',
      error: null,
    });

    const onSuccess = vi.fn();
    render(<ContributionForm onSuccess={onSuccess} />);

    const urlInput = screen.getByPlaceholderText(/https:\/\/rrk\.ir\/laws\/show\//);
    fireEvent.change(urlInput, { target: { value: 'https://rrk.ir/laws/show/123' } });

    await waitFor(() => {
      expect(apiClient.validateUrl).toHaveBeenCalledWith('https://rrk.ir/laws/show/123');
    });

    await waitFor(() => {
      expect(screen.getByText(/مرجع رسمی تایید شد:/)).toBeInTheDocument();
      expect(screen.getByText('روزنامه رسمی جمهوری اسلامی ایران')).toBeInTheDocument();
    });
  });

  it('displays warning when URL domain is unauthorized', async () => {
    vi.mocked(apiClient.validateUrl).mockResolvedValue({
      valid: false,
      authority: null,
      error: 'مرجع نامعتبر است. تنها مراجع رسمی کشور مجاز هستند.',
    });

    const onSuccess = vi.fn();
    render(<ContributionForm onSuccess={onSuccess} />);

    const urlInput = screen.getByPlaceholderText(/https:\/\/rrk\.ir\/laws\/show\//);
    fireEvent.change(urlInput, { target: { value: 'https://unauthorized-domain.com/doc/1' } });

    await waitFor(() => {
      expect(screen.getByText('مرجع نامعتبر است. تنها مراجع رسمی کشور مجاز هستند.')).toBeInTheDocument();
    });
  });

  it('shows warning when legal text is shorter than 20 characters', () => {
    const onSuccess = vi.fn();
    render(<ContributionForm onSuccess={onSuccess} />);

    const textarea = screen.getByPlaceholderText(/متن کامل ماده، تبصره‌ها و مفاد قانونی را در این قسمت وارد کنید\.\.\./);
    fireEvent.change(textarea, { target: { value: 'متن کوتاه' } });

    expect(screen.getByText('متن حقوقی باید حداقل ۲۰ نویسه داشته باشد.')).toBeInTheDocument();
  });
});
