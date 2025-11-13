/**
 * DOMAIN LAYER - Architecture Controller Port
 * Interface for controlling different architecture deployments
 */

import { ArchitectureType } from '../entities/Experiment';
import { SystemMetrics } from '../entities/Metrics';

export interface IArchitectureController {
  /**
   * Start specific architecture
   */
  start(architecture: ArchitectureType): Promise<void>;

  /**
   * Stop specific architecture
   */
  stop(architecture: ArchitectureType): Promise<void>;

  /**
   * Get current running architecture
   */
  getCurrent(): Promise<ArchitectureType | null>;

  /**
   * Get metrics for specific architecture
   */
  getMetrics(architecture: ArchitectureType): Promise<SystemMetrics>;

  /**
   * Check if architecture is healthy
   */
  isHealthy(architecture: ArchitectureType): Promise<boolean>;
}
