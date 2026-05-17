"use client";

import { useMemo, useState } from "react";
import { API_BASE, uploadFigure, uploadReferences } from "@/lib/api";
import { streamSse } from "@/lib/sse";
import {
  THESIS_STRUCTURE_LABELS,
  type ChapterConfig,
  type FigureRef,
  type RefSet,
  type ThesisResult,
  type ThesisStructure,
} from "@/lib/types";
import { Markdown } from "@/components/ui/Markdown";
import { ExportButtons } from "@/components/write/ExportButtons";

const MIN_CHAPTERS = 1;
const MAX_CHAPTERS = 15;
const DEFAULT_CHAPTER_COUNT = 6;

type ChapterUI = ChapterConfig & {
  refUploading?: boolean;
  refError?: string;
  refFilename?: string;
  figureUploading?: boolean;
  figureError?: string;
};

function emptyChapter(): ChapterUI {
  return { title: null, notes: null, set_id: null, figures: [] };
}

export function ThesisView() {
  const [title, setTitle] = useState("");
  const [discipline, setDiscipline] = useState("");
  const [structure, setStructure] = useState<ThesisStructure>("traditional");
  const [structureNotes, setStructureNotes] = useState("");
  const [chapters, setChapters] = useState<ChapterUI[]>(() =>
    Array.from({ length: DEFAULT_CHAPTER_COUNT }, emptyChapter),
  );
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<Record<number, "pending" | "active" | "done">>(
    {},
  );
  const [abstractState, setAbstractState] = useState<"pending" | "active" | "done">("pending");
  const [result, setResult] = useState<ThesisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canRun = useMemo(
    () => title.trim().length >= 3 && chapters.length >= 1 && !running,
    [title, chapters.length, running],
  );

  function updateChapter(idx: number, patch: Partial<ChapterUI>) {
    setChapters((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, ...patch } : c)),
    );
  }

  function addChapter() {
    setChapters((prev) =>
      prev.length >= MAX_CHAPTERS ? prev : [...prev, emptyChapter()],
    );
  }

  function removeChapter(idx: number) {
    setChapters((prev) =>
      prev.length <= MIN_CHAPTERS ? prev : prev.filter((_, i) => i !== idx),
    );
  }

  async function onUploadChapterPdfs(idx: number, files: File[]) {
    if (files.length === 0) return;
    updateChapter(idx, { refUploading: true, refError: undefined });
    try {
      const set: RefSet = await uploadReferences(files);
      updateChapter(idx, {
        set_id: set.set_id,
        refFilename: set.documents.map((d) => d.filename).join(", "),
        refUploading: false,
      });
    } catch (err) {
      updateChapter(idx, {
        refUploading: false,
        refError: err instanceof Error ? err.message : String(err),
      });
    }
  }

  async function onUploadChapterFigure(idx: number, file: File) {
    updateChapter(idx, { figureUploading: true, figureError: undefined });
    try {
      const fig = await uploadFigure(file);
      setChapters((prev) =>
        prev.map((c, i) =>
          i === idx
            ? {
                ...c,
                figureUploading: false,
                figures: [
                  ...c.figures,
                  {
                    figure_id: fig.figure_id,
                    caption: null,
                    filename: fig.filename,
                  },
                ],
              }
            : c,
        ),
      );
    } catch (err) {
      updateChapter(idx, {
        figureUploading: false,
        figureError: err instanceof Error ? err.message : String(err),
      });
    }
  }

  function updateFigureCaption(chapIdx: number, figIdx: number, caption: string) {
    setChapters((prev) =>
      prev.map((c, i) => {
        if (i !== chapIdx) return c;
        const newFigs = c.figures.map((f, j) =>
          j === figIdx ? { ...f, caption: caption || null } : f,
        );
        return { ...c, figures: newFigs };
      }),
    );
  }

  function removeFigure(chapIdx: number, figIdx: number) {
    setChapters((prev) =>
      prev.map((c, i) =>
        i === chapIdx
          ? { ...c, figures: c.figures.filter((_, j) => j !== figIdx) }
          : c,
      ),
    );
  }

  async function run() {
    if (!canRun) return;
    setRunning(true);
    setError(null);
    setResult(null);
    setProgress(Object.fromEntries(chapters.map((_, i) => [i + 1, "pending"])));
    setAbstractState("pending");

    const payload = {
      title,
      discipline: discipline || null,
      structure,
      structure_notes: structureNotes || null,
      chapters: chapters.map((c) => ({
        title: c.title || null,
        notes: c.notes || null,
        set_id: c.set_id || null,
        figures: c.figures.map((f: FigureRef) => ({
          figure_id: f.figure_id,
          caption: f.caption,
        })),
      })),
    };

    try {
      for await (const ev of streamSse(`${API_BASE}/api/thesis/write`, payload)) {
        if (ev.kind === "chapter_started") {
          const idx = ev.data.index as number;
          setProgress((p) => ({ ...p, [idx]: "active" }));
        } else if (ev.kind === "chapter_completed") {
          const idx = ev.data.index as number;
          setProgress((p) => ({ ...p, [idx]: "done" }));
        } else if (ev.kind === "abstract_started") {
          setAbstractState("active");
        } else if (ev.kind === "abstract_completed") {
          setAbstractState("done");
        } else if (ev.kind === "completed") {
          setResult(ev.data as unknown as ThesisResult);
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

  const exportTopic = `Thesis ${title.trim() || "untitled"}`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-2">
          <label className="text-base font-semibold block mb-2">Thesis title</label>
          <textarea
            rows={3}
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            placeholder="e.g. The role of mitochondrial dynamics in T-cell exhaustion"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={running}
          />
        </div>

        <div>
          <label className="text-base font-semibold block mb-2">Discipline</label>
          <input
            type="text"
            value={discipline}
            onChange={(e) => setDiscipline(e.target.value)}
            placeholder="e.g. Immunology"
            className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
            disabled={running}
          />
        </div>

        <div className="space-y-3">
          <div>
            <label className="text-base font-semibold block mb-2">Structure</label>
            <select
              value={structure}
              onChange={(e) => setStructure(e.target.value as ThesisStructure)}
              className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
              disabled={running}
            >
              {(Object.keys(THESIS_STRUCTURE_LABELS) as ThesisStructure[]).map((s) => (
                <option key={s} value={s}>{THESIS_STRUCTURE_LABELS[s]}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs block mb-0.5 text-neutral-500">University structure notes (optional)</label>
            <textarea
              rows={2}
              value={structureNotes}
              onChange={(e) => setStructureNotes(e.target.value)}
              placeholder="e.g. UQ HDR thesis must include a foreword listing co-authored work."
              className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
              disabled={running}
            />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-base font-semibold text-[color:var(--gold-bright)]">
          Chapters ({chapters.length})
        </span>
        <button
          onClick={addChapter}
          disabled={running || chapters.length >= MAX_CHAPTERS}
          className="text-sm font-medium rounded border border-[color:var(--gold-line)] text-[color:var(--gold)] px-3 py-1.5 hover:bg-[color:var(--gold-faint)] transition disabled:opacity-50"
        >
          + Add chapter
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {chapters.map((ch, idx) => (
          <ChapterCard
            key={idx}
            index={idx}
            chapter={ch}
            running={running}
            progress={progress[idx + 1]}
            canRemove={chapters.length > MIN_CHAPTERS}
            onChange={(patch) => updateChapter(idx, patch)}
            onUploadPdfs={(files) => onUploadChapterPdfs(idx, files)}
            onUploadFigure={(file) => onUploadChapterFigure(idx, file)}
            onUpdateCaption={(figIdx, caption) => updateFigureCaption(idx, figIdx, caption)}
            onRemoveFigure={(figIdx) => removeFigure(idx, figIdx)}
            onRemove={() => removeChapter(idx)}
          />
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <button
          onClick={run}
          disabled={!canRun}
          className="rounded bg-[color:var(--gold)] text-black text-base font-semibold px-8 py-3 disabled:opacity-50 hover:bg-[color:var(--gold-bright)] transition"
        >
          {running ? "Drafting thesis…" : "Generate thesis"}
        </button>
        <div className="text-sm font-mono flex flex-wrap gap-x-4 gap-y-1">
          {chapters.map((c, i) => (
            <Row
              key={i}
              state={progress[i + 1] ?? "pending"}
              label={`Ch ${i + 1}${c.title ? `: ${c.title}` : ""}`}
            />
          ))}
          <Row state={abstractState} label="Abstract" />
        </div>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="min-w-0 space-y-6">
        {!result && !running && (
          <p className="text-sm text-neutral-500">
            Set a title, configure chapters, then click <em>Generate thesis</em>. Per-chapter PDFs and figures are optional.
          </p>
        )}
        {result && (
          <>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{result.thesis.title}</h2>
              <ExportButtons markdown={result.thesis.markdown} topic={exportTopic} />
            </div>
            <article className="border border-neutral-200 dark:border-neutral-800 rounded p-4">
              <Markdown>{result.thesis.markdown}</Markdown>
            </article>
          </>
        )}
      </div>
    </div>
  );
}

// Per-chapter visual themes — rotated by index so each chapter has a
// distinct accent colour, badge, and border style. Makes a long list
// of chapters easier to scan.
const CHAPTER_THEMES = [
  {
    name: "gold",
    badge: "bg-[color:var(--gold)] text-black",
    border: "border-[color:var(--gold)]",
    accent: "text-[color:var(--gold-bright)]",
    bg: "bg-gradient-to-br from-[rgba(212,175,55,0.10)] to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(212,175,55,0.35)]",
  },
  {
    name: "emerald",
    badge: "bg-emerald-400 text-black",
    border: "border-emerald-500/60",
    accent: "text-emerald-300",
    bg: "bg-gradient-to-br from-emerald-500/10 to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(16,185,129,0.35)]",
  },
  {
    name: "sky",
    badge: "bg-sky-400 text-black",
    border: "border-sky-500/60",
    accent: "text-sky-300",
    bg: "bg-gradient-to-br from-sky-500/10 to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(56,189,248,0.35)]",
  },
  {
    name: "rose",
    badge: "bg-rose-400 text-black",
    border: "border-rose-500/60",
    accent: "text-rose-300",
    bg: "bg-gradient-to-br from-rose-500/10 to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(244,63,94,0.35)]",
  },
  {
    name: "violet",
    badge: "bg-violet-400 text-black",
    border: "border-violet-500/60",
    accent: "text-violet-300",
    bg: "bg-gradient-to-br from-violet-500/10 to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(167,139,250,0.35)]",
  },
  {
    name: "amber",
    badge: "bg-amber-400 text-black",
    border: "border-amber-500/60",
    accent: "text-amber-300",
    bg: "bg-gradient-to-br from-amber-500/10 to-transparent",
    ring: "shadow-[0_0_0_1px_rgba(245,158,11,0.35)]",
  },
];

function ChapterCard({
  index,
  chapter,
  running,
  progress,
  canRemove,
  onChange,
  onUploadPdfs,
  onUploadFigure,
  onUpdateCaption,
  onRemoveFigure,
  onRemove,
}: {
  index: number;
  chapter: ChapterUI;
  running: boolean;
  progress?: "pending" | "active" | "done";
  canRemove: boolean;
  onChange: (patch: Partial<ChapterUI>) => void;
  onUploadPdfs: (files: File[]) => void;
  onUploadFigure: (file: File) => void;
  onUpdateCaption: (figIdx: number, caption: string) => void;
  onRemoveFigure: (figIdx: number) => void;
  onRemove: () => void;
}) {
  const theme = CHAPTER_THEMES[index % CHAPTER_THEMES.length];
  return (
    <div
      className={`relative rounded-lg p-4 space-y-3 border ${theme.border} ${theme.bg} bg-black/40 overflow-hidden`}
    >
      {/* Coloured left rail */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 ${theme.badge.split(" ")[0]}`}
      />
      <div className="flex items-center justify-between gap-2 pl-2">
        <div className="flex items-center gap-2.5">
          <span
            className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${theme.badge}`}
          >
            {index + 1}
          </span>
          <span className={`text-base font-semibold ${theme.accent}`}>
            Chapter {index + 1}
            {progress === "done" && " ✓"}
            {progress === "active" && " …"}
          </span>
        </div>
        {canRemove && (
          <button
            onClick={onRemove}
            disabled={running}
            className="text-sm text-neutral-400 hover:text-red-400 transition"
          >
            Remove
          </button>
        )}
      </div>
      <input
        type="text"
        value={chapter.title ?? ""}
        onChange={(e) => onChange({ title: e.target.value || null })}
        placeholder={`Title (leave blank for auto)`}
        className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
        disabled={running}
      />
      <textarea
        rows={2}
        value={chapter.notes ?? ""}
        onChange={(e) => onChange({ notes: e.target.value || null })}
        placeholder="What this chapter should cover (optional)"
        className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
        disabled={running}
      />

      <details className="text-sm">
        <summary className="cursor-pointer select-none text-base font-medium text-neutral-200 hover:text-[color:var(--gold-bright)] transition">
          Reference PDFs {chapter.set_id && `✓`}
        </summary>
        <div className="mt-2">
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={(e) => onUploadPdfs(Array.from(e.target.files ?? []))}
            disabled={running || chapter.refUploading}
            className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-[color:var(--gold-faint)] file:px-3 file:py-1.5 file:text-sm file:text-[color:var(--gold-bright)]"
          />
          {chapter.refUploading && (
            <p className="text-sm text-amber-400 mt-1">Uploading…</p>
          )}
          {chapter.refError && (
            <p className="text-sm text-red-400 mt-1">{chapter.refError}</p>
          )}
          {chapter.refFilename && (
            <p className="text-sm text-neutral-400 mt-1">{chapter.refFilename}</p>
          )}
        </div>
      </details>

      <details className="text-sm">
        <summary className="cursor-pointer select-none text-base font-medium text-neutral-200 hover:text-[color:var(--gold-bright)] transition">
          Figures ({chapter.figures.length})
        </summary>
        <div className="mt-2 space-y-2">
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUploadFigure(f);
              e.target.value = "";
            }}
            disabled={running || chapter.figureUploading}
            className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-[color:var(--gold-faint)] file:px-3 file:py-1.5 file:text-sm file:text-[color:var(--gold-bright)]"
          />
          {chapter.figureUploading && (
            <p className="text-sm text-amber-400">Uploading figure…</p>
          )}
          {chapter.figureError && (
            <p className="text-sm text-red-400">{chapter.figureError}</p>
          )}
          {chapter.figures.map((f, j) => (
            <div
              key={f.figure_id}
              className="border-l-2 border-[color:var(--gold-line)] pl-3 space-y-1.5 py-1"
            >
              <div className="flex justify-between items-center">
                <span className="truncate text-sm text-neutral-300">
                  Fig {j + 1}: {f.filename ?? f.figure_id.slice(0, 8)}
                </span>
                <button
                  onClick={() => onRemoveFigure(j)}
                  disabled={running}
                  className="text-sm text-neutral-400 hover:text-red-400 transition px-1"
                >
                  ×
                </button>
              </div>
              <input
                type="text"
                value={f.caption ?? ""}
                onChange={(e) => onUpdateCaption(j, e.target.value)}
                placeholder="Caption (optional)"
                className="w-full rounded border border-[color:var(--gold-line)] p-2 text-sm bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition"
                disabled={running}
              />
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}

function Row({
  label,
  state,
}: {
  label: string;
  state: "pending" | "active" | "done";
}) {
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
