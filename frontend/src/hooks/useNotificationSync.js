import { useState, useEffect, useRef, useCallback } from 'react';
import { showNativeBrowserNotification } from '../services/browserNotificationService';

/**
 * State machine for single active real-time notification synchronization:
 * CONNECTING_WS -> WEBSOCKET_ACTIVE -> CONNECTING_SSE -> SSE_ACTIVE -> POLLING_ACTIVE
 */
export const ConnectionState = {
  CONNECTING_WS: 'CONNECTING_WS',
  WEBSOCKET_ACTIVE: 'WEBSOCKET_ACTIVE',
  CONNECTING_SSE: 'CONNECTING_SSE',
  SSE_ACTIVE: 'SSE_ACTIVE',
  POLLING_ACTIVE: 'POLLING_ACTIVE',
};

export const useNotificationSync = (userId, onSyncTrigger) => {
  const [connectionState, setConnectionState] = useState(ConnectionState.CONNECTING_WS);
  const socketRef = useRef(null);
  const sseRef = useRef(null);
  const pollingRef = useRef(null);
  const wsReconnectTimeoutRef = useRef(null);

  const handleNotificationPayload = useCallback((payload) => {
    if (onSyncTrigger) {
      onSyncTrigger(payload);
    }

    if (payload && payload.title) {
      showNativeBrowserNotification({
        title: payload.title,
        body: payload.message || payload.body || "Time to take your medication",
        tag: `notif-${payload.notification_id || payload.reminder_id}`,
        data: payload,
      });
    }
  }, [onSyncTrigger]);

  const cleanupSSE = useCallback(() => {
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
      console.log('[NotificationSync] Terminated SSE stream.');
    }
  }, []);

  const cleanupPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      console.log('[NotificationSync] Terminated Polling interval.');
    }
  }, []);

  const startPolling = useCallback(() => {
    cleanupSSE();
    setConnectionState(ConnectionState.POLLING_ACTIVE);
    console.log('[NotificationSync] Switched to POLLING_ACTIVE mode.');

    if (!pollingRef.current) {
      pollingRef.current = setInterval(() => {
        if (onSyncTrigger) {
          onSyncTrigger({ event: 'POLL_SYNC' });
        }
      }, 15000);
    }
  }, [cleanupSSE, onSyncTrigger]);

  const startSSE = useCallback(() => {
    if (!userId) return;
    cleanupPolling();
    setConnectionState(ConnectionState.CONNECTING_SSE);

    try {
      const sseUrl = `http://localhost:8000/notifications/sse/${userId}`;
      const es = new EventSource(sseUrl);
      sseRef.current = es;

      es.onopen = () => {
        setConnectionState(ConnectionState.SSE_ACTIVE);
        console.log('[NotificationSync] Switched to SSE_ACTIVE mode.');
      };

      es.addEventListener('notification', (event) => {
        try {
          const parsed = JSON.parse(event.data);
          handleNotificationPayload(parsed.data || parsed);
        } catch (e) {
          console.warn('[NotificationSync] Error parsing SSE payload:', e);
        }
      });

      es.onerror = () => {
        console.warn('[NotificationSync] SSE connection failed. Falling back to Polling.');
        cleanupSSE();
        startPolling();
      };
    } catch (err) {
      console.warn('[NotificationSync] SSE initialization failed:', err);
      startPolling();
    }
  }, [userId, cleanupPolling, cleanupSSE, startPolling, handleNotificationPayload]);

  const connectWebSocket = useCallback(() => {
    if (!userId) return;

    cleanupSSE();
    cleanupPolling();
    setConnectionState(ConnectionState.CONNECTING_WS);

    try {
      const wsUrl = `ws://localhost:8000/ws/notifications/${userId}`;
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setConnectionState(ConnectionState.WEBSOCKET_ACTIVE);
        console.log('[NotificationSync] Switched to WEBSOCKET_ACTIVE mode.');
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          handleNotificationPayload(parsed.data || parsed);
        } catch (e) {
          console.warn('[NotificationSync] Error parsing WS payload:', e);
        }
      };

      ws.onerror = () => {
        console.warn('[NotificationSync] WebSocket error. Attempting SSE fallback.');
      };

      ws.onclose = () => {
        console.warn('[NotificationSync] WebSocket closed. Transitioning to SSE.');
        if (socketRef.current) {
          socketRef.current = null;
        }
        startSSE();

        // Attempt WebSocket reconnection periodically
        wsReconnectTimeoutRef.current = setTimeout(() => {
          console.log('[NotificationSync] Attempting WebSocket reconnection...');
          connectWebSocket();
        }, 30000);
      };
    } catch (err) {
      console.warn('[NotificationSync] WebSocket initialization failed:', err);
      startSSE();
    }
  }, [userId, cleanupSSE, cleanupPolling, startSSE, handleNotificationPayload]);

  useEffect(() => {
    if (userId) {
      connectWebSocket();
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (wsReconnectTimeoutRef.current) {
        clearTimeout(wsReconnectTimeoutRef.current);
      }
      cleanupSSE();
      cleanupPolling();
    };
  }, [userId, connectWebSocket, cleanupSSE, cleanupPolling]);

  return {
    connectionState,
    isWebSocket: connectionState === ConnectionState.WEBSOCKET_ACTIVE,
    isSSE: connectionState === ConnectionState.SSE_ACTIVE,
    isPolling: connectionState === ConnectionState.POLLING_ACTIVE,
  };
};
