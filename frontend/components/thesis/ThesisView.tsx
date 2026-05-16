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
    <div className="grid lg:grid-cols-[420px_1fr] gap-6">
      <aside className="space-y-4">
        <div>
          <label className="text-sm font-medium block mb-1">Thesis title</label>
          <textarea
            rows={2}
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
            placeholder="e.g. The role of mitochondrial dynamics in T-cell exhaustion"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={running}
          />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-sm font-medium block mb-1">Discipline</label>
            <input
              type="text"
              value={discipline}
              onChange={(e) => setDiscipline(e.target.value)}
              placeholder="e.g. Immunology"
              className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
              disabled={running}
            />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1">Structure</label>
            <select
              value={structure}
              onChange={(e) => setStructure(e.target.value as ThesisStructure)}
              className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
              disabled={running}
            >
              {(Object.keys(THESIS_STRUCTURE_LABELS) as ThesisStructure[]).map(
                (s) => (
                  <option key={s} value={s}>
                    {THESIS_STRUCTURE_LABELS[s]}
                  </option>
                ),
              )}
            </select>
          </div>
        </div>

        <div>
          <label className="text-xs block mb-0.5 text-neutral-500">
            University structure notes (optional)
          </label>
          <textarea
            rows={2}
            value={structureNotes}
            onChange={(e) => setStructureNotes(e.target.value)}
            placeholder="e.g. UQ HDR thesis must include a foreword listing co-authored work."
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
            disabled={running}
          />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">
            Chapters ({chapters.length})
          </span>
          <button
            onClick={addChapter}
            disabled={running || chapters.length >= MAX_CHAPTERS}
            className="text-xs rounded border border-neutral-300 dark:border-neutral-700 px-2 py-1 disabled:opacity-50"
          >
            + Add chapter
          </button>
        </div>

        <div className="space-y-3 max-h-[55vh] overflow-y-auto pr-1">
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
              onUpdateCaption={(figIdx, caption) =>
                updateFigureCaption(idx, figIdx, caption)
              }
              onRemoveFigure={(figIdx) => removeFigure(idx, figIdx)}
              onRemove={() => removeChapter(idx)}
            />
          ))}
        </div>

        <button
          onClick={run}
          disabled={!canRun}
          className="w-full rounded bg-neutral-900 text-white text-sm py-2 disabled:opacity-50 dark:bg-white dark:text-neutral-900"
        >
          {running ? "Drafting thesis…" : "Generate thesis"}
        </button>
        {error && <p className="text-xs text-red-600">{error}</p>}

        <div className="text-sm font-mono space-y-1">
          {chapters.map((c, i) => (
            <Row
              key={i}
              state={progress[i + 1] ?? "pending"}
              label={`Chapter ${i + 1}${c.title ? `: ${c.title}` : ""}`}
            />
          ))}
          <Row state={abstractState} label="Synthesise abstract" />
        </div>
      </aside>

      <main className="min-w-0 space-y-6">
        {!result && !running && (
          <p className="text-sm text-neutral-500">
            Set a title, configure chapters, then click{" "}
            <em>Generate thesis</em>. Per-chapter PDFs and figures are
            optional.
          </p>
        )}
        {result && (
          <>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">{result.thesis.title}</h2>
              <ExportButtons
                markdown={result.thesis.markdown}
                topic={exportTopic}
              />
            </div>
            <article className="border border-neutral-200 dark:border-neutral-800 rounded p-4 max-h-[75vh] overflow-y-auto">
              <Markdown>{result.thesis.markdown}</Markdown>
            </article>
          </>
        )}
      </main>
    </div>
  );
}

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
  return (
    <div className="border border-neutral-200 dark:border-neutral-800 rounded p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-neutral-500">
          Chapter {index + 1}
          {progress === "done" && " ✓"}
          {progress === "active" && " …"}
        </span>
        {canRemove && (
          <button
            onClick={onRemove}
            disabled={running}
            className="text-xs text-neutral-500 hover:text-red-600"
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
        className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-sm bg-transparent"
        disabled={running}
      />
      <textarea
        rows={2}
        value={chapter.notes ?? ""}
        onChange={(e) => onChange({ notes: e.target.value || null })}
        placeholder="What this chapter should cover (optional)"
        className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-2 text-xs bg-transparent"
        disabled={running}
      />

      <details className="text-xs">
        <summary className="cursor-pointer select-none text-neutral-600 dark:text-neutral-400">
          Reference PDFs {chapter.set_id && `✓`}
        </summary>
        <div className="mt-1">
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={(e) => onUploadPdfs(Array.from(e.target.files ?? []))}
            disabled={running || chapter.refUploading}
            className="block w-full text-xs"
          />
          {chapter.refUploading && (
            <p className="text-amber-600 mt-0.5">Uploading…</p>
          )}
          {chapter.refError && (
            <p className="text-red-600 mt-0.5">{chapter.refError}</p>
          )}
          {chapter.refFilename && (
            <p className="text-neutral-500 mt-0.5">{chapter.refFilename}</p>
          )}
        </div>
      </details>

      <details className="text-xs">
        <summary className="cursor-pointer select-none text-neutral-600 dark:text-neutral-400">
          Figures ({chapter.figures.length})
        </summary>
        <div className="mt-1 space-y-2">
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUploadFigure(f);
              e.target.value = "";
            }}
            disabled={running || chapter.figureUploading}
            className="block w-full text-xs"
          />
          {chapter.figureUploading && (
            <p className="text-amber-600">Uploading figure…</p>
          )}
          {chapter.figureError && (
            <p className="text-red-600">{chapter.figureError}</p>
          )}
          {chapter.figures.map((f, j) => (
            <div
              key={f.figure_id}
              className="border-l-2 border-neutral-300 dark:border-neutral-700 pl-2 space-y-1"
            >
              <div className="flex justify-between items-center">
                <span className="truncate text-neutral-500">
                  Fig {j + 1}: {f.filename ?? f.figure_id.slice(0, 8)}
                </span>
                <button
                  onClick={() => onRemoveFigure(j)}
                  disabled={running}
                  className="text-neutral-400 hover:text-red-600"
                >
                  ×
                </button>
              </div>
              <input
                type="text"
                value={f.caption ?? ""}
                onChange={(e) => onUpdateCaption(j, e.target.value)}
                placeholder="Caption (optional)"
                className="w-full rounded border border-neutral-300 dark:border-neutral-700 p-1 text-xs bg-transparent"
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
