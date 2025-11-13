/**
 * APPLICATION LAYER - Use Case
 * Get experiment metrics
 */

import { IExperimentRepository } from '../../../domain/ports/IExperimentRepository';
import { IArchitectureController } from '../../../domain/ports/IArchitectureController';
import { SystemMetrics } from '../../../domain/entities/Metrics';

export class GetExperimentMetrics {
  constructor(
    private experimentRepo: IExperimentRepository,
    private architectureController: IArchitectureController
  ) {}

  async execute(experimentId: string): Promise<SystemMetrics> {
    // Get experiment
    const experiment = await this.experimentRepo.findById(experimentId);
    if (!experiment) {
      throw new Error(`Experiment ${experimentId} not found`);
    }

    // Get metrics from architecture
    const metrics = await this.architectureController.getMetrics(experiment.architecture);

    return metrics;
  }
}
