import React, { useEffect, useState } from 'react';
import { listSymptomTypes, deactivateSymptomType, SymptomTypeRead } from '../../services/symptomTypes';

interface Props {
  includeInactive?: boolean;
  onEdit?: (symptomType: SymptomTypeRead) => void;
  refreshToken?: number; // external trigger to reload
}

export const SymptomTypeTable: React.FC<Props> = ({ includeInactive = false, onEdit, refreshToken }) => {
  const [items, setItems] = useState<SymptomTypeRead[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true); setError(null);
    try {
      const data = await listSymptomTypes(includeInactive);
      setItems(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load symptom types');
    } finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [includeInactive, refreshToken]);

  async function handleDeactivate(id: number) {
    if (!confirm('Deactivate this symptom type?')) return;
    try {
      await deactivateSymptomType(id);
      await load();
    } catch (e: any) {
      alert(e.message || 'Failed to deactivate');
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Symptom Types</h2>
        <div className="text-sm text-muted-foreground">{items.length} items</div>
      </div>
      {loading && <div className="text-sm">Loading...</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}
      <table className="min-w-full text-sm border border-gray-200 rounded-md overflow-hidden">
        <thead>
          <tr className="bg-gray-50">
            <th className="px-3 py-2 text-left">Name</th>
            <th className="px-3 py-2 text-left">Description</th>
            <th className="px-3 py-2 text-left">Status</th>
            <th className="px-3 py-2" aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {items.map(st => (
            <tr key={st.id} className="border-t border-gray-100">
              <td className="px-3 py-2 font-medium">{st.name}</td>
              <td className="px-3 py-2 text-gray-600">{st.description || '—'}</td>
              <td className="px-3 py-2">
                {st.active ? (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-green-100 text-green-800" role="status" aria-label="Active">Active</span>
                ) : (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-200 text-gray-600" role="status" aria-label="Inactive">Inactive</span>
                )}
              </td>
              <td className="px-3 py-2 flex gap-2 justify-end">
                {onEdit && <button
                  onClick={() => onEdit(st)}
                  className="px-2 py-1 text-xs border rounded hover:bg-gray-50"
                  aria-label={`Edit ${st.name}`}
                >Edit</button>}
                {st.active && <button
                  onClick={() => handleDeactivate(st.id)}
                  className="px-2 py-1 text-xs border rounded text-red-600 border-red-300 hover:bg-red-50"
                  aria-label={`Deactivate ${st.name}`}
                >Deactivate</button>}
              </td>
            </tr>
          ))}
          {!loading && items.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3 py-6 text-center text-gray-500">No symptom types found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default SymptomTypeTable;
