"use client";

import { useState } from "react";
import { ARCView } from "./arc/ARCView";
import { ExploreView } from "./explore/ExploreView";
import { NHMRCView } from "./nhmrc/NHMRCView";
import SettingsDialog from "./SettingsDialog";
import { ThesisView } from "./thesis/ThesisView";
import { WriteView } from "./write/WriteView";

type Mode = "explore" | "write" | "nhmrc" | "arc" | "thesis";

const TABS: [Mode, string, string][] = [
  ["explore", "Explore", "Topic → idea + method + discussion"],
  ["write", "Write", "PDFs → full paper + peer review"],
  ["nhmrc", "NHMRC Grant", "Topic → NHMRC grant application"],
  ["arc", "ARC Grant", "Topic → ARC grant application"],
  ["thesis", "Thesis", "Title + chapters → full thesis"],
];

export function ModeTabs() {
  const [mode, setMode] = useState<Mode>("explore");
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="flex flex-col gap-6">
      <nav className="flex items-end gap-1 border-b border-neutral-200 dark:border-neutral-800 overflow-x-auto">
        {TABS.map(([id, label, hint]) => (
          <button
            key={id}
            onClick={() => setMode(id)}
            className={
              "px-4 py-2 text-sm border-b-2 -mb-px transition flex flex-col items-start whitespace-nowrap " +
              (mode === id
                ? "border-neutral-900 dark:border-white"
                : "border-transparent text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200")
            }
          >
            <span className="font-medium">{label}</span>
            <span className="text-xs text-neutral-400">{hint}</span>
          </button>
        ))}
        <button
          onClick={() => setSettingsOpen(true)}
          className="ml-auto mb-2 rounded border px-3 py-1 text-xs text-neutral-600 hover:bg-neutral-50 dark:text-neutral-300 dark:hover:bg-neutral-800"
          aria-label="Open settings"
        >
          Settings
        </button>
      </nav>
      {mode === "explore" && <ExploreView />}
      {mode === "write" && <WriteView />}
      {mode === "nhmrc" && <NHMRCView />}
      {mode === "arc" && <ARCView />}
      {mode === "thesis" && <ThesisView />}
      <SettingsDialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}
