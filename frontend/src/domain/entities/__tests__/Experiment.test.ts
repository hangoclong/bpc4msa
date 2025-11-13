import { Experiment, ExperimentStatus } from '../Experiment';

describe('Experiment Entity', () => {
  const mockConfig = {
    users: 10,
    spawnRate: 2,
    duration: 60,
    violationRate: 0.3
  };

  describe('canStart', () => {
    it('should return true for pending status', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'pending');
      expect(exp.canStart()).toBe(true);
    });

    it('should return false for running status', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'running');
      expect(exp.canStart()).toBe(false);
    });

    it('should return false for completed status', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'completed');
      expect(exp.canStart()).toBe(false);
    });
  });

  describe('start', () => {
    it('should change status to running and set startedAt', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'pending');
      const before = new Date();
      exp.start();

      expect(exp.status).toBe('running');
      expect(exp.startedAt).toBeDefined();
      expect(exp.startedAt!.getTime()).toBeGreaterThanOrEqual(before.getTime());
    });
  });

  describe('complete', () => {
    it('should change status to completed and set completedAt', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'running');
      const before = new Date();
      exp.complete();

      expect(exp.status).toBe('completed');
      expect(exp.completedAt).toBeDefined();
      expect(exp.completedAt!.getTime()).toBeGreaterThanOrEqual(before.getTime());
    });
  });

  describe('fail', () => {
    it('should change status to failed and set completedAt', () => {
      const exp = new Experiment('1', 'Test', 'bpc4msa', mockConfig, 'running');
      const before = new Date();
      exp.fail();

      expect(exp.status).toBe('failed');
      expect(exp.completedAt).toBeDefined();
      expect(exp.completedAt!.getTime()).toBeGreaterThanOrEqual(before.getTime());
    });
  });
});
