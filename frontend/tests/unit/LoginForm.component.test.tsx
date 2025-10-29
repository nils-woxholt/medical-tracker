import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LoginPage from '../../src/app/(auth)/login/page';
import * as authClient from '../../src/lib/api/authClient';

describe('LoginForm (component behavior spec)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('disables submit while loading and re-enables after', async () => {
    const spy = vi.spyOn(authClient, 'login').mockImplementation(async () => {
      return new Promise(resolve => setTimeout(() => resolve({ data: { id: 'u1', email: 'user@example.com' } }) , 10));
    });
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'longenough1' } });
    const btn = screen.getByRole('button', { name: /login/i });
    fireEvent.click(btn);
    expect(btn).toBeDisabled();
    await vi.waitUntil(() => spy.mock.calls.length === 1, { timeout: 1000 });
    await new Promise(r => setTimeout(r, 15));
    expect(btn).not.toBeDisabled();
  });

  it('shows INVALID_CREDENTIALS on rejected login', async () => {
    vi.spyOn(authClient, 'login').mockRejectedValue(new Error('INVALID_CREDENTIALS'));
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'longenough1' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('INVALID_CREDENTIALS');
  });
});
