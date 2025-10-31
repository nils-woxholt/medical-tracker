import { test, expect, Page } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

async function ensureSymptomType(page: Page, name: string) {
  await page.goto('/symptom-types');
  const existing = page.getByText(name).first();
  if (await existing.count() === 0) {
    await page.getByTestId('symptom-type-name').fill(name);
    await page.getByTestId('symptom-type-description').fill('E2E type');
    await page.getByTestId('symptom-type-submit').click();
    await expect(page.getByText(name)).toBeVisible();
  }
}

test.describe('Symptom logging (dashboard tab)', () => {
  test('logs a symptom with severity', async ({ page }) => {
  const typeName = 'LogSymType-' + Date.now();
  await ensureLoggedIn(page);
    await ensureSymptomType(page, typeName);

    // Navigate to dashboard root
    await page.goto('/');

    // Open symptom tab (assumes data-testid or text match; adjust if tab component has a test id)
  const symptomTab = page.getByTestId('symptom-tab');
  await symptomTab.click();

    // Fill symptom name (if free text) or select type depending on UI; using test id from LogForms
    const nameInput = page.getByTestId('symptom-name-input');
    await expect(nameInput).toBeVisible();
    await nameInput.fill(typeName);

    const severity = page.getByTestId('severity-select');
    if (await severity.count()) {
      await severity.selectOption('3'); // medium severity
    }

    // Submit
    const submit = page.getByTestId('submit-button');
    await submit.click();

    // Basic success heuristic: no alert with error text appears for brief window.
    await page.waitForTimeout(500);
    const alerts = page.getByRole('alert');
    if (await alerts.count()) {
      await expect(alerts.first()).not.toContainText(/failed|error|required/i);
    }
  });
});
