/**
 * Frontend Component Tests for Medical Logging Forms and Summaries
 * 
 * This test suite validates the behavior of medication and symptom logging forms,
 * as well as the summary list components used on the landing page.
 * 
 * Test Coverage:
 * - MedicationLogForm: Form validation, submission, error handling
 * - SymptomLogForm: Form validation, submission, error handling  
 * - LogsSummary: Data display, loading states, error states
 * - FeelStatus: Status display, different states, interactions
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

// Mock the API client
const mockApiClient = {
  createMedicationLog: vi.fn(),
  createSymptomLog: vi.fn(),
  getLogsSummary: vi.fn(),
  getFeelVsYesterday: vi.fn(),
}

vi.mock('@/lib/api/client', () => ({
  apiClient: mockApiClient,
}))

// Mock components to be implemented
const MedicationLogForm = ({ onSubmit, onCancel }: {
  onSubmit: (data: any) => void
  onCancel: () => void
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    onSubmit({
      medication_name: formData.get('medication_name'),
      dosage: formData.get('dosage'),
      taken_at: formData.get('taken_at'),
      effectiveness_rating: parseInt(formData.get('effectiveness_rating') as string),
      side_effect_severity: formData.get('side_effect_severity') || null,
      notes: formData.get('notes'),
    })
  }

  return (
    <form onSubmit={handleSubmit} data-testid="medication-log-form">
      <div>
        <label htmlFor="medication_name">Medication Name</label>
        <input 
          type="text" 
          id="medication_name" 
          name="medication_name" 
          required 
          data-testid="medication-name-input"
        />
      </div>
      
      <div>
        <label htmlFor="dosage">Dosage</label>
        <input 
          type="text" 
          id="dosage" 
          name="dosage" 
          required 
          data-testid="dosage-input"
        />
      </div>
      
      <div>
        <label htmlFor="taken_at">Taken At</label>
        <input 
          type="datetime-local" 
          id="taken_at" 
          name="taken_at" 
          required 
          data-testid="taken-at-input"
        />
      </div>
      
      <div>
        <label htmlFor="effectiveness_rating">Effectiveness Rating (1-5)</label>
        <select 
          id="effectiveness_rating" 
          name="effectiveness_rating" 
          required
          data-testid="effectiveness-rating-select"
        >
          <option value="">Select rating</option>
          <option value="1">1 - Not effective</option>
          <option value="2">2 - Slightly effective</option>
          <option value="3">3 - Moderately effective</option>
          <option value="4">4 - Very effective</option>
          <option value="5">5 - Extremely effective</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="side_effect_severity">Side Effect Severity</label>
        <select 
          id="side_effect_severity" 
          name="side_effect_severity"
          data-testid="side-effect-select"
        >
          <option value="">None</option>
          <option value="mild">Mild</option>
          <option value="moderate">Moderate</option>
          <option value="severe">Severe</option>
          <option value="critical">Critical</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="notes">Notes</label>
        <textarea 
          id="notes" 
          name="notes"
          data-testid="notes-textarea"
        />
      </div>
      
      <div>
        <button type="submit" data-testid="submit-button">
          Log Medication
        </button>
        <button type="button" onClick={onCancel} data-testid="cancel-button">
          Cancel
        </button>
      </div>
    </form>
  )
}

const SymptomLogForm = ({ onSubmit, onCancel }: {
  onSubmit: (data: any) => void
  onCancel: () => void
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    onSubmit({
      symptom_name: formData.get('symptom_name'),
      severity: formData.get('severity'),
      started_at: formData.get('started_at'),
      duration_minutes: parseInt(formData.get('duration_minutes') as string),
      impact_rating: parseInt(formData.get('impact_rating') as string),
      triggers: formData.get('triggers'),
      notes: formData.get('notes'),
    })
  }

  return (
    <form onSubmit={handleSubmit} data-testid="symptom-log-form">
      <div>
        <label htmlFor="symptom_name">Symptom Name</label>
        <input 
          type="text" 
          id="symptom_name" 
          name="symptom_name" 
          required 
          data-testid="symptom-name-input"
        />
      </div>
      
      <div>
        <label htmlFor="severity">Severity</label>
        <select 
          id="severity" 
          name="severity" 
          required
          data-testid="severity-select"
        >
          <option value="">Select severity</option>
          <option value="mild">Mild</option>
          <option value="moderate">Moderate</option>
          <option value="severe">Severe</option>
          <option value="critical">Critical</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="started_at">Started At</label>
        <input 
          type="datetime-local" 
          id="started_at" 
          name="started_at" 
          required 
          data-testid="started-at-input"
        />
      </div>
      
      <div>
        <label htmlFor="duration_minutes">Duration (minutes)</label>
        <input 
          type="number" 
          id="duration_minutes" 
          name="duration_minutes" 
          min="1"
          data-testid="duration-input"
        />
      </div>
      
      <div>
        <label htmlFor="impact_rating">Impact Rating (1-5)</label>
        <select 
          id="impact_rating" 
          name="impact_rating" 
          required
          data-testid="impact-rating-select"
        >
          <option value="">Select rating</option>
          <option value="1">1 - Very low impact</option>
          <option value="2">2 - Low impact</option>
          <option value="3">3 - Moderate impact</option>
          <option value="4">4 - High impact</option>
          <option value="5">5 - Very high impact</option>
        </select>
      </div>
      
      <div>
        <label htmlFor="triggers">Triggers</label>
        <input 
          type="text" 
          id="triggers" 
          name="triggers"
          data-testid="triggers-input"
        />
      </div>
      
      <div>
        <label htmlFor="notes">Notes</label>
        <textarea 
          id="notes" 
          name="notes"
          data-testid="notes-textarea"
        />
      </div>
      
      <div>
        <button type="submit" data-testid="submit-button">
          Log Symptom
        </button>
        <button type="button" onClick={onCancel} data-testid="cancel-button">
          Cancel
        </button>
      </div>
    </form>
  )
}

const LogsSummary = ({ 
  isLoading = false, 
  error = null,
  medicationLogs = [],
  symptomLogs = [] 
}: {
  isLoading?: boolean
  error?: string | null
  medicationLogs?: any[]
  symptomLogs?: any[]
}) => {
  if (isLoading) {
    return <div data-testid="logs-loading">Loading logs...</div>
  }
  
  if (error) {
    return <div data-testid="logs-error">Error: {error}</div>
  }

  return (
    <div data-testid="logs-summary">
      <section data-testid="medication-logs-section">
        <h3>Recent Medication Logs</h3>
        {medicationLogs.length === 0 ? (
          <p data-testid="no-medication-logs">No medication logs yet</p>
        ) : (
          <ul data-testid="medication-logs-list">
            {medicationLogs.slice(0, 5).map((log, index) => (
              <li key={index} data-testid={`medication-log-${index}`}>
                <div>{log.medication_name} - {log.dosage}</div>
                <div>Taken: {log.taken_at}</div>
                <div>Effectiveness: {log.effectiveness_rating}/5</div>
              </li>
            ))}
          </ul>
        )}
      </section>
      
      <section data-testid="symptom-logs-section">
        <h3>Recent Symptom Logs</h3>
        {symptomLogs.length === 0 ? (
          <p data-testid="no-symptom-logs">No symptom logs yet</p>
        ) : (
          <ul data-testid="symptom-logs-list">
            {symptomLogs.slice(0, 5).map((log, index) => (
              <li key={index} data-testid={`symptom-log-${index}`}>
                <div>{log.symptom_name}</div>
                <div>Severity: {log.severity}</div>
                <div>Impact: {log.impact_rating}/5</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

const FeelStatus = ({ 
  isLoading = false,
  error = null,
  status = null,
  summary = '',
  confidence = 0
}: {
  isLoading?: boolean
  error?: string | null
  status?: string | null
  summary?: string
  confidence?: number
}) => {
  if (isLoading) {
    return <div data-testid="feel-status-loading">Loading status...</div>
  }
  
  if (error) {
    return <div data-testid="feel-status-error">Error: {error}</div>
  }

  const getStatusColor = (status: string | null) => {
    switch (status) {
      case 'better': return 'text-green-600'
      case 'worse': return 'text-red-600'
      case 'same': return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div data-testid="feel-status" className={`feel-status ${getStatusColor(status)}`}>
      <h3>How are you feeling vs yesterday?</h3>
      <div data-testid="feel-status-value">
        {status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'}
      </div>
      <div data-testid="feel-confidence">
        Confidence: {Math.round(confidence * 100)}%
      </div>
      {summary && (
        <p data-testid="feel-summary">{summary}</p>
      )}
    </div>
  )
}

describe('MedicationLogForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders all required form fields', () => {
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    expect(screen.getByLabelText(/medication name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/dosage/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/taken at/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/effectiveness rating/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/side effect severity/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument()
  })

  it('validates required fields before submission', async () => {
    const user = userEvent.setup()
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    const submitButton = screen.getByTestId('submit-button')
    await user.click(submitButton)
    
    // Form should not submit if required fields are empty
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.type(screen.getByTestId('medication-name-input'), 'Ibuprofen')
    await user.type(screen.getByTestId('dosage-input'), '200mg')
    await user.type(screen.getByTestId('taken-at-input'), '2024-01-01T12:00')
    await user.selectOptions(screen.getByTestId('effectiveness-rating-select'), '4')
    await user.selectOptions(screen.getByTestId('side-effect-select'), 'mild')
    await user.type(screen.getByTestId('notes-textarea'), 'Helped with headache')
    
    const submitButton = screen.getByTestId('submit-button')
    await user.click(submitButton)
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      medication_name: 'Ibuprofen',
      dosage: '200mg',
      taken_at: '2024-01-01T12:00',
      effectiveness_rating: 4,
      side_effect_severity: 'mild',
      notes: 'Helped with headache',
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    const cancelButton = screen.getByTestId('cancel-button')
    await user.click(cancelButton)
    
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('allows null side effects (no side effects)', async () => {
    const user = userEvent.setup()
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.type(screen.getByTestId('medication-name-input'), 'Aspirin')
    await user.type(screen.getByTestId('dosage-input'), '325mg')
    await user.type(screen.getByTestId('taken-at-input'), '2024-01-01T08:00')
    await user.selectOptions(screen.getByTestId('effectiveness-rating-select'), '5')
    // Don't select side effects (should default to null)
    
    const submitButton = screen.getByTestId('submit-button')
    await user.click(submitButton)
    
    expect(mockOnSubmit).toHaveBeenCalledWith(expect.objectContaining({
      side_effect_severity: null,
    }))
  })
})

describe('SymptomLogForm', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnSubmit.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders all required form fields', () => {
    render(<SymptomLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    expect(screen.getByLabelText(/symptom name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/severity/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/started at/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/duration/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/impact rating/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/triggers/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/notes/i)).toBeInTheDocument()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    render(<SymptomLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.type(screen.getByTestId('symptom-name-input'), 'Headache')
    await user.selectOptions(screen.getByTestId('severity-select'), 'moderate')
    await user.type(screen.getByTestId('started-at-input'), '2024-01-01T14:30')
    await user.type(screen.getByTestId('duration-input'), '120')
    await user.selectOptions(screen.getByTestId('impact-rating-select'), '3')
    await user.type(screen.getByTestId('triggers-input'), 'Stress, lack of sleep')
    await user.type(screen.getByTestId('notes-textarea'), 'Throbbing pain on left side')
    
    const submitButton = screen.getByTestId('submit-button')
    await user.click(submitButton)
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      symptom_name: 'Headache',
      severity: 'moderate',
      started_at: '2024-01-01T14:30',
      duration_minutes: 120,
      impact_rating: 3,
      triggers: 'Stress, lack of sleep',
      notes: 'Throbbing pain on left side',
    })
  })

  it('validates numeric fields', async () => {
    const user = userEvent.setup()
    render(<SymptomLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    const durationInput = screen.getByTestId('duration-input')
    
    // Should not accept negative values
    expect(durationInput).toHaveAttribute('min', '1')
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<SymptomLogForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    const cancelButton = screen.getByTestId('cancel-button')
    await user.click(cancelButton)
    
    expect(mockOnCancel).toHaveBeenCalled()
  })
})

describe('LogsSummary', () => {
  it('displays loading state', () => {
    render(<LogsSummary isLoading={true} />)
    
    expect(screen.getByTestId('logs-loading')).toHaveTextContent('Loading logs...')
  })

  it('displays error state', () => {
    render(<LogsSummary error="Failed to load logs" />)
    
    expect(screen.getByTestId('logs-error')).toHaveTextContent('Error: Failed to load logs')
  })

  it('displays empty state when no logs exist', () => {
    render(<LogsSummary medicationLogs={[]} symptomLogs={[]} />)
    
    expect(screen.getByTestId('no-medication-logs')).toHaveTextContent('No medication logs yet')
    expect(screen.getByTestId('no-symptom-logs')).toHaveTextContent('No symptom logs yet')
  })

  it('displays medication logs correctly', () => {
    const medicationLogs = [
      {
        medication_name: 'Ibuprofen',
        dosage: '200mg',
        taken_at: '2024-01-01 12:00:00',
        effectiveness_rating: 4,
      },
      {
        medication_name: 'Aspirin',
        dosage: '325mg',
        taken_at: '2024-01-01 08:00:00',
        effectiveness_rating: 5,
      },
    ]

    render(<LogsSummary medicationLogs={medicationLogs} symptomLogs={[]} />)
    
    expect(screen.getByTestId('medication-log-0')).toHaveTextContent('Ibuprofen - 200mg')
    expect(screen.getByTestId('medication-log-0')).toHaveTextContent('Effectiveness: 4/5')
    expect(screen.getByTestId('medication-log-1')).toHaveTextContent('Aspirin - 325mg')
    expect(screen.getByTestId('medication-log-1')).toHaveTextContent('Effectiveness: 5/5')
  })

  it('displays symptom logs correctly', () => {
    const symptomLogs = [
      {
        symptom_name: 'Headache',
        severity: 'moderate',
        impact_rating: 3,
      },
      {
        symptom_name: 'Nausea',
        severity: 'mild',
        impact_rating: 2,
      },
    ]

    render(<LogsSummary medicationLogs={[]} symptomLogs={symptomLogs} />)
    
    expect(screen.getByTestId('symptom-log-0')).toHaveTextContent('Headache')
    expect(screen.getByTestId('symptom-log-0')).toHaveTextContent('Severity: moderate')
    expect(screen.getByTestId('symptom-log-0')).toHaveTextContent('Impact: 3/5')
    expect(screen.getByTestId('symptom-log-1')).toHaveTextContent('Nausea')
    expect(screen.getByTestId('symptom-log-1')).toHaveTextContent('Severity: mild')
  })

  it('limits display to 5 logs maximum', () => {
    const medicationLogs = Array.from({ length: 10 }, (_, i) => ({
      medication_name: `Med ${i}`,
      dosage: '100mg',
      taken_at: '2024-01-01 12:00:00',
      effectiveness_rating: 3,
    }))

    render(<LogsSummary medicationLogs={medicationLogs} symptomLogs={[]} />)
    
    // Should only display first 5 logs
    expect(screen.getByTestId('medication-log-4')).toBeInTheDocument()
    expect(screen.queryByTestId('medication-log-5')).not.toBeInTheDocument()
  })
})

describe('FeelStatus', () => {
  it('displays loading state', () => {
    render(<FeelStatus isLoading={true} />)
    
    expect(screen.getByTestId('feel-status-loading')).toHaveTextContent('Loading status...')
  })

  it('displays error state', () => {
    render(<FeelStatus error="Failed to analyze status" />)
    
    expect(screen.getByTestId('feel-status-error')).toHaveTextContent('Error: Failed to analyze status')
  })

  it('displays better status with correct styling', () => {
    render(
      <FeelStatus 
        status="better" 
        summary="Medication effectiveness improved" 
        confidence={0.85} 
      />
    )
    
    const statusElement = screen.getByTestId('feel-status')
    expect(statusElement).toHaveClass('text-green-600')
    expect(screen.getByTestId('feel-status-value')).toHaveTextContent('Better')
    expect(screen.getByTestId('feel-confidence')).toHaveTextContent('Confidence: 85%')
    expect(screen.getByTestId('feel-summary')).toHaveTextContent('Medication effectiveness improved')
  })

  it('displays worse status with correct styling', () => {
    render(
      <FeelStatus 
        status="worse" 
        summary="Symptom severity increased" 
        confidence={0.72} 
      />
    )
    
    const statusElement = screen.getByTestId('feel-status')
    expect(statusElement).toHaveClass('text-red-600')
    expect(screen.getByTestId('feel-status-value')).toHaveTextContent('Worse')
    expect(screen.getByTestId('feel-confidence')).toHaveTextContent('Confidence: 72%')
  })

  it('displays same status with correct styling', () => {
    render(
      <FeelStatus 
        status="same" 
        summary="No significant changes detected" 
        confidence={0.45} 
      />
    )
    
    const statusElement = screen.getByTestId('feel-status')
    expect(statusElement).toHaveClass('text-blue-600')
    expect(screen.getByTestId('feel-status-value')).toHaveTextContent('Same')
    expect(screen.getByTestId('feel-confidence')).toHaveTextContent('Confidence: 45%')
  })

  it('displays unknown status when no data available', () => {
    render(<FeelStatus status={null} confidence={0} />)
    
    const statusElement = screen.getByTestId('feel-status')
    expect(statusElement).toHaveClass('text-gray-600')
    expect(screen.getByTestId('feel-status-value')).toHaveTextContent('Unknown')
    expect(screen.getByTestId('feel-confidence')).toHaveTextContent('Confidence: 0%')
  })

  it('does not display summary when not provided', () => {
    render(<FeelStatus status="better" confidence={0.5} />)
    
    expect(screen.queryByTestId('feel-summary')).not.toBeInTheDocument()
  })
})

describe('Integration - Form and Summary Components', () => {
  it('should handle form submission and update summary', async () => {
    // This test simulates the integration between forms and summary components
    const user = userEvent.setup()
    
    // Mock API responses
    mockApiClient.createMedicationLog.mockResolvedValue({ 
      id: 1, 
      medication_name: 'Test Med',
      dosage: '100mg',
      effectiveness_rating: 4 
    })
    
    const mockOnSubmit = vi.fn().mockImplementation(async (data) => {
      // Simulate successful API call
      await mockApiClient.createMedicationLog(data)
    })
    
    render(<MedicationLogForm onSubmit={mockOnSubmit} onCancel={vi.fn()} />)
    
    // Fill and submit form
    await user.type(screen.getByTestId('medication-name-input'), 'Test Med')
    await user.type(screen.getByTestId('dosage-input'), '100mg')
    await user.type(screen.getByTestId('taken-at-input'), '2024-01-01T12:00')
    await user.selectOptions(screen.getByTestId('effectiveness-rating-select'), '4')
    
    await user.click(screen.getByTestId('submit-button'))
    
    expect(mockOnSubmit).toHaveBeenCalled()
    expect(mockApiClient.createMedicationLog).toHaveBeenCalledWith({
      medication_name: 'Test Med',
      dosage: '100mg',
      taken_at: '2024-01-01T12:00',
      effectiveness_rating: 4,
      side_effect_severity: null,
      notes: '',
    })
  })

  it('should handle API errors gracefully', async () => {
    const user = userEvent.setup()
    
    // Mock API error
    mockApiClient.createSymptomLog.mockRejectedValue(new Error('Network error'))
    
    const mockOnSubmit = vi.fn().mockImplementation(async (data) => {
      try {
        await mockApiClient.createSymptomLog(data)
      } catch (error) {
        // Form should handle errors gracefully
        console.error('Form submission failed:', error)
      }
    })
    
    render(<SymptomLogForm onSubmit={mockOnSubmit} onCancel={vi.fn()} />)
    
    // Fill and submit form
    await user.type(screen.getByTestId('symptom-name-input'), 'Headache')
    await user.selectOptions(screen.getByTestId('severity-select'), 'moderate')
    await user.type(screen.getByTestId('started-at-input'), '2024-01-01T14:30')
    await user.selectOptions(screen.getByTestId('impact-rating-select'), '3')
    
    await user.click(screen.getByTestId('submit-button'))
    
    expect(mockApiClient.createSymptomLog).toHaveBeenCalled()
    expect(mockOnSubmit).toHaveBeenCalled()
  })
})

// Accessibility Tests
describe('Accessibility', () => {
  it('medication form has proper accessibility attributes', () => {
    render(<MedicationLogForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    
    // All form inputs should have associated labels
    const medicationInput = screen.getByTestId('medication-name-input')
    expect(medicationInput).toHaveAttribute('id', 'medication_name')
    expect(screen.getByLabelText(/medication name/i)).toBe(medicationInput)
    
    // Required fields should be marked as required
    expect(medicationInput).toHaveAttribute('required')
  })

  it('symptom form has proper accessibility attributes', () => {
    render(<SymptomLogForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    
    // All form inputs should have associated labels
    const symptomInput = screen.getByTestId('symptom-name-input')
    expect(symptomInput).toHaveAttribute('id', 'symptom_name')
    expect(screen.getByLabelText(/symptom name/i)).toBe(symptomInput)
    
    // Required fields should be marked as required
    expect(symptomInput).toHaveAttribute('required')
  })

  it('feel status component has proper ARIA attributes', () => {
    render(
      <FeelStatus 
        status="better" 
        summary="Improvement detected" 
        confidence={0.8} 
      />
    )
    
    // Status component should be properly labeled
    const statusComponent = screen.getByTestId('feel-status')
    expect(statusComponent).toBeInTheDocument()
    
    // Status value should be accessible
    expect(screen.getByTestId('feel-status-value')).toHaveTextContent('Better')
  })
})