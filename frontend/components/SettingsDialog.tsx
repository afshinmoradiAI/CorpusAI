"use client";

import { useEffect, useState } from "react";

import { getApiKey, getUserId, setApiKey, setUserId } from "@/lib/auth";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function SettingsDialog({ open, onClose }: Props) {
  const [key, setKey] = useState("");
  const [user, setUser] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (open) {
      setKey(getApiKey());
      setUser(getUserId());
      setSaved(false);
    }
  }, [open]);

  if (!open) return null;

  function save() {
    setApiKey(key.trim());
    setUserId(user.trim());
    setSaved(true);
    setTimeout(onClose, 400);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-semibold">Settings</h2>

        <label className="mb-3 block">
          <span className="mb-1 block text-sm font-medium">API key</span>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="Paste your APP_API_KEY"
            className="w-full rounded border px-3 py-2 text-sm"
            autoComplete="off"
          />
          <span className="mt-1 block text-xs text-gray-500">
            Stored in this browser&apos;s local storage only.
          </span>
        </label>

        <label className="mb-4 block">
          <span className="mb-1 block text-sm font-medium">User ID (optional)</span>
          <input
            type="text"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            placeholder="e.g. your-email@example.com"
            className="w-full rounded border px-3 py-2 text-sm"
            autoComplete="off"
          />
          <span className="mt-1 block text-xs text-gray-500">
            Scopes uploaded papers to you. Leave blank for shared/dev mode.
          </span>
        </label>

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded border px-4 py-2 text-sm hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={save}
            className="rounded bg-black px-4 py-2 text-sm text-white hover:bg-gray-800"
          >
            {saved ? "Saved" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
