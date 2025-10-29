import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test('successful login redirects to home', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type=email]', 'login_test@example.com');
    await page.fill('input[type=password]', 'CorrectPass123');
    await page.click('button[type=submit]');
    await page.waitForURL('**/');
    expect(page.url()).toMatch(/\/$/);
  });
});
