"use client";
import React from 'react';

export interface TopBarIdentityProps {
  email?: string;
  displayName?: string | null;
  maxLength?: number; // truncate threshold for identity string
}

function maskEmail(email: string | undefined): string | undefined {
  if (!email) return undefined;
  const parts = email.split('@');
  if (parts.length < 2) return email;
  const local: string = parts[0] as string;
  const domain: string = parts[1] as string;
  const visible = local.length >= 3 ? local.slice(0, 3) : local;
  return `${visible}...@${domain}`;
}

function truncateIdentity(identity: string, maxLength: number): { text: string; truncated: boolean } {
  if (identity.length <= maxLength) return { text: identity, truncated: false };
  return { text: identity.slice(0, maxLength - 1) + '…', truncated: true };
}

export const TopBarIdentity: React.FC<TopBarIdentityProps> = ({ email, displayName, maxLength = 18 }) => {
  const base = displayName && displayName.trim().length > 0 ? displayName.trim() : maskEmail(email) || '';
  const { text, truncated } = truncateIdentity(base, maxLength);
  return (
    <span
      className="inline-flex items-center text-sm font-medium text-muted-foreground max-w-xs"
      data-testid="identity"
      aria-label={`Signed in as ${base}`}
      title={truncated ? base : undefined}
    >
      {text}
    </span>
  );
};

export default TopBarIdentity;