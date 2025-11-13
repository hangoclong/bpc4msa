/**
 * DOMAIN LAYER TESTS - Experiment Entity with Ramp-Up Duration
 * Tests for new rampUpDuration feature (Future Experiment Design Plan)
 */

import { Experiment, ExperimentConfig } from '../Experiment';

describe('Experiment - Ramp-Up Duration Feature', () => {
  describe('ExperimentConfig with rampUpDuration', () => {
    it('should accept rampUpDuration parameter', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: 60 // NEW: Separate ramp-up phase
      };

      expect(config.rampUpDuration).toBe(60);
    });

    it('should allow optional rampUpDuration (backward compatibility)', () => {
      const config: ExperimentConfig = {
        users: 25,
        spawnRate: 2,
        duration: 120,
        violationRate: 0.2
        // rampUpDuration is optional
      };

      expect(config.rampUpDuration).toBeUndefined();
    });

    it('should create experiment with rampUpDuration', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: 60
      };

      const experiment = new Experiment(
        'exp-001',
        'High Load with Ramp-Up',
        'bpc4msa',
        config,
        'pending'
      );

      expect(experiment.config.rampUpDuration).toBe(60);
    });

    it('should validate rampUpDuration is positive', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: -10 // Invalid
      };

      expect(() => {
        new Experiment(
          'exp-002',
          'Invalid Ramp-Up',
          'bpc4msa',
          config,
          'pending'
        );
      }).toThrow('rampUpDuration must be positive');
    });

    it('should validate rampUpDuration is less than total duration', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 60,
        violationRate: 0.15,
        rampUpDuration: 120 // Ramp-up longer than total duration
      };

      expect(() => {
        new Experiment(
          'exp-003',
          'Invalid Ramp-Up Duration',
          'bpc4msa',
          config,
          'pending'
        );
      }).toThrow('rampUpDuration must be less than duration');
    });
  });

  describe('Concurrency Spike Preset', () => {
    it('should support high-concurrency spike configuration', () => {
      // From Future_Experiment_Design_Plan.md: Scenario B
      const spikeConfig: ExperimentConfig = {
        users: 150,
        spawnRate: 150, // High spawn rate for spike test
        duration: 30,
        violationRate: 0.1,
        rampUpDuration: 0 // Immediate spike
      };

      const experiment = new Experiment(
        'exp-spike-001',
        'Concurrency Spike Test',
        'bpc4msa',
        spikeConfig,
        'pending'
      );

      expect(experiment.config.users).toBe(150);
      expect(experiment.config.duration).toBe(30);
      expect(experiment.config.rampUpDuration).toBe(0);
    });

    it('should calculate total experiment time including ramp-up', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: 60
      };

      const experiment = new Experiment(
        'exp-004',
        'Test Total Time',
        'bpc4msa',
        config,
        'pending'
      );

      // Total time = rampUpDuration + duration
      expect(experiment.getTotalDuration()).toBe(660);
    });

    it('should calculate total experiment time without ramp-up', () => {
      const config: ExperimentConfig = {
        users: 25,
        spawnRate: 2,
        duration: 120,
        violationRate: 0.2
      };

      const experiment = new Experiment(
        'exp-005',
        'Test No Ramp-Up',
        'bpc4msa',
        config,
        'pending'
      );

      expect(experiment.getTotalDuration()).toBe(120);
    });
  });

  describe('Low-Resource Scenario Tagging', () => {
    it('should support resource constraint tags for experiments', () => {
      const config: ExperimentConfig = {
        users: 20,
        spawnRate: 2,
        duration: 300,
        violationRate: 0.2,
        resourceConstrained: true // NEW: Tag for resource-constrained tests
      };

      const experiment = new Experiment(
        'exp-resource-001',
        'Low-Resource Environment Test',
        'monolithic',
        config,
        'pending'
      );

      expect(experiment.config.resourceConstrained).toBe(true);
    });

    it('should default resourceConstrained to false', () => {
      const config: ExperimentConfig = {
        users: 25,
        spawnRate: 2,
        duration: 120,
        violationRate: 0.2
      };

      const experiment = new Experiment(
        'exp-006',
        'Normal Test',
        'bpc4msa',
        config,
        'pending'
      );

      expect(experiment.config.resourceConstrained).toBe(false);
    });
  });

  describe('Experiment Phase Tracking', () => {
    it('should track current phase (ramp-up vs steady-state)', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: 60
      };

      const experiment = new Experiment(
        'exp-007',
        'Phase Tracking Test',
        'bpc4msa',
        config,
        'pending'
      );

      experiment.start();

      // Should be in ramp-up phase initially
      expect(experiment.getCurrentPhase()).toBe('ramp-up');
    });

    it('should transition to steady-state after ramp-up', () => {
      const config: ExperimentConfig = {
        users: 100,
        spawnRate: 10,
        duration: 600,
        violationRate: 0.15,
        rampUpDuration: 60
      };

      const experiment = new Experiment(
        'exp-008',
        'Phase Transition Test',
        'bpc4msa',
        config,
        'pending'
      );

      experiment.start();

      // Simulate time passing beyond ramp-up
      const elapsedTime = 61; // 61 seconds (past ramp-up)
      expect(experiment.getCurrentPhase(elapsedTime)).toBe('steady-state');
    });

    it('should have no phases when rampUpDuration is not set', () => {
      const config: ExperimentConfig = {
        users: 25,
        spawnRate: 2,
        duration: 120,
        violationRate: 0.2
      };

      const experiment = new Experiment(
        'exp-009',
        'No Phase Test',
        'bpc4msa',
        config,
        'pending'
      );

      experiment.start();
      expect(experiment.getCurrentPhase()).toBe('steady-state');
    });
  });
});
