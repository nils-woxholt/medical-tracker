/**
 * End-to-End Tests for User Story 1: Log Daily Medication & Symptoms
 * 
 * This test suite validates the complete user journey for logging medication 
 * and symptom entries, viewing summaries, and checking feel-vs-yesterday status.
 * 
 * Test Coverage:
 * - Complete medication logging flow
 * - Complete symptom logging flow  
 * - Summary display and updates
 * - Feel vs yesterday status computation
 * - Integration between all components
 * - Error handling and edge cases
 */

import { test, expect, Page } from '@playwright/test'

// Test configuration
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'

// Test user credentials (these would be set up in test database)
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123',
  id: 'test-user-e2e'
}

// Helper function to authenticate user
async function authenticateUser(page: Page) {
  // Mock authentication for E2E tests
  // In real implementation, this would go through login flow
  await page.addInitScript(() => {
    // Mock JWT token in localStorage
    localStorage.setItem('auth_token', 'mock-jwt-token-for-e2e-tests')
    localStorage.setItem('user_id', 'test-user-e2e')
  })
}

// Helper function to wait for API calls to complete
async function waitForApiResponse(page: Page, urlPattern: string) {
  return page.waitForResponse(response => 
    response.url().includes(urlPattern) && response.status() === 200
  )
}

// Helper function to clear all test data
async function clearTestData(page: Page) {
  // Clear any existing test data via API
  await page.request.delete(`${BACKEND_URL}/api/test/cleanup/${TEST_USER.id}`)
}

