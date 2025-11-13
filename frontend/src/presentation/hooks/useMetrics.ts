/**
 * PRESENTATION LAYER - React Hook
 * Metrics monitoring hook
 */

import { useState, useCallback } from 'react';
import { getContainer } from '../../infrastructure/di/container';
import { SystemMetrics } from '../../domain/entities/Metrics';
import { ArchitectureType } from '../../domain/entities/Experiment';

export function useMetrics() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const container = getContainer();

  const fetchMetrics = useCallback(
    async (architecture: ArchitectureType) => {
      try {
        setLoading(true);
        setError(null);
        const stats = await container.architectureController.getMetrics(architecture);
        setMetrics(stats);
        return stats;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [container]
  );

  const checkHealth = useCallback(
    async (architecture: ArchitectureType) => {
      try {
        return await container.architectureController.isHealthy(architecture);
      } catch (err) {
        console.error('Health check failed:', err);
        return false;
      }
    },
    [container]
  );

  return {
    metrics,
    loading,
    error,
    fetchMetrics,
    checkHealth,
  };
}
