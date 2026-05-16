"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import type { RefSet, ResearchOutput } from "@/lib/types";
import { StreamLog } from "@/components/ui/StreamLog";
import { PdfUploader } from "@/components/write/PdfUploader";

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
  const [refSet, setRefSet] = useState<RefSet | null>(null);
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
      const body: Record<string, unknown> = { topic };
      if (refSet) body.set_id = refSet.set_id;

      for await (const ev of streamSse(url, body)) {
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
    <div className="grid md:grid-cols-[360px_1fr] gap-8">
      <aside className="space-y-5">
        <div>
          <label className="text-base font-semibold block mb-2">Research topic</label>
          <textarea
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            rows={4}
            placeholder="e.g. Mitochondrial dynamics in T-cell exhaustion"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={running}
          />
        </div>

        <div>
          <p className="text-base font-semibold mb-1">
            Reference PDFs{" "}
            <span className="text-neutral-400 text-sm font-normal">(optional, 1–100 papers)</span>
          </p>
          <p className="text-sm text-neutral-400 mb-2">
            Upload your own papers to ground the proposal in your literature.
          </p>
          <PdfUploader refSet={refSet} onUploaded={setRefSet} disabled={running} />
        </div>

        <button
          onClick={run}
          disabled={running || !topic.trim()}
          className="w-full rounded bg-[color:var(--gold)] text-black text-base font-semibold py-3 disabled:opacity-50 hover:bg-[color:var(--gold-bright)] transition"
        >
          {running ? "Generating…" : "Generate proposal"}
        </button>

        <StreamLog
          steps={STEP_LABELS.map((s, i) => ({ label: s.label, state: steps[i] }))}
        />
        {paperCount !== null && (
          <p className="text-sm text-neutral-400">{paperCount} papers retrieved from literature</p>
        )}
        {error && (
          <p className="text-sm text-red-400">Error: {error}</p>
        )}
      </aside>

      <main className="min-w-0">
        {!result && !running && (
          <p className="text-base text-neutral-400">
            Enter a topic and click <em>Generate proposal</em>. Steps stream as they complete.
            Optionally upload reference PDFs to ground the proposal in your literature.
          </p>
        )}
        {result && <ExploreResult result={result} />}
      </main>
    </div>
  );
}

function ExploreResult({ result }: { result: ResearchOutput }) {
  return (
    <article className="space-y-7">
      <header>
        <h2 className="text-2xl font-semibold font-display text-[color:var(--gold-bright)]">{result.topic}</h2>
      </header>
      <Section heading="Research gap">
        <p className="text-base leading-relaxed">{result.gap.description}</p>
        {result.gap.evidence.length > 0 && (
          <ul className="list-disc ml-5 mt-3 space-y-1 text-base text-neutral-300">
            {result.gap.evidence.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        )}
      </Section>
      <Section heading="Novel idea">
        <p className="text-base leading-relaxed">{result.idea}</p>
      </Section>
      <Section heading="Hypothetical method">
        <p className="text-base leading-relaxed">{result.method}</p>
      </Section>
      <Section heading="Aim &amp; importance">
        <p className="text-base leading-relaxed">{result.discussion}</p>
      </Section>
      <Section heading={`References (${result.references.length})`}>
        <ol className="list-decimal ml-5 space-y-1.5">
          {result.references.map((r, i) => (
            <li key={i} className="text-base">
              <span className="font-medium">{r.title}</span>
              {r.year && <> ({r.year})</>}
              {r.authors.length > 0 && (
                <span className="text-neutral-400"> — {r.authors.slice(0, 4).join(", ")}{r.authors.length > 4 ? " et al." : ""}</span>
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
      <h3 className="text-sm font-semibold uppercase tracking-widest text-[color:var(--gold)] mb-3">
        {heading}
      </h3>
      <div className="leading-relaxed">{children}</div>
    </section>
  );
}