test.describe('User Story 1: Log Daily Medication & Symptoms', () => {
  test.beforeEach(async ({ page }) => {
    // Set up clean test environment
    await clearTestData(page)
    await authenticateUser(page)
    
    // Navigate to landing page
    await page.goto(FRONTEND_URL)
    await page.waitForLoadState('networkidle')
  })

  test.afterEach(async ({ page }) => {
    // Clean up test data after each test
    await clearTestData(page)
  })

  test('should complete full medication logging flow', async ({ page }) => {
    // Navigate to medication logging
    await page.getByRole('button', { name: /log medication/i }).click()
    
    // Verify medication form is displayed
    await expect(page.getByTestId('medication-log-form')).toBeVisible()
    
    // Fill out medication form
    await page.getByTestId('medication-name-input').fill('Ibuprofen')
    await page.getByTestId('dosage-input').fill('200mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T10:30')
    await page.getByTestId('effectiveness-rating-select').selectOption('4')
    await page.getByTestId('side-effect-select').selectOption('mild')
    await page.getByTestId('notes-textarea').fill('Took for headache after morning meeting')
    
    // Submit the form
    const apiResponsePromise = waitForApiResponse(page, '/api/logs/medications')
    await page.getByTestId('submit-button').click()
    await apiResponsePromise
    
    // Verify success message or redirect
    await expect(page.getByText(/medication logged successfully/i)).toBeVisible()
    
    // Verify medication appears in summary
    await expect(page.getByTestId('medication-logs-section')).toBeVisible()
    await expect(page.getByText('Ibuprofen - 200mg')).toBeVisible()
    await expect(page.getByText('Effectiveness: 4/5')).toBeVisible()
  })

  test('should complete full symptom logging flow', async ({ page }) => {
    // Navigate to symptom logging  
    await page.getByRole('button', { name: /log symptom/i }).click()
    
    // Verify symptom form is displayed
    await expect(page.getByTestId('symptom-log-form')).toBeVisible()
    
    // Fill out symptom form
    await page.getByTestId('symptom-name-input').fill('Migraine')
    await page.getByTestId('severity-select').selectOption('severe')
    await page.getByTestId('started-at-input').fill('2024-01-15T14:15')
    await page.getByTestId('duration-input').fill('180')
    await page.getByTestId('impact-rating-select').selectOption('4')
    await page.getByTestId('triggers-input').fill('Stress, bright lights')
    await page.getByTestId('notes-textarea').fill('Sharp pain on right side, sensitivity to light')
    
    // Submit the form
    const apiResponsePromise = waitForApiResponse(page, '/api/logs/symptoms')
    await page.getByTestId('submit-button').click()
    await apiResponsePromise
    
    // Verify success message
    await expect(page.getByText(/symptom logged successfully/i)).toBeVisible()
    
    // Verify symptom appears in summary
    await expect(page.getByTestId('symptom-logs-section')).toBeVisible()
    await expect(page.getByText('Migraine')).toBeVisible()
    await expect(page.getByText('Severity: severe')).toBeVisible()
    await expect(page.getByText('Impact: 4/5')).toBeVisible()
  })

  test('should display and update feel vs yesterday status', async ({ page }) => {
    // Initially should show unknown status (no data)
    await expect(page.getByTestId('feel-status')).toBeVisible()
    await expect(page.getByTestId('feel-status-value')).toHaveText('Unknown')
    
    // Log a medication entry for "today"
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('medication-name-input').fill('Aspirin')
    await page.getByTestId('dosage-input').fill('325mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T08:00')
    await page.getByTestId('effectiveness-rating-select').selectOption('5')
    
    const medicationResponsePromise = waitForApiResponse(page, '/api/logs/medications')
    await page.getByTestId('submit-button').click()
    await medicationResponsePromise
    
    // Go back to main page and wait for feel status update
    await page.getByRole('button', { name: /back|close|cancel/i }).click()
    
    const feelResponsePromise = waitForApiResponse(page, '/api/feel/vs-yesterday')
    await page.reload()
    await feelResponsePromise
    
    // Status might still be unknown without yesterday's data, but should show confidence
    await expect(page.getByTestId('feel-status')).toBeVisible()
    await expect(page.getByTestId('feel-confidence')).toBeVisible()
  })

  test('should handle form validation errors', async ({ page }) => {
    // Try to submit medication form without required fields
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('submit-button').click()
    
    // Form should show validation errors
    await expect(page.getByText(/medication name is required/i)).toBeVisible()
    await expect(page.getByText(/dosage is required/i)).toBeVisible()
    
    // Try to submit symptom form without required fields
    await page.getByRole('button', { name: /log symptom/i }).click()
    await page.getByTestId('submit-button').click()
    
    // Form should show validation errors
    await expect(page.getByText(/symptom name is required/i)).toBeVisible()
    await expect(page.getByText(/severity is required/i)).toBeVisible()
  })

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error response
    await page.route(`${BACKEND_URL}/api/logs/medications`, route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' })
      })
    })
    
    // Try to submit medication form
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('medication-name-input').fill('Test Med')
    await page.getByTestId('dosage-input').fill('100mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T12:00')
    await page.getByTestId('effectiveness-rating-select').selectOption('3')
    
    await page.getByTestId('submit-button').click()
    
    // Should display error message
    await expect(page.getByText(/failed to save medication log/i)).toBeVisible()
    
    // Form should remain open for retry
    await expect(page.getByTestId('medication-log-form')).toBeVisible()
  })

  test('should display multiple logs in summary correctly', async ({ page }) => {
    // Create multiple medication logs
    const medications = [
      { name: 'Aspirin', dosage: '325mg', effectiveness: '4' },
      { name: 'Ibuprofen', dosage: '200mg', effectiveness: '3' },
      { name: 'Acetaminophen', dosage: '500mg', effectiveness: '5' }
    ]
    
    for (const med of medications) {
      await page.getByRole('button', { name: /log medication/i }).click()
      await page.getByTestId('medication-name-input').fill(med.name)
      await page.getByTestId('dosage-input').fill(med.dosage)
      await page.getByTestId('taken-at-input').fill('2024-01-15T12:00')
      await page.getByTestId('effectiveness-rating-select').selectOption(med.effectiveness)
      
      const responsePromise = waitForApiResponse(page, '/api/logs/medications')
      await page.getByTestId('submit-button').click()
      await responsePromise
      
      // Wait for success and go back
      await page.getByRole('button', { name: /back|close|cancel/i }).click()
    }
    
    // Verify all medications appear in summary
    const medicationSection = page.getByTestId('medication-logs-section')
    await expect(medicationSection).toBeVisible()
    
    for (const med of medications) {
      await expect(medicationSection.getByText(`${med.name} - ${med.dosage}`)).toBeVisible()
    }
    
    // Create multiple symptom logs
    const symptoms = [
      { name: 'Headache', severity: 'moderate', impact: '3' },
      { name: 'Nausea', severity: 'mild', impact: '2' }
    ]
    
    for (const symptom of symptoms) {
      await page.getByRole('button', { name: /log symptom/i }).click()
      await page.getByTestId('symptom-name-input').fill(symptom.name)
      await page.getByTestId('severity-select').selectOption(symptom.severity)
      await page.getByTestId('started-at-input').fill('2024-01-15T14:00')
      await page.getByTestId('impact-rating-select').selectOption(symptom.impact)
      
      const responsePromise = waitForApiResponse(page, '/api/logs/symptoms')
      await page.getByTestId('submit-button').click()
      await responsePromise
      
      await page.getByRole('button', { name: /back|close|cancel/i }).click()
    }
    
    // Verify all symptoms appear in summary
    const symptomSection = page.getByTestId('symptom-logs-section')
    await expect(symptomSection).toBeVisible()
    
    for (const symptom of symptoms) {
      await expect(symptomSection.getByText(symptom.name)).toBeVisible()
      await expect(symptomSection.getByText(`Severity: ${symptom.severity}`)).toBeVisible()
    }
  })

  test('should limit summary display to 5 most recent logs', async ({ page }) => {
    // Create 7 medication logs
    for (let i = 1; i <= 7; i++) {
      await page.getByRole('button', { name: /log medication/i }).click()
      await page.getByTestId('medication-name-input').fill(`Medicine ${i}`)
      await page.getByTestId('dosage-input').fill('100mg')
      await page.getByTestId('taken-at-input').fill(`2024-01-${i.toString().padStart(2, '0')}T12:00`)
      await page.getByTestId('effectiveness-rating-select').selectOption('3')
      
      const responsePromise = waitForApiResponse(page, '/api/logs/medications')
      await page.getByTestId('submit-button').click()
      await responsePromise
      
      await page.getByRole('button', { name: /back|close|cancel/i }).click()
    }
    
    // Verify only 5 medications are displayed (most recent)
    const medicationLogs = page.getByTestId('medication-logs-list').getByRole('listitem')
    await expect(medicationLogs).toHaveCount(5)
    
    // Verify it shows the most recent ones (Medicine 7, 6, 5, 4, 3)
    await expect(page.getByText('Medicine 7 - 100mg')).toBeVisible()
    await expect(page.getByText('Medicine 3 - 100mg')).toBeVisible()
    
    // Verify older ones are not shown
    await expect(page.getByText('Medicine 1 - 100mg')).not.toBeVisible()
    await expect(page.getByText('Medicine 2 - 100mg')).not.toBeVisible()
  })

  test('should support keyboard navigation and accessibility', async ({ page }) => {
    // Navigate to medication form using keyboard
    await page.keyboard.press('Tab') // Focus on first interactive element
    await page.keyboard.press('Enter') // Activate log medication button
    
    // Should be able to navigate form with keyboard
    await expect(page.getByTestId('medication-log-form')).toBeVisible()
    
    // Tab through form fields
    await page.keyboard.press('Tab') // Medication name
    await page.keyboard.type('Test Med')
    
    await page.keyboard.press('Tab') // Dosage
    await page.keyboard.type('100mg')
    
    await page.keyboard.press('Tab') // Taken at
    await page.keyboard.type('2024-01-15T12:00')
    
    // Verify form can be submitted with keyboard
    await page.keyboard.press('Tab') // Effectiveness rating
    await page.keyboard.press('ArrowDown') // Select option
    await page.keyboard.press('ArrowDown') // Select option 2
    
    // Continue tabbing to submit button
    let tabCount = 0
    while (tabCount < 10) { // Prevent infinite loop
      const submitButton = page.getByTestId('submit-button')
      if (await submitButton.isVisible()) {
        // Check if submit button is focused by trying to activate it
        const focused = await page.evaluate(() => (document.activeElement as HTMLElement)?.dataset?.testid)
        if (focused === 'submit-button') break
      }
      await page.keyboard.press('Tab')
      tabCount++
    }
    
    // Submit with keyboard
    const responsePromise = waitForApiResponse(page, '/api/logs/medications')
    await page.keyboard.press('Enter')
    await responsePromise
    
    // Verify success
    await expect(page.getByText(/medication logged successfully/i)).toBeVisible()
  })

  test('should maintain data consistency across page reloads', async ({ page }) => {
    // Log a medication
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('medication-name-input').fill('Persistent Med')
    await page.getByTestId('dosage-input').fill('250mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T09:00')
    await page.getByTestId('effectiveness-rating-select').selectOption('4')
    
    const responsePromise = waitForApiResponse(page, '/api/logs/medications')
    await page.getByTestId('submit-button').click()
    await responsePromise
    
    await page.getByRole('button', { name: /back|close|cancel/i }).click()
    
    // Verify medication appears in summary
    await expect(page.getByText('Persistent Med - 250mg')).toBeVisible()
    
    // Reload the page
    await page.reload()
    await page.waitForLoadState('networkidle')
    
    // Verify data persists after reload
    await expect(page.getByText('Persistent Med - 250mg')).toBeVisible()
    await expect(page.getByText('Effectiveness: 4/5')).toBeVisible()
  })

  test('should handle concurrent user interactions', async ({ page, context }) => {
    // Simulate multiple browser tabs/windows
    const page2 = await context.newPage()
    await authenticateUser(page2)
    await page2.goto(FRONTEND_URL)
    await page2.waitForLoadState('networkidle')
    
    // Log medication in first tab
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('medication-name-input').fill('Concurrent Med 1')
    await page.getByTestId('dosage-input').fill('100mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T10:00')
    await page.getByTestId('effectiveness-rating-select').selectOption('3')
    
    // Log symptom in second tab simultaneously
    await page2.getByRole('button', { name: /log symptom/i }).click()
    await page2.getByTestId('symptom-name-input').fill('Concurrent Symptom')
    await page2.getByTestId('severity-select').selectOption('moderate')
    await page2.getByTestId('started-at-input').fill('2024-01-15T10:00')
    await page2.getByTestId('impact-rating-select').selectOption('3')
    
    // Submit both forms
    const medicationPromise = waitForApiResponse(page, '/api/logs/medications')
    const symptomPromise = waitForApiResponse(page2, '/api/logs/symptoms')
    
    await Promise.all([
      page.getByTestId('submit-button').click(),
      page2.getByTestId('submit-button').click()
    ])
    
    await Promise.all([medicationPromise, symptomPromise])
    
    // Both entries should be saved successfully
    await expect(page.getByText(/medication logged successfully/i)).toBeVisible()
    await expect(page2.getByText(/symptom logged successfully/i)).toBeVisible()
    
    // Refresh both pages and verify both entries appear
    await page.reload()
    await page2.reload()
    await Promise.all([
      page.waitForLoadState('networkidle'),
      page2.waitForLoadState('networkidle')
    ])
    
    // Both pages should show both entries
    await expect(page.getByText('Concurrent Med 1 - 100mg')).toBeVisible()
    await expect(page.getByText('Concurrent Symptom')).toBeVisible()
    await expect(page2.getByText('Concurrent Med 1 - 100mg')).toBeVisible()
    await expect(page2.getByText('Concurrent Symptom')).toBeVisible()
    
    await page2.close()
  })
})

