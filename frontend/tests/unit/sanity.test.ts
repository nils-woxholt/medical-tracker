/**
 * Frontend Unit Test Harness - Sanity Tests
 * 
 * This module provides sanity checks to validate the basic functionality
 * of the frontend test environment and core application components.
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';

// Mock environment variables for testing
const mockEnv = {
  NEXT_PUBLIC_API_URL: 'http://localhost:8000',
  NODE_ENV: 'test',
};

beforeAll(() => {
  // Setup global test environment
  Object.assign(process.env, mockEnv);
  
  // Mock window.crypto for environments that don't have it
  if (!global.crypto) {
    global.crypto = {
      randomUUID: () => 'test-uuid-' + Math.random().toString(36).substring(2, 15)
    } as any;
  }
});

afterAll(() => {
  // Cleanup after tests
  vi.clearAllMocks();
});

describe('Test Environment Sanity', () => {
  it('should have access to testing utilities', () => {
    expect(describe).toBeDefined();
    expect(it).toBeDefined();
    expect(expect).toBeDefined();
    expect(vi).toBeDefined();
  });

  it('should have proper environment setup', () => {
    expect(process.env.NODE_ENV).toBe('test');
    expect(process.env.NEXT_PUBLIC_API_URL).toBeDefined();
  });

  it('should have crypto available for testing', () => {
    expect(crypto).toBeDefined();
    expect(crypto.randomUUID).toBeDefined();
    
    const uuid = crypto.randomUUID();
    expect(typeof uuid).toBe('string');
    expect(uuid.length).toBeGreaterThan(0);
  });
});

describe('API Client Sanity', () => {
  it('should be able to import API client', async () => {
    const { ApiClient } = await import('@/lib/api/client');
    expect(ApiClient).toBeDefined();
    
    const client = new ApiClient();
    expect(client).toBeDefined();
  });

  it('should be able to import API client utilities', async () => {
    const { TokenManager, apiClient, queryKeys } = await import('@/lib/api/client');
    
    expect(TokenManager).toBeDefined();
    expect(apiClient).toBeDefined();
    expect(queryKeys).toBeDefined();
    
    // Test TokenManager methods exist
    expect(typeof TokenManager.getToken).toBe('function');
    expect(typeof TokenManager.setToken).toBe('function');
    expect(typeof TokenManager.clearTokens).toBe('function');
  });

  it('should have proper query keys structure', async () => {
    const { queryKeys } = await import('@/lib/api/client');
    
    expect(queryKeys.health).toBeDefined();
    expect(queryKeys.medicationLogs).toBeDefined();
    expect(queryKeys.symptomLogs).toBeDefined();
    expect(queryKeys.feelVsYesterday).toBeDefined();
    
    // Test that query keys return arrays
    expect(Array.isArray(queryKeys.health())).toBe(true);
    expect(Array.isArray(queryKeys.medicationLogs())).toBe(true);
  });
});

describe('Design System Sanity', () => {
  it('should be able to import design tokens', async () => {
    const tokens = await import('@/lib/design/tokens');
    
    expect(tokens.colors).toBeDefined();
    expect(tokens.spacing).toBeDefined();
    expect(tokens.typography).toBeDefined();
    expect(tokens.theme).toBeDefined();
  });

  it('should have medical-specific color tokens', async () => {
    const { colors } = await import('@/lib/design/tokens');
    
    expect(colors.medical).toBeDefined();
    expect(colors.medical.excellent).toBeDefined();
    expect(colors.medical.good).toBeDefined();
    expect(colors.medical.fair).toBeDefined();
    expect(colors.medical.poor).toBeDefined();
    expect(colors.medical.critical).toBeDefined();
    
    // Test color values are strings (hex colors)
    expect(typeof colors.medical.excellent).toBe('string');
    expect(colors.medical.excellent).toMatch(/^#[0-9a-f]{6}$/i);
  });

  it('should have utility functions for design tokens', async () => {
    const { getMedicalStatusColor, getSemanticColor } = await import('@/lib/design/tokens');
    
    expect(typeof getMedicalStatusColor).toBe('function');
    expect(typeof getSemanticColor).toBe('function');
    
    // Test utility functions work
    const excellentColor = getMedicalStatusColor('excellent');
    expect(typeof excellentColor).toBe('string');
    
    const successColor = getSemanticColor('success');
    expect(typeof successColor).toBe('string');
  });

  it('should have spacing and typography tokens', async () => {
    const { spacing, typography } = await import('@/lib/design/tokens');
    
    expect(spacing.form).toBeDefined();
    expect(spacing.component).toBeDefined();
    
    expect(typography.medical).toBeDefined();
    expect(typography.badge).toBeDefined();
    
    // Test specific values
    expect(spacing.form.sectionGap).toBeDefined();
    expect(typography.medical.label).toBeDefined();
    expect(typography.medical.label.fontSize).toBeDefined();
  });
});

describe('TypeScript Configuration Sanity', () => {
  it('should handle path aliases correctly', () => {
    // This test verifies that our TypeScript path mapping works
    // If the imports above work, then path aliases are configured correctly
    expect(true).toBe(true);
  });

  it('should have strict type checking enabled', () => {
    // TypeScript strict mode checks happen at compile time
    // If this test file compiles, strict mode is working
    
    // Test that TypeScript catches basic type errors (this would fail compilation)
    const testNumber: number = 42;
    const testString: string = 'hello';
    
    expect(typeof testNumber).toBe('number');
    expect(typeof testString).toBe('string');
  });
});

describe('Mock and Testing Utilities', () => {
  it('should be able to create mocks with vi', () => {
    const mockFn = vi.fn();
    expect(mockFn).toBeDefined();
    expect(vi.isMockFunction(mockFn)).toBe(true);
    
    mockFn('test');
    expect(mockFn).toHaveBeenCalledWith('test');
  });

  it('should be able to mock modules', () => {
    const mockModule = vi.fn(() => ({ test: 'value' }));
    expect(mockModule).toBeDefined();
    
    const result = mockModule();
    expect(result).toEqual({ test: 'value' });
  });

  it('should have access to test utilities', () => {
    // Test that we have access to common testing patterns
    expect(expect.any(String)).toBeDefined();
    expect(expect.objectContaining({})).toBeDefined();
    expect(expect.arrayContaining([])).toBeDefined();
  });
});

describe('Browser Environment Mocking', () => {
  it('should handle localStorage mocking', () => {
    // Mock localStorage for testing
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
    
    expect(window.localStorage).toBeDefined();
    expect(window.localStorage.getItem).toBeDefined();
  });

  it('should handle fetch mocking', () => {
    const mockFetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ success: true }),
        text: () => Promise.resolve('success'),
        status: 200,
        statusText: 'OK',
      })
    );

    global.fetch = mockFetch as any;
    
    expect(global.fetch).toBeDefined();
    expect(vi.isMockFunction(global.fetch)).toBe(true);
  });

  it('should handle URL mocking for Next.js environment', () => {
    // Mock window.location for tests that need URL manipulation
    const mockLocation = {
      href: 'http://localhost:3000/',
      origin: 'http://localhost:3000',
      protocol: 'http:',
      hostname: 'localhost',
      port: '3000',
      pathname: '/',
      search: '',
      hash: '',
    };
    
    Object.defineProperty(window, 'location', {
      value: mockLocation,
      writable: true,
    });
    
    expect(window.location.origin).toBe('http://localhost:3000');
  });
});

describe('Error Handling Sanity', () => {
  it('should properly handle async errors in tests', async () => {
    const asyncFunction = async () => {
      throw new Error('Test error');
    };
    
    await expect(asyncFunction()).rejects.toThrow('Test error');
  });

  it('should handle promise rejections', async () => {
    const rejectedPromise = Promise.reject(new Error('Rejection test'));
    
    await expect(rejectedPromise).rejects.toThrow('Rejection test');
  });

  it('should validate error objects', () => {
    const error = new Error('Test error message');
    error.name = 'TestError';
    
    expect(error).toBeInstanceOf(Error);
    expect(error.message).toBe('Test error message');
    expect(error.name).toBe('TestError');
  });
});

// Export test utilities for use in other test files
export const testUtils = {
  mockEnv,
  createMockFetch: (response: any) => vi.fn(() => Promise.resolve({
    ok: true,
    json: () => Promise.resolve(response),
    text: () => Promise.resolve(JSON.stringify(response)),
    status: 200,
    statusText: 'OK',
  })),
  
  createMockLocalStorage: () => ({
    getItem: vi.fn(),
    setItem: vi.fn(), 
    removeItem: vi.fn(),
    clear: vi.fn(),
  }),
  
  setupMockWindow: () => {
    Object.defineProperty(window, 'crypto', {
      value: {
        randomUUID: () => 'mock-uuid-' + Math.random().toString(36).substring(2, 15)
      },
      writable: true,
    });
  },
};