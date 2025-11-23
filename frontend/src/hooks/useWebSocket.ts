import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url: string;
  shouldConnect?: boolean;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  protocols?: string | string[];
}

interface UseWebSocketReturn {
  socket: WebSocket | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: Event | null;
  sendMessage: (message: any) => void;
  close: (code?: number, reason?: string) => void;
  reconnect: () => void;
}

export const useWebSocket = ({
  url,
  shouldConnect = true,
  onOpen,
  onClose,
  onError,
  onMessage,
  protocols
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Event | null>(null);

  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!shouldConnect || isConnecting) return;

    setIsConnecting(true);
    setError(null);

    try {
      const wsUrl = url.startsWith('ws') ? url : `ws://${window.location.host}${url}`;
      const newSocket = new WebSocket(wsUrl, protocols);

      newSocket.onopen = (event) => {
        console.log('WebSocket connected:', url);
        setSocket(newSocket);
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectAttempts.current = 0;
        onOpen?.(event);
      };

      newSocket.onclose = (event) => {
        console.log('WebSocket disconnected:', url, event.code, event.reason);
        setSocket(null);
        setIsConnected(false);
        setIsConnecting(false);

        // Auto-reconnect logic
        if (shouldConnect && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${reconnectAttempts.current})`);
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }

        onClose?.(event);
      };

      newSocket.onerror = (event) => {
        console.error('WebSocket error:', url, event);
        setError(event);
        setIsConnecting(false);
        onError?.(event);
      };

      newSocket.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (err) {
          console.warn('Failed to parse WebSocket message:', event.data, err);
        }
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setIsConnecting(false);
      setError(err as Event);
    }
  }, [url, shouldConnect, onOpen, onClose, onError, onMessage, protocols]);

  const close = useCallback((code?: number, reason?: string) => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    if (socket) {
      socket.close(code, reason);
    }
  }, [socket]);

  const sendMessage = useCallback((message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try {
        const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
        socket.send(messageStr);
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  }, [socket]);

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    if (socket) {
      socket.close();
    } else {
      connect();
    }
  }, [socket, connect]);

  useEffect(() => {
    if (shouldConnect && !socket && !isConnecting) {
      connect();
    } else if (!shouldConnect && socket) {
      socket.close();
    }

    return () => {
      if (socket) {
        socket.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [shouldConnect, connect]);

  return {
    socket,
    isConnected,
    isConnecting,
    error,
    sendMessage,
    close,
    reconnect
  };
};

// Specialized hooks for common use cases
export const useChatWebSocket = (chatId: string, userId?: number) => {
  const token = localStorage.getItem('auth_token');
  const url = `/ws/chat/${chatId}?token=${token}`;

  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  const { socket, isConnected, sendMessage, ...rest } = useWebSocket({
    url,
    shouldConnect: !!chatId,
    onMessage: (message) => {
      if (message.type === 'chat_message') {
        setMessages(prev => [...prev, message]);
      }
    }
  });

  return {
    socket,
    isConnected,
    messages,
    sendMessage: (content: string) => {
      sendMessage({
        content,
        timestamp: new Date().toISOString(),
        message_type: 'text'
      });
    },
    ...rest
  };
};

export const useNotificationWebSocket = (userId: number) => {
  const token = localStorage.getItem('auth_token');
  const url = `/ws/notifications/${userId}?token=${token}`;

  const [notifications, setNotifications] = useState<WebSocketMessage[]>([]);

  const { socket, isConnected, sendMessage, ...rest } = useWebSocket({
    url,
    shouldConnect: !!userId,
    onMessage: (message) => {
      if (message.type === 'notification' || message.type === 'system_message') {
        setNotifications(prev => [...prev, message]);
      }
    }
  });

  return {
    socket,
    isConnected,
    notifications,
    sendMessage,
    ...rest
  };
};

export const useGlobalWebSocket = () => {
  const token = localStorage.getItem('auth_token');
  const url = `/ws/global?token=${token}`;

  const [globalMessages, setGlobalMessages] = useState<WebSocketMessage[]>([]);

  const { socket, isConnected, sendMessage, ...rest } = useWebSocket({
    url,
    shouldConnect: true,
    onMessage: (message) => {
      setGlobalMessages(prev => [...prev, message]);
    }
  });

  return {
    socket,
    isConnected,
    globalMessages,
    sendMessage,
    ...rest
  };
};
