import React, { useState } from 'react';
import SymptomTypeTable from '../../components/symptom-types/SymptomTypeTable';
import SymptomTypeForm from '../../components/symptom-types/SymptomTypeForm';
import { SymptomTypeRead } from '../../services/symptomTypes';

// Simple client page (assuming app router with client components)
// If server components are default, we mark this as a client component.
'use client';

export default function SymptomTypesPage() {
  const [editing, setEditing] = useState<SymptomTypeRead | null>(null);
  const [refreshToken, setRefreshToken] = useState(0);

  function handleSaved() {
    setEditing(null);
    setRefreshToken(t => t + 1);
  }

  return (
    <div className="max-w-3xl mx-auto p-4 space-y-8" data-testid="symptom-types-page">
      <SymptomTypeForm
        editing={editing || undefined}
        onSaved={handleSaved}
        onCancelEdit={() => setEditing(null)}
      />
      <SymptomTypeTable
        onEdit={st => setEditing(st)}
        refreshToken={refreshToken}
      />
    </div>
  );
}
