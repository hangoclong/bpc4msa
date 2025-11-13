/**
 * Professional Dashboard - Central Hub for All Experiment Controls
 * Production-ready UI with advanced visualizations
 */

'use client';

import { useState, useEffect } from 'react';
import { Activity, BarChart3, Database, Zap, TrendingUp, AlertTriangle } from 'lucide-react';
import { ExperimentControlAdvanced } from '../../src/presentation/components/ExperimentControlAdvanced';
import { ExperimentList } from '../../src/presentation/components/ExperimentList';
import { EventMonitor } from '../../src/presentation/components/EventMonitor';
import { ArchitectureStatus } from '../../src/presentation/components/ArchitectureStatus';
import { MetricsCard } from '../../src/presentation/components/MetricsCard';
import { ComparisonChart } from '../../src/presentation/components/charts/ComparisonChart';
import { QuickActions } from '../../src/presentation/components/QuickActions';
import { StatisticalAnalysis } from '../../src/presentation/components/StatisticalAnalysis';
import { useEventStream } from '../../src/presentation/hooks/useEventStream';
import { SystemMetrics } from '../../src/domain/entities/Metrics';
import Link from 'next/link';

type MetricsData = Record<string, SystemMetrics>;

export default function ProfessionalDashboard() {
  const { events } = useEventStream();
  const [metricsData, setMetricsData] = useState<MetricsData>({});
  const [activeTab, setActiveTab] = useState<'control' | 'monitor' | 'compare' | 'statistics'>('control');
  const [quickActionArchitecture, setQuickActionArchitecture] = useState<'bpc4msa' | 'synchronous' | 'monolithic'>('bpc4msa');
  const [overviewArchitecture, setOverviewArchitecture] = useState<'bpc4msa' | 'synchronous' | 'monolithic'>('bpc4msa');

  // Fetch comparative metrics from database
  useEffect(() => {
    const fetchAllMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/compare/metrics');
        if (response.ok) {
          const data: MetricsData = await response.json();
          setMetricsData(data);
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    fetchAllMetrics();
    const interval = setInterval(fetchAllMetrics, 2000); // Refresh every 2s
    return () => clearInterval(interval);
  }, []);

  // Get metrics for the selected overview architecture
  const selectedMetrics = metricsData[overviewArchitecture];

  const totalTransactions = selectedMetrics?.total_transactions || 0;
  const totalViolations = selectedMetrics?.total_violations || 0;
  const avgLatency = selectedMetrics?.avg_latency_ms || 0;
  const violationRate = totalTransactions > 0 ? (totalViolations / totalTransactions) * 100 : 0;

  const tabs = [
    { id: 'control' as const, label: 'Experiment Control', icon: Zap },
    { id: 'monitor' as const, label: 'Live Monitoring', icon: Activity },
    { id: 'compare' as const, label: 'Compare Results', icon: BarChart3 },
    { id: 'statistics' as const, label: 'Statistical Analysis', icon: TrendingUp }
  ];

  const architectureSelector = (
    <div className="flex items-center justify-center gap-2 mb-4 bg-gray-100 p-2 rounded-lg">
      <h3 className="text-sm font-semibold mr-2">Displaying Metrics For:</h3>
      {[
        { value: 'bpc4msa' as const, label: 'BPC4MSA' },
        { value: 'synchronous' as const, label: 'Synchronous' },
        { value: 'monolithic' as const, label: 'Monolithic' }
      ].map((arch) => (
        <button
          key={arch.value}
          onClick={() => setOverviewArchitecture(arch.value)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
            overviewArchitecture === arch.value
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          {arch.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <Database className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">BPC4MSA Research Platform</h1>
                <p className="text-sm text-gray-600">Comparative Architecture Experiment Hub</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <div className="px-3 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                System Active
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Architecture Selector for Overview Metrics */}
        {architectureSelector}

        {/* Overview Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <MetricsCard
            title="Total Transactions"
            value={totalTransactions}
            icon={<Activity className="w-8 h-8" />}
            color="blue"
          />
          <MetricsCard
            title="Avg Latency"
            value={avgLatency.toFixed(2)}
            unit="ms"
            icon={<TrendingUp className="w-8 h-8" />}
            color="green"
          />
          <MetricsCard
            title="Violations Detected"
            value={totalViolations}
            icon={<AlertTriangle className="w-8 h-8" />}
            color="yellow"
          />
          <MetricsCard
            title="Violation Rate"
            value={violationRate.toFixed(1)}
            unit="%"
            icon={<BarChart3 className="w-8 h-8" />}
            color="purple"
          />
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm border mb-6">
          <div className="flex border-b">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-6 py-4 font-medium transition-colors flex items-center justify-center gap-2 ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'control' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <ExperimentControlAdvanced />
                </div>
                <div className="space-y-6">
                  <ArchitectureStatus />
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="font-bold text-gray-900 mb-4">Recent Experiments</h3>
                    <ExperimentList />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'monitor' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <EventMonitor />
                </div>
                <div className="space-y-6">
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h3 className="font-bold text-gray-900 mb-3 text-sm">Target Architecture</h3>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { value: 'bpc4msa' as const, label: 'BPC4MSA' },
                        { value: 'synchronous' as const, label: 'Sync' },
                        { value: 'monolithic' as const, label: 'Mono' }
                      ].map((arch) => (
                        <button
                          key={arch.value}
                          onClick={() => setQuickActionArchitecture(arch.value)}
                          className={`px-3 py-2 rounded text-xs font-medium transition-all ${
                            quickActionArchitecture === arch.value
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          {arch.label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <QuickActions architecture={quickActionArchitecture} />
                  <div className="bg-white rounded-lg shadow-sm border p-6">
                    <h3 className="font-bold text-gray-900 mb-4">Event Statistics</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Total Events</span>
                        <span className="font-bold text-gray-900">{events.length}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">With Violations</span>
                        <span className="font-bold text-red-600">
                          {events.filter(e => e.hasViolations()).length}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Compliant</span>
                        <span className="font-bold text-green-600">
                          {events.filter(e => e.isCompliant()).length}
                        </span>
                      </div>
                    </div>
                  </div>
                  <ArchitectureStatus />
                </div>
              </div>
            )}

            {activeTab === 'compare' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-800">
                    <strong>Comparative Analysis:</strong> This view shows side-by-side comparison
                    of all three architectures based on real database metrics.
                  </p>
                  <button
                    onClick={async () => {
                      if (confirm('Are you sure you want to clear all data for all architectures? This cannot be undone.')) {
                        try {
                          const response = await fetch('http://localhost:8080/api/data/clear', {
                            method: 'DELETE'
                          });
                          if (response.ok) {
                            alert('All data cleared successfully!');
                            window.location.reload();
                          } else {
                            alert('Failed to clear data');
                          }
                        } catch (error) {
                          alert('Error clearing data: ' + error);
                        }
                      }
                    }}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm font-medium whitespace-nowrap"
                  >
                    Clear All Data
                  </button>
                </div>
                <ComparisonChart metrics={metricsData} />
              </div>
            )}

            {activeTab === 'statistics' && (
              <StatisticalAnalysis />
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🎯 Research Objectives</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Compare event-driven vs synchronous architectures</li>
                <li>• Measure compliance detection accuracy</li>
                <li>• Analyze performance under load</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">📊 Key Metrics</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Average response time (latency)</li>
                <li>• Throughput (requests/second)</li>
                <li>• Violation detection rate</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🔗 Quick Links</h4>
              <ul className="text-sm text-blue-600 space-y-1">
                <li><Link href="/dashboard" className="hover:underline">→ Simple Dashboard</Link></li>
                <li><Link href="/" className="hover:underline">→ Original View</Link></li>
                <li><a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="hover:underline">→ API Docs</a></li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
