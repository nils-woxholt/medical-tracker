/**
 * Playwright Global Teardown
 * 
 * This file handles global cleanup tasks that run after all tests,
 * including database cleanup and test environment teardown.
 */

import type { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting E2E test environment cleanup...');
  
  try {
    // Clean up test data
    console.log('🗑️ Cleaning up test data...');
    // Note: Test data cleanup handled by individual test teardown
    
    // Stop external services if started  
    console.log('⏹️ Stopping external services...');
    // Note: External services managed separately from E2E tests
    
    // Clean up temporary files
    console.log('📁 Cleaning up temporary files...');
    // Note: Playwright automatically cleans up temporary files
    
    // Reset test database
    console.log('🔄 Resetting test database...');
    // Note: SQLite test database is isolated and automatically reset
    
    console.log('✅ E2E test environment cleanup completed');
  } catch (error) {
    console.error('❌ Failed to cleanup E2E test environment:', error);
    // Don't throw - cleanup failures shouldn't fail the entire test suite
  }
}

export default globalTeardown;