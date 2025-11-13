/**
 * APPLICATION LAYER - Use Case
 * Execute experiment by sending transactions
 */

import { IExperimentRepository } from '../../../domain/ports/IExperimentRepository';
import { ArchitectureType } from '../../../domain/entities/Experiment';

const CONTROL_API_URL = 'http://localhost:8080';

export class ExecuteExperiment {
  constructor(private experimentRepo: IExperimentRepository) {}

  async execute(experimentId: string, onProgress?: (sent: number, total: number) => void): Promise<void> {
    const experiment = await this.experimentRepo.findById(experimentId);
    if (!experiment) {
      throw new Error(`Experiment ${experimentId} not found`);
    }

    if (!experiment.isRunning()) {
      throw new Error('Experiment must be running to execute');
    }

    const { users, duration, violationRate } = experiment.config;

    // Calculate total transactions to send
    // Simple approach: send transactions at rate of users per second
    const transactionsPerSecond = Math.max(1, Math.floor(users / 10));
    const totalTransactions = transactionsPerSecond * duration;

    let sent = 0;
    const delayMs = 1000 / transactionsPerSecond;

    for (let i = 0; i < totalTransactions; i++) {
      const shouldViolate = Math.random() < violationRate;

      try {
        await this.sendTransaction(experiment.architecture, shouldViolate);
        sent++;

        if (onProgress) {
          onProgress(sent, totalTransactions);
        }

        // Delay between transactions
        await new Promise(resolve => setTimeout(resolve, delayMs));
      } catch (error) {
        console.error('Failed to send transaction:', error);
      }
    }
  }

  private async sendTransaction(architecture: ArchitectureType, withViolation: boolean): Promise<void> {
    const payload = withViolation
      ? {
          applicant_name: 'Test Violator',
          loan_amount: 2000000,
          applicant_role: 'invalid_role',
          credit_score: 400,
          employment_status: 'unemployed',
          status: 'pending'
        }
      : {
          applicant_name: 'Test Customer',
          loan_amount: Math.floor(Math.random() * 9000) + 1000, // Random amount between 1000-9999 (compliant)
          applicant_role: 'customer',
          credit_score: 750,
          employment_status: 'employed',
          status: 'pending'
        };

    const response = await fetch(`${CONTROL_API_URL}/api/architectures/${architecture}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Failed to send transaction: ${response.statusText}`);
    }
  }
}
