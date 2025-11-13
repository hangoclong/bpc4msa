/**
 * PRESENTATION LAYER - Architecture Status Panel
 * Real-time health status for all architectures
 */

'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Server, Database, Network } from 'lucide-react';
import { useMetrics } from '../hooks/useMetrics';
import { ArchitectureType } from '../../domain/entities/Experiment';

interface ArchitectureInfo {
  name: string;
  type: ArchitectureType;
  port: number;
  color: string;
  description: string;
}

const architectures: ArchitectureInfo[] = [
  {
    name: 'BPC4MSA',
    type: 'bpc4msa',
    port: 8000,
    color: 'blue',
    description: 'Event-Driven Microservices'
  },
  {
    name: 'Synchronous',
    type: 'synchronous',
    port: 8001,
    color: 'green',
    description: 'Traditional SOA'
  },
  {
    name: 'Monolithic',
    type: 'monolithic',
    port: 8002,
    color: 'purple',
    description: 'All-in-One BPMS'
  }
];

export function ArchitectureStatus() {
  const { checkHealth } = useMetrics();
  const [healthStatus, setHealthStatus] = useState<Record<string, boolean | null>>({});
  const [checking, setChecking] = useState(false);

  const checkAllHealth = async () => {
    setChecking(true);
    const results: Record<string, boolean> = {};

    for (const arch of architectures) {
      try {
        const healthy = await checkHealth(arch.type);
        results[arch.type] = healthy;
      } catch {
        results[arch.type] = false;
      }
    }

    setHealthStatus(results);
    setChecking(false);
  };

  useEffect(() => {
    checkAllHealth();
    const interval = setInterval(checkAllHealth, 10000); // Check every 10s
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getStatusIcon = (status: boolean | null) => {
    if (status === null) return <Loader2 className="w-5 h-5 animate-spin text-gray-400" />;
    if (status) return <CheckCircle2 className="w-5 h-5 text-green-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const getStatusText = (status: boolean | null) => {
    if (status === null) return 'Checking...';
    if (status) return 'Healthy';
    return 'Offline';
  };

  const getColorClasses = (color: string, status: boolean | null) => {
    if (!status) return 'bg-gray-50 border-gray-200';

    const colors: Record<string, string> = {
      blue: 'bg-blue-50 border-blue-200',
      green: 'bg-green-50 border-green-200',
      purple: 'bg-purple-50 border-purple-200'
    };
    return colors[color] || 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Architecture Status</h2>
        <button
          onClick={checkAllHealth}
          disabled={checking}
          className="text-sm text-blue-600 hover:text-blue-700 disabled:text-gray-400 flex items-center gap-1"
        >
          {checking ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Checking...
            </>
          ) : (
            'Refresh'
          )}
        </button>
      </div>

      <div className="space-y-3">
        {architectures.map((arch) => {
          const status = healthStatus[arch.type];
          return (
            <div
              key={arch.type}
              className={`rounded-lg border p-4 transition-all ${getColorClasses(arch.color, status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    <Server className="w-6 h-6 text-gray-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{arch.name}</h3>
                      <span className="text-xs px-2 py-0.5 bg-white border rounded-full text-gray-600">
                        Port {arch.port}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{arch.description}</p>

                    {status && (
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-600">
                        <div className="flex items-center gap-1">
                          <Database className="w-3 h-3" />
                          <span>PostgreSQL</span>
                        </div>
                        {arch.type === 'bpc4msa' && (
                          <div className="flex items-center gap-1">
                            <Network className="w-3 h-3" />
                            <span>Kafka</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusIcon(status)}
                  <span className="text-sm font-medium text-gray-700">
                    {getStatusText(status)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>Tip:</strong> Start an architecture using{' '}
          <code className="px-1 py-0.5 bg-white rounded text-xs">docker-compose up -d</code>
        </p>
      </div>
    </div>
  );
}
