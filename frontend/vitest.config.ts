/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    css: true,
    deps: {
      moduleDirectories: ['node_modules', 'src']
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary', 'json'],
      reportsDirectory: './coverage',
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        }
      },
      exclude: [
        'coverage/**',
        'dist/**',
        'packages/*/test{,s}/**',
        '**/*.d.ts',
        'cypress/**',
        'test{,s}/**',
        'test{,-*}.{js,cjs,mjs,ts,tsx,jsx}',
        '**/*{.,-}test.{js,cjs,mjs,ts,tsx,jsx}',
        '**/*{.,-}spec.{js,cjs,mjs,ts,tsx,jsx}',
        '**/__tests__/**',
        '**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*',
        '**/.{eslint,mocha,prettier}rc.{js,cjs,yml}',
        '**/next.config.{js,ts}',
        '**/tailwind.config.{js,ts}',
        '**/postcss.config.{js,ts}',
        'pages/_app.tsx',
        'pages/_document.tsx',
        'pages/api/**',
        '**/layout.tsx',
        '**/loading.tsx',
        '**/not-found.tsx',
        '**/error.tsx',
        '**/global-error.tsx'
      ]
    },
    // Test file patterns
    include: [
      'tests/unit/**/*.{test,spec}.{js,ts,tsx}',
      'src/**/*.{test,spec}.{js,ts,tsx}',
      'components/**/*.{test,spec}.{js,ts,tsx}',
      'lib/**/*.{test,spec}.{js,ts,tsx}'
    ],
    exclude: [
      'node_modules/**',
      'dist/**',
      '.next/**',
      'coverage/**',
      'tests/e2e/**'
    ]
  },
  resolve: {
    alias: {
      '@': 'C:/dev/lseg/spec-kit/todo/frontend/src',
      '@/components': 'C:/dev/lseg/spec-kit/todo/frontend/src/components',
      '@/lib': 'C:/dev/lseg/spec-kit/todo/frontend/src/lib',
      '@/app': 'C:/dev/lseg/spec-kit/todo/frontend/src/app',
      '@/types': 'C:/dev/lseg/spec-kit/todo/frontend/src/types'
    }
  }
})