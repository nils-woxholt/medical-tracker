import { test, expect } from '@playwright/test';

// Legacy /login redirected; new unified screen is /access?mode=login.
// This spec focuses on presence of login form elements; success covered in globalSetup.

test.describe('Access Login Presence', () => {
  test('renders login form elements', async ({ page }) => {
    await page.goto('/access?mode=login');
    await expect(page.getByTestId('access-screen')).toBeVisible();
    await expect(page.getByTestId('login-email')).toBeVisible();
    await expect(page.getByTestId('login-password')).toBeVisible();
    await expect(page.getByTestId('login-submit')).toBeVisible();
  });
});
