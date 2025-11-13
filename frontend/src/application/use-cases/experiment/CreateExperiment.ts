/**
 * APPLICATION LAYER - Use Case
 * Create new experiment
 */

import { Experiment, ArchitectureType, ExperimentConfig } from '../../../domain/entities/Experiment';
import { IExperimentRepository } from '../../../domain/ports/IExperimentRepository';

export interface CreateExperimentInput {
  name: string;
  architecture: ArchitectureType;
  config: ExperimentConfig;
}

export class CreateExperiment {
  constructor(private experimentRepo: IExperimentRepository) {}

  async execute(input: CreateExperimentInput): Promise<Experiment> {
    // Generate unique ID
    const id = `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Create experiment entity
    const experiment = new Experiment(
      id,
      input.name,
      input.architecture,
      input.config,
      'pending',
      new Date()
    );

    // Persist
    await this.experimentRepo.save(experiment);

    return experiment;
  }
}
