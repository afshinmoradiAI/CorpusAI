"use client";

import { useState } from "react";
import type { ReviewReport, Severity } from "@/lib/types";

const SEVERITY_COLOR: Record<Severity, string> = {
  critical: "text-red-600 dark:text-red-400",
  major: "text-amber-600 dark:text-amber-400",
  minor: "text-neutral-500",
};

type Tab = "synthesis" | "biology" | "statistics" | "gap";

export function ReviewPanel({ review }: { review: ReviewReport }) {
  const [tab, setTab] = useState<Tab>("synthesis");
  return (
    <div className="border border-neutral-200 dark:border-neutral-800 rounded">
      <nav className="flex border-b border-neutral-200 dark:border-neutral-800">
        {(
          [
            ["synthesis", "Synthesis"],
            ["biology", `Biology · ${review.biology.overall_score}/5`],
            ["statistics", `Statistics · ${review.statistics.overall_score}/5`],
            ["gap", "Gap"],
          ] as [Tab, string][]
        ).map(([id, label]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={
              "px-3 py-2 text-xs font-medium border-b-2 -mb-px transition " +
              (tab === id
                ? "border-neutral-900 dark:border-white"
                : "border-transparent text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200")
            }
          >
            {label}
          </button>
        ))}
      </nav>
      <div className="p-3 text-sm space-y-3">
        {tab === "synthesis" && (
          <>
            <p>{review.synthesis.executive_summary}</p>
            {review.synthesis.top_revisions.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-1">
                  Top revisions
                </h4>
                <ol className="list-decimal ml-5 space-y-0.5">
                  {review.synthesis.top_revisions.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ol>
              </div>
            )}
          </>
        )}
        {tab === "biology" && <ScoredReview review={review.biology} />}
        {tab === "statistics" && <ScoredReview review={review.statistics} />}
        {tab === "gap" && (
          <>
            <p>{review.gap.summary}</p>
            <Listing label="Unaddressed gaps" items={review.gap.unaddressed_gaps} />
            <Listing label="Future work" items={review.gap.future_work} />
          </>
        )}
      </div>
    </div>
  );
}

function ScoredReview({
  review,
}: {
  review: { summary: string; strengths: string[]; issues: { severity: Severity; section: string; comment: string }[] };
}) {
  return (
    <>
      <p>{review.summary}</p>
      <Listing label="Strengths" items={review.strengths} />
      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-1">
          Issues
        </h4>
        {review.issues.length === 0 ? (
          <p className="text-xs text-neutral-500">None reported.</p>
        ) : (
          <ul className="space-y-1">
            {review.issues.map((i, idx) => (
              <li key={idx} className="text-sm">
                <span className={"font-semibold " + SEVERITY_COLOR[i.severity]}>
                  [{i.severity}]
                </span>{" "}
                <span className="text-neutral-500">{i.section}</span> — {i.comment}
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

function Listing({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-neutral-500 mb-1">
        {label}
      </h4>
      <ul className="list-disc ml-5 space-y-0.5">
        {items.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  );
}
