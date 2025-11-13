/**
 * PRESENTATION LAYER - React Hook
 * Real-time event streaming hook with persistence
 */

import { useState, useEffect, useCallback } from 'react';
import { getContainer } from '../../infrastructure/di/container';
import { ComplianceEvent, EventType, Violation } from '../../domain/entities/Event';

const EVENTS_STORAGE_KEY = 'bpc4msa_live_events';
const MAX_EVENTS = 100;

// Type guard to validate EventType
function isValidEventType(type: string): type is EventType {
  return ['TransactionCreated', 'ComplianceChecked', 'ViolationDetected', 'AuditLogged'].includes(type);
}

// Load events from localStorage
function loadPersistedEvents(): ComplianceEvent[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = localStorage.getItem(EVENTS_STORAGE_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored);
    return parsed
      .filter((e: {eventType: string; timestamp: string; transactionId: string; violations: Violation[]; metadata: Record<string, unknown>}) =>
        isValidEventType(e.eventType)
      )
      .map((e: {eventType: string; timestamp: string; transactionId: string; violations: Violation[]; metadata: Record<string, unknown>}) => new ComplianceEvent(
        e.eventType as EventType,
        new Date(e.timestamp),
        e.transactionId,
        e.violations,
        e.metadata
      ));
  } catch {
    return [];
  }
}

// Save events to localStorage
function persistEvents(events: ComplianceEvent[]) {
  if (typeof window === 'undefined') return;

  try {
    const serialized = events.map(e => ({
      eventType: e.eventType,
      timestamp: e.timestamp.toISOString(),
      transactionId: e.transactionId,
      violations: e.violations,
      metadata: e.metadata
    }));
    localStorage.setItem(EVENTS_STORAGE_KEY, JSON.stringify(serialized));
  } catch (error) {
    console.error('Failed to persist events:', error);
  }
}

export function useEventStream() {
  const [events, setEvents] = useState<ComplianceEvent[]>(loadPersistedEvents());
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const container = getContainer();

  const handleEvent = useCallback((event: ComplianceEvent) => {
    setEvents((prev) => {
      const newEvents = [event, ...prev].slice(0, MAX_EVENTS);
      persistEvents(newEvents); // Persist to localStorage
      return newEvents;
    });
  }, []);

  useEffect(() => {
    let mounted = true;

    const connect = async () => {
      try {
        await container.subscribeToEvents.execute(handleEvent);
        if (mounted) {
          setConnected(true);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to connect');
        }
      }
    };

    connect();

    return () => {
      mounted = false;
      container.subscribeToEvents.unsubscribe(handleEvent);
    };
  }, [container, handleEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    persistEvents([]);
  }, []);

  return {
    events,
    connected,
    error,
    clearEvents,
  };
}
