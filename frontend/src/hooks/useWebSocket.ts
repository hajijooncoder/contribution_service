import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../api/client';

export interface WebSocketNotification {
  type: string;
  submission_id?: string;
  title?: string;
  new_status?: string;
  decision?: string;
  message: string;
  timestamp?: string;
}

export function useWebSocket(userId: string | null) {
  const [notifications, setNotifications] = useState<WebSocketNotification[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [latestNotification, setLatestNotification] = useState<WebSocketNotification | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const connect = useCallback(() => {
    if (!userId || typeof window === 'undefined') return;

    const token = apiClient.getToken();
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/${userId}${token ? `?token=${encodeURIComponent(token)}` : ''}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketNotification;
          if (data.type !== 'connection_established') {
            setLatestNotification(data);
            setNotifications((prev) => [data, ...prev]);
          }
        } catch {
          // ignore non-json
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      setIsConnected(false);
    }
  }, [userId]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const clearLatest = () => setLatestNotification(null);

  return { notifications, isConnected, latestNotification, clearLatest };
}
