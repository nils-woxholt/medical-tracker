import { test, expect } from '@playwright/test';

// Registration flow adapted to unified /access screen.
// The /auth/register route is now an alias that redirects to /access?mode=register.
// We assert the redirect, fill the form, trigger success, and confirm banner + mode switch.

test.describe('Access registration flow', () => {
  test('can register via alias redirect', async ({ page }) => {
    await page.goto('/auth/register');

    // After redirect we should be on /access?mode=register and see the register form elements.
    await expect(page).toHaveURL(/\/access\?mode=register/);
    // We rely on test IDs defined inside RegisterForm (adapt if needed).
    const email = `user${Date.now()}@example.com`;
    await page.getByTestId('reg-email').fill(email);
    await page.getByTestId('reg-password').fill('Secure123');
    await page.getByTestId('reg-display-name').fill('Test User');
    await page.getByTestId('reg-submit').click();

    // On success the component switches to login mode and shows a banner.
    await expect(page.getByTestId('registration-banner')).toBeVisible();
    await expect(page.getByTestId('access-form-container')).toBeVisible();
    // The login form should now be present (email/password inputs with different IDs).
    await expect(page.getByTestId('login-email')).toBeVisible();
  });
});
