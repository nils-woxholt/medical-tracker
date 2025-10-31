import { useEffect, useState } from 'react';
import { SymptomTypeRead } from '../../services/symptomTypes';

// In Lean Mode we do not yet store per-type default severity/impact.
// This hook provides heuristic defaults and a future extension point.
// Strategy: When a type is selected, severity defaults to mid (5), impact to mid (5).
// If type name matches certain keywords we can adjust (example logic included but minimal).

function deriveDefaults(name: string | undefined) {
  if (!name) return { severity: 5, impact: 5 };
  const lower = name.toLowerCase();
  if (/(pain|migraine)/.test(lower)) return { severity: 7, impact: 6 };
  if (/(nausea|dizzy)/.test(lower)) return { severity: 6, impact: 5 };
  return { severity: 5, impact: 5 };
}

export function useSymptomDefaults(selectedTypeId: number | null, types: SymptomTypeRead[]) {
  const [severityDefault, setSeverityDefault] = useState(5);
  const [impactDefault, setImpactDefault] = useState(5);

  useEffect(() => {
    if (!selectedTypeId) return;
    const found = types.find(t => t.id === selectedTypeId);
    const { severity, impact } = deriveDefaults(found?.name);
    setSeverityDefault(severity);
    setImpactDefault(impact);
  }, [selectedTypeId, types]);

  return { severityDefault, impactDefault };
}

export default useSymptomDefaults;
