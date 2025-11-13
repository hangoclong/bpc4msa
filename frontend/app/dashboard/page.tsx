/**
 * Dashboard Page - Clean Architecture Integration
 * Central experiment control and monitoring dashboard
 */

'use client';

import { ExperimentControl } from '../../src/presentation/components/ExperimentControl';
import { ExperimentList } from '../../src/presentation/components/ExperimentList';
import { EventMonitor } from '../../src/presentation/components/EventMonitor';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            BPC4MSA Experiment Dashboard
          </h1>
          <p className="text-gray-600 mt-2">
            Comparative Analysis of Business Process Compliance Architectures
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Experiment Control */}
          <div className="lg:col-span-1 space-y-6">
            <ExperimentControl />
            <div className="border rounded-lg p-6 bg-white shadow-sm">
              <h2 className="text-xl font-bold mb-4">Experiments</h2>
              <ExperimentList />
            </div>
          </div>

          {/* Right column - Event Monitor */}
          <div className="lg:col-span-2">
            <EventMonitor />
          </div>
        </div>

        {/* Architecture Info */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <h3 className="font-bold text-blue-600 mb-2">BPC4MSA</h3>
            <p className="text-sm text-gray-600">
              Event-driven microservices with Kafka, async compliance validation
            </p>
            <p className="text-xs text-gray-500 mt-2">Port: 8000</p>
          </div>

          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <h3 className="font-bold text-green-600 mb-2">Synchronous</h3>
            <p className="text-sm text-gray-600">
              Traditional SOA with blocking compliance checks and audit writes
            </p>
            <p className="text-xs text-gray-500 mt-2">Port: 8001</p>
          </div>

          <div className="border rounded-lg p-4 bg-white shadow-sm">
            <h3 className="font-bold text-purple-600 mb-2">Monolithic</h3>
            <p className="text-sm text-gray-600">
              Single-process layered architecture with embedded compliance
            </p>
            <p className="text-xs text-gray-500 mt-2">Port: 8002</p>
          </div>
        </div>
      </div>
    </div>
  );
}
