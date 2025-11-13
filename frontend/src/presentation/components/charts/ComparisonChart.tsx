/**
 * PRESENTATION LAYER - Architecture Comparison Chart
 * Side-by-side comparison of all three architectures
 */

'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { SystemMetrics } from '../../../domain/entities/Metrics';

interface ComparisonChartProps {
  metrics: {
    bpc4msa?: SystemMetrics;
    synchronous?: SystemMetrics;
    monolithic?: SystemMetrics;
  };
}

const COLORS = {
  bpc4msa: '#3b82f6',
  synchronous: '#10b981',
  monolithic: '#8b5cf6'
};

export function ComparisonChart({ metrics }: ComparisonChartProps) {
  const latencyData = [
    {
      name: 'BPC4MSA',
      value: metrics.bpc4msa?.avg_latency_ms || 0,
      architecture: 'bpc4msa'
    },
    {
      name: 'Synchronous',
      value: metrics.synchronous?.avg_latency_ms || 0,
      architecture: 'synchronous'
    },
    {
      name: 'Monolithic',
      value: metrics.monolithic?.avg_latency_ms || 0,
      architecture: 'monolithic'
    }
  ];

  const throughputData = [
    {
      name: 'BPC4MSA',
      value: metrics.bpc4msa?.total_transactions || 0,
      architecture: 'bpc4msa'
    },
    {
      name: 'Synchronous',
      value: metrics.synchronous?.total_transactions || 0,
      architecture: 'synchronous'
    },
    {
      name: 'Monolithic',
      value: metrics.monolithic?.total_transactions || 0,
      architecture: 'monolithic'
    }
  ];

  const calculateComplianceRate = (metric?: SystemMetrics) => {
    if (!metric || !metric.total_transactions) {
      return 0;
    }
    const compliantTransactions = metric.total_transactions - metric.total_violations;
    return (compliantTransactions / metric.total_transactions) * 100;
  };

  const complianceData = [
    {
      name: 'BPC4MSA',
      value: calculateComplianceRate(metrics.bpc4msa),
      architecture: 'bpc4msa'
    },
    {
      name: 'Synchronous',
      value: calculateComplianceRate(metrics.synchronous),
      architecture: 'synchronous'
    },
    {
      name: 'Monolithic',
      value: calculateComplianceRate(metrics.monolithic),
      architecture: 'monolithic'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Latency Comparison */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Average Latency Comparison
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={latencyData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="name" stroke="#666" style={{ fontSize: '12px' }} />
            <YAxis
              stroke="#666"
              label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e0e0',
                borderRadius: '8px'
              }}
              formatter={(value: number) => [`${value.toFixed(2)} ms`, 'Avg Latency']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {latencyData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.architecture as keyof typeof COLORS]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-2 text-center">
          Lower is better
        </p>
      </div>

      {/* Throughput Comparison */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Total Transactions Processed
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={throughputData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="name" stroke="#666" style={{ fontSize: '12px' }} />
            <YAxis
              stroke="#666"
              label={{ value: 'Transactions', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e0e0',
                borderRadius: '8px'
              }}
              formatter={(value: number) => [`${value}`, 'Transactions']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {throughputData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.architecture as keyof typeof COLORS]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-2 text-center">
          Higher is better
        </p>
      </div>

      {/* Compliance Rate Comparison */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">
          Compliance Rate
        </h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={complianceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis dataKey="name" stroke="#666" style={{ fontSize: '12px' }} />
            <YAxis
              stroke="#666"
              domain={[0, 100]}
              label={{ value: 'Compliance Rate (%)', angle: -90, position: 'insideLeft' }}
              style={{ fontSize: '12px' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #e0e0e0',
                borderRadius: '8px'
              }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Compliance Rate']}
            />
            <Bar dataKey="value" radius={[8, 8, 0, 0]}>
              {complianceData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.architecture as keyof typeof COLORS]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p className="text-sm text-gray-600 mt-2 text-center">
          Target: 100% (all violations detected)
        </p>
      </div>
    </div>
  );
}
