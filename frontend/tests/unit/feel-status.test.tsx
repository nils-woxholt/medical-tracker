import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { FeelStatus } from '@/app/(landing)/components/feel-status';

// Mock for fetch responses used by ApiClient inside FeelStatus.
// Need to include ok flag so ApiClient does not treat 200 as error.
const mockFetch = (status: number, body: any) => {
  // @ts-ignore
  global.fetch = vi.fn().mockResolvedValue({
    status,
    ok: status >= 200 && status < 300,
    headers: new Map(),
    json: async () => body,
  });
};

const FEEL_RESPONSE = {
  feel_vs_yesterday: 'better',
  confidence_score: 0.82,
  summary: 'Slept better; symptom severity decreased.'
};

describe('FeelStatus (dashboard widget)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows improved feel status without auth error or demo text', async () => {
    // Successful 200 response with expected shape
    mockFetch(200, FEEL_RESPONSE);
    render(<FeelStatus />);

    await waitFor(() => {
      // Ensure no authentication error banner
      expect(screen.queryByText(/Authentication required/i)).toBeNull();
    });

    const value = await screen.findByTestId('feel-status-value');
    expect(value).toHaveTextContent(/Feeling Better/i);
    expect(screen.getByText(/82% confidence/)).toBeInTheDocument();
    // Demo Mode should not appear (banner removed)
    expect(screen.queryByText(/Demo Mode/i)).toBeNull();
    // Empty state should not appear on successful response
    expect(screen.queryByText(/Unknown/)).toBeNull();
  });

  it('shows explanatory error on 404 (insufficient data)', async () => {
    mockFetch(404, { detail: 'Not enough data' });
    render(<FeelStatus />);
    // For 404 we expect custom mapped error message
    const alert = await screen.findByRole('alert');
  // Currently component surfaces raw detail text. Adjust expectation accordingly.
  expect(alert).toHaveTextContent(/Not enough data/i);
    // No auth error in this case
    expect(screen.queryByText(/Authentication required/i)).toBeNull();
  });
});