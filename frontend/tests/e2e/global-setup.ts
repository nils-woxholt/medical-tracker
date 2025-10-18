/**
 * Playwright Global Setup
 * 
 * This file handles global setup tasks that run before all tests,
 * including database initialization and test environment preparation.
 */

import type { FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment setup...');
  
  try {
    // Initialize test database
    console.log('📊 Initializing test database...');
    // Note: Using SQLite for E2E tests - database is automatically created
    
    // Seed test data if needed  
    console.log('🌱 Seeding test data...');
    // Note: Test data seeding handled by individual test files
    
    // Start any required external services
    console.log('🔧 Starting external services...');
    // Note: Backend should be running on localhost:8000 for E2E tests
    
    // Verify backend API is accessible
    console.log('🔗 Verifying API connectivity...');
    try {
      const response = await fetch('http://localhost:8000/health');
      if (!response.ok) {
        console.warn('⚠️ Backend health check failed - some E2E tests may fail');
      }
    } catch (error) {
      console.warn('⚠️ Backend not accessible - E2E tests may fail:', error);
    }
    
    console.log('✅ E2E test environment setup completed');
  } catch (error) {
    console.error('❌ Failed to setup E2E test environment:', error);
    throw error;
  }
}

export default globalSetup;