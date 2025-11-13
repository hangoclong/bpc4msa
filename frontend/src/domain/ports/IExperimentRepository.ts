/**
 * DOMAIN LAYER - Repository Port
 * Interface for experiment persistence (Hexagonal Architecture port)
 */

import { Experiment } from '../entities/Experiment';

export interface IExperimentRepository {
  /**
   * Find experiment by ID
   */
  findById(id: string): Promise<Experiment | null>;

  /**
   * Get all experiments
   */
  findAll(): Promise<Experiment[]>;

  /**
   * Save or update experiment
   */
  save(experiment: Experiment): Promise<void>;

  /**
   * Delete experiment
   */
  delete(id: string): Promise<void>;

  /**
   * Delete all experiments
   */
  deleteAll(): Promise<void>;
}
