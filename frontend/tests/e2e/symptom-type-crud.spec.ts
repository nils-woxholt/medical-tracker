import { test, expect, Page } from '@playwright/test';
import { ensureLoggedIn } from './helpers/auth';

const PAGE_URL = '/symptom-types';

async function createSymptomType(page: Page, name: string, description: string) {
  await page.getByTestId('symptom-type-name').fill(name);
  await page.getByTestId('symptom-type-description').fill(description);
  await page.getByTestId('symptom-type-submit').click();
}

async function editSymptomType(page: Page, name: string, newDescription: string) {
  // Button naming convention assumed: Edit <name>
  await page.getByRole('button', { name: `Edit ${name}` }).click();
  const desc = page.getByTestId('symptom-type-description');
  await desc.fill(newDescription);
  await page.getByTestId('symptom-type-submit').click();
}

async function deactivateSymptomType(page: Page, name: string) {
  // Accept native confirm if present; if replaced later adjust accordingly.
  page.on('dialog', d => d.accept());
  await page.getByRole('button', { name: `Deactivate ${name}` }).click();
}

test.describe('Symptom Type CRUD flow', () => {
  test('create, edit, deactivate symptom type', async ({ page }) => {
  await ensureLoggedIn(page);
  await page.goto(PAGE_URL);
    await expect(page.getByTestId('symptom-types-page')).toBeVisible();
    // Wait for form inputs to hydrate
    await page.getByTestId('symptom-type-name').waitFor({ state: 'visible' });
    await page.getByTestId('symptom-type-description').waitFor({ state: 'visible' });

    const uniqueName = `Dizzy-${Date.now()}`;
    await createSymptomType(page, uniqueName, 'Spinning');
    await expect(page.getByText(uniqueName)).toBeVisible();

    await editSymptomType(page, uniqueName, 'Spinning sensation improved');
    await expect(page.getByText('Spinning sensation improved')).toBeVisible();

    await deactivateSymptomType(page, uniqueName);
    await expect(page.getByText('Inactive')).toBeVisible();
  });
});
