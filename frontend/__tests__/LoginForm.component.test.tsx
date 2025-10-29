import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
// Target component (will be implemented in US1 T025). Adjust path once created.
// For now, this test intentionally fails if component not present or behaviors not implemented.
import LoginPage from '../src/app/(auth)/login/page';
import * as authClient from '../src/lib/api/authClient';

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
    // Wait for spy to be called
    await vi.waitUntil(() => spy.mock.calls.length === 1, { timeout: 1000 });
    // After promise resolution tick, button should re-enable
    await new Promise(r => setTimeout(r, 15));
    expect(btn).not.toBeDisabled();
  });

  it('masks backend INVALID_CREDENTIALS as INVALID_CREDENTIALS (generic) and clears loading', async () => {
    vi.spyOn(authClient, 'login').mockRejectedValue(new Error('INVALID_CREDENTIALS'));
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'longenough1' } });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('INVALID_CREDENTIALS');
  });
});
