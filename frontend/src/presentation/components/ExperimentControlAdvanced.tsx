/**
 * PRESENTATION LAYER - Advanced Experiment Control
 * Professional experiment setup with validation and presets
 */

'use client';

import { useState } from 'react';
import { Play, Loader2, AlertCircle, Settings, Zap } from 'lucide-react';
import { useExperiment } from '../hooks/useExperiment';
import { ArchitectureType } from '../../domain/entities/Experiment';

interface ExperimentPreset {
  name: string;
  description: string;
  users: number;
  duration: number;
  violationRate: number;
  rampUpDuration?: number;
  resourceConstrained?: boolean;
}

const PRESETS: ExperimentPreset[] = [
  {
    name: 'Quick Test',
    description: 'Fast validation run',
    users: 5,
    duration: 30,
    violationRate: 0.3
  },
  {
    name: 'Standard Load',
    description: 'Typical production load',
    users: 25,
    duration: 120,
    violationRate: 0.2
  },
  {
    name: 'High Load (Revised)',
    description: 'Stress test with ramp-up and steady state',
    users: 100,
    duration: 600,
    violationRate: 0.15,
    rampUpDuration: 60
  },
  {
    name: 'Concurrency Spike',
    description: 'High-concurrency burst test',
    users: 150,
    duration: 30,
    violationRate: 0.1,
    rampUpDuration: 0
  },
  {
    name: 'Violation Heavy',
    description: 'High violation rate test',
    users: 20,
    duration: 60,
    violationRate: 0.7
  }
];

