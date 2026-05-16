"use client";

import Link from "next/link";
import { useState } from "react";
import SettingsDialog from "./SettingsDialog";

const LINKS = [
  { href: "/explore", label: "Proposal" },
  { href: "/write", label: "Paper" },
  { href: "/nhmrc", label: "NHMRC" },
  { href: "/arc", label: "ARC" },
  { href: "/thesis", label: "Thesis" },
];

export function LandingHeader() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 backdrop-blur-md bg-black/60 border-b border-[color:var(--gold-line)]">
      <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
        <Link
          href="/"
          className="font-display text-3xl tracking-tight text-gold-gradient font-semibold"
        >
          CorpusAI
        </Link>
        <div className="flex items-center gap-2 md:gap-5">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="hidden md:inline text-base font-medium text-neutral-200 hover:text-[color:var(--gold-bright)] transition px-2 py-1"
            >
              {l.label}
            </Link>
          ))}
          <button
            onClick={() => setSettingsOpen(true)}
            className="rounded-md border border-[color:var(--gold-line)] px-4 py-2 text-sm font-medium text-[color:var(--gold)] hover:bg-[color:var(--gold-faint)] transition"
          >
            Settings
          </button>
        </div>
      </div>
      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </header>
  );
}
