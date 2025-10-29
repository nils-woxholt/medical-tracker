"use client";
import React, { useState, useRef, useEffect } from 'react';
import { login } from '../../lib/auth/client';
import { redirectAfterLogin } from '../../lib/auth/useSessionGuard';

interface Props {
  onSuccess?: () => void;
}

export default function LoginForm({ onSuccess }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => { emailRef.current?.focus(); }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('INVALID_CREDENTIALS'); // generic to avoid enumeration
      return;
    }
    if (password.length < 8) {
      setError('INVALID_CREDENTIALS');
      return;
    }
    setSubmitting(true);
    try {
      const base = process.env.NEXT_PUBLIC_E2E ? 'http://localhost:8000' : '';
      // If in E2E mode, bypass rewrite by calling absolute URL
      if (base) {
        const res = await fetch(base + '/auth/login', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        });
        console.warn('login.fetch.status', res.status);
        if (!res.ok) throw new Error('INVALID_CREDENTIALS');
      } else {
        await login({ email, password });
      }
      onSuccess?.();
      redirectAfterLogin();
    } catch (err: any) {
      // backend returns 401 -> throws INVALID_CREDENTIALS; any other -> AUTH_ERROR -> map to generic
      setError(err?.message === 'INVALID_CREDENTIALS' ? 'INVALID_CREDENTIALS' : 'AUTH_ERROR');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative" data-testid="login-form-wrapper">
      {submitting && (
        <div aria-hidden="true" className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center text-sm" data-testid="login-loading-overlay">
          Processing…
        </div>
      )}
      <form onSubmit={onSubmit} aria-label="login form" data-testid="login-form" className="space-y-4" noValidate>
        <div className="flex flex-col gap-1">
          <label htmlFor="login-email" className="text-sm font-medium">Email</label>
          <input
            id="login-email"
            ref={emailRef}
            type="email"
            autoComplete="email"
            disabled={submitting}
            className="border rounded px-3 py-2 text-sm"
            value={email}
            onChange={e => setEmail(e.target.value)}
            data-testid="login-email"
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="login-password" className="text-sm font-medium">Password</label>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            disabled={submitting}
            className="border rounded px-3 py-2 text-sm"
            value={password}
            onChange={e => setPassword(e.target.value)}
            data-testid="login-password"
            required
            minLength={8}
          />
        </div>
        {error && (
          <div role="alert" aria-live="assertive" className="text-red-600 text-xs" data-testid="login-error">
            {error === 'INVALID_CREDENTIALS' ? 'Invalid credentials' : 'Authentication error'}
          </div>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-semibold disabled:opacity-50"
          data-testid="login-submit"
        >
          {submitting ? 'Logging in…' : 'Login'}
        </button>
      </form>
    </div>
  );
}
