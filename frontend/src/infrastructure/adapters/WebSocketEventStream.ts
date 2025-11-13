/**
 * INFRASTRUCTURE LAYER - Adapter
 * WebSocket implementation of IEventStream
 */

import { ComplianceEvent, EventType, Violation } from '../../domain/entities/Event';
import { IEventStream, EventCallback } from '../../domain/ports/IEventStream';

interface EventData {
  event_type: EventType;
  timestamp: string;
  transaction_id?: string;
  violations?: Violation[];
  [key: string]: unknown;
}

export class WebSocketEventStream implements IEventStream {
  private ws: WebSocket | null = null;
  private callbacks: Set<EventCallback> = new Set();
  private reconnectInterval = 5000;
  private reconnectTimer?: NodeJS.Timeout;

  constructor(private url: string = 'ws://localhost:8765') {}

  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = undefined;
          }
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const rawData = JSON.parse(event.data);

            // Handle nested event structure from socket-service
            const eventData = rawData.event || rawData;

            const complianceEvent = new ComplianceEvent(
              eventData.event_type || 'unknown',
              new Date(eventData.timestamp || rawData.timestamp || new Date()),
              eventData.transaction_id,
              eventData.violations,
              eventData,
              eventData.architecture
            );

            // Notify all subscribers
            this.callbacks.forEach((callback) => callback(complianceEvent));
          } catch (error) {
            console.error('Error processing WebSocket message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.ws = null;

          // Auto-reconnect
          this.reconnectTimer = setTimeout(() => {
            console.log('Attempting to reconnect...');
            this.connect().catch(console.error);
          }, this.reconnectInterval);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  async disconnect(): Promise<void> {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(callback: EventCallback): void {
    this.callbacks.add(callback);
  }

  unsubscribe(callback: EventCallback): void {
    this.callbacks.delete(callback);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
