import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StatisticalAnalysis } from './StatisticalAnalysis';

const MOCK_SIGNIFICANT_RESULT = {
  test_name: 'BPC4MSA vs Monolithic - Latency',
  test_type: 't_test',
  p_value: 0.001,
  is_significant: true,
  effect_size: 0.85,
  effect_size_interpretation: 'Large',
  confidence_interval: [-1500, -500],
  alpha: 0.05,
  analysis_metadata: {
    architectures: ['bpc4msa', 'monolithic'],
    metric: 'latency',
    sample_sizes: [150, 150],
    analysis_date: new Date().toISOString(),
    alpha_level: 0.05,
  },
};

// Mock the global fetch function
global.fetch = jest.fn();

describe('StatisticalAnalysis Component', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear();
  });

  test('should display a user-friendly conclusion for a significant result', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => MOCK_SIGNIFICANT_RESULT,
    });

    render(<StatisticalAnalysis />);

    // Simulate user actions
    fireEvent.click(screen.getByRole('button', { name: /Run Statistical Test/i }));

    // Assertion: Check for the dynamically generated conclusion text
    // This findByTestId will fail because the element with data-testid='statistical-conclusion' does not exist.
    const conclusionElement = await screen.findByTestId('statistical-conclusion');

    await waitFor(() => {
        expect(conclusionElement).toHaveTextContent('Based on the T-test, the difference in latency between bpc4msa and monolithic is statistically significant (p < 0.05). The effect size is Large, indicating a substantial and meaningful difference in performance.');
    });

  });
});
