import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SymptomTypeForm } from '../src/components/symptom-types/SymptomTypeForm';
import * as service from '../src/services/symptomTypes';

const createSpy = vi.spyOn(service, 'createSymptomType');
const updateSpy = vi.spyOn(service, 'updateSymptomType');

describe('SymptomTypeForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders create form defaults', () => {
    render(<SymptomTypeForm />);
    expect(screen.getByRole('heading', { name: /New Symptom Type/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Name/i)).toHaveValue('');
  });

  it('creates a new symptom type', async () => {
    createSpy.mockResolvedValue({ id: 11, name: 'Dizziness', description: 'Spinning sensation', active: true });
    const onSaved = vi.fn();
    render(<SymptomTypeForm onSaved={onSaved} />);
    fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'Dizziness' } });
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: 'Spinning sensation' } });
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    // After create resets fields
    expect(screen.getByLabelText(/Name/i)).toHaveValue('');
  });

  it('edits existing symptom type including active toggle', async () => {
    updateSpy.mockResolvedValue({ id: 12, name: 'Fatigue', description: 'Updated', active: false });
    const onSaved = vi.fn();
    render(<SymptomTypeForm editing={{ id: 12, name: 'Fatigue', description: 'Tiredness', active: true }} onSaved={onSaved} />);
    // Active toggle visible
    const activeCheckbox = screen.getByRole('checkbox', { name: /Active/i });
    expect(activeCheckbox).toBeChecked();
    fireEvent.click(activeCheckbox); // deactivate
    fireEvent.change(screen.getByLabelText(/Description/i), { target: { value: 'Updated' } });
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/i }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(expect.objectContaining({ active: false, description: 'Updated' })));
  });

  it('shows error on failure', async () => {
    createSpy.mockRejectedValue(new Error('Name exists'));
    render(<SymptomTypeForm />);
    fireEvent.change(screen.getByLabelText(/Name/i), { target: { value: 'Duplicate' } });
    fireEvent.click(screen.getByRole('button', { name: /Create/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/Name exists/i);
  });

  it('cancel edit resets to create mode', async () => {
    const onCancel = vi.fn();
    const { rerender } = render(<SymptomTypeForm editing={{ id: 99, name: 'Headache', description: '', active: true }} onCancelEdit={onCancel} />);
    fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(onCancel).toHaveBeenCalled();
    // simulate parent clearing edit prop
    rerender(<SymptomTypeForm />);
    expect(screen.getByRole('heading', { name: /New Symptom Type/i })).toBeInTheDocument();
  });
});
