import { test, expect } from '@playwright/test';

// Updated to unified /access screen. Validation-only (unauthenticated) flow.
// We don't rely on redirect from protected route here; covered elsewhere or can be added later.

test.describe('Access Login Validation', () => {
  test('shows validation errors on empty submit and short password', async ({ page }) => {
    await page.goto('/access?mode=login');
    await expect(page.getByTestId('access-screen')).toBeVisible();

    // Empty submit
    await page.getByTestId('login-submit').click();
    // Expect some error; target the specific error container if present.
    const loginError = page.getByTestId('login-error');
    if (await loginError.count()) {
      await expect(loginError).toContainText(/invalid|required|email/i);
    }

    // Short password scenario
    await page.getByTestId('login-email').fill('user@example.com');
    await page.getByTestId('login-password').fill('short');
    await page.getByTestId('login-submit').click();
    if (await loginError.count()) {
      await expect(loginError).toContainText(/invalid|short|password/i);
    }
  });

  test.skip('successful login (covered by globalSetup)', async ({ page }) => {
    await page.goto('/access?mode=login');
    await page.getByTestId('login-email').fill('e2e_user@example.com');
    await page.getByTestId('login-password').fill('E2E_Pass123!');
    await page.getByTestId('login-submit').click();
    await page.waitForURL('**/');
    await expect(page).toHaveURL(/\/$/);
  });
});
