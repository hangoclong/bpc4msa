/**
 * INFRASTRUCTURE LAYER - Dependency Injection Container
 * Central place to wire up all dependencies
 */

import { IExperimentRepository } from '../../domain/ports/IExperimentRepository';
import { IEventStream } from '../../domain/ports/IEventStream';
import { IArchitectureController } from '../../domain/ports/IArchitectureController';

import { LocalStorageExperimentRepository } from '../adapters/LocalStorageExperimentRepository';
import { WebSocketEventStream } from '../adapters/WebSocketEventStream';
import { DockerArchitectureController } from '../adapters/DockerArchitectureController';

import { CreateExperiment } from '../../application/use-cases/experiment/CreateExperiment';
import { StartExperiment } from '../../application/use-cases/experiment/StartExperiment';
import { ExecuteExperiment } from '../../application/use-cases/experiment/ExecuteExperiment';
import { GetExperimentMetrics } from '../../application/use-cases/experiment/GetExperimentMetrics';
import { SubscribeToEvents } from '../../application/use-cases/events/SubscribeToEvents';

export class DIContainer {
  // Repositories (adapters)
  private _experimentRepo?: IExperimentRepository;
  private _eventStream?: IEventStream;
  private _architectureController?: IArchitectureController;

  // Use cases
  private _createExperiment?: CreateExperiment;
  private _startExperiment?: StartExperiment;
  private _executeExperiment?: ExecuteExperiment;
  private _getExperimentMetrics?: GetExperimentMetrics;
  private _subscribeToEvents?: SubscribeToEvents;

  // Lazy initialization for repositories
  get experimentRepo(): IExperimentRepository {
    if (!this._experimentRepo) {
      this._experimentRepo = new LocalStorageExperimentRepository();
    }
    return this._experimentRepo;
  }

  get eventStream(): IEventStream {
    if (!this._eventStream) {
      this._eventStream = new WebSocketEventStream();
    }
    return this._eventStream;
  }

  get architectureController(): IArchitectureController {
    if (!this._architectureController) {
      this._architectureController = new DockerArchitectureController();
    }
    return this._architectureController;
  }

  // Lazy initialization for use cases
  get createExperiment(): CreateExperiment {
    if (!this._createExperiment) {
      this._createExperiment = new CreateExperiment(this.experimentRepo);
    }
    return this._createExperiment;
  }

  get startExperiment(): StartExperiment {
    if (!this._startExperiment) {
      this._startExperiment = new StartExperiment(
        this.experimentRepo,
        this.architectureController
      );
    }
    return this._startExperiment;
  }

  get getExperimentMetrics(): GetExperimentMetrics {
    if (!this._getExperimentMetrics) {
      this._getExperimentMetrics = new GetExperimentMetrics(
        this.experimentRepo,
        this.architectureController
      );
    }
    return this._getExperimentMetrics;
  }

  get executeExperiment(): ExecuteExperiment {
    if (!this._executeExperiment) {
      this._executeExperiment = new ExecuteExperiment(this.experimentRepo);
    }
    return this._executeExperiment;
  }

  get subscribeToEvents(): SubscribeToEvents {
    if (!this._subscribeToEvents) {
      this._subscribeToEvents = new SubscribeToEvents(this.eventStream);
    }
    return this._subscribeToEvents;
  }

  // Cleanup method
  async cleanup(): Promise<void> {
    if (this._eventStream) {
      await this._eventStream.disconnect();
    }
  }
}

// Singleton instance
let container: DIContainer | null = null;

export function getContainer(): DIContainer {
  if (!container) {
    container = new DIContainer();
  }
  return container;
}
