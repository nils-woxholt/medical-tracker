"use client";
import React, { useEffect, useState } from 'react';
import { listSymptomTypes, SymptomTypeRead } from '../../services/symptomTypes';

interface SymptomLogFormProps {
  onSaved?: () => void;
}

interface FormState {
  symptom_type_id: number | null;
  started_at: string; // ISO local input value
  ended_at: string; // optional, for closed logs
  severity_numeric: number;
  impact_numeric: number;
  notes: string;
  confirmation_long_duration: boolean;
}

// Simple client-side API call for create (can be refactored into dedicated service)
async function createSymptomLog(payload: any) {
  const res = await fetch('/api/v1/symptom-logs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(body.detail || 'CREATE_FAILED');
  return body;
}

export const SymptomLogForm: React.FC<SymptomLogFormProps> = ({ onSaved }) => {
  const [types, setTypes] = useState<SymptomTypeRead[]>([]);
  const [loadingTypes, setLoadingTypes] = useState(false);
  const [errorTypes, setErrorTypes] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(() => ({
    symptom_type_id: null,
    started_at: new Date().toISOString().slice(0, 16), // yyyy-MM-ddTHH:mm
    ended_at: '',
    severity_numeric: 5,
    impact_numeric: 5,
    notes: '',
    confirmation_long_duration: false,
  }));

  useEffect(() => {
    async function load() {
      setLoadingTypes(true); setErrorTypes(null);
      try { setTypes(await listSymptomTypes(false)); } catch (e: any) { setErrorTypes(e.message); } finally { setLoadingTypes(false); }
    }
    load();
  }, []);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  // Duration confirmation helper (client-side hint)
  function requiresLongConfirmation(): boolean {
    if (!form.started_at || !form.ended_at) return false;
    try {
      const start = new Date(form.started_at);
      const end = new Date(form.ended_at);
      const diffMin = Math.floor((end.getTime() - start.getTime()) / 60000);
      return diffMin > 720 && diffMin <= 1440;
    } catch { return false; }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null); setSaving(true);
    try {
      if (!form.symptom_type_id) throw new Error('SELECT_TYPE_REQUIRED');
      const payload = {
        symptom_type_id: form.symptom_type_id,
        started_at: new Date(form.started_at).toISOString(),
        ended_at: form.ended_at ? new Date(form.ended_at).toISOString() : null,
        severity_numeric: form.severity_numeric,
        impact_numeric: form.impact_numeric,
        notes: form.notes || null,
        confirmation_long_duration: form.confirmation_long_duration,
      };
      await createSymptomLog(payload);
      // Reset minimal fields (keep selected type for convenience)
      setForm(f => ({ ...f, started_at: new Date().toISOString().slice(0,16), ended_at: '', notes: '', confirmation_long_duration: false }));
      onSaved?.();
    } catch (err: any) {
      setError(err.message);
    } finally { setSaving(false); }
  }

  const longNeedsConfirm = requiresLongConfirmation();

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold">Log Symptom</h2>
      {error && <div role="alert" className="text-sm text-red-600">{error}</div>}
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm font-medium">Symptom Type
          <select
            value={form.symptom_type_id ?? ''}
            onChange={e => update('symptom_type_id', e.target.value ? Number(e.target.value) : null)}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            disabled={loadingTypes}
            required
          >
            <option value="">{loadingTypes ? 'Loading types...' : 'Select type'}</option>
            {types.map(t => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium">Started At
          <input
            type="datetime-local"
            value={form.started_at}
            onChange={e => update('started_at', e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            required
          />
        </label>
        <label className="text-sm font-medium">Ended At (optional)
          <input
            type="datetime-local"
            value={form.ended_at}
            onChange={e => update('ended_at', e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
          />
        </label>
        <label className="text-sm font-medium">Severity (1-10)
          <input
            type="number"
            min={1}
            max={10}
            value={form.severity_numeric}
            onChange={e => update('severity_numeric', Number(e.target.value))}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            required
          />
        </label>
        <label className="text-sm font-medium">Impact (1-10)
          <input
            type="number"
            min={1}
            max={10}
            value={form.impact_numeric}
            onChange={e => update('impact_numeric', Number(e.target.value))}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            required
          />
        </label>
        <label className="text-sm font-medium md:col-span-2">Notes
          <textarea
            value={form.notes}
            onChange={e => update('notes', e.target.value)}
            rows={3}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            placeholder="Optional notes"
          />
        </label>
        {longNeedsConfirm && (
          <label className="inline-flex items-center gap-2 text-sm md:col-span-2">
            <input
              type="checkbox"
              checked={form.confirmation_long_duration}
              onChange={e => update('confirmation_long_duration', e.target.checked)}
            /> Confirm long duration (&gt;12h)
          </label>
        )}
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="px-3 py-1.5 text-sm rounded bg-green-600 text-white disabled:opacity-60"
        >{saving ? 'Saving…' : 'Log Symptom'}</button>
      </div>
    </form>
  );
};

export default SymptomLogForm;
