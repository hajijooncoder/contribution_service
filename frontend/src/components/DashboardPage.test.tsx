import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardPage } from './DashboardPage';
import { apiClient } from '../api/client';
import type { UserProfile } from '../types';

vi.mock('../api/client', () => ({
  apiClient: {
    getToken: vi.fn(),
    getStats: vi.fn(),
    getRecentActivity: vi.fn(),
  },
}));

describe('DashboardPage', () => {
  const mockUser: UserProfile = {
    id: 'user-1',
    email: 'lawyer@test.ir',
    full_name: 'دکتر علوی',
    role: 'contributor',
    total_credits: 150,
  };

  const mockStats = {
    total_submissions: 42,
    pending_submissions: 10,
    accepted_submissions: 28,
    rejected_submissions: 4,
    contribution_credits: 150,
  };

  const mockActivities = [
    {
      id: 'sub-1',
      title: 'ماده ۲ قانون تجارت',
      status: 'accepted' as const,
      date: '2026-11-04T12:00:00Z',
      awarded_credits: 20,
    },
    {
      id: 'sub-2',
      title: 'ماده ۱۰ قانون مدنی',
      status: 'submitted' as const,
      date: '2026-11-05T08:00:00Z',
      awarded_credits: 0,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders stats and welcome message for logged in user', async () => {
    vi.mocked(apiClient.getToken).mockReturnValue('valid-token');
    vi.mocked(apiClient.getStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getRecentActivity).mockResolvedValue(mockActivities);

    const onNavigate = vi.fn();
    const onLoginClick = vi.fn();

    render(
      <DashboardPage
        user={mockUser}
        onNavigate={onNavigate}
        onLoginClick={onLoginClick}
      />
    );

    // Welcome title
    expect(screen.getByText(/سلام، دکتر علوی/)).toBeInTheDocument();

    // Stats cards
    await waitFor(() => {
      expect(screen.getByText(/۴۲/)).toBeInTheDocument();
      expect(screen.getByText(/۲۸/)).toBeInTheDocument();
      expect(screen.getByText(/۱۵۰/)).toBeInTheDocument();
    });

    // Activities
    expect(screen.getByText('ماده ۲ قانون تجارت')).toBeInTheDocument();
    expect(screen.getByText('ماده ۱۰ قانون مدنی')).toBeInTheDocument();
  });

  it('triggers onNavigate when clicking quick action button', async () => {
    vi.mocked(apiClient.getToken).mockReturnValue('valid-token');
    vi.mocked(apiClient.getStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getRecentActivity).mockResolvedValue([]);

    const onNavigate = vi.fn();
    const onLoginClick = vi.fn();

    render(
      <DashboardPage
        user={mockUser}
        onNavigate={onNavigate}
        onLoginClick={onLoginClick}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('ارسال مشارکت حقوقی جدید')).toBeInTheDocument();
    });

    const submitBtn = screen.getByText('ارسال مشارکت حقوقی جدید');
    fireEvent.click(submitBtn);
    expect(onNavigate).toHaveBeenCalledWith('submit');
  });

  it('renders guest state when user is null', async () => {
    vi.mocked(apiClient.getToken).mockReturnValue(null);
    vi.mocked(apiClient.getStats).mockResolvedValue(mockStats);
    vi.mocked(apiClient.getRecentActivity).mockResolvedValue([]);

    const onNavigate = vi.fn();
    const onLoginClick = vi.fn();

    render(
      <DashboardPage
        user={null}
        onNavigate={onNavigate}
        onLoginClick={onLoginClick}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('داشبورد کاربری پلتفرم مشارکت')).toBeInTheDocument();
    });
    expect(screen.getByText('جهت مشاهده سوابق، وارد شوید')).toBeInTheDocument();

    const loginBtn = screen.getAllByText('ورود به حساب کاربری')[0];
    fireEvent.click(loginBtn);
    expect(onLoginClick).toHaveBeenCalled();
  });
});
