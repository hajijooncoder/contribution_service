import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ContributionHistory } from './ContributionHistory';
import { apiClient } from '../api/client';

describe('ContributionHistory Search and Filter integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders search input, filter controls, and triggers searchContributions', async () => {
    vi.spyOn(apiClient, 'getMyHistory').mockResolvedValue([]);
    const searchSpy = vi.spyOn(apiClient, 'searchContributions').mockResolvedValue({
      items: [
        {
          id: 'sub-search-100',
          date: '2026-11-05',
          legal_document_name: 'قانون تجارت الکترونیکی مصوب ۱۳۸۲',
          source_title: 'روزنامه رسمی',
          document_type: 'law',
          issuing_authority: 'مجلس شورای اسلامی',
          status: 'accepted',
          quality_score: 95,
          awarded_credits: 50,
          submitter_id: 'user-1'
        }
      ],
      total: 1,
      skip: 0,
      limit: 20
    });

    render(<ContributionHistory />);

    await waitFor(() => {
      expect(screen.getByText('تاریخچه مشارکت‌های حقوقی شما')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('جستجو در عنوان، متن قانون یا مرجع تصویب...');
    fireEvent.change(searchInput, { target: { value: 'تجارت' } });

    const filterButton = screen.getByRole('button', { name: /اعمال فیلتر/ });
    fireEvent.click(filterButton);

    await waitFor(() => {
      expect(searchSpy).toHaveBeenCalledWith({
        q: 'تجارت',
        document_type: undefined,
        status_filter: undefined,
        issuing_authority: undefined
      });
      expect(screen.getByText('قانون تجارت الکترونیکی مصوب ۱۳۸۲')).toBeInTheDocument();
      expect(screen.getByText(/نتایج فیلتر:/)).toBeInTheDocument();
      expect(screen.getByText('+50 اعتبار')).toBeInTheDocument();
    });
  });

  it('clears filters when clear button is clicked', async () => {
    vi.spyOn(apiClient, 'getMyHistory').mockResolvedValue([]);
    vi.spyOn(apiClient, 'searchContributions').mockResolvedValue({
      items: [],
      total: 0,
      skip: 0,
      limit: 20
    });

    render(<ContributionHistory />);

    const searchInput = screen.getByPlaceholderText('جستجو در عنوان، متن قانون یا مرجع تصویب...');
    fireEvent.change(searchInput, { target: { value: 'نامعتبر' } });

    const filterButton = screen.getByRole('button', { name: /اعمال فیلتر/ });
    fireEvent.click(filterButton);

    await waitFor(() => {
      expect(screen.getByText('موردی مطابق با فیلترهای جستجو یافت نشد')).toBeInTheDocument();
    });

    const clearButton = screen.getByText('پاک کردن فیلترها');
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.getByText('هنوز مشارکتی ثبت نکرده‌اید')).toBeInTheDocument();
    });
  });
});
