"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import SettingsDialog from "./SettingsDialog";

const MODES: { href: string; label: string }[] = [
  { href: "/explore", label: "Proposal" },
  { href: "/write", label: "Paper" },
  { href: "/nhmrc", label: "NHMRC" },
  { href: "/arc", label: "ARC" },
  { href: "/thesis", label: "Thesis" },
];

export function TopNav() {
  const pathname = usePathname();
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 backdrop-blur-md bg-black/60 border-b border-[color:var(--gold-line)]">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-display text-2xl tracking-tight"
        >
          <span className="text-gold-gradient font-semibold">CorpusAI</span>
        </Link>

        <nav className="hidden md:flex items-center gap-1 ml-4">
          {MODES.map((m) => {
            const active = pathname === m.href;
            return (
              <Link
                key={m.href}
                href={m.href}
                className={
                  "px-4 py-2 rounded text-base font-medium transition " +
                  (active
                    ? "text-[color:var(--gold-bright)] bg-[color:var(--gold-faint)]"
                    : "text-neutral-300 hover:text-[color:var(--gold-bright)]")
                }
              >
                {m.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/"
            className="text-sm text-neutral-400 hover:text-[color:var(--gold-bright)]"
          >
            ← Home
          </Link>
          <button
            onClick={() => setSettingsOpen(true)}
            className="rounded border border-[color:var(--gold-line)] px-4 py-1.5 text-sm text-[color:var(--gold)] hover:bg-[color:var(--gold-faint)] transition"
          >
            Settings
          </button>
        </div>
      </div>
      <SettingsDialog open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </header>
  );
}
