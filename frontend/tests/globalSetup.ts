import { chromium, FullConfig, Page } from '@playwright/test';

// Global setup to ensure a deterministic authenticated storage state for E2E specs.
// Strategy:
// 1. Visit /access?mode=register with a fixed email; if registration fails because user exists, ignore.
// 2. Perform login via /access?mode=login using the same credentials.
// 3. Save storageState to tests/.auth/storageState.json
// Relies on frontend exposing forms with data-testid login-email/login-password/login-submit & reg-email/reg-password/reg-display-name/reg-submit.
// If backend returns 4xx for existing user, we proceed to login step regardless.

const TEST_EMAIL = 'e2e_user@example.com';
const TEST_PASSWORD = 'E2E_Pass123!';
const DISPLAY_NAME = 'E2E User';

async function attemptRegister(page: Page) {
  await page.goto('/access?mode=register');
  await page.getByTestId('reg-email').fill(TEST_EMAIL);
  await page.getByTestId('reg-password').fill(TEST_PASSWORD);
  await page.getByTestId('reg-display-name').fill(DISPLAY_NAME);
  await page.getByTestId('reg-submit').click();
  // Wait a short time for either success or error banner
  await page.waitForTimeout(1000);
}

async function performLogin(page: Page) {
  await page.goto('/access?mode=login');
  await page.getByTestId('login-email').fill(TEST_EMAIL);
  await page.getByTestId('login-password').fill(TEST_PASSWORD);
  await page.getByTestId('login-submit').click();
  // Wait for redirect to dashboard/home (assume '/')
  await page.waitForURL('**/');
}

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await attemptRegister(page); // ignore if user already exists
  } catch (e) {
    // swallow errors (user may already exist)
  }

  // Always attempt login
  await performLogin(page);

  await page.context().storageState({ path: 'tests/.auth/storageState.json' });
  await browser.close();
}

export default globalSetup;
