"use client";
import React from 'react';
import { isDemoSession, useSession } from '@/lib/session';
import Link from 'next/link';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface DemoSessionBannerProps {
  className?: string;
}

export const DemoSessionBanner: React.FC<DemoSessionBannerProps> = ({ className }) => {
  const { session, user, loading } = useSession({ pollIntervalMs: 45000 });

  if (loading) {
    return null; // Could render a skeleton here
  }
  if (!isDemoSession(session)) {
    return null;
  }

  return (
    <Alert className={className} variant="default">
      <AlertTitle>Demo Mode</AlertTitle>
      <AlertDescription>
        You are exploring the tracker in a temporary demo session ({user?.email}).
        Your data may be cleared periodically. Create a full account to save progress.
      </AlertDescription>
      <div className="mt-3 flex gap-2">
        <Button asChild variant="secondary" size="sm">
          <Link href="/auth/register">Create Account</Link>
        </Button>
        <Button asChild variant="ghost" size="sm">
          <Link href="/auth/login">Login</Link>
        </Button>
      </div>
    </Alert>
  );
};

export default DemoSessionBanner;
