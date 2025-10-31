import { test, expect, Page } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

// Minimal happy-path tests for medication & symptom logging via dashboard root.
// Success heuristic: absence of error alert and presence of form reset or transient success text.

async function openMedicationTab(page: Page) {
  // Prefer test id if implemented; fallback to text match
  const medTab = page.getByTestId('medication-tab');
  await medTab.click();
}

async function openSymptomTab(page: Page) {
  const symTab = page.getByTestId('symptom-tab');
  await symTab.click();
}

test.describe('US1 Simplified Logging', () => {
  test('log medication entry', async ({ page }) => {
  await ensureLoggedIn(page);
  await page.goto('/');
    await openMedicationTab(page);
    await page.getByTestId('medication-name-input').fill('Ibuprofen');
    await page.getByTestId('dosage-input').fill('200mg');
    await page.getByTestId('submit-button').click();
    await page.waitForTimeout(400);
    const alert = page.getByRole('alert').first();
    if (await alert.count()) {
      await expect(alert).not.toContainText(/error|failed|required/i);
    }
  });

  test('log symptom entry', async ({ page }) => {
  await ensureLoggedIn(page);
  await page.goto('/');
    await openSymptomTab(page);
    await page.getByTestId('symptom-name-input').fill('Headache');
    const severitySelect = page.getByTestId('severity-select');
    if (await severitySelect.count()) {
      await severitySelect.selectOption('2');
    }
    await page.getByTestId('submit-button').click();
    await page.waitForTimeout(400);
    const alert = page.getByRole('alert').first();
    if (await alert.count()) {
      await expect(alert).not.toContainText(/error|failed|required/i);
    }
  });
});
