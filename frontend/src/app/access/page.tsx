"use client";
import React, { useState, useEffect } from 'react';
import LoginForm from '@/components/auth/LoginForm';
import RegisterForm from '@/components/auth/RegisterForm';
import RegistrationBanner from '@/components/auth/RegistrationBanner';
import AuthToggle from '@/components/auth/AuthToggle';

export default function AccessScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [bannerName, setBannerName] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const created = params.get('registered');
    const name = params.get('name');
    if (created) {
      setBannerName(name);
    }
  }, []);

  function handleRegistered() {
    // Add query param to reflect success (enables deep-link reload still showing banner)
    const nameParam = bannerName ? `&name=${encodeURIComponent(bannerName)}` : '';
    const displayName = (document.getElementById('reg-display-name') as HTMLInputElement | null)?.value || '';
    const url = new URL(window.location.href);
    url.search = `registered=1${displayName ? `&name=${encodeURIComponent(displayName)}` : ''}`;
    window.history.replaceState({}, '', url.toString());
    setBannerName(displayName || null);
    setMode('login'); // switch to login (user is now logged in - could redirect elsewhere later)
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-start pt-12" data-testid="access-screen">
      <div className="w-full max-w-sm">
        {bannerName && <RegistrationBanner displayName={bannerName} />}
      </div>
      <div className="mb-6">
        <AuthToggle mode={mode} onChange={setMode} />
      </div>
      <div className="w-full max-w-sm" data-testid="access-form-container">
        {mode === 'login' ? (
          <LoginForm />
        ) : (
          <RegisterForm onSuccess={handleRegistered} />
        )}
      </div>
    </main>
  );
}
