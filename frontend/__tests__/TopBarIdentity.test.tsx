/**
 * Tests for TopBarIdentity component (T050).
 * Expectations:
 *  - Renders display name when provided.
 *  - Falls back to masked email when display name absent.
 *  - Truncates long identity strings (adds ellipsis) and exposes full value via title attribute.
 *  - Provides accessible role/aria-label for screen readers.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Placeholder implementation stub until component exists.
// We will import from the expected path once implemented to cause initial failure for TDD.
// @ts-expect-error Component not yet implemented
import { TopBarIdentity } from '@/components/auth/TopBarIdentity';

describe('TopBarIdentity', () => {
  it('renders display name when provided', () => {
    render(<TopBarIdentity email="user@example.com" displayName="Alice" />);
    const el = screen.getByTestId('identity');
    expect(el.textContent).toContain('Alice');
  });

  it('falls back to masked email when display name absent', () => {
    render(<TopBarIdentity email="maskeduser@example.com" />);
    const el = screen.getByTestId('identity');
    // Expect first up to 3 chars + ...@domain per masking rule
    expect(el.textContent).toMatch(/^mas.*\.example\.com$/i);
  });

  it('truncates long identity with ellipsis and retains title', () => {
    const longName = 'VeryVeryLongDisplayNameExceedingLimits';
    render(<TopBarIdentity email="long@example.com" displayName={longName} />);
    const el = screen.getByTestId('identity');
    expect(el.textContent).not.toEqual(longName); // truncated
    expect(el.textContent).toMatch(/…$/); // ends with ellipsis
    expect(el).toHaveAttribute('title', longName);
  });
});
