import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import RegisterForm from '../src/components/auth/RegisterForm';

describe('RegisterForm', () => {
  function setup() { render(<RegisterForm />); }

  it('shows required error when empty submit', async () => {
    setup();
    fireEvent.click(screen.getByTestId('reg-submit'));
    expect(await screen.findByTestId('reg-error')).toHaveTextContent('EMAIL_PASSWORD_REQUIRED');
  });

  it('shows weak password error', async () => {
    setup();
    fireEvent.change(screen.getByTestId('reg-email'), { target: { value: 'user@example.com' } });
    fireEvent.change(screen.getByTestId('reg-password'), { target: { value: 'abc' } });
    fireEvent.click(screen.getByTestId('reg-submit'));
    expect(await screen.findByTestId('reg-error')).toHaveTextContent('WEAK_PASSWORD');
  });
});
