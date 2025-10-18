/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MedicationForm } from '../src/components/MedicationForm'
import { jest } from '@jest/globals'

// Mock the medication service
jest.mock('../src/services/medicationService', () => ({
  createMedication: jest.fn(),
  updateMedication: jest.fn(),
  getMedications: jest.fn(),
}))

const mockCreateMedication = jest.fn()
const mockUpdateMedication = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
})

describe('MedicationForm', () => {
  const mockOnSuccess = jest.fn()
  const mockOnCancel = jest.fn()

  beforeEach(() => {
    mockOnSuccess.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders form fields correctly', () => {
    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByLabelText(/medication name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
  })

  it('displays validation errors for empty required fields', async () => {
    const user = userEvent.setup()

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/medication name is required/i)).toBeInTheDocument()
    })
  })

  it('submits form with valid data for new medication', async () => {
    const user = userEvent.setup()
    mockCreateMedication.mockResolvedValue({ 
      id: 1, 
      name: 'Test Medication', 
      description: 'Test description',
      is_active: true
    })

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const descriptionInput = screen.getByLabelText(/description/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    await user.type(nameInput, 'Test Medication')
    await user.type(descriptionInput, 'Test description')
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockCreateMedication).toHaveBeenCalledWith({
        name: 'Test Medication',
        description: 'Test description',
        is_active: true
      })
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('submits form with valid data for existing medication', async () => {
    const user = userEvent.setup()
    const existingMedication = {
      id: 1,
      name: 'Existing Medication',
      description: 'Existing description',
      is_active: true
    }

    mockUpdateMedication.mockResolvedValue({
      ...existingMedication,
      name: 'Updated Medication',
      description: 'Updated description'
    })

    render(
      <MedicationForm 
        medication={existingMedication}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const descriptionInput = screen.getByLabelText(/description/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    // Clear and update fields
    await user.clear(nameInput)
    await user.clear(descriptionInput)
    await user.type(nameInput, 'Updated Medication')
    await user.type(descriptionInput, 'Updated description')
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockUpdateMedication).toHaveBeenCalledWith(1, {
        name: 'Updated Medication',
        description: 'Updated description',
        is_active: true
      })
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('handles form submission errors gracefully', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Medication name already exists'
    mockCreateMedication.mockRejectedValue(new Error(errorMessage))

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    await user.type(nameInput, 'Duplicate Medication')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(mockOnSuccess).not.toHaveBeenCalled()
    })
  })

  it('calls onCancel when cancel button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const cancelButton = screen.getByRole('button', { name: /cancel/i })
    await user.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('validates medication name length', async () => {
    const user = userEvent.setup()

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    // Test name too short
    await user.type(nameInput, 'A')
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/medication name must be at least 2 characters/i)).toBeInTheDocument()
    })

    // Test name too long
    await user.clear(nameInput)
    await user.type(nameInput, 'A'.repeat(101))
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/medication name must be less than 100 characters/i)).toBeInTheDocument()
    })
  })

  it('validates description length', async () => {
    const user = userEvent.setup()

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const descriptionInput = screen.getByLabelText(/description/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    await user.type(nameInput, 'Valid Name')
    await user.type(descriptionInput, 'A'.repeat(501))
    await user.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/description must be less than 500 characters/i)).toBeInTheDocument()
    })
  })

  it('disables submit button while submitting', async () => {
    const user = userEvent.setup()
    let resolvePromise: (value: any) => void
    const pendingPromise = new Promise(resolve => {
      resolvePromise = resolve
    })
    mockCreateMedication.mockReturnValue(pendingPromise)

    render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i)
    const saveButton = screen.getByRole('button', { name: /save/i })

    await user.type(nameInput, 'Test Medication')
    await user.click(saveButton)

    expect(saveButton).toBeDisabled()
    expect(screen.getByText(/saving/i)).toBeInTheDocument()

    // Resolve the promise to complete the test
    resolvePromise!({ id: 1, name: 'Test Medication', is_active: true })
    await waitFor(() => {
      expect(saveButton).not.toBeDisabled()
    })
  })

  it('populates form fields when editing existing medication', () => {
    const existingMedication = {
      id: 1,
      name: 'Existing Medication',
      description: 'Existing description',
      is_active: true
    }

    render(
      <MedicationForm 
        medication={existingMedication}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    const nameInput = screen.getByLabelText(/medication name/i) as HTMLInputElement
    const descriptionInput = screen.getByLabelText(/description/i) as HTMLTextAreaElement

    expect(nameInput.value).toBe('Existing Medication')
    expect(descriptionInput.value).toBe('Existing description')
  })

  it('shows different button text when editing vs creating', () => {
    const existingMedication = {
      id: 1,
      name: 'Existing Medication',
      description: 'Existing description',
      is_active: true
    }

    const { rerender } = render(
      <MedicationForm 
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByRole('button', { name: /create medication/i })).toBeInTheDocument()

    rerender(
      <MedicationForm 
        medication={existingMedication}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />
    )

    expect(screen.getByRole('button', { name: /update medication/i })).toBeInTheDocument()
  })
})