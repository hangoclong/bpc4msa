/**
 * INFRASTRUCTURE LAYER - Adapter
 * LocalStorage implementation of IExperimentRepository
 */

import { Experiment, ArchitectureType, ExperimentStatus, ExperimentConfig } from '../../domain/entities/Experiment';
import { IExperimentRepository } from '../../domain/ports/IExperimentRepository';

const STORAGE_KEY = 'bpc4msa_experiments';

interface ExperimentDTO {
  id: string;
  name: string;
  architecture: ArchitectureType;
  config: ExperimentConfig;
  status: ExperimentStatus;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export class LocalStorageExperimentRepository implements IExperimentRepository {
  private toDTO(experiment: Experiment): ExperimentDTO {
    return {
      id: experiment.id,
      name: experiment.name,
      architecture: experiment.architecture,
      config: experiment.config,
      status: experiment.status,
      createdAt: experiment.createdAt.toISOString(),
      startedAt: experiment.startedAt?.toISOString(),
      completedAt: experiment.completedAt?.toISOString(),
    };
  }

  private fromDTO(dto: ExperimentDTO): Experiment {
    return new Experiment(
      dto.id,
      dto.name,
      dto.architecture,
      dto.config,
      dto.status,
      new Date(dto.createdAt),
      dto.startedAt ? new Date(dto.startedAt) : undefined,
      dto.completedAt ? new Date(dto.completedAt) : undefined
    );
  }

  private getAll(): ExperimentDTO[] {
    if (typeof window === 'undefined') return [];

    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];

    try {
      return JSON.parse(data);
    } catch {
      return [];
    }
  }

  private saveAll(experiments: ExperimentDTO[]): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(experiments));
  }

  async findById(id: string): Promise<Experiment | null> {
    const experiments = this.getAll();
    const dto = experiments.find((e) => e.id === id);
    return dto ? this.fromDTO(dto) : null;
  }

  async findAll(): Promise<Experiment[]> {
    const experiments = this.getAll();
    return experiments.map((dto) => this.fromDTO(dto));
  }

  async save(experiment: Experiment): Promise<void> {
    const experiments = this.getAll();
    const index = experiments.findIndex((e) => e.id === experiment.id);
    const dto = this.toDTO(experiment);

    if (index >= 0) {
      experiments[index] = dto;
    } else {
      experiments.push(dto);
    }

    this.saveAll(experiments);
  }

  async delete(id: string): Promise<void> {
    const experiments = this.getAll();
    const filtered = experiments.filter((e) => e.id !== id);
    this.saveAll(filtered);
  }

  async deleteAll(): Promise<void> {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(STORAGE_KEY);
  }
}
