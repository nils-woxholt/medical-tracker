/**
 * Tests for TopBarIdentity component (T050).
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { TopBarIdentity } from '../TopBarIdentity';

describe('TopBarIdentity', () => {
  it('renders display name when provided', () => {
    render(<TopBarIdentity email="user@example.com" displayName="Alice" />);
    const el = screen.getByTestId('identity');
    expect(el.textContent).toContain('Alice');
  });

  it('falls back to masked email when display name absent', () => {
    render(<TopBarIdentity email="maskeduser@example.com" />);
    const el = screen.getByTestId('identity');
    expect(el.textContent).toMatch(/^mas.*@example\.com$/i);
  });

  it('truncates long identity with ellipsis and retains title', () => {
    const longName = 'VeryVeryLongDisplayNameExceedingLimits';
    render(<TopBarIdentity email="long@example.com" displayName={longName} />);
    const el = screen.getByTestId('identity');
    expect(el.textContent).not.toEqual(longName);
    expect(el.textContent).toMatch(/…$/); // ends with ellipsis
    expect(el).toHaveAttribute('title', longName);
  });
});
