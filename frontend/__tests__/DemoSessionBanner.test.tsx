import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import DemoSessionBanner from '@/components/auth/DemoSessionBanner';

// Mock fetch
const mockFetch = (status: number, body: any) => {
  // @ts-ignore
  global.fetch = jest.fn().mockResolvedValue({
    status,
    json: async () => body,
  });
};

describe('DemoSessionBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when no session', async () => {
    mockFetch(401, {});
    render(<DemoSessionBanner />);
    await waitFor(() => {
      expect(screen.queryByText(/Demo Mode/i)).toBeNull();
    });
  });

  it('renders banner for demo session', async () => {
    mockFetch(200, {
      data: {
        user: { id: 'u1', email: 'demo@example.com' },
        session: { id: 's1', demo: true, last_activity_at: '2025-01-01T00:00:00Z', expires_at: '2025-01-01T00:30:00Z' },
      },
      error: null,
    });
    render(<DemoSessionBanner />);
    expect(await screen.findByText(/Demo Mode/i)).toBeInTheDocument();
    expect(screen.getByText(/demo@example.com/)).toBeInTheDocument();
  });
});
