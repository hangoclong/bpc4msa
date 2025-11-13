/**
 * PRESENTATION LAYER - Component
 * Experiment control panel
 */

'use client';

import { useState } from 'react';
import { useExperiment } from '../hooks/useExperiment';
import { ArchitectureType } from '../../domain/entities/Experiment';

export function ExperimentControl() {
  const { createExperiment, loading, error } = useExperiment();
  const [name, setName] = useState('');
  const [architecture, setArchitecture] = useState<ArchitectureType>('bpc4msa');
  const [users, setUsers] = useState(10);
  const [duration, setDuration] = useState(60);
  const [violationRate, setViolationRate] = useState(0.3);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await createExperiment(name || `Experiment ${Date.now()}`, architecture, {
        users,
        spawnRate: 1,
        duration,
        violationRate,
      });

      // Reset form
      setName('');
      alert('Experiment created successfully!');
    } catch (err) {
      console.error('Failed to create experiment:', err);
    }
  };

  return (
    <div className="border rounded-lg p-6 bg-white shadow-sm">
      <h2 className="text-xl font-bold mb-4">Create Experiment</h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Experiment Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Optional - auto-generated if empty"
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Architecture
          </label>
          <select
            value={architecture}
            onChange={(e) => setArchitecture(e.target.value as ArchitectureType)}
            className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="bpc4msa">BPC4MSA (Event-Driven)</option>
            <option value="synchronous">Synchronous (SOA)</option>
            <option value="monolithic">Monolithic (Baseline)</option>
          </select>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Users: {users}
            </label>
            <input
              type="range"
              min="1"
              max="100"
              value={users}
              onChange={(e) => setUsers(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Duration (s): {duration}
            </label>
            <input
              type="range"
              min="10"
              max="300"
              value={duration}
              onChange={(e) => setDuration(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Violation Rate: {(violationRate * 100).toFixed(0)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={violationRate}
            onChange={(e) => setViolationRate(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Creating...' : 'Create Experiment'}
        </button>
      </form>
    </div>
  );
}
