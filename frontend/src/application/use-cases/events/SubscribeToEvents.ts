/**
 * APPLICATION LAYER - Use Case
 * Subscribe to real-time events
 */

import { IEventStream, EventCallback } from '../../../domain/ports/IEventStream';

export class SubscribeToEvents {
  constructor(private eventStream: IEventStream) {}

  async execute(callback: EventCallback): Promise<void> {
    // Connect if not already connected
    if (!this.eventStream.isConnected()) {
      await this.eventStream.connect();
    }

    // Subscribe to events
    this.eventStream.subscribe(callback);
  }

  async unsubscribe(callback: EventCallback): Promise<void> {
    this.eventStream.unsubscribe(callback);
  }
}
