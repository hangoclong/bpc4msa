/**
 * INFRASTRUCTURE LAYER - Adapter
 * Docker-based implementation of IArchitectureController
 * Uses Control API as proxy to avoid CORS issues
 */

import { ArchitectureType } from '../../domain/entities/Experiment';
import { SystemMetrics } from '../../domain/entities/Metrics';
import { IArchitectureController } from '../../domain/ports/IArchitectureController';

interface HealthResponse {
  architecture: string;
  healthy: boolean;
  status_code?: number;
  error?: string;
}

export class DockerArchitectureController implements IArchitectureController {
  // Control API serves as proxy to avoid CORS issues
  private controlApiUrl = 'http://localhost:8080';

  async start(architecture: ArchitectureType): Promise<void> {
    // Check if architecture is already running
    const healthy = await this.isHealthy(architecture);

    if (!healthy) {
      throw new Error(
        `${architecture} architecture is not running. Please start it with: docker-compose ${
          architecture === 'bpc4msa' ? '' : `-f docker-compose.${architecture === 'synchronous' ? 'sync' : 'mono'}.yml `
        }up -d`
      );
    }

    console.log(`${architecture} architecture is running and ready`);
  }

  async stop(architecture: ArchitectureType): Promise<void> {
    try {
      const response = await fetch(
        `${this.controlApiUrl}/api/architectures/stop/${architecture}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error(`Failed to stop ${architecture}`);
      }

      console.log(`Stopped ${architecture} architecture`);
    } catch (error) {
      console.error(`Error stopping ${architecture}:`, error);
      throw error;
    }
  }

  async getCurrent(): Promise<ArchitectureType | null> {
    try {
      const response = await fetch(`${this.controlApiUrl}/api/architectures/health`);

      if (!response.ok) {
        return null;
      }

      const data: Record<string, HealthResponse> = await response.json();

      // Return the first healthy architecture
      for (const [arch, health] of Object.entries(data)) {
        if (health.healthy) {
          return arch as ArchitectureType;
        }
      }

      return null;
    } catch {
      return null;
    }
  }

  async getMetrics(architecture: ArchitectureType): Promise<SystemMetrics> {
    try {
      const response = await fetch(
        `${this.controlApiUrl}/api/architectures/stats/${architecture}`
      );

      if (!response.ok) {
        throw new Error(`Failed to get metrics for ${architecture}`);
      }

      // The API returns data in the flat SystemMetrics format, so we can cast and return directly.
      const data: SystemMetrics = await response.json();
      return data;

    } catch (error) {
      console.error(`Error fetching metrics for ${architecture}:`, error);
      throw error;
    }
  }

  async isHealthy(architecture: ArchitectureType): Promise<boolean> {
    try {
      const response = await fetch(
        `${this.controlApiUrl}/api/architectures/health/${architecture}`,
        {
          method: 'GET',
          signal: AbortSignal.timeout(3000),
        }
      );

      if (!response.ok) {
        return false;
      }

      const data: HealthResponse = await response.json();
      return data.healthy;
    } catch (error) {
      console.error(`Error checking health for ${architecture}:`, error);
      return false;
    }
  }
}
