import React, { useEffect, useState } from 'react';
import { createSymptomType, updateSymptomType, SymptomTypeCreate, SymptomTypeRead } from '../../services/symptomTypes';

interface Props {
  editing?: SymptomTypeRead | null;
  onSaved?: (saved: SymptomTypeRead) => void;
  onCancelEdit?: () => void;
}

interface FormState {
  name: string;
  description: string;
  active: boolean; // only used when editing
}

export const SymptomTypeForm: React.FC<Props> = ({ editing, onSaved, onCancelEdit }) => {
  const [form, setForm] = useState<FormState>({ name: '', description: '', active: true });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (editing) {
      setForm({ name: editing.name, description: editing.description || '', active: editing.active });
    } else {
      setForm({ name: '', description: '', active: true });
    }
  }, [editing]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm(prev => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null); setSaving(true);
    try {
      if (editing) {
        const updated = await updateSymptomType(editing.id, { name: form.name, description: form.description, active: form.active });
        onSaved?.(updated);
      } else {
        const payload: SymptomTypeCreate = { name: form.name, description: form.description };
        const created = await createSymptomType(payload);
        onSaved?.(created);
        setForm({ name: '', description: '', active: true });
      }
    } catch (e: any) {
      setError(e.message || 'Failed to save');
    } finally { setSaving(false); }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-lg font-semibold">{editing ? 'Edit Symptom Type' : 'New Symptom Type'}</h2>
      {error && <div className="text-sm text-red-600" role="alert">{error}</div>}
      <div className="space-y-2">
        <label className="block text-sm font-medium">Name
          <input
            type="text"
            required
            value={form.name}
            onChange={e => update('name', e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            placeholder="e.g. Headache"
            data-testid="symptom-type-name"
          />
        </label>
        <label className="block text-sm font-medium">Description
          <textarea
            value={form.description}
            onChange={e => update('description', e.target.value)}
            className="mt-1 w-full border rounded px-2 py-1 text-sm"
            placeholder="Optional details for clarity"
            rows={3}
            data-testid="symptom-type-description"
          />
        </label>
        {editing && (
          <label className="inline-flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.active}
              onChange={e => update('active', e.target.checked)}
              data-testid="symptom-type-active"
            /> Active
          </label>
        )}
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={saving}
          className="px-3 py-1.5 text-sm rounded bg-blue-600 text-white disabled:opacity-60"
          data-testid="symptom-type-submit"
        >{saving ? 'Saving…' : editing ? 'Save Changes' : 'Create'}</button>
        {editing && (
          <button type="button" onClick={onCancelEdit} className="px-3 py-1.5 text-sm rounded border">
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};

export default SymptomTypeForm;
