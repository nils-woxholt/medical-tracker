import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SymptomLogForm } from '../src/components/logging/SymptomLogForm';
import * as symptomTypesService from '../src/services/symptomTypes';

describe('SymptomLogForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads symptom types and populates dropdown', async () => {
    vi.spyOn(symptomTypesService, 'listSymptomTypes').mockResolvedValue([
      { id: 1, name: 'Headache', description: '', active: true },
      { id: 2, name: 'Nausea', description: '', active: true },
    ]);
    render(<SymptomLogForm />);
    // Wait for select options
    await waitFor(() => expect(screen.getByRole('combobox')).toBeInTheDocument());
    expect(screen.getByText('Headache')).toBeInTheDocument();
    expect(screen.getByText('Nausea')).toBeInTheDocument();
  });

  it('requires symptom type selection before submit', async () => {
    vi.spyOn(symptomTypesService, 'listSymptomTypes').mockResolvedValue([]);
    render(<SymptomLogForm />);
    fireEvent.click(screen.getByRole('button', { name: /Log Symptom/i }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(/SELECT_TYPE_REQUIRED/);
  });

  it('shows long duration confirmation checkbox when >12h but <=24h', async () => {
    vi.spyOn(symptomTypesService, 'listSymptomTypes').mockResolvedValue([
      { id: 1, name: 'Headache', description: '', active: true },
    ]);
    render(<SymptomLogForm />);
    await waitFor(() => expect(screen.getByText('Headache')).toBeInTheDocument());
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '1' } });
    // Set ended_at to 13h after started_at
    const startedInput = screen.getByLabelText(/Started At/i) as HTMLInputElement;
    const endInput = screen.getByLabelText(/Ended At/i) as HTMLInputElement;
    const startVal = startedInput.value; // yyyy-MM-ddTHH:mm
    const startDate = new Date(startVal);
    const endDate = new Date(startDate.getTime() + 13 * 60 * 60000);
    const endLocal = endDate.toISOString().slice(0,16);
    fireEvent.change(endInput, { target: { value: endLocal } });
    expect(await screen.findByLabelText(/Confirm long duration/i)).toBeInTheDocument();
  });

  it('submits valid log payload', async () => {
    vi.spyOn(symptomTypesService, 'listSymptomTypes').mockResolvedValue([
      { id: 3, name: 'Dizziness', description: '', active: true },
    ]);
    const fetchSpy = vi.spyOn(global, 'fetch' as any).mockResolvedValue({
      ok: true,
      json: async () => ({ id: 55 }),
    });
    render(<SymptomLogForm />);
    await waitFor(() => screen.getByText('Dizziness'));
    fireEvent.change(screen.getByRole('combobox'), { target: { value: '3' } });
    fireEvent.click(screen.getByRole('button', { name: /Log Symptom/i }));
    await waitFor(() => expect(fetchSpy).toHaveBeenCalledTimes(1));
  const args = fetchSpy.mock.calls[0];
  expect(args).toBeDefined();
  const [url, init] = args as [string, RequestInit];
  expect(url).toMatch(/symptom-logs/);
  const rawBody = init.body as string;
  const body = JSON.parse(rawBody);
  expect(body.symptom_type_id).toBe(3);
  expect(body.severity_numeric).toBeGreaterThan(0);
  expect(body.impact_numeric).toBeGreaterThan(0);
  });
});
