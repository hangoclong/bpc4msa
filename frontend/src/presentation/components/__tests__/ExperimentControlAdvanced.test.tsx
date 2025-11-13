/**
 * PRESENTATION LAYER TESTS - ExperimentControlAdvanced Component
 * Tests for new presets and ramp-up features
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExperimentControlAdvanced } from '../ExperimentControlAdvanced';
import { useExperiment } from '../../hooks/useExperiment';

// Mock the useExperiment hook
jest.mock('../../hooks/useExperiment');

describe('ExperimentControlAdvanced - New Presets', () => {
  const mockCreateExperiment = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useExperiment as jest.Mock).mockReturnValue({
      createExperiment: mockCreateExperiment,
      loading: false,
      error: null
    });
  });

  describe('Concurrency Spike Preset', () => {
    it('should display Concurrency Spike preset', () => {
      render(<ExperimentControlAdvanced />);

      expect(screen.getByText('Concurrency Spike')).toBeInTheDocument();
      expect(screen.getByText('High-concurrency burst test')).toBeInTheDocument();
    });

    it('should apply Concurrency Spike preset configuration', () => {
      render(<ExperimentControlAdvanced />);

      const spikeButton = screen.getByText('Concurrency Spike');
      fireEvent.click(spikeButton);

      // Should set: users=150, duration=30, violationRate=0.1
      expect(screen.getByText(/150 users/)).toBeInTheDocument();
      expect(screen.getByText(/30s/)).toBeInTheDocument();
    });

    it('should create experiment with Concurrency Spike config', async () => {
      render(<ExperimentControlAdvanced />);

      // Click preset
      const spikeButton = screen.getByText('Concurrency Spike');
      fireEvent.click(spikeButton);

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Create & Queue Experiment/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockCreateExperiment).toHaveBeenCalledWith(
          expect.any(String),
          'bpc4msa',
          expect.objectContaining({
            users: 150,
            duration: 30,
            violationRate: 0.1,
            spawnRate: 15 // High spawn rate for spike
          })
        );
      });
    });
  });

  describe('Ramp-Up Duration Field', () => {
    it('should display ramp-up duration slider in advanced mode', () => {
      render(<ExperimentControlAdvanced />);

      // Open advanced settings
      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      expect(screen.getByText(/Ramp-Up Duration:/i)).toBeInTheDocument();
    });

    it('should allow setting ramp-up duration', () => {
      render(<ExperimentControlAdvanced />);

      // Open advanced settings
      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      // Find and adjust ramp-up slider
      const rampUpSlider = screen.getByRole('slider', { name: /Ramp-Up Duration/i });
      fireEvent.change(rampUpSlider, { target: { value: '60' } });

      expect(screen.getByText(/60s/i)).toBeInTheDocument();
    });

    it('should create experiment with ramp-up duration', async () => {
      render(<ExperimentControlAdvanced />);

      // Open advanced settings
      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      // Set ramp-up duration
      const rampUpSlider = screen.getByRole('slider', { name: /Ramp-Up Duration/i });
      fireEvent.change(rampUpSlider, { target: { value: '60' } });

      // Submit form
      const submitButton = screen.getByRole('button', { name: /Create & Queue Experiment/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockCreateExperiment).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(String),
          expect.objectContaining({
            rampUpDuration: 60
          })
        );
      });
    });

    it('should validate ramp-up duration less than total duration', () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      // Set duration to 60s
      const durationSlider = screen.getByRole('slider', { name: /Duration:/i });
      fireEvent.change(durationSlider, { target: { value: '60' } });

      // Try to set ramp-up to 120s (invalid)
      const rampUpSlider = screen.getByRole('slider', { name: /Ramp-Up Duration/i });
      fireEvent.change(rampUpSlider, { target: { value: '120' } });

      // Should show validation error
      expect(screen.getByText(/Ramp-up duration must be less than total duration/i)).toBeInTheDocument();
    });
  });

  describe('Updated High Load Preset', () => {
    it('should have revised High Load preset with ramp-up', () => {
      render(<ExperimentControlAdvanced />);

      const highLoadButton = screen.getByText('High Load (Revised)');
      fireEvent.click(highLoadButton);

      // From Future_Experiment_Design_Plan.md:
      // users=100, rampUpDuration=60, duration=600
      expect(screen.getByText(/100 users/)).toBeInTheDocument();
      expect(screen.getByText(/600s/)).toBeInTheDocument();
      expect(screen.getByText(/60s ramp-up/i)).toBeInTheDocument();
    });
  });

  describe('Resource Constraint Toggle', () => {
    it('should display resource constraint checkbox', () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      expect(screen.getByLabelText(/Resource Constrained Environment/i)).toBeInTheDocument();
    });

    it('should include resourceConstrained flag when checked', async () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      const resourceCheckbox = screen.getByLabelText(/Resource Constrained Environment/i);
      fireEvent.click(resourceCheckbox);

      const submitButton = screen.getByRole('button', { name: /Create & Queue Experiment/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockCreateExperiment).toHaveBeenCalledWith(
          expect.any(String),
          expect.any(String),
          expect.objectContaining({
            resourceConstrained: true
          })
        );
      });
    });

    it('should show warning when resource constrained is enabled', () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      const resourceCheckbox = screen.getByLabelText(/Resource Constrained Environment/i);
      fireEvent.click(resourceCheckbox);

      expect(screen.getByText(/Docker resource limits will be applied/i)).toBeInTheDocument();
    });
  });

  describe('Estimated Load Calculations', () => {
    it('should show separate estimates for ramp-up and steady-state', () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      // Set ramp-up duration
      const rampUpSlider = screen.getByRole('slider', { name: /Ramp-Up Duration/i });
      fireEvent.change(rampUpSlider, { target: { value: '60' } });

      // Should show two separate estimates
      expect(screen.getByText(/Ramp-up phase:/i)).toBeInTheDocument();
      expect(screen.getByText(/Steady-state phase:/i)).toBeInTheDocument();
    });

    it('should calculate requests correctly with ramp-up', () => {
      render(<ExperimentControlAdvanced />);

      const advancedButton = screen.getByText(/Show Custom Configuration/i);
      fireEvent.click(advancedButton);

      // Set: users=100, duration=600, rampUpDuration=60
      const usersSlider = screen.getByRole('slider', { name: /Concurrent Users/i });
      fireEvent.change(usersSlider, { target: { value: '100' } });

      const durationSlider = screen.getByRole('slider', { name: /Duration:/i });
      fireEvent.change(durationSlider, { target: { value: '600' } });

      const rampUpSlider = screen.getByRole('slider', { name: /Ramp-Up Duration/i });
      fireEvent.change(rampUpSlider, { target: { value: '60' } });

      // Ramp-up requests: (100/2) * 60 = 3000
      // Steady-state requests: 100 * 600 / 2 = 30000
      expect(screen.getByText(/~3,000 requests during ramp-up/i)).toBeInTheDocument();
      expect(screen.getByText(/~30,000 requests during steady-state/i)).toBeInTheDocument();
    });
  });
});
