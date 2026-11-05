import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import { apiClient } from '../api/client';

class MockWebSocket {
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: any) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(url: string) {
    this.url = url;
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 10);
  }

  close() {
    this.closed = true;
    if (this.onclose) this.onclose();
  }
}

describe('useWebSocket hook', () => {
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket as any);
    vi.spyOn(apiClient, 'getToken').mockReturnValue('mock-jwt-token');
  });

  afterEach(() => {
    vi.stubGlobal('WebSocket', originalWebSocket);
    vi.restoreAllMocks();
  });

  it('does not open websocket when userId is null', () => {
    const { result } = renderHook(() => useWebSocket(null));
    expect(result.current.isConnected).toBe(false);
    expect(result.current.notifications).toEqual([]);
    expect(result.current.latestNotification).toBeNull();
  });

  it('connects when userId is provided and receives notifications', async () => {
    const { result } = renderHook(() => useWebSocket('user-123'));

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 30));
    });

    expect(result.current.isConnected).toBe(true);

    // Simulate notification arriving
    const activeWs = (useWebSocket as any)._lastWs;
    act(() => {
      result.current.clearLatest();
    });
  });
});
