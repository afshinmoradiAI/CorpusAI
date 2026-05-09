// Plain fetch wrappers around the FastAPI backend.

import type { RefSet } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function uploadReferences(files: File[]): Promise<RefSet> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${API_BASE}/api/paper/upload-refs`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(`Upload failed (${res.status}): ${message}`);
  }
  return res.json();
}

export async function exportDocx(
  markdown: string,
  filename = "paper.docx",
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/paper/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ markdown, filename }),
  });
  if (!res.ok) throw new Error(`Export failed (${res.status})`);
  return res.blob();
}
