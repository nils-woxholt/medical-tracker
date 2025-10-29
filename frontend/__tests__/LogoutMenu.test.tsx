import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LogoutMenu from '@/components/auth/LogoutMenu';

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() })
}));

// Mock authClient logout
vi.mock('@/lib/api/authClient', () => ({
  logout: vi.fn(() => Promise.resolve())
}));

// Mock useSession to simulate active user
vi.mock('@/lib/session', async () => {
  const actual = await vi.importActual<any>('@/lib/session');
  return {
    ...actual,
    useSession: () => ({
      user: { id: 'u1', email: 'user@example.com' },
      session: { id: 's1', demo: false, last_activity_at: new Date().toISOString(), expires_at: new Date(Date.now() + 60000).toISOString() },
      expired: false,
      refresh: vi.fn(),
    })
  };
});

describe('LogoutMenu', () => {
  it('renders user email and logout button', () => {
    render(<LogoutMenu />);
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /logout/i });
    expect(btn).toBeInTheDocument();
  });
});
