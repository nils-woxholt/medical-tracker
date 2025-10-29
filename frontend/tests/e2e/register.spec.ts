import { test, expect } from '@playwright/test';

// E2E registration flow (T037): user registers, sees success banner, auto-login occurs (login form visible with banner)

function uniqueEmail() {
  return `user_${Date.now()}_${Math.floor(Math.random()*10000)}@example.com`;
}

const strongPassword = 'Str0ng!Pass123';

test.describe('Registration Flow', () => {
  test('rejects weak password', async ({ page }) => {
    await page.goto('/access');
    await page.getByTestId('auth-toggle-register').click();
    await page.getByTestId('reg-email').fill(uniqueEmail());
    await page.getByTestId('reg-password').fill('abc'); // weak
    await page.getByTestId('reg-submit').click();
    await expect(page.getByTestId('reg-error')).toContainText('WEAK_PASSWORD');
  });

  test('successful registration shows banner and switches to login', async ({ page }) => {
    const email = uniqueEmail();
    const displayName = 'TestUser';
    await page.goto('/access');
    await page.getByTestId('auth-toggle-register').click();
    await page.getByTestId('reg-email').fill(email);
    await page.getByTestId('reg-display-name').fill(displayName);
    await page.getByTestId('reg-password').fill(strongPassword);
    await page.getByTestId('reg-submit').click();
    // Banner appears
    await expect(page.getByTestId('registration-banner')).toBeVisible();
    await expect(page.getByTestId('registration-banner')).toContainText('Welcome');
    await expect(page.getByTestId('registration-banner')).toContainText(displayName);
    // Mode switches to login form
    await expect(page.getByTestId('login-form')).toBeVisible();
  });
});
