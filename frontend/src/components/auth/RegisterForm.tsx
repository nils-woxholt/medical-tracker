"use client";
import React, { useState, useRef, useEffect } from 'react';

interface Props { onSuccess?: () => void }

function scorePassword(pw: string): number {
  let score = 0;
  if (pw.length >= 10) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score; // 0-5
}

export default function RegisterForm({ onSuccess }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const emailRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => { emailRef.current?.focus(); }, []);

  const strength = scorePassword(password);
  const weak = strength < 3;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('EMAIL_PASSWORD_REQUIRED');
      return;
    }
    if (weak) {
      setError('WEAK_PASSWORD');
      return;
    }
    setSubmitting(true);
    try {
        console.warn('register.submit.start', { email, hasDisplay: !!displayName, e2e: !!process.env.NEXT_PUBLIC_E2E });
  // Registration endpoint is unversioned (/auth/register). The versioned /api/v1/auth/register returns 501 (legacy placeholder).
  const base = process.env.NEXT_PUBLIC_E2E ? 'http://localhost:8000' : '';
  const res = await fetch(base + '/auth/register', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, display_name: displayName || undefined }),
      });
        console.warn('register.submit.response', { status: res.status });
      if (res.status === 409) throw new Error('EMAIL_EXISTS');
      if (res.status === 400) {
  const body = await res.json().catch(() => ({}));
        if (body?.error === 'WEAK_PASSWORD') throw new Error('WEAK_PASSWORD');
        throw new Error('REGISTRATION_ERROR');
      }
      if (!res.ok) {
        // Emit console debug for Playwright to capture
        console.warn('register.failed', { status: res.status });
        throw new Error('REGISTRATION_ERROR');
      }
        console.warn('register.success', { email });
  // Registration auto-logs in per backend contract (session cookie set).
  // Invoke onSuccess so parent can show success banner & switch mode. We no longer force a
  // redirect here; tests will navigate to /dashboard explicitly when needed.
  onSuccess?.();
    } catch (err: any) {
      setError(err?.message || 'REGISTRATION_ERROR');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative" data-testid="register-form-wrapper">
      {submitting && (
        <div aria-hidden="true" className="absolute inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center text-sm" data-testid="register-loading-overlay">Processing…</div>
      )}
      <form onSubmit={onSubmit} aria-label="register form" data-testid="register-form" className="space-y-4" noValidate>
        <div className="flex flex-col gap-1">
          <label htmlFor="reg-email" className="text-sm font-medium">Email</label>
          <input id="reg-email" ref={emailRef} type="email" autoComplete="email" disabled={submitting} className="border rounded px-3 py-2 text-sm" value={email} onChange={e => setEmail(e.target.value)} required data-testid="reg-email" />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="reg-display-name" className="text-sm font-medium">Display Name (optional)</label>
          <input id="reg-display-name" type="text" disabled={submitting} className="border rounded px-3 py-2 text-sm" value={displayName} onChange={e => setDisplayName(e.target.value)} data-testid="reg-display-name" />
        </div>
        <div className="flex flex-col gap-1">
          <label htmlFor="reg-password" className="text-sm font-medium">Password</label>
          <input id="reg-password" type="password" autoComplete="new-password" disabled={submitting} className="border rounded px-3 py-2 text-sm" value={password} onChange={e => setPassword(e.target.value)} required data-testid="reg-password" />
          <div className="flex items-center gap-2" aria-hidden="true">
            <div className="h-2 flex-1 bg-gray-200 rounded overflow-hidden">
              <div className={`h-full transition-all ${strength >= 1 ? 'bg-red-500' : 'bg-transparent'}`} style={{ width: '20%' }} />
              <div className={`h-full transition-all ${strength >= 2 ? 'bg-orange-500' : 'bg-transparent'}`} style={{ width: '20%' }} />
              <div className={`h-full transition-all ${strength >= 3 ? 'bg-yellow-500' : 'bg-transparent'}`} style={{ width: '20%' }} />
              <div className={`h-full transition-all ${strength >= 4 ? 'bg-green-500' : 'bg-transparent'}`} style={{ width: '20%' }} />
              <div className={`h-full transition-all ${strength >= 5 ? 'bg-emerald-600' : 'bg-transparent'}`} style={{ width: '20%' }} />
            </div>
            <span className="text-xs" data-testid="reg-strength-label">{weak ? 'Weak' : 'Good'}</span>
          </div>
        </div>
        {error && (
          <div role="alert" aria-live="assertive" className="text-red-600 text-xs" data-testid="reg-error">{error}</div>
        )}
        <button type="submit" disabled={submitting} className="w-full bg-blue-600 text-white rounded px-4 py-2 text-sm font-semibold disabled:opacity-50" data-testid="reg-submit">
          {submitting ? 'Registering…' : 'Register'}
        </button>
      </form>
    </div>
  );
}
