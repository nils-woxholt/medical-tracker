import { test, expect } from '@playwright/test';

// Assumptions:
// - Dev server serves protected dashboard at /dashboard which uses ProtectedLayout guard.
// - Visiting /dashboard unauthenticated redirects to /login.
// - Login page has labeled inputs 'Email' and 'Password' and a button with text 'Login'.
// - Backend test environment: registering via API may not be available; this test currently
//   focuses on redirect + validation skeleton and will be extended once stable login endpoint returns identity.

test.describe('Login Flow (US1)', () => {
  test('unauthenticated visit to protected route redirects to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('shows validation errors then (placeholder) attempts login', async ({ page }) => {
    await page.goto('/login');
    // Click submit with empty fields
    await page.getByRole('button', { name: /login/i }).click();
    await expect(page.getByRole('alert')).toHaveText(/EMAIL_PASSWORD_REQUIRED/);
    // Fill invalid short password
    await page.getByLabel(/email/i).fill('user@example.com');
    await page.getByLabel(/password/i).fill('short');
    await page.getByRole('button', { name: /login/i }).click();
    await expect(page.getByRole('alert')).toHaveText(/PASSWORD_TOO_SHORT/);
  });

  // Placeholder success test (will be enabled once a deterministic test user + login endpoint is wired)
  test.skip('successful login redirects back to originally requested protected route', async ({ page }) => {
    // Arrange: start at protected path
    await page.goto('/dashboard');
    await page.waitForURL('**/login');
    await page.getByLabel(/email/i).fill('user@example.com');
    await page.getByLabel(/password/i).fill('ValidPass123');
    await page.getByRole('button', { name: /login/i }).click();
    // Expect redirect to /dashboard without intermediate protected content flash markers
    await page.waitForURL('**/dashboard');
    await expect(page).toHaveURL(/\/dashboard$/);
  });
});
