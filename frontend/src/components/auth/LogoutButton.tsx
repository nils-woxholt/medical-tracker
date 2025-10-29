"use client";
import React, { useState } from 'react';
import { logout, refreshIdentity } from '@/lib/auth/client';

export interface LogoutButtonProps {
  onLoggedOut?: () => void;
}

export const LogoutButton: React.FC<LogoutButtonProps> = ({ onLoggedOut }) => {
  const [loading, setLoading] = useState(false);
  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      await logout();
      await refreshIdentity();
      onLoggedOut?.();
      // Redirect to access screen client-side (SSR guard handles server path)
      if (typeof window !== 'undefined') {
        window.location.href = '/access';
      }
    } finally {
      setLoading(false);
    }
  };
  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="inline-flex items-center rounded px-3 py-1 text-sm font-medium bg-muted hover:bg-muted/80 disabled:opacity-50"
      aria-label="Log out"
      data-testid="logout"
    >
      {loading ? (
        <span className="flex items-center gap-2" data-testid="logout-loading">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
          Logging out…
        </span>
      ) : (
        'Logout'
      )}
    </button>
  );
};

export default LogoutButton;