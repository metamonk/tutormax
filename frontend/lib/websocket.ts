/**
 * WebSocket Service for Real-Time Dashboard Updates
 */

import { WebSocketMessage } from '@/lib/types';

export type MessageHandler = (message: WebSocketMessage) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number = 5000;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private messageHandlers: Set<MessageHandler> = new Set();
  private reconnectTimeout: NodeJS.Timeout | null = null;

  constructor(url: string) {
    this.url = url;
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    // WebSocket is only available in the browser
    if (typeof window === 'undefined') {
      console.warn('WebSocket can only be used in the browser');
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyConnectionChange(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.notifyHandlers(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.notifyConnectionChange(false);
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.attemptReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Subscribe to WebSocket messages
   */
  subscribe(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.delete(handler);
    };
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Attempt to reconnect to WebSocket server
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, this.reconnectInterval);
  }

  /**
   * Notify all message handlers
   */
  private notifyHandlers(message: WebSocketMessage): void {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  /**
   * Notify connection state change
   */
  private notifyConnectionChange(connected: boolean): void {
    const message: WebSocketMessage = {
      type: 'analytics_update',
      data: { connected } as any,
      timestamp: new Date().toISOString(),
    };
    this.notifyHandlers(message);
  }
}

// Singleton instance
let wsService: WebSocketService | null = null;

/**
 * Get or create WebSocket service instance
 */
export function getWebSocketService(url?: string): WebSocketService {
  if (!wsService && url) {
    wsService = new WebSocketService(url);
  }

  if (!wsService) {
    throw new Error('WebSocket service not initialized. Provide URL on first call.');
  }

  return wsService;
}
