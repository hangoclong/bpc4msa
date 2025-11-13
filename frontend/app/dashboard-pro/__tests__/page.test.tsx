/**
 * @jest-environment jsdom
 */

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import ProfessionalDashboard from '../page';

// Mock fetch API
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      bpc4msa: { total_transactions: 100, avg_latency_ms: 10, total_violations: 5 },
      synchronous: { total_transactions: 200, avg_latency_ms: 20, total_violations: 20 },
      monolithic: { total_transactions: 300, avg_latency_ms: 30, total_violations: 45 },
    }),
  }) as Promise<Response>
);

// Mock child components that are not relevant to this test
jest.mock('../../../src/presentation/components/ExperimentControlAdvanced', () => ({ ExperimentControlAdvanced: () => <div>ExperimentControlAdvanced</div> }));
jest.mock('../../../src/presentation/components/ExperimentList', () => ({ ExperimentList: () => <div>ExperimentList</div> }));
jest.mock('../../../src/presentation/components/EventMonitor', () => ({ EventMonitor: () => <div>EventMonitor</div> }));
jest.mock('../../../src/presentation/components/ArchitectureStatus', () => ({ ArchitectureStatus: () => <div>ArchitectureStatus</div> }));
jest.mock('../../../src/presentation/components/QuickActions', () => ({ QuickActions: () => <div>QuickActions</div> }));
jest.mock('../../../src/presentation/components/charts/ComparisonChart', () => ({ ComparisonChart: () => <div>ComparisonChart</div> }));

describe('ProfessionalDashboard Page', () => {

  beforeEach(() => {
    // Clear mock history before each test
    (fetch as jest.Mock).mockClear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should display metrics for the default architecture (BPC4MSA) on initial render', async () => {
    render(<ProfessionalDashboard />);

    // Advance timers to allow useEffect to run
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    // Check that the BPC4MSA transaction count is displayed in the card
    const transactionsCard = await screen.findByText('100');
    expect(transactionsCard).toBeInTheDocument();
    expect(screen.getByText('Total Transactions')).toBeInTheDocument();
  });

  it('should switch the displayed metrics when a new architecture is selected', async () => {
    render(<ProfessionalDashboard />);

    // Advance timers to allow initial data fetch
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    // Initially shows 100 for BPC4MSA
    expect(await screen.findByText('100')).toBeInTheDocument();

    // Find and click the 'Synchronous' button
    const synchronousButton = screen.getByRole('button', { name: /synchronous/i });
    fireEvent.click(synchronousButton);

    // Now, the card should update to show the metrics for the Synchronous architecture
    const updatedTransactionsCard = await screen.findByText('200');
    expect(updatedTransactionsCard).toBeInTheDocument();

    // Check that the old value is gone
    expect(screen.queryByText('100')).not.toBeInTheDocument();
  });

  it('should periodically refresh the metrics data', async () => {
    render(<ProfessionalDashboard />);

    // Wait for the initial fetch on mount to complete
    await screen.findByText('Total Transactions');
    expect(fetch).toHaveBeenCalledTimes(1);

    // Second fetch after interval
    await act(async () => {
      jest.advanceTimersByTime(2000);
    });
    expect(fetch).toHaveBeenCalledTimes(2);
  });

});
