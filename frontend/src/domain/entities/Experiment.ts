/**
 * DOMAIN LAYER - Entities
 * Pure business logic, no dependencies on external frameworks
 */

export type ArchitectureType = 'bpc4msa' | 'synchronous' | 'monolithic';
export type ExperimentStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ExperimentConfig {
  users: number;
  spawnRate: number;
  duration: number;
  violationRate: number;
  rampUpDuration?: number; // Optional: Separate ramp-up phase before steady-state
  resourceConstrained?: boolean; // Optional: Tag for resource-constrained tests
}

export class Experiment {
  public startedAt?: Date;
  public completedAt?: Date;

  constructor(
    public readonly id: string,
    public readonly name: string,
    public readonly architecture: ArchitectureType,
    public readonly config: ExperimentConfig,
    private _status: ExperimentStatus,
    public readonly createdAt: Date = new Date(),
    startedAt?: Date,
    completedAt?: Date
  ) {
    this.startedAt = startedAt;
    this.completedAt = completedAt;

    // Set defaults
    if (this.config.resourceConstrained === undefined) {
      this.config.resourceConstrained = false;
    }

    this.validateConfig();
  }

  private validateConfig(): void {
    // Validate rampUpDuration
    if (this.config.rampUpDuration !== undefined) {
      if (this.config.rampUpDuration < 0) {
        throw new Error('rampUpDuration must be positive');
      }
      if (this.config.rampUpDuration >= this.config.duration) {
        throw new Error('rampUpDuration must be less than duration');
      }
    }
  }

  get status(): ExperimentStatus {
    return this._status;
  }

  start(): void {
    if (this._status !== 'pending') {
      throw new Error('Can only start pending experiments');
    }
    this._status = 'running';
    this.startedAt = new Date();
  }

  complete(): void {
    if (this._status !== 'running') {
      throw new Error('Can only complete running experiments');
    }
    this._status = 'completed';
    this.completedAt = new Date();
  }

  fail(): void {
    if (this._status !== 'running') {
      throw new Error('Can only fail running experiments');
    }
    this._status = 'failed';
    this.completedAt = new Date();
  }

  isRunning(): boolean {
    return this._status === 'running';
  }

  canStart(): boolean {
    return this._status === 'pending';
  }

  getTotalDuration(): number {
    const rampUp = this.config.rampUpDuration || 0;
    return rampUp + this.config.duration;
  }

  getCurrentPhase(elapsedSeconds?: number): 'ramp-up' | 'steady-state' {
    if (!this.config.rampUpDuration || this.config.rampUpDuration === 0) {
      return 'steady-state';
    }

    if (elapsedSeconds === undefined) {
      // If no elapsed time provided, assume we're at the start
      return 'ramp-up';
    }

    return elapsedSeconds < this.config.rampUpDuration ? 'ramp-up' : 'steady-state';
  }
}
