import { defineConfig, devices } from '@playwright/test';

// Root Playwright config (added to ensure Playwright picks configuration when run from project root or frontend folder).
// Mirrors existing detailed config under tests/e2e but adjusts webServer to use dev mode for faster iteration
// and uses uv per backend instructions.

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['json', { outputFile: 'test-results/results.json' }],
    process.env.CI ? ['github'] : ['line'],
  ],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    extraHTTPHeaders: { 'X-Test-Environment': 'e2e' },
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    navigationTimeout: 30000,
    actionTimeout: 10000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 720 } } },
  ],
  webServer: [
    {
      // Use dev server for speed; build currently fails due to unrelated pages.
      command: 'npm run dev',
      port: 3000,
      reuseExistingServer: true,
      timeout: 60000,
      env: {
        NODE_ENV: 'test',
        NEXT_PUBLIC_API_URL: process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000',
        NEXT_PUBLIC_E2E: '1',
      },
    },
    {
      // Backend: run migrations then start uvicorn (schema needed for auth endpoints during E2E).
      command: process.platform === 'win32'
        ? 'pwsh -NoLogo -NoProfile -Command "cd ../backend; uv run alembic upgrade head; uv run uvicorn app.main:app --host localhost --port 8000"'
        : 'bash -lc "cd ../backend && uv run alembic upgrade head && uv run uvicorn app.main:app --host localhost --port 8000"',
      port: 8000,
      reuseExistingServer: true,
      timeout: 30000,
      env: {
        DATABASE_URL: 'sqlite:///test_e2e.db',
        ENVIRONMENT: 'testing',
        NEXT_PUBLIC_E2E: '1',
      },
    },
  ],
  expect: { timeout: 5000 },
  timeout: 30000,
  testMatch: [
    'tests/e2e/**/*.spec.ts',
    'tests/e2e/**/*.test.ts',
  ],
  testIgnore: [
    '**/node_modules/**',
    '**/dist/**',
    '**/*.config.ts',
  ],
  outputDir: 'test-results/',
});
