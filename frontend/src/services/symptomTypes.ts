// Frontend service client for SymptomType CRUD (Feature 004 Phase 3 US1)
// Provides minimal fetch-based wrappers. Lean Mode: no global state lib; simple functions.

export interface SymptomTypeRead {
  id: number;
  name: string;
  description?: string | null;
  active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface SymptomTypeCreate {
  name: string;
  description?: string | null;
}

export interface SymptomTypeUpdate {
  name?: string;
  description?: string | null;
  active?: boolean;
}

const BASE = '/symptom-types';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let body: any = null;
    try { body = await res.json(); } catch { /* ignore parse errors */ }
    const error = body?.detail || body?.error || res.statusText;
    throw new Error(error);
  }
  return res.json() as Promise<T>;
}

export async function listSymptomTypes(includeInactive = false): Promise<SymptomTypeRead[]> {
  const url = includeInactive ? `${BASE}?include_inactive=true` : BASE;
  const res = await fetch(url, { credentials: 'include' });
  return handleResponse<SymptomTypeRead[]>(res);
}

export async function createSymptomType(payload: SymptomTypeCreate): Promise<SymptomTypeRead> {
  const res = await fetch(BASE, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleResponse<SymptomTypeRead>(res);
}

export async function updateSymptomType(id: number, payload: SymptomTypeUpdate): Promise<SymptomTypeRead> {
  const res = await fetch(`${BASE}/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleResponse<SymptomTypeRead>(res);
}

export async function deactivateSymptomType(id: number): Promise<SymptomTypeRead> {
  const res = await fetch(`${BASE}/${id}/deactivate`, {
    method: 'PATCH',
    credentials: 'include'
  });
  return handleResponse<SymptomTypeRead>(res);
}
