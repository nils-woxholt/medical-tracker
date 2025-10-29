/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
// NOTE: We deliberately omit @vitejs/plugin-react here and instead rely on automatic React JSX transform.
// If tests need the React identifier (older patterns), we inject it below via esbuild.jsxInject.

export default defineConfig({
  // React plugin omitted; using esbuild.jsxInject ensures legacy tests that expect global React still pass.
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
        '.next/**',
        '.next/static/**',
        '.next/cache/**',
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
        '**/global-error.tsx',
        // Generated vendor / runtime chunks (avoid skewing coverage %)
        '**/vendor-chunks/**',
        '**/webpack-runtime.js',
        '**/polyfills.js'
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
  },
  esbuild: {
    jsx: 'automatic',
    jsxImportSource: 'react',
    // Some existing test files rely on React being in scope (ReferenceError: React is not defined).
    // Inject `import React from "react"` automatically to satisfy those without adding manual imports everywhere.
    jsxInject: 'import React from "react"'
  }
})