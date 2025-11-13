'use client';

import { useEffect, useRef, useState } from 'react';

interface Violation {
  rule_id: string;
  rule_description: string;
  violated_field: string;
  violated_value: string | number | boolean;
}

interface EventData {
  event_type: string;
  timestamp: string;
  transaction_id?: string;
  amount?: number;
  status?: string;
  user_role?: string;
  violations?: Violation[];
  original_event?: Record<string, unknown>;
}

interface Event {
  topic: string;
  event: EventData;
  timestamp: string;
}

export default function Home() {
  const [events, setEvents] = useState<Event[]>([]);
  const [connected, setConnected] = useState(false);
  const [wsUrl] = useState('ws://localhost:8765');
  const eventsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      const data: Event = JSON.parse(event.data);
      setEvents((prev) => [...prev, data]);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [wsUrl]);

  useEffect(() => {
    // Auto-scroll to bottom when new events arrive
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const isViolation = (event: Event) => event.topic === 'violations';

  const clearEvents = () => {
    setEvents([]);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            BPC4MSA Live Audit Monitor
          </h1>
          <p className="text-gray-600 mb-4">
            Real-time monitoring of business events and compliance violations
          </p>

          {/* Status and Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    connected ? 'bg-green-500' : 'bg-red-500'
                  }`}
                />
                <span className="text-sm font-medium">
                  {connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                Events: <span className="font-semibold">{events.length}</span>
              </div>
            </div>

            <button
              onClick={clearEvents}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Clear Events
            </button>
          </div>
        </div>

        {/* Events Display */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            Event Stream
          </h2>

          <div className="h-[600px] overflow-y-auto border border-gray-200 rounded-md p-4 bg-gray-50">
            {events.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                Waiting for events...
              </div>
            ) : (
              <div className="space-y-3">
                {events.map((event, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-md border-l-4 ${
                      isViolation(event)
                        ? 'bg-red-50 border-red-500'
                        : 'bg-blue-50 border-blue-500'
                    }`}
                  >
                    {/* Event Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                            isViolation(event)
                              ? 'bg-red-600 text-white'
                              : 'bg-blue-600 text-white'
                          }`}
                        >
                          {event.event.event_type || 'Unknown'}
                        </span>
                        <span className="text-xs text-gray-600 font-mono">
                          {event.topic}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* Event Details */}
                    <div className="text-sm text-gray-700">
                      {event.event.transaction_id && (
                        <div className="mb-1">
                          <span className="font-semibold">Transaction:</span>{' '}
                          {event.event.transaction_id}
                        </div>
                      )}

                      {/* Violation Details */}
                      {isViolation(event) && event.event.violations && (
                        <div className="mt-2 space-y-1">
                          <div className="font-semibold text-red-700">
                            Violations ({event.event.violations.length}):
                          </div>
                          {event.event.violations.map((violation, vIndex) => (
                            <div
                              key={vIndex}
                              className="ml-4 text-xs bg-white p-2 rounded border border-red-200"
                            >
                              <div className="font-semibold text-red-600">
                                {violation.rule_id}: {violation.rule_description}
                              </div>
                              <div className="text-gray-600 mt-1">
                                Field: <code className="bg-gray-100 px-1 rounded">{violation.violated_field}</code> =
                                <code className="bg-gray-100 px-1 rounded ml-1">
                                  {JSON.stringify(violation.violated_value)}
                                </code>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Original Event for Violations */}
                      {isViolation(event) && event.event.original_event && (
                        <details className="mt-2">
                          <summary className="cursor-pointer text-xs text-gray-600 hover:text-gray-800">
                            Original Event
                          </summary>
                          <pre className="mt-1 text-xs bg-white p-2 rounded overflow-x-auto border">
                            {JSON.stringify(event.event.original_event, null, 2)}
                          </pre>
                        </details>
                      )}

                      {/* Business Event Details */}
                      {!isViolation(event) && (
                        <div className="text-xs text-gray-600 mt-1">
                          {event.event.amount !== undefined && (
                            <span className="mr-3">
                              Amount: <span className="font-semibold">${event.event.amount}</span>
                            </span>
                          )}
                          {event.event.status && (
                            <span className="mr-3">
                              Status: <span className="font-semibold">{event.event.status}</span>
                            </span>
                          )}
                          {event.event.user_role && (
                            <span>
                              Role: <span className="font-semibold">{event.event.user_role}</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <div ref={eventsEndRef} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
