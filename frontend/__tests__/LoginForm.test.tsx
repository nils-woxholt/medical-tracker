import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from '../src/app/(auth)/login/page';
import * as authClient from '../src/lib/api/authClient';

describe('LoginPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('shows validation error when fields empty', async () => {
    render(<LoginPage />);
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('EMAIL_PASSWORD_REQUIRED');
  });

  it('shows error for short password', async () => {
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'short' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('PASSWORD_TOO_SHORT');
  });

  it('submits and redirects on success', async () => {
    const spy = vi.spyOn(authClient, 'login').mockResolvedValue({ data: { id: '1', email: 'user@example.com' } });
    const loc = vi.spyOn(window, 'location', 'get').mockReturnValue({ href: '', assign: vi.fn() } as any);
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'longenough1' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    expect(spy).toHaveBeenCalled();
  });

  it('displays API error', async () => {
    vi.spyOn(authClient, 'login').mockRejectedValue(new Error('INVALID_CREDENTIALS'));
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'longenough1' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    expect(await screen.findByRole('alert')).toHaveTextContent('INVALID_CREDENTIALS');
  });
});
