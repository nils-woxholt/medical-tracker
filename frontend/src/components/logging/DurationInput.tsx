import React, { useEffect, useState } from 'react';

interface DurationInputProps {
  startedAt: string; // datetime-local value
  endedAt: string; // datetime-local value
  onChange: (startedAt: string, endedAt: string) => void;
  onLongFlagChange?: (needsConfirmation: boolean) => void;
}

// Computes diff minutes; returns null if invalid order or missing values
function diffMinutes(start: string, end: string): number | null {
  if (!start || !end) return null;
  const s = new Date(start); const e = new Date(end);
  const ms = e.getTime() - s.getTime();
  if (ms <= 0) return null;
  return Math.floor(ms / 60000);
}

export const DurationInput: React.FC<DurationInputProps> = ({ startedAt, endedAt, onChange, onLongFlagChange }) => {
  const [hours, setHours] = useState<string>('');
  const [minutes, setMinutes] = useState<string>('');
  const [warning, setWarning] = useState<string | null>(null);

  // Keep derived hours/minutes in sync when endedAt changes
  useEffect(() => {
    const d = diffMinutes(startedAt, endedAt);
    if (d === null) { setHours(''); setMinutes(''); setWarning(null); onLongFlagChange?.(false); return; }
    const h = Math.floor(d / 60); const m = d % 60;
    setHours(String(h)); setMinutes(String(m));
    if (d > 1440) {
      setWarning('Duration exceeds 24h limit');
      onLongFlagChange?.(false);
    } else if (d > 720) {
      setWarning('Duration >12h requires confirmation');
      onLongFlagChange?.(true);
    } else {
      setWarning(null); onLongFlagChange?.(false);
    }
  }, [startedAt, endedAt]);

  function handleHoursChange(val: string) {
    setHours(val);
    applyComposite(val, minutes);
  }

  function handleMinutesChange(val: string) {
    setMinutes(val);
    applyComposite(hours, val);
  }

  function applyComposite(hStr: string, mStr: string) {
    const h = parseInt(hStr, 10); const m = parseInt(mStr, 10);
    if (isNaN(h) || isNaN(m)) return;
    // Derive endedAt from startedAt + duration
    const startDate = new Date(startedAt);
    const endDate = new Date(startDate.getTime() + (h * 60 + m) * 60000);
    const iso = endDate.toISOString().slice(0,16);
    onChange(startedAt, iso);
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2 items-end">
        <label className="text-sm font-medium">Hours
          <input
            type="number"
            min={0}
            max={24}
            value={hours}
            onChange={e => handleHoursChange(e.target.value)}
            className="mt-1 w-24 border rounded px-2 py-1 text-sm"
            placeholder="h"
          />
        </label>
        <label className="text-sm font-medium">Minutes
          <input
            type="number"
            min={0}
            max={59}
            value={minutes}
            onChange={e => handleMinutesChange(e.target.value)}
            className="mt-1 w-24 border rounded px-2 py-1 text-sm"
            placeholder="m"
          />
        </label>
        <div className="text-xs text-gray-500">Auto-computes Ended At field</div>
      </div>
      {warning && <div className="text-xs text-amber-700" role="alert">{warning}</div>}
    </div>
  );
};

export default DurationInput;
