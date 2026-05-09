"use client";

import { useState } from "react";
import { exportDocx } from "@/lib/api";

export function ExportButtons({ markdown, topic }: { markdown: string; topic: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const safe = topic.replace(/[^a-z0-9-_ ]+/gi, "").slice(0, 60).trim() || "paper";

  function downloadBlob(blob: Blob, name: string) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadMarkdown() {
    downloadBlob(new Blob([markdown], { type: "text/markdown" }), `${safe}.md`);
  }

  async function downloadDocx() {
    setBusy(true);
    setError(null);
    try {
      const blob = await exportDocx(markdown, `${safe}.docx`);
      downloadBlob(blob, `${safe}.docx`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={downloadDocx}
        disabled={busy}
        className="text-sm rounded bg-neutral-900 text-white px-3 py-1.5 disabled:opacity-50 dark:bg-white dark:text-neutral-900"
      >
        {busy ? "Building…" : "Download .docx"}
      </button>
      <button
        onClick={downloadMarkdown}
        className="text-sm rounded border border-neutral-300 dark:border-neutral-700 px-3 py-1.5"
      >
        Download .md
      </button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
