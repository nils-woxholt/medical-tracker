"use client";
import React, { useCallback, useState } from 'react';
import { logout } from '@/lib/api/authClient';
import { useRouter } from 'next/navigation';
import { useSession } from '@/lib/session';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';

interface LogoutMenuProps {
  className?: string;
}

export const LogoutMenu: React.FC<LogoutMenuProps> = ({ className }) => {
  const router = useRouter();
  const { user, session, expired, refresh } = useSession({ pollIntervalMs: 45000, autoStart: true, onExpire: () => setShowExpired(true) });
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showExpired, setShowExpired] = useState(false);

  const doLogout = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
  await logout();
  // After logout navigate to login page route (frontend page path)
  router.push('/login');
    } catch (e: any) {
      setError(e.message || 'Logout failed');
    } finally {
      setPending(false);
    }
  }, [router]);

  if (!user) {
    return null;
  }

  return (
    <div className={className}>
      <div className="flex items-center gap-3">
        <div className="text-right hidden md:block">
          <p className="text-sm font-medium text-gray-900 truncate max-w-[140px]" title={user.email}>{user.email}</p>
          {/* Demo session label removed */}
          {expired && showExpired && <p className="text-xs text-red-600">Session expired</p>}
        </div>
        <Button variant="ghost" size="sm" disabled={pending} onClick={doLogout} aria-label="Logout">
          <LogOut className="w-4 h-4" />
        </Button>
      </div>
      {error && <p className="text-xs text-red-600 mt-1" role="alert">{error}</p>}
    </div>
  );
};

export default LogoutMenu;
