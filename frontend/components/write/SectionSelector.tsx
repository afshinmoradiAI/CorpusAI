"use client";

import { SECTION_LABELS, type SectionName } from "@/lib/types";

const ALL: SectionName[] = ["abstract", "introduction", "methods", "results", "discussion"];

interface Props {
  selected: Set<SectionName>;
  onChange: (next: Set<SectionName>) => void;
  disabled?: boolean;
}

export function SectionSelector({ selected, onChange, disabled }: Props) {
  function toggle(s: SectionName) {
    const next = new Set(selected);
    if (next.has(s)) next.delete(s);
    else next.add(s);
    onChange(next);
  }
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-sm font-medium">Sections to generate</span>
        <button
          type="button"
          onClick={() =>
            onChange(selected.size === ALL.length ? new Set() : new Set(ALL))
          }
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
          disabled={disabled}
        >
          {selected.size === ALL.length ? "Clear" : "Select all"}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-1 text-sm">
        {ALL.map((s) => (
          <label key={s} className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selected.has(s)}
              onChange={() => toggle(s)}
              disabled={disabled}
            />
            {SECTION_LABELS[s]}
          </label>
        ))}
      </div>
    </div>
  );
}
