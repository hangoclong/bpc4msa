/**
 * PRESENTATION LAYER - React Hook
 * Bridge between React components and use cases
 */

import { useState, useCallback } from 'react';
import { getContainer } from '../../infrastructure/di/container';
import { Experiment, ArchitectureType, ExperimentConfig } from '../../domain/entities/Experiment';

export function useExperiment() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const container = getContainer();

  const loadExperiments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const exps = await container.experimentRepo.findAll();
      setExperiments(exps);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experiments');
    } finally {
      setLoading(false);
    }
  }, [container]);

  const createExperiment = useCallback(
    async (name: string, architecture: ArchitectureType, config: ExperimentConfig) => {
      try {
        setLoading(true);
        setError(null);
        const experiment = await container.createExperiment.execute({
          name,
          architecture,
          config,
        });
        await loadExperiments();
        return experiment;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create experiment');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [container, loadExperiments]
  );

  const startExperiment = useCallback(
    async (experimentId: string) => {
      try {
        setLoading(true);
        setError(null);
        await container.startExperiment.execute(experimentId);
        await loadExperiments();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to start experiment');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [container, loadExperiments]
  );

  const clearAllExperiments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await container.experimentRepo.deleteAll();
      await loadExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear experiments');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [container, loadExperiments]);

  return {
    experiments,
    loading,
    error,
    loadExperiments,
    createExperiment,
    startExperiment,
    clearAllExperiments,
  };
}
