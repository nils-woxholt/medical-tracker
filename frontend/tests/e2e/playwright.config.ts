import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Testing Configuration for SaaS Medical Tracker
 * 
 * This configuration provides comprehensive end-to-end testing setup for
 * medical tracking workflows, including multi-browser testing, mobile viewport
 * simulation, and accessibility testing integration.
 */

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  // Test directory configuration
  testDir: './tests/e2e',
  
  // Run tests in files in parallel
  fullyParallel: true,
  
  // Fail the build on CI if you accidentally left test.only in the source code.
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI.
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter to use. See https://playwright.dev/docs/test-reporters
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    // Add JSON reporter for CI integration
    ['json', { outputFile: 'test-results/results.json' }],
    // Terminal output for development
    process.env.CI ? ['github'] : ['list'],
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL to use in actions like `await page.goto('/')`.
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    
    // Backend API URL for testing
    extraHTTPHeaders: {
      'X-Test-Environment': 'e2e',
    },
    
    // Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer
    trace: 'on-first-retry',
    
    // Capture screenshots on failure
    screenshot: 'only-on-failure',
    
    // Record video on failure for debugging
    video: 'retain-on-failure',
    
    // Navigation timeout
    navigationTimeout: 30000,
    
    // Action timeout
    actionTimeout: 10000,
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },
    
    // Desktop Browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Medical forms often need larger viewports
        viewport: { width: 1280, height: 720 },
      },
      dependencies: ['setup'],
    },
    
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        viewport: { width: 1280, height: 720 },
      },
      dependencies: ['setup'],
    },
    
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        viewport: { width: 1280, height: 720 },
      },
      dependencies: ['setup'],
    },

    // Mobile Browsers - Critical for medical accessibility
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
      },
      dependencies: ['setup'],
    },
    
    {
      name: 'Mobile Safari',
      use: { 
        ...devices['iPhone 12'],
      },
      dependencies: ['setup'],
    },

    // Tablet Testing - Important for healthcare environments
    {
      name: 'iPad',
      use: { 
        ...devices['iPad Pro'],
      },
      dependencies: ['setup'],
    },

    // Accessibility Testing Configuration
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
      },
      testMatch: /.*\.a11y\.spec\.ts/,
      dependencies: ['setup'],
    },

    // High Contrast Mode Testing (Important for medical accessibility)
    {
      name: 'high-contrast',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 },
        colorScheme: 'dark',
        // Force prefers-reduced-motion for accessibility testing
        reducedMotion: 'reduce',
      },
      testMatch: /.*\.contrast\.spec\.ts/,
      dependencies: ['setup'],
    },
  ],

  // Run your local dev server before starting the tests
  webServer: [
    {
      command: 'npm run build && npm run start',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
      env: {
        NODE_ENV: 'test',
        NEXT_PUBLIC_API_URL: process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000',
      },
    },
    // Also start backend for integration testing
    {
      command: process.platform === 'win32' 
        ? 'cd ../backend && .\\venv\\Scripts\\Activate.ps1 && uvicorn app.main:app --port 8000'
        : 'cd ../backend && source venv/bin/activate && uvicorn app.main:app --port 8000',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      env: {
        DATABASE_URL: 'sqlite:///test_e2e.db',
        ENVIRONMENT: 'testing',
      },
    },
  ],

  // Global test configuration
  globalSetup: require.resolve('./tests/e2e/global-setup.ts'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.ts'),

  // Expect configuration
  expect: {
    // Maximum time expect() should wait for the condition to be met.
    timeout: 5000,
    
    // Threshold for screenshot comparison (medical UIs need pixel-perfect accuracy)
    threshold: 0.2,
    
    // Configure visual comparison for medical forms
    toHaveScreenshot: {
      mode: 'css',
      animations: 'disabled', // Important for consistent medical form screenshots
    },
  },

  // Test execution configuration
  timeout: 30000,
  
  // Test file patterns
  testMatch: [
    'tests/e2e/**/*.spec.ts',
    'tests/e2e/**/*.test.ts',
  ],
  
  // Ignore files
  testIgnore: [
    '**/node_modules/**',
    '**/dist/**',
    '**/*.config.ts',
  ],

  // Output directory
  outputDir: 'test-results/',
  
  // Maximum number of failures before stopping
  maxFailures: process.env.CI ? 5 : undefined,

  // Medical application specific metadata
  metadata: {
    applicationName: 'SaaS Medical Tracker',
    testEnvironment: 'e2e',
    complianceNote: 'Tests include HIPAA-compliant data handling scenarios',
    accessibilityLevel: 'WCAG 2.1 AA',
  },
});