// Performance and reliability tests
test.describe('Performance and Reliability', () => {
  test('should handle rapid form submissions', async ({ page }) => {
    await authenticateUser(page)
    await page.goto(FRONTEND_URL)
    
    // Rapidly create multiple logs
    const logCount = 5
    const promises = []
    
    for (let i = 0; i < logCount; i++) {
      promises.push(async () => {
        await page.getByRole('button', { name: /log medication/i }).click()
        await page.getByTestId('medication-name-input').fill(`Rapid Med ${i}`)
        await page.getByTestId('dosage-input').fill('100mg')
        await page.getByTestId('taken-at-input').fill(`2024-01-15T${(10 + i).toString().padStart(2, '0')}:00`)
        await page.getByTestId('effectiveness-rating-select').selectOption('3')
        
        const responsePromise = waitForApiResponse(page, '/api/logs/medications')
        await page.getByTestId('submit-button').click()
        await responsePromise
        
        await page.getByRole('button', { name: /back|close|cancel/i }).click()
      })
    }
    
    // Execute all submissions
    for (const submitFn of promises) {
      await submitFn()
    }
    
    // Verify all logs were created successfully
    for (let i = 0; i < logCount; i++) {
      await expect(page.getByText(`Rapid Med ${i} - 100mg`)).toBeVisible()
    }
  })

  test('should recover from network interruptions', async ({ page, context }) => {
    await authenticateUser(page)
    await page.goto(FRONTEND_URL)
    
    // Start logging medication
    await page.getByRole('button', { name: /log medication/i }).click()
    await page.getByTestId('medication-name-input').fill('Network Test Med')
    await page.getByTestId('dosage-input').fill('200mg')
    await page.getByTestId('taken-at-input').fill('2024-01-15T12:00')
    await page.getByTestId('effectiveness-rating-select').selectOption('4')
    
    // Simulate network failure
    await context.setOffline(true)
    
    // Attempt to submit (should fail gracefully)
    await page.getByTestId('submit-button').click()
    
    // Should show network error
    await expect(page.getByText(/network error|failed to connect/i)).toBeVisible()
    
    // Restore network
    await context.setOffline(false)
    
    // Retry submission (form data should still be there)
    expect(await page.getByTestId('medication-name-input').inputValue()).toBe('Network Test Med')
    
    const responsePromise = waitForApiResponse(page, '/api/logs/medications')
    await page.getByTestId('submit-button').click()
    await responsePromise
    
    // Should succeed after network restoration
    await expect(page.getByText(/medication logged successfully/i)).toBeVisible()
  })
})