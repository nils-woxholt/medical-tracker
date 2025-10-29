"use client";
import React from 'react';

interface Props { displayName?: string | null }

export default function RegistrationBanner({ displayName }: Props) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="mb-4 rounded border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-800"
      data-testid="registration-banner"
    >
      <strong className="font-semibold">Welcome{displayName ? `, ${displayName}` : ''}!</strong> Your account was created successfully.
    </div>
  );
}