import { test, expect } from '@playwright/test';

// E2E Demo session journey (T048)
// 1. Start demo session via POST /auth/demo (simulate button or direct call)
// 2. Navigate to dashboard and see demo banner
// 3. Click Create Account -> go to register page

async function startDemo(request: any) {
  const resp = await request.post('/auth/demo');
  expect(resp.ok()).toBeTruthy();
  const body = await resp.json();
  expect(body.data.session.demo).toBeTruthy();
}

test('demo session banner appears and registration reachable', async ({ page, request }) => {
  await startDemo(request);
  // Go to dashboard
  await page.goto('/dashboard');
  // Banner should appear
  const bannerTitle = page.getByText('Demo Mode');
  await expect(bannerTitle).toBeVisible();
  // Click Create Account
  const createBtn = page.getByRole('button', { name: /Create Account/i });
  await createBtn.click();
  await expect(page).toHaveURL(/\/auth\/register/);
});
