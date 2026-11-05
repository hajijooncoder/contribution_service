import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AdminPanel } from './AdminPanel';
import { apiClient } from '../api/client';
import { UserProfile } from '../types';

vi.mock('../api/client', () => ({
  apiClient: {
    getAdminUsers: vi.fn(),
    toggleUserActivation: vi.fn(),
    updateUserRole: vi.fn(),
    getAdminStats: vi.fn(),
    getAdminExportOverview: vi.fn(),
    downloadDatasetJsonl: vi.fn(),
  },
}));

describe('AdminPanel Component', () => {
  const adminUser: UserProfile = {
    id: 'admin-1',
    email: 'admin@mahoun.local',
    full_name: 'مدیر کل سیستم',
    role: 'admin',
    total_credits: 500,
  };

  const contributorUser: UserProfile = {
    id: 'user-1',
    email: 'user@test.ir',
    full_name: 'کاربر مشارکت‌کننده',
    role: 'contributor',
    total_credits: 20,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('blocks non-admin users with access denied message', () => {
    render(<AdminPanel currentUser={contributorUser} />);
    expect(screen.getByText('دسترسی غیرمجاز')).toBeInTheDocument();
  });

  it('renders admin console and loads user list for admin', async () => {
    vi.mocked(apiClient.getAdminUsers).mockResolvedValue({
      users: [
        {
          id: 'user-100',
          email: 'lawyer@test.ir',
          full_name: 'دکتر ستوده',
          role: 'contributor',
          is_active: true,
          total_credits: 80,
          created_at: '2026-11-01T10:00:00Z',
        },
      ],
      total: 1,
    });

    render(<AdminPanel currentUser={adminUser} />);

    expect(screen.getByText('میزکار مدیریت و درگاه استخراج داده')).toBeInTheDocument();
    expect(screen.getByText('مدیریت کاربران')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('دکتر ستوده')).toBeInTheDocument();
      expect(screen.getByText('lawyer@test.ir')).toBeInTheDocument();
      expect(screen.getByText('۸۰ MCC')).toBeInTheDocument();
    });
  });

  it('navigates to Owner Export Gateway and displays air-gap isolation badge', async () => {
    vi.mocked(apiClient.getAdminUsers).mockResolvedValue({ users: [], total: 0 });
    vi.mocked(apiClient.getAdminExportOverview).mockResolvedValue({
      total_export_ready: 25,
      schema_version: 'mahoun-1.0',
      isolation_verified: true,
      export_token_configured: true,
    });

    render(<AdminPanel currentUser={adminUser} />);

    const exportTabBtn = screen.getByText('درگاه مالک (Export)');
    fireEvent.click(exportTabBtn);

    await waitFor(() => {
      expect(screen.getByText(/درگاه استخراج ایزوله مالک/)).toBeInTheDocument();
      expect(screen.getByText('✓ ISOLATION VERIFIED')).toBeInTheDocument();
      expect(screen.getByText('۲۵ سند')).toBeInTheDocument();
      expect(screen.getByText('mahoun-1.0')).toBeInTheDocument();
    });
  });
});
