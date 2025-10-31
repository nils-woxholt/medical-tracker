"use client";
import React, { useEffect, useMemo, useState } from 'react';

interface Option {
  value: number | string;
  label: string;
}

interface SearchableDropdownProps {
  options: Option[];
  value: number | string | null;
  onChange: (value: number | string | null) => void;
  placeholder?: string;
  disabled?: boolean;
  ariaLabel?: string;
}

export const SearchableDropdown: React.FC<SearchableDropdownProps> = ({ options, value, onChange, placeholder = 'Select', disabled, ariaLabel }) => {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState<number>(-1);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options.slice(0, 500);
    return options.filter(o => o.label.toLowerCase().includes(q)).slice(0, 500);
  }, [query, options]);

  function handleSelect(opt: Option) {
    onChange(opt.value);
    setOpen(false);
    setQuery('');
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!open && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      setOpen(true); e.preventDefault(); return;
    }
    if (!open) return;
    if (e.key === 'Escape') { setOpen(false); return; }
    if (e.key === 'ArrowDown') {
      setActiveIndex(i => Math.min(i + 1, filtered.length - 1)); e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      setActiveIndex(i => Math.max(i - 1, 0)); e.preventDefault();
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      const opt = filtered[activeIndex];
      if (opt) { e.preventDefault(); handleSelect(opt); }
    }
  }

  useEffect(() => {
    if (open) setActiveIndex(filtered.length ? 0 : -1);
  }, [open, filtered.length]);

  return (
    <div className="relative" onKeyDown={handleKeyDown} aria-label={ariaLabel}>
      <button
        type="button"
        disabled={disabled}
        className="w-full border rounded px-2 py-1 text-left text-sm bg-white"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen(o => !o)}
      >
        {value == null ? placeholder : options.find(o => o.value === value)?.label || placeholder}
      </button>
      {open && (
        <div className="absolute z-10 mt-1 w-full border rounded bg-white shadow">
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="w-full px-2 py-1 text-sm border-b"
            placeholder="Search..."
            aria-label="Search options"
          />
          <ul role="listbox" className="max-h-60 overflow-auto" aria-label="Options list">
            {filtered.map((opt, idx) => (
              <li
                key={opt.value}
                role="option"
                aria-selected={value === opt.value}
                className={`px-2 py-1 text-sm cursor-pointer ${idx === activeIndex ? 'bg-blue-600 text-white' : 'hover:bg-blue-50'}`}
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => handleSelect(opt)}
              >
                {opt.label}
              </li>
            ))}
            {filtered.length === 0 && <li className="px-2 py-2 text-sm text-gray-500">No matches</li>}
          </ul>
        </div>
      )}
    </div>
  );
};

export default SearchableDropdown;
