"use client";
import React, { useState, useEffect, useRef } from 'react';
import { login } from '../../../lib/api/authClient';
import { redirectAfterLogin } from '../../../lib/auth/useSessionGuard';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const emailRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    emailRef.current?.focus();
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email || !password) {
      setError('EMAIL_PASSWORD_REQUIRED');
      return;
    }
    if (password.length < 8) {
      setError('PASSWORD_TOO_SHORT');
      return;
    }
    setLoading(true);
    try {
  await login({ email, password });
  redirectAfterLogin();
    } catch (err: any) {
      setError(err.message || 'LOGIN_FAILED');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-12 p-4 border rounded">
      <h1 className="text-xl font-semibold mb-4">Login</h1>
      <form onSubmit={onSubmit} className="flex flex-col gap-3" aria-describedby={error ? 'login-error' : undefined}>
        <label className="flex flex-col text-sm">
          Email
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="border rounded p-2"
            required
            ref={emailRef}
          />
        </label>
        <label className="flex flex-col text-sm">
          Password
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="border rounded p-2"
            required
            minLength={8}
          />
        </label>
        {error && (
          <div id="login-error" role="alert" className="text-red-600 text-sm">
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white rounded px-4 py-2 disabled:opacity-50"
        >
          {loading ? 'Logging in…' : 'Login'}
        </button>
      </form>
    </div>
  );
}
