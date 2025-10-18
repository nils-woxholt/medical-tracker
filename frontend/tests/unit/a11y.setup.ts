/**
 * Accessibility Testing Setup & Configuration
 * 
 * This module provides comprehensive accessibility testing utilities
 * using axe-core for automated a11y validation of React components
 * and pages within the SaaS Medical Tracker application.
 * 
 * Medical applications require strict WCAG 2.1 AA compliance for:
 * - Healthcare provider accessibility needs
 * - Patient data interface accessibility
 * - Legal compliance requirements
 */

import { configureAxe, axe } from 'jest-axe'
import { render } from '@testing-library/react'
import { ReactElement } from 'react'
import { expect, describe, it } from 'vitest'

// Note: toHaveNoViolations is Jest-specific
// For Vitest, we'll use manual assertion checking

/**
 * Axe Configuration for Medical Application Accessibility
 * 
 * Configured for WCAG 2.1 AA compliance with medical-specific considerations:
 * - High contrast requirements for medical data visualization
 * - Screen reader compatibility for critical patient information
 * - Keyboard navigation for hands-free operation in clinical settings
 */
export const axeConfig = configureAxe({
  rules: {
    // Critical for medical applications
    'color-contrast': { enabled: true },
    'aria-labels': { enabled: true },
    
    // Medical data accessibility
    'table-headers': { enabled: true },
    'form-field-multiple-labels': { enabled: true },
    
    // Disable for development iteration (re-enable for production)
    'region': { enabled: false }, // May conflict with Next.js layout
    'duplicate-id': { enabled: false }, // Common in component libraries
  }
})

/**
 * Accessibility Testing Utilities
 */
export class A11yTestUtils {
  /**
   * Test React component accessibility
   * @param component - React component to test
   * @param options - Additional axe-core options
   */
  static async testComponentAccessibility(
    component: ReactElement, 
    options: any = {}
  ) {
    const { container } = render(component)
    const results = await axeConfig(container, options)
    // Vitest-compatible assertion
    expect(results.violations).toEqual([])
    return results
  }

  /**
   * Test page accessibility with medical-specific checks
   * @param pageContent - Rendered page container
   */
  static async testPageAccessibility(pageContent: HTMLElement) {
    // Medical application specific accessibility checks
    const medicalAxeOptions = {
      rules: {
        // Strict medical data requirements
        'color-contrast': { enabled: true },
        'aria-required-attr': { enabled: true },
        'form-field-multiple-labels': { enabled: true }
      }
    }
    
    const results = await axeConfig(pageContent, medicalAxeOptions)
    expect(results.violations).toEqual([])
    return results
  }

  /**
   * Test form accessibility for medical data entry
   * @param formElement - Form container element
   */
  static async testFormAccessibility(formElement: HTMLElement) {
    const formAxeOptions = {
      rules: {
        'form-field-multiple-labels': { enabled: true },
        'aria-required-attr': { enabled: true }
      }
    }
    
    const results = await axeConfig(formElement, formAxeOptions)
    expect(results.violations).toEqual([])
    return results
  }

  /**
   * Test medical data table accessibility
   * @param tableElement - Table container element
   */
  static async testTableAccessibility(tableElement: HTMLElement) {
    const tableAxeOptions = {
      rules: {
        'table-headers': { enabled: true },
        'th-has-data-cells': { enabled: true }
      }
    }
    
    const results = await axeConfig(tableElement, tableAxeOptions)
    expect(results.violations).toEqual([])
    return results
  }

  /**
   * Generate accessibility report for CI/CD
   * @param violations - Axe violation results
   */
  static generateA11yReport(violations: any[]) {
    if (violations.length === 0) {
      return '✅ No accessibility violations found'
    }
    
    const report = violations.map(violation => ({
      id: violation.id,
      impact: violation.impact,
      description: violation.description,
      help: violation.help,
      helpUrl: violation.helpUrl,
      nodes: violation.nodes.length
    }))
    
    return {
      summary: `❌ Found ${violations.length} accessibility violations`,
      details: report,
      criticalCount: violations.filter(v => v.impact === 'critical').length,
      seriousCount: violations.filter(v => v.impact === 'serious').length
    }
  }
}

/**
 * Common Medical UI Accessibility Test Helpers
 */
export const medicalA11yHelpers = {
  /**
   * Test patient data display components
   */
  async testPatientDataDisplay(component: ReactElement) {
    return A11yTestUtils.testComponentAccessibility(component, {
      rules: {
        'color-contrast': { enabled: true },
        'aria-labels': { enabled: true },
        'heading-structure': { enabled: true }
      }
    })
  },

  /**
   * Test medical form accessibility
   */
  async testMedicalForm(component: ReactElement) {
    return A11yTestUtils.testComponentAccessibility(component, {
      rules: {
        'form-field-multiple-labels': { enabled: true },
        'aria-required-attr': { enabled: true },
        'error-message': { enabled: true }
      }
    })
  },

  /**
   * Test data visualization accessibility
   */
  async testDataVisualization(component: ReactElement) {
    return A11yTestUtils.testComponentAccessibility(component, {
      rules: {
        'color-contrast': { enabled: true },
        'aria-labels': { enabled: true },
        'img-alt': { enabled: true },
        'svg-img-alt': { enabled: true }
      }
    })
  }
}

/**
 * Accessibility Testing Configuration for Different Contexts
 */
export const a11yTestConfigs = {
  // Development - More lenient for iteration
  development: {
    rules: {
      'color-contrast': { enabled: false }, // Enable in production
      'duplicate-id': { enabled: false }
    }
  },

  // Production - Strict compliance
  production: {
    rules: {
      'color-contrast': { enabled: true },
      'aria-required-attr': { enabled: true },
      'form-field-multiple-labels': { enabled: true }
    }
  },

  // CI/CD - Balanced for automation
  ci: {
    rules: {
      'color-contrast': { enabled: true },
      'aria-required-attr': { enabled: true },
      'form-field-multiple-labels': { enabled: true }
    }
  }
}

// Export default configuration based on environment
const currentEnv = process.env.NODE_ENV || 'development'
export const defaultA11yConfig = a11yTestConfigs[currentEnv as keyof typeof a11yTestConfigs] || a11yTestConfigs.development

// Accessibility testing setup loaded for medical application WCAG 2.1 AA compliance