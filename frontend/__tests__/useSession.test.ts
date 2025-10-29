import { renderHook, act } from '@testing-library/react';
import { useSession } from '@/lib/session';

const mockFetch = (status: number, body: any) => {
  // @ts-ignore
  global.fetch = jest.fn().mockResolvedValue({
    status,
    json: async () => body,
  });
};

describe('useSession hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sets session and user on success', async () => {
    mockFetch(200, {
      data: {
        user: { id: 'u1', email: 'user@example.com' },
        session: { id: 's1', demo: false, last_activity_at: '2025-01-01T00:00:00Z', expires_at: '2025-01-01T00:30:00Z' },
      },
      error: null,
    });
    const { result } = renderHook(() => useSession({ autoStart: true, pollIntervalMs: 999999 }));
    // wait microtask
    await act(async () => {});
    expect(result.current.user?.email).toBe('user@example.com');
    expect(result.current.session?.id).toBe('s1');
    expect(result.current.error).toBeNull();
  });

  it('handles 401 as no session', async () => {
    mockFetch(401, {});
    const { result } = renderHook(() => useSession({ autoStart: true, pollIntervalMs: 999999 }));
    await act(async () => {});
    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
