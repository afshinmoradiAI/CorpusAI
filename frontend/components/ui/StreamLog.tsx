"use client";

interface Step {
  label: string;
  state: "pending" | "active" | "done" | "error";
}

export function StreamLog({ steps }: { steps: Step[] }) {
  return (
    <ol className="text-sm space-y-1 font-mono">
      {steps.map((s, i) => (
        <li
          key={i}
          className={
            s.state === "done"
              ? "text-emerald-600 dark:text-emerald-400"
              : s.state === "active"
                ? "text-amber-600 dark:text-amber-400 animate-pulse"
                : s.state === "error"
                  ? "text-red-600 dark:text-red-400"
                  : "text-neutral-400"
          }
        >
          {s.state === "done"
            ? "✓"
            : s.state === "active"
              ? "…"
              : s.state === "error"
                ? "✗"
                : "·"}{" "}
          {s.label}
        </li>
      ))}
    </ol>
  );
}
