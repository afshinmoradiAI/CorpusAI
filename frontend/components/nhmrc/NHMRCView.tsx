"use client";

import { useMemo, useState } from "react";
import { API_BASE } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import {
  NHMRC_SCHEME_LABELS,
  NHMRC_SECTION_LABELS,
  STUDY_TYPE_LABELS,
  type NHMRCResult,
  type NHMRCScheme,
  type NHMRCSectionName,
  type RefSet,
  type StudyType,
} from "@/lib/types";
import { Markdown } from "@/components/ui/Markdown";
import { ExportButtons } from "@/components/write/ExportButtons";
import { PdfUploader } from "@/components/write/PdfUploader";

const SECTION_ORDER: NHMRCSectionName[] = [
  "burden_of_disease",
  "aims_hypotheses",
  "methods",
  "consumer_involvement",
  "significance_impact",
  "synopsis",
];

type SectionState = "pending" | "active" | "done";

export function NHMRCView() {
  const [refSet, setRefSet] = useState<RefSet | null>(null);
  const [topic, setTopic] = useState("");
  const [scheme, setScheme] = useState<NHMRCScheme>("ideas");
  const [studyType, setStudyType] = useState<StudyType>("laboratory");
  const [healthCondition, setHealthCondition] = useState("");
  const [targetPopulation, setTargetPopulation] = useState("");
  const [notes, setNotes] = useState("");
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<Record<NHMRCSectionName, SectionState>>(
    Object.fromEntries(SECTION_ORDER.map((s) => [s, "pending"])) as Record<
      NHMRCSectionName,
      SectionState
    >,
  );
  const [result, setResult] = useState<NHMRCResult | null>(null);
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
        NHMRCSectionName,
        SectionState
      >,
    );

    try {
      for await (const ev of streamSse(`${API_BASE}/api/nhmrc/write`, {
        topic,
        scheme,
        study_type: studyType,
        health_condition: healthCondition || null,
        target_population: targetPopulation || null,
        set_id: refSet?.set_id ?? null,
        notes: notes || null,
      })) {
        if (ev.kind === "section_started") {
          const s = ev.data.section as NHMRCSectionName;
          setProgress((p) => ({ ...p, [s]: "active" }));
        } else if (ev.kind === "section_completed") {
          const s = ev.data.section as NHMRCSectionName;
          setProgress((p) => ({ ...p, [s]: "done" }));
        } else if (ev.kind === "completed") {
          setResult(ev.data as unknown as NHMRCResult);
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

  const filenameTopic = topic.trim() || "nhmrc-grant";
  const exportTopic = `NHMRC ${filenameTopic}`;

  return (
    <div className="grid md:grid-cols-[360px_1fr] gap-6">
      <aside className="space-y-4">
        <div>
          <label className="text-base font-semibold block mb-2">Grant topic</label>
          <textarea
            rows={2}
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            placeholder="e.g. A targeted T-cell therapy for treatment-resistant rheumatoid arthritis"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            disabled={running}
          />
        </div>

        <div>
          <label className="text-base font-semibold block mb-2">NHMRC scheme</label>
          <select
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            value={scheme}
            onChange={(e) => setScheme(e.target.value as NHMRCScheme)}
            disabled={running}
          >
            {(Object.keys(NHMRC_SCHEME_LABELS) as NHMRCScheme[]).map((s) => (
              <option key={s} value={s}>
                {NHMRC_SCHEME_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-base font-semibold block mb-2">Study type</label>
          <select
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            value={studyType}
            onChange={(e) => setStudyType(e.target.value as StudyType)}
            disabled={running}
          >
            {(Object.keys(STUDY_TYPE_LABELS) as StudyType[]).map((s) => (
              <option key={s} value={s}>
                {STUDY_TYPE_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        <details className="text-sm">
          <summary className="cursor-pointer font-medium select-none">
            Optional context
          </summary>
          <div className="mt-2 space-y-2">
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Health condition
              </label>
              <input
                type="text"
                value={healthCondition}
                onChange={(e) => setHealthCondition(e.target.value)}
                placeholder="e.g. Treatment-resistant depression"
                className="w-full rounded border border-[color:var(--gold-line)] p-2 text-sm bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
                disabled={running}
              />
            </div>
            <div>
              <label className="text-xs block mb-0.5 text-neutral-500">
                Target population
              </label>
              <input
                type="text"
                value={targetPopulation}
                onChange={(e) => setTargetPopulation(e.target.value)}
                placeholder="e.g. Australian adults aged 18–65"
                className="w-full rounded border border-[color:var(--gold-line)] p-2 text-sm bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
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
                placeholder="Named consumers, partner organisations, ATSI involvement, etc."
                className="w-full rounded border border-[color:var(--gold-line)] p-2 text-sm bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
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
          className="w-full rounded bg-[color:var(--gold)] text-black text-base font-semibold py-3 disabled:opacity-50 hover:bg-[color:var(--gold-bright)] transition"
        >
          {running ? "Drafting…" : "Generate NHMRC application"}
        </button>
        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="text-sm font-mono space-y-1">
          {SECTION_ORDER.map((s) => (
            <Row
              key={s}
              state={progress[s]}
              label={`Write ${NHMRC_SECTION_LABELS[s]}`}
            />
          ))}
        </div>
      </aside>

      <main className="min-w-0 space-y-6">
        {!result && !running && (
          <p className="text-base text-neutral-400">
            Enter a topic, choose your scheme, and click{" "}
            <em>Generate NHMRC application</em>.
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
