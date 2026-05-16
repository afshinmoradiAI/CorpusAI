"use client";

import { useMemo, useState } from "react";
import { API_BASE } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import {
  SECTION_LABELS,
  type RefSet,
  type SectionName,
  type WriteResult,
} from "@/lib/types";
import { Markdown } from "@/components/ui/Markdown";
import { ExportButtons } from "./ExportButtons";
import { PdfUploader } from "./PdfUploader";
import { ReviewPanel } from "./ReviewPanel";
import { SectionSelector } from "./SectionSelector";

const DEFAULT_SECTIONS: SectionName[] = [
  "introduction",
  "methods",
  "results",
  "discussion",
  "abstract",
];

type SectionState = "pending" | "active" | "done";

interface Progress {
  sections: Record<SectionName, SectionState>;
  references: SectionState;
  review: SectionState;
}

const INITIAL_PROGRESS: Progress = {
  sections: {
    abstract: "pending",
    introduction: "pending",
    methods: "pending",
    results: "pending",
    discussion: "pending",
  },
  references: "pending",
  review: "pending",
};

export function WriteView() {
  const [refSet, setRefSet] = useState<RefSet | null>(null);
  const [topic, setTopic] = useState("");
  const [selected, setSelected] = useState<Set<SectionName>>(
    new Set(DEFAULT_SECTIONS),
  );
  const [userResults, setUserResults] = useState("");
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<Progress>(INITIAL_PROGRESS);
  const [result, setResult] = useState<WriteResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canRun = useMemo(
    () => !!refSet && topic.trim().length >= 3 && selected.size > 0 && !running,
    [refSet, topic, selected, running],
  );

  async function run() {
    if (!refSet || !canRun) return;
    setRunning(true);
    setError(null);
    setResult(null);

    const next: Progress = {
      sections: { ...INITIAL_PROGRESS.sections },
      references: "pending",
      review: "pending",
    };
    for (const s of selected) next.sections[s] = "pending";
    setProgress(next);

    try {
      for await (const ev of streamSse(`${API_BASE}/api/paper/write`, {
        topic,
        set_id: refSet.set_id,
        sections: Array.from(selected),
        user_results: userResults || null,
        notes: notes || null,
      })) {
        if (ev.kind === "section_started") {
          const s = ev.data.section as SectionName;
          setProgress((p) => ({
            ...p,
            sections: { ...p.sections, [s]: "active" },
          }));
        } else if (ev.kind === "section_completed") {
          const s = ev.data.section as SectionName;
          setProgress((p) => ({
            ...p,
            sections: { ...p.sections, [s]: "done" },
          }));
        } else if (ev.kind === "references_formatted") {
          setProgress((p) => ({ ...p, references: "done" }));
        } else if (ev.kind === "review_started") {
          setProgress((p) => ({ ...p, review: "active" }));
        } else if (ev.kind === "review_completed") {
          setProgress((p) => ({ ...p, review: "done" }));
        } else if (ev.kind === "completed") {
          setResult(ev.data as unknown as WriteResult);
        } else if (ev.kind === "error") {
          setError((ev.data.message as string) ?? "Unknown error");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="grid md:grid-cols-[360px_1fr] gap-6">
      <aside className="space-y-4">
        <PdfUploader
          refSet={refSet}
          onUploaded={setRefSet}
          disabled={running}
        />
        <div>
          <label className="text-base font-semibold block mb-2">Paper topic</label>
          <textarea
            rows={2}
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            placeholder="e.g. Mitochondrial dynamics in T-cell exhaustion"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={running}
          />
        </div>
        <SectionSelector selected={selected} onChange={setSelected} disabled={running} />
        <details className="text-sm">
          <summary className="cursor-pointer font-medium select-none">
            Optional context
          </summary>
          <div className="mt-2 space-y-2">
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Your results / data (paste raw findings here)
              </label>
              <textarea
                rows={3}
                value={userResults}
                onChange={(e) => setUserResults(e.target.value)}
                className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
                disabled={running}
              />
            </div>
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Notes for writers
              </label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
                disabled={running}
              />
            </div>
          </div>
        </details>
        <button
          onClick={run}
          disabled={!canRun}
          className="w-full rounded bg-[color:var(--gold)] text-black text-base font-semibold py-3 disabled:opacity-50 hover:bg-[color:var(--gold-bright)] transition"
        >
          {running ? "Writing…" : "Generate paper"}
        </button>
        {!refSet && (
          <p className="text-sm text-neutral-400">
            Upload at least one reference PDF to begin.
          </p>
        )}
        {error && <p className="text-sm text-red-400">{error}</p>}

        <ProgressView selected={selected} progress={progress} />
      </aside>

      <main className="min-w-0 space-y-6">
        {!result && !running && (
          <p className="text-base text-neutral-400">
            Upload 1–100 reference PDFs, choose sections, and click <em>Generate paper</em>.
          </p>
        )}
        {result && (
          <>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{result.paper.topic}</h2>
              <ExportButtons markdown={result.paper.markdown} topic={result.paper.topic} />
            </div>
            <article className="border border-neutral-200 dark:border-neutral-800 rounded p-4 max-h-[60vh] overflow-y-auto">
              <Markdown>{result.paper.markdown}</Markdown>
            </article>
            {result.review && (
              <section>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-neutral-500 mb-2">
                  Peer review
                </h3>
                <ReviewPanel review={result.review} />
              </section>
            )}
          </>
        )}
      </main>
    </div>
  );
}

function ProgressView({
  selected,
  progress,
}: {
  selected: Set<SectionName>;
  progress: Progress;
}) {
  return (
    <div className="text-sm font-mono space-y-1">
      {Array.from(selected).map((s) => (
        <Row key={s} state={progress.sections[s]} label={`Write ${SECTION_LABELS[s]}`} />
      ))}
      <Row state={progress.references} label="Format references" />
      <Row state={progress.review} label="Peer review (3 reviewers + synthesis)" />
    </div>
  );
}

function Row({ label, state }: { label: string; state: SectionState }) {
  const icon = state === "done" ? "✓" : state === "active" ? "…" : "·";
  const colour =
    state === "done"
      ? "text-emerald-600 dark:text-emerald-400"
      : state === "active"
        ? "text-amber-600 dark:text-amber-400 animate-pulse"
        : "text-neutral-400";
  return (
    <div className={colour}>
      {icon} {label}
    </div>
  );
}
