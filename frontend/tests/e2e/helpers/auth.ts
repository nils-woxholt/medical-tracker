import { Page } from '@playwright/test';

// Deterministic credentials (idempotent registration)
const TEST_EMAIL = 'e2e_user@example.com';
const TEST_PASSWORD = 'E2E_Pass123!!'; // >=10 chars per schema
const DISPLAY_NAME = 'E2E User';
const TOKEN_STORAGE_KEY = 'saas_medical_tracker_token';

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

async function apiRegister(page: Page) {
  const res = await page.request.post(apiBase() + '/auth/register', {
    data: { email: TEST_EMAIL, password: TEST_PASSWORD, display_name: DISPLAY_NAME }
  });
  if (![201, 400, 409].includes(res.status())) {
    throw new Error('Unexpected register status ' + res.status());
  }
}

async function apiLogin(page: Page): Promise<void> {
  const candidatePasswords = [TEST_PASSWORD, 'E2E_Pass123!'];
  for (const pwd of candidatePasswords) {
    const res = await page.request.post(apiBase() + '/auth/login', {
      data: { email: TEST_EMAIL, password: pwd }
    });
    if (res.status() === 200) {
      const setCookie = res.headers()['set-cookie'];
      if (setCookie) {
        const parts = setCookie.split(/,(?=[^;]+=[^;]+)/);
        const cookies = parts.map(p => {
          const first = p.split(';')[0];
          if (!first) return { name: '', value: '', url: apiBase() };
          const eq = first.indexOf('=');
          const name = eq > 0 ? first.slice(0, eq).trim() : '';
          const value = eq > 0 ? first.slice(eq + 1).trim() : '';
          return { name, value, url: apiBase() };
        }).filter(c => c.name && c.value);
        if (cookies.length) await page.context().addCookies(cookies);
      }
      return;
    }
  }
  throw new Error('Login failed with all candidate passwords');
}

export async function ensureLoggedIn(page: Page) {
  // If already authenticated (log forms visible), skip.
  if (await page.getByTestId('log-forms-tabs').count()) return;
  // Register (ignore errors if already exists)
  await apiRegister(page).catch(() => {});
  await apiLogin(page);
  await page.goto('/dashboard');
  await page.getByTestId('log-forms-tabs').waitFor({ state: 'visible', timeout: 10000 });
}
