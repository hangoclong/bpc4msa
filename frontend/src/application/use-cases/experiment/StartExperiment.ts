/**
 * APPLICATION LAYER - Use Case
 * Start experiment
 */

import { IExperimentRepository } from '../../../domain/ports/IExperimentRepository';
import { IArchitectureController } from '../../../domain/ports/IArchitectureController';

export class StartExperiment {
  constructor(
    private experimentRepo: IExperimentRepository,
    private architectureController: IArchitectureController
  ) {}

  async execute(experimentId: string): Promise<void> {
    // Get experiment
    const experiment = await this.experimentRepo.findById(experimentId);
    if (!experiment) {
      throw new Error(`Experiment ${experimentId} not found`);
    }

    // Validate can start
    if (!experiment.canStart()) {
      throw new Error(`Experiment is not in pending state`);
    }

    // Start architecture
    await this.architectureController.start(experiment.architecture);

    // Update experiment status
    experiment.start();
    await this.experimentRepo.save(experiment);
  }
}
