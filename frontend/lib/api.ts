// Plain fetch wrappers around the FastAPI backend.

import { getApiKey, getUserId } from "./auth";
import type { RefSet, UploadedFigure } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const key = getApiKey();
  if (key) headers["X-API-Key"] = key;
  const user = getUserId();
  if (user) headers["X-User-ID"] = user;
  return headers;
}

export class AuthRequiredError extends Error {
  constructor(message = "Authentication failed — open Settings to enter your API key.") {
    super(message);
    this.name = "AuthRequiredError";
  }
}

export class RateLimitError extends Error {
  constructor(message = "Rate limit exceeded — wait a minute and try again.") {
    super(message);
    this.name = "RateLimitError";
  }
}

function throwForStatus(status: number, fallback: string): never {
  if (status === 401) throw new AuthRequiredError();
  if (status === 429) throw new RateLimitError();
  throw new Error(fallback);
}

export async function uploadReferences(files: File[]): Promise<RefSet> {
  const form = new FormData();
  for (const f of files) form.append("files", f);
  const res = await fetch(`${API_BASE}/api/paper/upload-refs`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const message = await res.text().catch(() => res.statusText);
    throwForStatus(res.status, `Upload failed (${res.status}): ${message}`);
  }
  return res.json();
}

export async function deleteReferenceSet(setId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/paper/refs/${encodeURIComponent(setId)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok && res.status !== 204) {
    const message = await res.text().catch(() => res.statusText);
    throwForStatus(res.status, `Delete failed (${res.status}): ${message}`);
  }
}

export async function uploadFigure(file: File): Promise<UploadedFigure> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/thesis/upload-figure`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  if (!res.ok) {
    const message = await res.text().catch(() => res.statusText);
    throwForStatus(res.status, `Figure upload failed (${res.status}): ${message}`);
  }
  return res.json();
}

export async function exportDocx(
  markdown: string,
  filename = "paper.docx",
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/paper/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ markdown, filename }),
  });
  if (!res.ok) {
    throwForStatus(res.status, `Export failed (${res.status})`);
  }
  return res.blob();
}
