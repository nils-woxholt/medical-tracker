"use client";
import React, { useEffect, useState } from 'react';
import { SessionProvider, useSession } from '../../lib/auth/sessionContext';
import { useSessionGuard } from '../../lib/auth/useSessionGuard';
import { TopBarIdentity } from '@/components/auth/TopBarIdentity';
import { LogoutButton } from '@/components/auth/LogoutButton';
import { getIdentity } from '@/lib/auth/client';

// ProtectedLayout: wraps authenticated routes preventing unauthenticated flash.
// Displays a lightweight loading skeleton while session state resolves.

function GuardedContent({ children }: { children: React.ReactNode }) {
  const pathname = typeof window !== 'undefined' ? window.location.pathname : '/';
  const session = useSessionGuard(pathname);
  const [identity, setIdentity] = useState<{ email?: string; displayName?: string | null }>({});

  useEffect(() => {
    if (session.authenticated) {
      getIdentity().then((id) => {
        if (id.authenticated) {
          setIdentity({ email: id.email, displayName: id.displayName });
        }
      });
    }
  }, [session.authenticated]);

  if (session.loading) {
    return (
      <div className="flex min-h-screen items-center justify-center" data-testid="protected-loading">
        <div className="animate-pulse text-sm text-muted-foreground">Checking session…</div>
      </div>
    );
  }
  if (!session.authenticated) return null;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-4 py-2 border-b bg-background/50 backdrop-blur-sm" data-testid="topbar">
        <TopBarIdentity email={identity.email} displayName={identity.displayName} />
        <LogoutButton />
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}

export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <GuardedContent>{children}</GuardedContent>
    </SessionProvider>
  );
}
