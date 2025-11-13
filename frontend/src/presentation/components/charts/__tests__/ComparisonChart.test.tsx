/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { ComparisonChart } from '../ComparisonChart';
import { SystemMetrics } from '../../../../domain/entities/Metrics';

// Mock the ResponsiveContainer to make charts render in a non-browser environment
jest.mock('recharts', () => {
  const OriginalModule = jest.requireActual('recharts');
  return {
    ...OriginalModule,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div style={{ width: 800, height: 250 }}>{children}</div>
    ),
  };
});

describe('ComparisonChart', () => {
  const mockMetrics = {
    bpc4msa: {
      architecture: 'bpc4msa',
      total_transactions: 100,
      total_violations: 10,
      avg_processing_time_ms: 15.5,
      max_processing_time_ms: 50,
      min_processing_time_ms: 5,
    } as SystemMetrics,
    synchronous: {
      architecture: 'synchronous',
      total_transactions: 120,
      total_violations: 24,
      avg_processing_time_ms: 8.2,
      max_processing_time_ms: 30,
      min_processing_time_ms: 2,
    } as SystemMetrics,
    monolithic: {
      architecture: 'monolithic',
      total_transactions: 150,
      total_violations: 45,
      avg_processing_time_ms: 5.1,
      max_processing_time_ms: 25,
      min_processing_time_ms: 1,
    } as SystemMetrics,
  };

  it('renders all three chart titles', () => {
    render(<ComparisonChart metrics={mockMetrics} />);

    expect(screen.getByText('Average Latency Comparison')).toBeInTheDocument();
    expect(screen.getByText('Total Transactions Processed')).toBeInTheDocument();
    expect(screen.getByText('Compliance Rate')).toBeInTheDocument();
  });

  it('renders without crashing when data is provided', () => {
    const { container } = render(<ComparisonChart metrics={mockMetrics} />);
    expect(container).toBeDefined();
  });

});
