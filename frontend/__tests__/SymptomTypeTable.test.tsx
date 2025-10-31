import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { SymptomTypeTable } from '../src/components/symptom-types/SymptomTypeTable';
import * as service from '../src/services/symptomTypes';

describe('SymptomTypeTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading then data rows', async () => {
    const mockList = vi.spyOn(service, 'listSymptomTypes').mockResolvedValue([
      { id: 1, name: 'Headache', description: 'Pain in head', active: true },
      { id: 2, name: 'Nausea', description: 'Feeling sick', active: true },
    ]);
    render(<SymptomTypeTable />);
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
    await waitFor(() => expect(mockList).toHaveBeenCalled());
    expect(screen.getByText('Headache')).toBeInTheDocument();
    expect(screen.getByText('Nausea')).toBeInTheDocument();
  });

  it('shows empty state when no items', async () => {
    vi.spyOn(service, 'listSymptomTypes').mockResolvedValue([]);
    render(<SymptomTypeTable />);
    const empty = await screen.findByText(/No symptom types found/i);
    expect(empty).toBeInTheDocument();
  });

  it('displays error when list fails', async () => {
    vi.spyOn(service, 'listSymptomTypes').mockRejectedValue(new Error('Network issue'));
    render(<SymptomTypeTable />);
    const err = await screen.findByText(/Network issue/i);
    expect(err).toBeInTheDocument();
  });

  it('calls onEdit when edit clicked', async () => {
    vi.spyOn(service, 'listSymptomTypes').mockResolvedValue([
      { id: 3, name: 'Fatigue', description: '', active: true },
    ]);
    const onEdit = vi.fn();
    render(<SymptomTypeTable onEdit={onEdit} />);
    const editBtn = await screen.findByRole('button', { name: /Edit Fatigue/i });
    fireEvent.click(editBtn);
    expect(onEdit).toHaveBeenCalledWith(expect.objectContaining({ id: 3, name: 'Fatigue' }));
  });

  it('deactivates an item and reloads list', async () => {
    const listSpy = vi.spyOn(service, 'listSymptomTypes');
    listSpy.mockResolvedValueOnce([
      { id: 5, name: 'Pain', description: '', active: true },
    ]);
    listSpy.mockResolvedValueOnce([
      { id: 5, name: 'Pain', description: '', active: false },
    ]);
  const deactivateSpy = vi.spyOn(service, 'deactivateSymptomType').mockResolvedValue({ id: 5, name: 'Pain', description: '', active: true });

    // mock confirm to auto-accept
    vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(<SymptomTypeTable />);
    const deactivateBtn = await screen.findByRole('button', { name: /Deactivate Pain/i });
    fireEvent.click(deactivateBtn);

    await waitFor(() => {
      expect(deactivateSpy).toHaveBeenCalledWith(5);
      expect(listSpy).toHaveBeenCalledTimes(2);
    });
    expect(await screen.findByText(/Inactive/i)).toBeInTheDocument();
  });
});
