// Lightweight client for Server-Sent Events sent over a POST request.
// Browser EventSource only supports GET, so we parse the SSE stream manually
// from a fetch ReadableStream. Each yielded value is one parsed event.

import { authHeaders } from "./api";
import type { SseEvent } from "./types";

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

export async function* streamSse(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncIterable<SseEvent> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...authHeaders(),
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok || !response.body) {
    if (response.status === 401) throw new AuthRequiredError();
    if (response.status === 429) throw new RateLimitError();
    const message = await response.text().catch(() => response.statusText);
    throw new Error(`Stream failed (${response.status}): ${message}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = parseEventBlock(block);
      if (event) yield event;
      boundary = buffer.indexOf("\n\n");
    }
  }
}

function parseEventBlock(block: string): SseEvent | null {
  let kind = "message";
  const dataLines: string[] = [];
  for (const raw of block.split("\n")) {
    const line = raw.trimEnd();
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) kind = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return null;
  try {
    return { kind, data: JSON.parse(dataLines.join("\n")) };
  } catch {
    return { kind, data: { raw: dataLines.join("\n") } };
  }
}
