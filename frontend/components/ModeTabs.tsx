"use client";

import { useState } from "react";
import { ExploreView } from "./explore/ExploreView";
import { WriteView } from "./write/WriteView";

type Mode = "explore" | "write";

export function ModeTabs() {
  const [mode, setMode] = useState<Mode>("explore");
  return (
    <div className="flex flex-col gap-6">
      <nav className="flex gap-1 border-b border-neutral-200 dark:border-neutral-800">
        {(
          [
            ["explore", "Explore", "Topic → idea + method + discussion"],
            ["write", "Write", "PDFs → full paper + peer review"],
          ] as [Mode, string, string][]
        ).map(([id, label, hint]) => (
          <button
            key={id}
            onClick={() => setMode(id)}
            className={
              "px-4 py-2 text-sm border-b-2 -mb-px transition flex flex-col items-start " +
              (mode === id
                ? "border-neutral-900 dark:border-white"
                : "border-transparent text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200")
            }
          >
            <span className="font-medium">{label}</span>
            <span className="text-xs text-neutral-400">{hint}</span>
          </button>
        ))}
      </nav>
      {mode === "explore" ? <ExploreView /> : <WriteView />}
    </div>
  );
}
