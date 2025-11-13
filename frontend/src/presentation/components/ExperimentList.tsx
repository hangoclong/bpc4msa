/**
 * PRESENTATION LAYER - Component
 * List of experiments
 */

'use client';

import { useEffect, useState } from 'react';
import { Trash2, Play, Loader2 } from 'lucide-react';
import { useExperiment } from '../hooks/useExperiment';
import { getContainer } from '../../infrastructure/di/container';

export function ExperimentList() {
  const { experiments, loading, loadExperiments, startExperiment, clearAllExperiments } = useExperiment();
  const [executing, setExecuting] = useState<string | null>(null);
  const [progress, setProgress] = useState<{ sent: number; total: number } | null>(null);

  useEffect(() => {
    loadExperiments();

    // Auto-refresh every 3 seconds
    const interval = setInterval(() => {
      loadExperiments();
    }, 3000);

    return () => clearInterval(interval);
  }, [loadExperiments]);

  const handleStart = async (id: string) => {
    try {
      await startExperiment(id);
    } catch (err) {
      console.error('Failed to start experiment:', err);
    }
  };

  const handleRun = async (id: string) => {
    try {
      setExecuting(id);
      setProgress(null);

      // First start the experiment
      await startExperiment(id);

      // Reload experiments to get updated status
      await loadExperiments();

      // Then execute it (send transactions)
      const container = getContainer();
      await container.executeExperiment.execute(id, (sent, total) => {
        setProgress({ sent, total });
      });

      // Reload again and mark as completed
      await loadExperiments();
      const updatedExp = (await container.experimentRepo.findAll()).find(e => e.id === id);
      if (updatedExp && updatedExp.status === 'running') {
        updatedExp.complete();
        await container.experimentRepo.save(updatedExp);
      }

      await loadExperiments();
    } catch (err) {
      console.error('Failed to run experiment:', err);
      alert(`Failed to run experiment: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExecuting(null);
      setProgress(null);
    }
  };

  const handleClearAll = async () => {
    if (confirm('Are you sure you want to delete all experiments? This cannot be undone.')) {
      try {
        await clearAllExperiments();
      } catch (err) {
        console.error('Failed to clear experiments:', err);
      }
    }
  };

  if (loading && experiments.length === 0) {
    return <div className="text-center py-4">Loading experiments...</div>;
  }

  if (experiments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No experiments yet. Create one to get started.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-gray-700">Recent Experiments ({experiments.length})</h3>
        <button
          onClick={handleClearAll}
          className="flex items-center gap-1 text-xs text-red-600 hover:text-red-700 hover:underline"
          title="Clear all experiments"
        >
          <Trash2 className="w-3 h-3" />
          Clear All
        </button>
      </div>
      {experiments.map((exp) => (
        <div
          key={exp.id}
          className="border rounded-lg p-4 bg-white shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex justify-between items-start mb-2">
            <div>
              <h3 className="font-semibold">{exp.name}</h3>
              <p className="text-sm text-gray-600 capitalize">
                {exp.architecture} architecture
              </p>
            </div>
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${
                exp.status === 'completed'
                  ? 'bg-green-100 text-green-700'
                  : exp.status === 'running'
                  ? 'bg-blue-100 text-blue-700'
                  : exp.status === 'failed'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {exp.status}
            </span>
          </div>

          <div className="text-sm text-gray-600 space-y-1">
            <p>Users: {exp.config.users} | Duration: {exp.config.duration}s</p>
            <p>Violation Rate: {(exp.config.violationRate * 100).toFixed(0)}%</p>
            <p className="text-xs">Created: {exp.createdAt.toLocaleString()}</p>
          </div>

          {exp.canStart() && (
            <button
              onClick={() => handleRun(exp.id)}
              disabled={executing === exp.id}
              className="mt-3 bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:bg-gray-400 flex items-center gap-2"
            >
              {executing === exp.id ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running... {progress && `${progress.sent}/${progress.total}`}
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Experiment
                </>
              )}
            </button>
          )}
          {executing === exp.id && progress && (
            <div className="mt-2 bg-blue-50 border border-blue-200 rounded p-2">
              <div className="flex justify-between text-xs text-blue-800 mb-1">
                <span>Progress</span>
                <span>{Math.round((progress.sent / progress.total) * 100)}%</span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${(progress.sent / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
