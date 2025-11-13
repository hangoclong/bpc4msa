import { LocalStorageExperimentRepository } from '../LocalStorageExperimentRepository';
import { Experiment } from '../../../domain/entities/Experiment';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    }
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
});

describe('LocalStorageExperimentRepository', () => {
  let repo: LocalStorageExperimentRepository;

  beforeEach(() => {
    localStorageMock.clear();
    repo = new LocalStorageExperimentRepository();
  });

  describe('save and findById', () => {
    it('should save and retrieve experiment', async () => {
      const config = { users: 10, spawnRate: 2, duration: 60, violationRate: 0.3 };
      const experiment = new Experiment('test-1', 'Test Exp', 'bpc4msa', config, 'pending');

      await repo.save(experiment);
      const retrieved = await repo.findById('test-1');

      expect(retrieved).toBeDefined();
      expect(retrieved!.id).toBe('test-1');
      expect(retrieved!.name).toBe('Test Exp');
      expect(retrieved!.architecture).toBe('bpc4msa');
    });

    it('should return null for non-existent experiment', async () => {
      const result = await repo.findById('non-existent');
      expect(result).toBeNull();
    });
  });

  describe('findAll', () => {
    it('should return all experiments', async () => {
      const config = { users: 10, spawnRate: 2, duration: 60, violationRate: 0.3 };
      const exp1 = new Experiment('1', 'Exp 1', 'bpc4msa', config, 'pending');
      const exp2 = new Experiment('2', 'Exp 2', 'synchronous', config, 'pending');

      await repo.save(exp1);
      await repo.save(exp2);

      const all = await repo.findAll();
      expect(all).toHaveLength(2);
      expect(all.map(e => e.id)).toContain('1');
      expect(all.map(e => e.id)).toContain('2');
    });

    it('should return empty array when no experiments', async () => {
      const all = await repo.findAll();
      expect(all).toEqual([]);
    });
  });

  describe('delete', () => {
    it('should delete experiment', async () => {
      const config = { users: 10, spawnRate: 2, duration: 60, violationRate: 0.3 };
      const experiment = new Experiment('delete-me', 'Test', 'bpc4msa', config, 'pending');

      await repo.save(experiment);
      expect(await repo.findById('delete-me')).toBeDefined();

      await repo.delete('delete-me');
      expect(await repo.findById('delete-me')).toBeNull();
    });
  });

  describe('deleteAll', () => {
    it('should delete all experiments', async () => {
      const config = { users: 10, spawnRate: 2, duration: 60, violationRate: 0.3 };
      const exp1 = new Experiment('1', 'Exp 1', 'bpc4msa', config, 'pending');
      const exp2 = new Experiment('2', 'Exp 2', 'synchronous', config, 'pending');

      await repo.save(exp1);
      await repo.save(exp2);
      expect((await repo.findAll()).length).toBe(2);

      await repo.deleteAll();
      expect(await repo.findAll()).toEqual([]);
    });
  });

  describe('update', () => {
    it('should update existing experiment', async () => {
      const config = { users: 10, spawnRate: 2, duration: 60, violationRate: 0.3 };
      const experiment = new Experiment('update-me', 'Original', 'bpc4msa', config, 'pending');

      await repo.save(experiment);

      experiment.start();
      await repo.save(experiment);

      const retrieved = await repo.findById('update-me');
      expect(retrieved!.status).toBe('running');
      expect(retrieved!.startedAt).toBeDefined();
    });
  });
});
