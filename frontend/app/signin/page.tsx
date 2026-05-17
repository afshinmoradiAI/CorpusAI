"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { setApiKey, setUserId } from "@/lib/auth";

export default function SignInPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [apiKey, setApiKeyInput] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Please enter your name.");
      return;
    }
    setUserId(trimmedName);
    setApiKey(apiKey.trim());
    router.replace("/");
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4 hero-photo">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <h1 className="font-display text-5xl font-semibold text-gold-gradient mb-2">
            CorpusAI
          </h1>
          <p className="text-neutral-400 text-base">
            Multi-agent academic writing assistant
          </p>
        </div>

        {/* Card */}
        <div className="surface rounded-xl p-8 shadow-2xl border border-[color:var(--gold-line)]">
          <h2 className="font-display text-2xl font-semibold text-[color:var(--gold-bright)] mb-6">
            Sign in
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-sm font-medium block mb-1.5 text-neutral-200">
                Your name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => { setName(e.target.value); setError(""); }}
                placeholder="e.g. Dr Jane Smith"
                autoFocus
                className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition text-neutral-100 placeholder:text-neutral-600"
              />
            </div>

            <div>
              <label className="text-sm font-medium block mb-1.5 text-neutral-200">
                API key{" "}
                <span className="text-neutral-500 font-normal">(optional)</span>
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKeyInput(e.target.value)}
                placeholder="Leave blank for open-access mode"
                className="w-full rounded border border-[color:var(--gold-line)] p-3 text-base bg-transparent focus:outline-none focus:border-[color:var(--gold)] transition text-neutral-100 placeholder:text-neutral-600"
              />
              <p className="text-xs text-neutral-500 mt-1">
                Required only if the backend is protected by an API key.
              </p>
            </div>

            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}

            <button
              type="submit"
              className="w-full rounded bg-[color:var(--gold)] text-black text-base font-semibold py-3 hover:bg-[color:var(--gold-bright)] transition shadow-lg"
            >
              Enter CorpusAI →
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-neutral-600 mt-6">
          Your name and key are stored locally in your browser only.
        </p>
      </div>
    </main>
  );
}
