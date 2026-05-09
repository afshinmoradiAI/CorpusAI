"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import type { ResearchOutput } from "@/lib/types";
import { StreamLog } from "@/components/ui/StreamLog";

type StepState = "pending" | "active" | "done" | "error";

const STEP_LABELS: { kind: string; label: string }[] = [
  { kind: "topic_analysed", label: "Analysing topic" },
  { kind: "papers_found", label: "Searching literature" },
  { kind: "papers_summarised", label: "Summarising papers" },
  { kind: "gap_found", label: "Identifying research gap" },
  { kind: "idea_generated", label: "Generating idea" },
  { kind: "method_designed", label: "Designing method" },
  { kind: "discussion_written", label: "Writing discussion" },
];

export function ExploreView() {
  const [topic, setTopic] = useState("");
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<StepState[]>(STEP_LABELS.map(() => "pending"));
  const [result, setResult] = useState<ResearchOutput | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [paperCount, setPaperCount] = useState<number | null>(null);

  async function run() {
    if (!topic.trim() || running) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setPaperCount(null);
    const initial = STEP_LABELS.map(() => "pending" as StepState);
    initial[0] = "active";
    setSteps(initial);

    try {
      const url = `${API_BASE}/api/research/explore`;
      for await (const ev of streamSse(url, { topic })) {
        const idx = STEP_LABELS.findIndex((s) => s.kind === ev.kind);
        if (idx !== -1) {
          setSteps((prev) => {
            const next = [...prev];
            next[idx] = "done";
            if (idx + 1 < next.length) next[idx + 1] = "active";
            return next;
          });
        }
        if (ev.kind === "papers_found") {
          setPaperCount((ev.data.count as number) ?? 0);
        }
        if (ev.kind === "completed") {
          setResult(ev.data as unknown as ResearchOutput);
        }
        if (ev.kind === "error") {
          setError((ev.data.message as string) ?? "Unknown error");
          setSteps((prev) => prev.map((s) => (s === "active" ? "error" : s)));
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grid md:grid-cols-[320px_1fr] gap-6">
      <aside className="space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1">Biology topic</label>
          <textarea
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
            rows={4}
            placeholder="e.g. Mitochondrial dynamics in T-cell exhaustion"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={running}
          />
        </div>
        <button
          onClick={run}
          disabled={running || !topic.trim()}
          className="w-full rounded bg-neutral-900 text-white text-sm py-2 disabled:opacity-50 dark:bg-white dark:text-neutral-900"
        >
          {running ? "Running…" : "Generate idea"}
        </button>
        <StreamLog
          steps={STEP_LABELS.map((s, i) => ({ label: s.label, state: steps[i] }))}
        />
        {paperCount !== null && (
          <p className="text-xs text-neutral-500">{paperCount} papers retrieved</p>
        )}
        {error && (
          <p className="text-xs text-red-600 dark:text-red-400">Error: {error}</p>
        )}
      </aside>

      <main className="min-w-0">
        {!result && !running && (
          <p className="text-sm text-neutral-500">
            Enter a topic and click <em>Generate idea</em>. Each step streams as
            it completes.
          </p>
        )}
        {result && <ExploreResult result={result} />}
      </main>
    </div>
  );
}

function ExploreResult({ result }: { result: ResearchOutput }) {
  return (
    <article className="space-y-6">
      <header>
        <h2 className="text-lg font-semibold">{result.topic}</h2>
      </header>
      <Section heading="Research gap">
        <p>{result.gap.description}</p>
        {result.gap.evidence.length > 0 && (
          <ul className="list-disc ml-5 mt-2 text-sm text-neutral-600 dark:text-neutral-400">
            {result.gap.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
      </Section>
      <Section heading="Idea">
        <p>{result.idea}</p>
      </Section>
      <Section heading="Hypothetical method">
        <p>{result.method}</p>
      </Section>
      <Section heading="Aim &amp; importance">
        <p>{result.discussion}</p>
      </Section>
      <Section heading={`References (${result.references.length})`}>
        <ol className="list-decimal ml-5 text-sm space-y-1">
          {result.references.map((r, i) => (
            <li key={i}>
              <span className="font-medium">{r.title}</span>
              {r.year && <> ({r.year})</>}
              {r.authors.length > 0 && (
                <span className="text-neutral-500"> — {r.authors.slice(0, 4).join(", ")}{r.authors.length > 4 ? " et al." : ""}</span>
              )}
            </li>
          ))}
        </ol>
      </Section>
    </article>
  );
}

function Section({
  heading,
  children,
}: {
  heading: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-neutral-500 mb-2">
        {heading}
      </h3>
      <div className="text-sm leading-relaxed">{children}</div>
    </section>
  );
}
