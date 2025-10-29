import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { FeelStatus } from '@/app/(landing)/components/feel-status';

// We simulate a successful feel vs yesterday API response via fetch mock.
// FeelStatus uses ApiClient which ultimately calls fetch on /api/v1/feel-vs-yesterday.

const mockFetch = (status: number, body: any) => {
  // @ts-ignore
  global.fetch = vi.fn().mockResolvedValue({
    status,
    json: async () => body,
  });
};

// Provide a stable date for confidence display
const FEEL_RESPONSE = {
  feel_vs_yesterday: 'better',
  confidence_score: 0.82,
  summary: 'Slept better; symptom severity decreased.'
};

describe('Dashboard FeelStatus component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders feel status without authentication error banner when API succeeds', async () => {
    mockFetch(200, FEEL_RESPONSE);
    render(<FeelStatus />);

    // Should not show authentication error message
    await waitFor(() => {
      expect(screen.queryByText(/Authentication required/i)).toBeNull();
    });

    // Shows the main heading label based on response (Feeling Better)
    const value = await screen.findByTestId('feel-status-value');
    expect(value).toHaveTextContent(/Feeling Better/i);

    // Confidence badge text should appear
    expect(screen.getByText(/82% confidence/)).toBeInTheDocument();

    // Should not show demo mode text (component removed) or Unknown empty state
    expect(screen.queryByText(/Demo Mode/i)).toBeNull();
    expect(screen.queryByText(/Unknown/)).toBeNull();
  });

  it('renders empty state when 404 returned (insufficient data)', async () => {
    mockFetch(404, { detail: 'Not enough data' });
    render(<FeelStatus />);

    // Wait for empty state value
    const value = await screen.findByTestId('feel-status-value');
    expect(value).toHaveTextContent(/Unknown/i);

    // Should provide hint about logging; authentication error absent
    expect(screen.queryByText(/Authentication required/i)).toBeNull();
  });
});
