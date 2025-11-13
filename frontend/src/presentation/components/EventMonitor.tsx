/**
 * PRESENTATION LAYER - Component
 * Real-time event monitoring
 */

'use client';

import { useEventStream } from '../hooks/useEventStream';

export function EventMonitor() {
  const { events, connected, error, clearEvents } = useEventStream();

  const getArchColor = (arch?: string) => {
    switch (arch) {
      case 'bpc4msa': return 'bg-blue-100 text-blue-800';
      case 'synchronous': return 'bg-green-100 text-green-800';
      case 'monolithic': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Live Events</h2>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                connected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <button
            onClick={clearEvents}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-sm">
          {error}
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-2">No events yet. Waiting for transactions...</p>
            <p className="text-xs text-gray-400">
              WebSocket: ws://localhost:8765 | Send transactions using Quick Actions below
            </p>
          </div>
        ) : (
          events.map((event, idx) => (
            <div
              key={idx}
              className={`p-3 rounded border ${
                event.hasViolations()
                  ? 'bg-red-50 border-red-200'
                  : 'bg-green-50 border-green-200'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{event.eventType}</span>
                  {event.architecture && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getArchColor(event.architecture)}`}>
                      {event.architecture}
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-600">
                  {event.timestamp.toLocaleString()}
                </span>
              </div>

              {event.transactionId && (
                <p className="text-xs text-gray-600 font-mono">
                  {event.transactionId}
                </p>
              )}

              {event.hasViolations() && (
                <div className="mt-2 space-y-1">
                  {event.violations?.map((v, vidx) => (
                    <div key={vidx} className="text-xs text-red-700">
                      {v.rule_id}: {v.rule_description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
