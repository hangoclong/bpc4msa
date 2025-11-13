/**
 * DOMAIN LAYER - Event Stream Port
 * Interface for real-time event streaming
 */

import { ComplianceEvent } from '../entities/Event';

export type EventCallback = (event: ComplianceEvent) => void;

export interface IEventStream {
  /**
   * Connect to event stream
   */
  connect(): Promise<void>;

  /**
   * Disconnect from event stream
   */
  disconnect(): Promise<void>;

  /**
   * Subscribe to events
   */
  subscribe(callback: EventCallback): void;

  /**
   * Unsubscribe from events
   */
  unsubscribe(callback: EventCallback): void;

  /**
   * Check if connected
   */
  isConnected(): boolean;
}
