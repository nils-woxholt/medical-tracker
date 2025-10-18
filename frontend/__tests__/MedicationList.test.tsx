/**
 * @jest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MedicationList } from '../src/components/MedicationList'

// Mock the medication service
jest.mock('../src/services/medicationService', () => ({
  getMedications: jest.fn(),
  deactivateMedication: jest.fn(),
  deleteMedication: jest.fn(),
}))

const mockGetMedications = jest.fn()
const mockDeactivateMedication = jest.fn()
const mockDeleteMedication = jest.fn()

beforeEach(() => {
  jest.clearAllMocks()
})

describe('MedicationList', () => {
  const mockMedications = [
    {
      id: 1,
      name: 'Aspirin',
      description: 'Pain reliever',
      is_active: true,
      created_at: '2023-01-01T10:00:00Z',
      updated_at: '2023-01-01T10:00:00Z'
    },
    {
      id: 2,
      name: 'Vitamin D',
      description: 'Daily vitamin supplement',
      is_active: true,
      created_at: '2023-01-02T10:00:00Z',
      updated_at: '2023-01-02T10:00:00Z'
    },
    {
      id: 3,
      name: 'Inactive Med',
      description: 'No longer used',
      is_active: false,
      created_at: '2023-01-03T10:00:00Z',
      updated_at: '2023-01-03T10:00:00Z'
    }
  ]

  const mockOnEdit = jest.fn()
  const mockOnAdd = jest.fn()

  beforeEach(() => {
    mockOnEdit.mockClear()
    mockOnAdd.mockClear()
    mockGetMedications.mockResolvedValue(mockMedications)
  })

  it('renders loading state initially', () => {
    mockGetMedications.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('renders medication list after loading', async () => {
    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
      expect(screen.getByText('Vitamin D')).toBeInTheDocument()
    })
  })

  it('displays active medications by default', async () => {
    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
      expect(screen.getByText('Vitamin D')).toBeInTheDocument()
      expect(screen.queryByText('Inactive Med')).not.toBeInTheDocument()
    })

    expect(mockGetMedications).toHaveBeenCalledWith({ active_only: true })
  })

  it('shows inactive medications when filter is toggled', async () => {
    const user = userEvent.setup()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    // Toggle to show inactive
    const showInactiveToggle = screen.getByLabelText(/show inactive/i)
    await user.click(showInactiveToggle)

    await waitFor(() => {
      expect(mockGetMedications).toHaveBeenCalledWith({ active_only: false })
    })
  })

  it('filters medications by search term', async () => {
    const user = userEvent.setup()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    // Search for specific medication
    const searchInput = screen.getByPlaceholderText(/search medications/i)
    await user.type(searchInput, 'Aspirin')

    await waitFor(() => {
      expect(mockGetMedications).toHaveBeenCalledWith({ 
        active_only: true, 
        search: 'Aspirin' 
      })
    })
  })

  it('debounces search input', async () => {
    const user = userEvent.setup()
    jest.useFakeTimers()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    const searchInput = screen.getByPlaceholderText(/search medications/i)
    
    // Type rapidly
    await user.type(searchInput, 'A')
    await user.type(searchInput, 's')
    await user.type(searchInput, 'p')

    // Should not have called with partial searches yet
    expect(mockGetMedications).toHaveBeenCalledTimes(1) // Initial load only

    // Fast-forward timer to trigger debounce
    jest.advanceTimersByTime(500)

    await waitFor(() => {
      expect(mockGetMedications).toHaveBeenCalledWith({ 
        active_only: true, 
        search: 'Asp' 
      })
    })

    jest.useRealTimers()
  })

  it('handles pagination correctly', async () => {
    const user = userEvent.setup()
    const paginatedResponse = {
      items: mockMedications.slice(0, 2),
      total: 10,
      page: 1,
      per_page: 2,
      pages: 5
    }
    mockGetMedications.mockResolvedValue(paginatedResponse)

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 5')).toBeInTheDocument()
    })

    // Navigate to next page
    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    expect(mockGetMedications).toHaveBeenCalledWith({ 
      active_only: true, 
      page: 2,
      per_page: 2
    })
  })

  it('calls onEdit when edit button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    const editButtons = screen.getAllByRole('button', { name: /edit/i })
    await user.click(editButtons[0])

    expect(mockOnEdit).toHaveBeenCalledWith(mockMedications[0])
  })

  it('calls onAdd when add button is clicked', async () => {
    const user = userEvent.setup()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    const addButton = screen.getByRole('button', { name: /add medication/i })
    await user.click(addButton)

    expect(mockOnAdd).toHaveBeenCalled()
  })

  it('deactivates medication when deactivate button is clicked', async () => {
    const user = userEvent.setup()
    mockDeactivateMedication.mockResolvedValue({ ...mockMedications[0], is_active: false })

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    const deactivateButtons = screen.getAllByRole('button', { name: /deactivate/i })
    await user.click(deactivateButtons[0])

    // Confirm deactivation in modal
    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    expect(mockDeactivateMedication).toHaveBeenCalledWith(1)
  })

  it('shows error state when loading fails', async () => {
    const errorMessage = 'Failed to load medications'
    mockGetMedications.mockRejectedValue(new Error(errorMessage))

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/error loading medications/i)).toBeInTheDocument()
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('shows empty state when no medications found', async () => {
    mockGetMedications.mockResolvedValue([])

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/no medications found/i)).toBeInTheDocument()
      expect(screen.getByText(/add your first medication/i)).toBeInTheDocument()
    })
  })

  it('refreshes list after successful deactivation', async () => {
    const user = userEvent.setup()
    mockDeactivateMedication.mockResolvedValue({ ...mockMedications[0], is_active: false })

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    // Initial load
    expect(mockGetMedications).toHaveBeenCalledTimes(1)

    const deactivateButtons = screen.getAllByRole('button', { name: /deactivate/i })
    await user.click(deactivateButtons[0])

    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    await waitFor(() => {
      // Should reload list after deactivation
      expect(mockGetMedications).toHaveBeenCalledTimes(2)
    })
  })

  it('displays medication status badges correctly', async () => {
    // Mock response with both active and inactive medications
    mockGetMedications.mockResolvedValue(mockMedications)

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
        showInactive={true}
      />
    )

    await waitFor(() => {
      const activeBadges = screen.getAllByText(/active/i)
      const inactiveBadges = screen.getAllByText(/inactive/i)
      
      expect(activeBadges).toHaveLength(2) // Aspirin and Vitamin D
      expect(inactiveBadges).toHaveLength(1) // Inactive Med
    })
  })

  it('sorts medications by name alphabetically', async () => {
    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
      />
    )

    await waitFor(() => {
      const medicationNames = screen.getAllByTestId('medication-name')
      const names = medicationNames.map(el => el.textContent)
      expect(names).toEqual(['Aspirin', 'Vitamin D']) // Should be sorted
    })
  })

  it('handles bulk operations selection', async () => {
    const user = userEvent.setup()

    render(
      <MedicationList 
        onEdit={mockOnEdit}
        onAdd={mockOnAdd}
        enableBulkOperations={true}
      />
    )

    await waitFor(() => {
      expect(screen.getByText('Aspirin')).toBeInTheDocument()
    })

    // Select medications using checkboxes
    const checkboxes = screen.getAllByRole('checkbox')
    await user.click(checkboxes[0]) // Select first medication
    await user.click(checkboxes[1]) // Select second medication

    // Bulk deactivate button should appear
    expect(screen.getByRole('button', { name: /deactivate selected/i })).toBeInTheDocument()
  })
})