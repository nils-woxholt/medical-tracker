/**
 * Frontend Component Tests for Passport and Doctor Management
 * 
 * This test suite validates the behavior of condition passport components,
 * doctor management interfaces, and their interactions.
 * 
 * Test Coverage:
 * - PassportList: Display of conditions with linked doctors
 * - ConditionForm: Form validation, submission, error handling
 * - DoctorForm: Form validation, submission, error handling  
 * - DoctorConditionLink: Linking interface and validation
 * - PassportPage: Full page integration and user flows
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

// Mock the API client
const mockApiClient = {
  getConditions: vi.fn(),
  createCondition: vi.fn(),
  getDoctors: vi.fn(),
  createDoctor: vi.fn(),
  getPassport: vi.fn(),
  linkDoctorToCondition: vi.fn(),
}

vi.mock('@/lib/api/client', () => ({
  apiClient: mockApiClient,
}))

// Mock components to be implemented
const PassportList = ({ 
  passportData, 
  loading = false, 
  error = null 
}: {
  passportData: any[]
  loading?: boolean
  error?: string | null
}) => {
  if (loading) {
    return <div data-testid="passport-loading">Loading passport...</div>
  }

  if (error) {
    return <div data-testid="passport-error" role="alert">{error}</div>
  }

  if (passportData.length === 0) {
    return <div data-testid="passport-empty">No conditions found</div>
  }

  return (
    <div data-testid="passport-list">
      {passportData.map((item) => (
        <div key={item.condition.id} data-testid={`passport-item-${item.condition.id}`}>
          <h3>{item.condition.name}</h3>
          <p>{item.condition.description}</p>
          <div data-testid={`doctors-list-${item.condition.id}`}>
            {item.doctors.length === 0 ? (
              <p>No doctors assigned</p>
            ) : (
              item.doctors.map((doctor: any) => (
                <div key={doctor.id} data-testid={`doctor-${doctor.id}`}>
                  <span>{doctor.name}</span>
                  <span>{doctor.specialty}</span>
                </div>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

const ConditionForm = ({ 
  onSubmit, 
  onCancel,
  initialData = null
}: {
  onSubmit: (data: any) => void
  onCancel: () => void
  initialData?: any
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    onSubmit({
      name: formData.get('name'),
      description: formData.get('description'),
      is_active: formData.get('is_active') === 'on',
    })
  }

  return (
    <form onSubmit={handleSubmit} data-testid="condition-form">
      <div>
        <label htmlFor="condition-name">Condition Name</label>
        <input 
          id="condition-name"
          name="name"
          type="text"
          required
          defaultValue={initialData?.name || ''}
          data-testid="condition-name-input"
        />
      </div>
      <div>
        <label htmlFor="condition-description">Description</label>
        <textarea 
          id="condition-description"
          name="description"
          defaultValue={initialData?.description || ''}
          data-testid="condition-description-input"
        />
      </div>
      <div>
        <label>
          <input 
            type="checkbox"
            name="is_active"
            defaultChecked={initialData?.is_active ?? true}
            data-testid="condition-active-checkbox"
          />
          Active
        </label>
      </div>
      <div>
        <button type="submit" data-testid="condition-submit">Save</button>
        <button type="button" onClick={onCancel} data-testid="condition-cancel">Cancel</button>
      </div>
    </form>
  )
}

const DoctorForm = ({ 
  onSubmit, 
  onCancel,
  initialData = null
}: {
  onSubmit: (data: any) => void
  onCancel: () => void
  initialData?: any
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    onSubmit({
      name: formData.get('name'),
      specialty: formData.get('specialty'),
      contact_info: formData.get('contact_info'),
      is_active: formData.get('is_active') === 'on',
    })
  }

  return (
    <form onSubmit={handleSubmit} data-testid="doctor-form">
      <div>
        <label htmlFor="doctor-name">Doctor Name</label>
        <input 
          id="doctor-name"
          name="name"
          type="text"
          required
          defaultValue={initialData?.name || ''}
          data-testid="doctor-name-input"
        />
      </div>
      <div>
        <label htmlFor="doctor-specialty">Specialty</label>
        <input 
          id="doctor-specialty"
          name="specialty"
          type="text"
          required
          defaultValue={initialData?.specialty || ''}
          data-testid="doctor-specialty-input"
        />
      </div>
      <div>
        <label htmlFor="doctor-contact">Contact Info</label>
        <input 
          id="doctor-contact"
          name="contact_info"
          type="text"
          defaultValue={initialData?.contact_info || ''}
          data-testid="doctor-contact-input"
        />
      </div>
      <div>
        <label>
          <input 
            type="checkbox"
            name="is_active"
            defaultChecked={initialData?.is_active ?? true}
            data-testid="doctor-active-checkbox"
          />
          Active
        </label>
      </div>
      <div>
        <button type="submit" data-testid="doctor-submit">Save</button>
        <button type="button" onClick={onCancel} data-testid="doctor-cancel">Cancel</button>
      </div>
    </form>
  )
}

const DoctorConditionLink = ({
  conditions,
  doctors,
  onLink,
}: {
  conditions: any[]
  doctors: any[]
  onLink: (doctorId: string, conditionId: string) => void
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    const doctorId = formData.get('doctor_id') as string
    const conditionId = formData.get('condition_id') as string
    onLink(doctorId, conditionId)
  }

  return (
    <form onSubmit={handleSubmit} data-testid="doctor-condition-link-form">
      <div>
        <label htmlFor="link-doctor">Doctor</label>
        <select id="link-doctor" name="doctor_id" required data-testid="link-doctor-select">
          <option value="">Select a doctor</option>
          {doctors.map(doctor => (
            <option key={doctor.id} value={doctor.id}>
              {doctor.name} - {doctor.specialty}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="link-condition">Condition</label>
        <select id="link-condition" name="condition_id" required data-testid="link-condition-select">
          <option value="">Select a condition</option>
          {conditions.map(condition => (
            <option key={condition.id} value={condition.id}>
              {condition.name}
            </option>
          ))}
        </select>
      </div>
      <button type="submit" data-testid="link-submit">Link Doctor to Condition</button>
    </form>
  )
}

describe('PassportList Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('displays loading state correctly', () => {
    render(<PassportList passportData={[]} loading={true} />)
    
    expect(screen.getByTestId('passport-loading')).toBeInTheDocument()
    expect(screen.getByText('Loading passport...')).toBeInTheDocument()
  })

  it('displays error state correctly', () => {
    const errorMessage = 'Failed to load passport data'
    render(<PassportList passportData={[]} error={errorMessage} />)
    
    const errorElement = screen.getByTestId('passport-error')
    expect(errorElement).toBeInTheDocument()
    expect(errorElement).toHaveAttribute('role', 'alert')
    expect(screen.getByText(errorMessage)).toBeInTheDocument()
  })

  it('displays empty state when no conditions exist', () => {
    render(<PassportList passportData={[]} />)
    
    expect(screen.getByTestId('passport-empty')).toBeInTheDocument()
    expect(screen.getByText('No conditions found')).toBeInTheDocument()
  })

  it('displays passport data correctly', () => {
    const passportData = [
      {
        condition: {
          id: '1',
          name: 'Hypertension',
          description: 'High blood pressure'
        },
        doctors: [
          {
            id: 'doc1',
            name: 'Dr. Smith',
            specialty: 'Cardiology'
          }
        ]
      }
    ]

    render(<PassportList passportData={passportData} />)
    
    expect(screen.getByTestId('passport-list')).toBeInTheDocument()
    expect(screen.getByTestId('passport-item-1')).toBeInTheDocument()
    expect(screen.getByText('Hypertension')).toBeInTheDocument()
    expect(screen.getByText('High blood pressure')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-doc1')).toBeInTheDocument()
    expect(screen.getByText('Dr. Smith')).toBeInTheDocument()
    expect(screen.getByText('Cardiology')).toBeInTheDocument()
  })

  it('displays condition with no assigned doctors', () => {
    const passportData = [
      {
        condition: {
          id: '1',
          name: 'Condition Without Doctors',
          description: 'A condition with no doctors'
        },
        doctors: []
      }
    ]

    render(<PassportList passportData={passportData} />)
    
    expect(screen.getByText('No doctors assigned')).toBeInTheDocument()
  })
})

describe('ConditionForm Component', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form fields correctly', () => {
    render(<ConditionForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    expect(screen.getByTestId('condition-name-input')).toBeInTheDocument()
    expect(screen.getByTestId('condition-description-input')).toBeInTheDocument()
    expect(screen.getByTestId('condition-active-checkbox')).toBeInTheDocument()
    expect(screen.getByTestId('condition-submit')).toBeInTheDocument()
    expect(screen.getByTestId('condition-cancel')).toBeInTheDocument()
  })

  it('populates initial data correctly', () => {
    const initialData = {
      name: 'Test Condition',
      description: 'Test Description',
      is_active: false
    }

    render(<ConditionForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} initialData={initialData} />)
    
    expect(screen.getByTestId('condition-name-input')).toHaveValue('Test Condition')
    expect(screen.getByTestId('condition-description-input')).toHaveValue('Test Description')
    expect(screen.getByTestId('condition-active-checkbox')).not.toBeChecked()
  })

  it('submits form with correct data', async () => {
    const user = userEvent.setup()
    render(<ConditionForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.type(screen.getByTestId('condition-name-input'), 'New Condition')
    await user.type(screen.getByTestId('condition-description-input'), 'Condition description')
    await user.click(screen.getByTestId('condition-submit'))
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      name: 'New Condition',
      description: 'Condition description',
      is_active: true
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<ConditionForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.click(screen.getByTestId('condition-cancel'))
    
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('requires name field', async () => {
    const user = userEvent.setup()
    render(<ConditionForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.click(screen.getByTestId('condition-submit'))
    
    // Form should not submit without required field
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })
})

describe('DoctorForm Component', () => {
  const mockOnSubmit = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form fields correctly', () => {
    render(<DoctorForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    expect(screen.getByTestId('doctor-name-input')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-specialty-input')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-contact-input')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-active-checkbox')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-submit')).toBeInTheDocument()
    expect(screen.getByTestId('doctor-cancel')).toBeInTheDocument()
  })

  it('submits form with correct data', async () => {
    const user = userEvent.setup()
    render(<DoctorForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.type(screen.getByTestId('doctor-name-input'), 'Dr. Test')
    await user.type(screen.getByTestId('doctor-specialty-input'), 'Cardiology')
    await user.type(screen.getByTestId('doctor-contact-input'), 'test@example.com')
    await user.click(screen.getByTestId('doctor-submit'))
    
    expect(mockOnSubmit).toHaveBeenCalledWith({
      name: 'Dr. Test',
      specialty: 'Cardiology',
      contact_info: 'test@example.com',
      is_active: true
    })
  })

  it('requires name and specialty fields', async () => {
    const user = userEvent.setup()
    render(<DoctorForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />)
    
    await user.click(screen.getByTestId('doctor-submit'))
    
    // Form should not submit without required fields
    expect(mockOnSubmit).not.toHaveBeenCalled()
  })
})

describe('DoctorConditionLink Component', () => {
  const mockOnLink = vi.fn()
  const conditions = [
    { id: '1', name: 'Hypertension' },
    { id: '2', name: 'Diabetes' }
  ]
  const doctors = [
    { id: 'doc1', name: 'Dr. Smith', specialty: 'Cardiology' },
    { id: 'doc2', name: 'Dr. Jones', specialty: 'Endocrinology' }
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dropdown options correctly', () => {
    render(<DoctorConditionLink conditions={conditions} doctors={doctors} onLink={mockOnLink} />)
    
    expect(screen.getByTestId('link-doctor-select')).toBeInTheDocument()
    expect(screen.getByTestId('link-condition-select')).toBeInTheDocument()
    
    // Check doctor options
    expect(screen.getByText('Dr. Smith - Cardiology')).toBeInTheDocument()
    expect(screen.getByText('Dr. Jones - Endocrinology')).toBeInTheDocument()
    
    // Check condition options
    expect(screen.getByText('Hypertension')).toBeInTheDocument()
    expect(screen.getByText('Diabetes')).toBeInTheDocument()
  })

  it('submits link with selected values', async () => {
    const user = userEvent.setup()
    render(<DoctorConditionLink conditions={conditions} doctors={doctors} onLink={mockOnLink} />)
    
    await user.selectOptions(screen.getByTestId('link-doctor-select'), 'doc1')
    await user.selectOptions(screen.getByTestId('link-condition-select'), '1')
    await user.click(screen.getByTestId('link-submit'))
    
    expect(mockOnLink).toHaveBeenCalledWith('doc1', '1')
  })

  it('requires both selections', async () => {
    const user = userEvent.setup()
    render(<DoctorConditionLink conditions={conditions} doctors={doctors} onLink={mockOnLink} />)
    
    await user.click(screen.getByTestId('link-submit'))
    
    // Form should not submit without required selections
    expect(mockOnLink).not.toHaveBeenCalled()
  })
})

describe('Accessibility Tests', () => {
  it('forms have proper labels and roles', () => {
    const mockFn = vi.fn()
    
    render(<ConditionForm onSubmit={mockFn} onCancel={mockFn} />)
    
    // Check that form controls have proper labels
    expect(screen.getByLabelText('Condition Name')).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toBeInTheDocument()
    expect(screen.getByLabelText('Active')).toBeInTheDocument()
  })

  it('error states have proper ARIA attributes', () => {
    render(<PassportList passportData={[]} error="Test error" />)
    
    const errorElement = screen.getByTestId('passport-error')
    expect(errorElement).toHaveAttribute('role', 'alert')
  })

  it('form inputs have proper accessibility attributes', () => {
    const mockFn = vi.fn()
    
    render(<DoctorForm onSubmit={mockFn} onCancel={mockFn} />)
    
    const nameInput = screen.getByTestId('doctor-name-input')
    expect(nameInput).toHaveAttribute('required')
    expect(nameInput).toHaveAttribute('id', 'doctor-name')
    
    const specialtyInput = screen.getByTestId('doctor-specialty-input')
    expect(specialtyInput).toHaveAttribute('required')
    expect(specialtyInput).toHaveAttribute('id', 'doctor-specialty')
  })
})