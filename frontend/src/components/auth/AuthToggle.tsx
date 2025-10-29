"use client";
import React from 'react';

interface Props {
  mode: 'login' | 'register';
  onChange: (m: 'login' | 'register') => void;
}

export default function AuthToggle({ mode, onChange }: Props) {
  return (
    <div className="inline-flex rounded border overflow-hidden" role="tablist" data-testid="auth-toggle">
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'login'}
        onClick={() => onChange('login')}
        className={`px-4 py-2 text-sm ${mode === 'login' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
        data-testid="auth-toggle-login"
      >Login</button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === 'register'}
        onClick={() => onChange('register')}
        className={`px-4 py-2 text-sm ${mode === 'register' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700'}`}
        data-testid="auth-toggle-register"
      >Register</button>
    </div>
  );
}
