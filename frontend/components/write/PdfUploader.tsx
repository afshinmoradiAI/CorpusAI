"use client";

import { useState } from "react";
import { uploadReferences } from "@/lib/api";
import type { RefSet } from "@/lib/types";

interface Props {
  refSet: RefSet | null;
  onUploaded: (set: RefSet) => void;
  disabled?: boolean;
}

export function PdfUploader({ refSet, onUploaded, disabled }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const set = await uploadReferences(files);
      onUploaded(set);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  return (
    <div>
      <label className="text-sm font-medium block mb-1">
        Reference PDFs <span className="text-neutral-400 text-xs">(up to 30, 25 MB each)</span>
      </label>
      <input
        type="file"
        accept="application/pdf"
        multiple
        onChange={onChange}
        disabled={busy || disabled}
        className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-neutral-200 dark:file:bg-neutral-800 file:px-3 file:py-1.5 file:text-sm"
      />
      {busy && <p className="text-xs text-amber-600 mt-1">Uploading and indexing…</p>}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
      {refSet && (
        <ul className="mt-2 text-xs text-neutral-600 dark:text-neutral-400 space-y-0.5">
          {refSet.documents.map((d) => (
            <li key={d.ref_id}>
              • {d.filename}{" "}
              <span className="text-neutral-400">
                ({d.page_count}p, {(d.char_count / 1000).toFixed(1)}k chars)
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
