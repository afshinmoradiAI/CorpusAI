"use client";

import { useMemo, useState } from "react";
import { API_BASE } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import {
  ARC_SCHEME_LABELS,
  ARC_SECTION_LABELS,
  INNOVATION_TYPE_LABELS,
  type ARCResult,
  type ARCScheme,
  type ARCSectionName,
  type InnovationType,
  type RefSet,
} from "@/lib/types";
import { Markdown } from "@/components/ui/Markdown";
import { ExportButtons } from "@/components/write/ExportButtons";
import { PdfUploader } from "@/components/write/PdfUploader";

const SECTION_ORDER: ARCSectionName[] = [
  "significance",
  "innovation",
  "aims",
  "approach_methodology",
  "national_benefit",
  "opening_statement",
];

type SectionState = "pending" | "active" | "done";

export function ARCView() {
  const [refSet, setRefSet] = useState<RefSet | null>(null);
  const [topic, setTopic] = useState("");
  const [scheme, setScheme] = useState<ARCScheme>("discovery");
  const [innovationType, setInnovationType] =
    useState<InnovationType>("methodological");
  const [discipline, setDiscipline] = useState("");
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<Record<ARCSectionName, SectionState>>(
    Object.fromEntries(SECTION_ORDER.map((s) => [s, "pending"])) as Record<
      ARCSectionName,
      SectionState
    >,
  );
  const [result, setResult] = useState<ARCResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canRun = useMemo(
    () => topic.trim().length >= 3 && !running,
    [topic, running],
  );

  async function run() {
    if (!canRun) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setProgress(
      Object.fromEntries(SECTION_ORDER.map((s) => [s, "pending"])) as Record<
        ARCSectionName,
        SectionState
      >,
    );

    try {
      for await (const ev of streamSse(`${API_BASE}/api/arc/write`, {
        topic,
        scheme,
        innovation_type: innovationType,
        discipline: discipline || null,
        set_id: refSet?.set_id ?? null,
        notes: notes || null,
      })) {
        if (ev.kind === "section_started") {
          const s = ev.data.section as ARCSectionName;
          setProgress((p) => ({ ...p, [s]: "active" }));
        } else if (ev.kind === "section_completed") {
          const s = ev.data.section as ARCSectionName;
          setProgress((p) => ({ ...p, [s]: "done" }));
        } else if (ev.kind === "completed") {
          setResult(ev.data as unknown as ARCResult);
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

  const filenameTopic = topic.trim() || "arc-grant";
  const exportTopic = `ARC ${filenameTopic}`;

  return (
    <div className="grid md:grid-cols-[360px_1fr] gap-6">
      <aside className="space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1">Grant topic</label>
          <textarea
            rows={2}
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
            placeholder="e.g. Quantifying high-angle grain boundary effects in additively manufactured Ti-6Al-4V fatigue"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={running}
          />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">ARC scheme</label>
          <select
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
            value={scheme}
            onChange={(e) => setScheme(e.target.value as ARCScheme)}
            disabled={running}
          >
            {(Object.keys(ARC_SCHEME_LABELS) as ARCScheme[]).map((s) => (
              <option key={s} value={s}>
                {ARC_SCHEME_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">Innovation type</label>
          <select
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
            value={innovationType}
            onChange={(e) =>
              setInnovationType(e.target.value as InnovationType)
            }
            disabled={running}
          >
            {(Object.keys(INNOVATION_TYPE_LABELS) as InnovationType[]).map(
              (s) => (
                <option key={s} value={s}>
                  {INNOVATION_TYPE_LABELS[s]}
                </option>
              ),
            )}
          </select>
        </div>

        <details className="text-sm">
          <summary className="cursor-pointer font-medium select-none">
            Optional context
          </summary>
          <div className="mt-2 space-y-2">
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Discipline
              </label>
              <input
                type="text"
                value={discipline}
                onChange={(e) => setDiscipline(e.target.value)}
                placeholder="e.g. Materials engineering, linguistics, oceanography"
                className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
                disabled={running}
              />
            </div>
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Notes for writers
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Industry partners, career disruptions, specific risks, prior work to cite"
                className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
                disabled={running}
              />
            </div>
          </div>
        </details>

        <details className="text-sm">
          <summary className="cursor-pointer font-medium select-none">
            Reference PDFs (optional)
          </summary>
          <div className="mt-2">
            <PdfUploader
              refSet={refSet}
              onUploaded={setRefSet}
              disabled={running}
            />
          </div>
        </details>

        <button
          onClick={run}
          disabled={!canRun}
          className="w-full rounded bg-neutral-900 text-white text-sm py-2 disabled:opacity-50 dark:bg-white dark:text-neutral-900"
        >
          {running ? "Drafting…" : "Generate ARC application"}
        </button>
        {error && <p className="text-xs text-red-600">{error}</p>}

        <div className="text-sm font-mono space-y-1">
          {SECTION_ORDER.map((s) => (
            <Row
              key={s}
              state={progress[s]}
              label={`Write ${ARC_SECTION_LABELS[s]}`}
            />
          ))}
        </div>
      </aside>

      <main className="min-w-0 space-y-6">
        {!result && !running && (
          <p className="text-sm text-neutral-500">
            Enter a topic, choose a scheme and innovation type, then click{" "}
            <em>Generate ARC application</em>.
          </p>
        )}
        {result && (
          <>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{result.grant.topic}</h2>
              <ExportButtons
                markdown={result.grant.markdown}
                topic={exportTopic}
              />
            </div>
            <article className="border border-neutral-200 dark:border-neutral-800 rounded p-4 max-h-[70vh] overflow-y-auto">
              <Markdown>{result.grant.markdown}</Markdown>
            </article>
          </>
        )}
      </main>
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
