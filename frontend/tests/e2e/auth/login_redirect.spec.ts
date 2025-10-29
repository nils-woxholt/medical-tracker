import { test, expect } from '@playwright/test';

test.describe('Login Redirect Preservation', () => {
  test('redirects back to protected path after login', async ({ page }) => {
    // Simulate visiting protected page triggering guard
    await page.goto('/protected');
    // Guard should redirect to /login
    await page.waitForURL('**/login');
    // Fill login form
    await page.fill('input[type=email]', 'login_test@example.com');
    await page.fill('input[type=password]', 'CorrectPass123');
    await page.click('button[type=submit]');
    // Expect navigation back to original path
    await page.waitForURL('**/protected');
    expect(page.url()).toMatch(/\/protected$/);
  });
});