export function ExperimentControlAdvanced() {
  const { createExperiment, loading, error } = useExperiment();
  const [name, setName] = useState('');
  const [architecture, setArchitecture] = useState<ArchitectureType>('bpc4msa');
  const [users, setUsers] = useState(10);
  const [duration, setDuration] = useState(60);
  const [violationRate, setViolationRate] = useState(0.3);
  const [rampUpDuration, setRampUpDuration] = useState(0);
  const [resourceConstrained, setResourceConstrained] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const applyPreset = (preset: ExperimentPreset) => {
    setUsers(preset.users);
    setDuration(preset.duration);
    setViolationRate(preset.violationRate);
    setRampUpDuration(preset.rampUpDuration || 0);
    setResourceConstrained(preset.resourceConstrained || false);
    setSelectedPreset(preset.name);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createExperiment(
        name || `${architecture.toUpperCase()} - ${new Date().toLocaleString()}`,
        architecture,
        {
          users,
          spawnRate: rampUpDuration > 0 ? Math.max(1, Math.floor(users / rampUpDuration)) : Math.max(1, Math.floor(users / 10)),
          duration,
          violationRate,
          rampUpDuration: rampUpDuration > 0 ? rampUpDuration : undefined,
          resourceConstrained
        }
      );

      setName('');
      setSelectedPreset(null);
    } catch (err) {
      console.error('Failed to create experiment:', err);
    }
  };

  const rampUpRequests = rampUpDuration > 0 ? Math.floor((users / 2) * rampUpDuration) : 0;
  const steadyStateRequests = Math.floor((users * (duration - rampUpDuration)) / 2);
  const estimatedRequests = rampUpRequests + steadyStateRequests;

  return (
    <div className="bg-white rounded-lg shadow-lg border p-6">
      <div className="flex items-center gap-2 mb-6">
        <Zap className="w-6 h-6 text-blue-600" />
        <h2 className="text-xl font-bold text-gray-900">Create Experiment</h2>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Architecture Selection */}
        <div>
          <label className="block text-sm font-semibold mb-3 text-gray-900">
            Select Architecture
          </label>
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: 'bpc4msa', label: 'BPC4MSA', desc: 'Event-Driven', color: 'blue' },
              { value: 'synchronous', label: 'Synchronous', desc: 'SOA', color: 'green' },
              { value: 'monolithic', label: 'Monolithic', desc: 'All-in-One', color: 'purple' }
            ].map((arch) => (
              <button
                key={arch.value}
                type="button"
                onClick={() => setArchitecture(arch.value as ArchitectureType)}
                className={`p-4 rounded-lg border-2 transition-all text-left ${
                  architecture === arch.value
                    ? `border-${arch.color}-500 bg-${arch.color}-50`
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-semibold text-gray-900">{arch.label}</div>
                <div className="text-xs text-gray-600 mt-1">{arch.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Presets */}
        <div>
          <label className="block text-sm font-semibold mb-3 text-gray-900">
            Quick Presets (Optional)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {PRESETS.map((preset) => (
              <button
                key={preset.name}
                type="button"
                onClick={() => applyPreset(preset)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedPreset === preset.name
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="font-medium text-sm text-gray-900">{preset.name}</div>
                <div className="text-xs text-gray-600 mt-1">{preset.description}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {preset.users} users • {preset.duration}s
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Custom Configuration */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700"
          >
            <Settings className="w-4 h-4" />
            {showAdvanced ? 'Hide' : 'Show'} Custom Configuration
          </button>

          {showAdvanced && (
            <div className="mt-4 space-y-4 p-4 bg-gray-50 rounded-lg border">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">
                  Experiment Name (Optional)
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Auto-generated if empty"
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">
                  Concurrent Users: <span className="font-bold text-gray-900">{users}</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={users}
                  onChange={(e) => {
                    setUsers(parseInt(e.target.value));
                    setSelectedPreset(null);
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1</span>
                  <span>50</span>
                  <span>100</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">
                  Duration: <span className="font-bold text-gray-900">{duration}s</span>
                </label>
                <input
                  type="range"
                  min="10"
                  max="300"
                  step="10"
                  value={duration}
                  onChange={(e) => {
                    setDuration(parseInt(e.target.value));
                    setSelectedPreset(null);
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>10s</span>
                  <span>2.5min</span>
                  <span>5min</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">
                  Violation Rate: <span className="font-bold text-gray-900">{(violationRate * 100).toFixed(0)}%</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={violationRate}
                  onChange={(e) => {
                    setViolationRate(parseFloat(e.target.value));
                    setSelectedPreset(null);
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">
                  Ramp-Up Duration: <span className="font-bold text-gray-900">{rampUpDuration}s</span>
                  {rampUpDuration > 0 && <span className="text-xs text-blue-600 ml-2">({rampUpDuration}s ramp-up)</span>}
                </label>
                <input
                  type="range"
                  min="0"
                  max="120"
                  step="10"
                  value={rampUpDuration}
                  onChange={(e) => {
                    const newRampUp = parseInt(e.target.value);
                    if (newRampUp >= duration) {
                      alert('Ramp-up duration must be less than total duration');
                      return;
                    }
                    setRampUpDuration(newRampUp);
                    setSelectedPreset(null);
                  }}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0s</span>
                  <span>60s</span>
                  <span>120s</span>
                </div>
                {rampUpDuration >= duration && (
                  <p className="text-xs text-red-600 mt-1">Ramp-up duration must be less than total duration</p>
                )}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="resourceConstrained"
                  checked={resourceConstrained}
                  onChange={(e) => {
                    setResourceConstrained(e.target.checked);
                    setSelectedPreset(null);
                  }}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="resourceConstrained" className="text-sm font-medium text-gray-700">
                  Resource Constrained Environment
                </label>
              </div>
              {resourceConstrained && (
                <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded p-2">
                  ⚠️ Docker resource limits will be applied (Scenario A: Low-Resource Test)
                </div>
              )}
            </div>
          )}
        </div>

        {/* Estimated Load */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium mb-1">Estimated Load:</p>
              {rampUpDuration > 0 ? (
                <>
                  <p>• <span className="font-semibold">Ramp-up phase:</span> ~{rampUpRequests.toLocaleString()} requests during ramp-up</p>
                  <p>• <span className="font-semibold">Steady-state phase:</span> ~{steadyStateRequests.toLocaleString()} requests during steady-state</p>
                  <p>• Total: ~{estimatedRequests.toLocaleString()} requests</p>
                </>
              ) : (
                <p>• ~{estimatedRequests.toLocaleString()} total requests</p>
              )}
              <p>• ~{Math.floor(estimatedRequests * violationRate)} violations expected</p>
              <p>• Spawn rate: {rampUpDuration > 0 ? Math.max(1, Math.floor(users / rampUpDuration)) : Math.max(1, Math.floor(users / 10))} users/second</p>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2 transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Creating Experiment...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Create & Queue Experiment
            </>
          )}
        </button>
      </form>
    </div>
  );
}
