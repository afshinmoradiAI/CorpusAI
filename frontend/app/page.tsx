import { ModeTabs } from "@/components/ModeTabs";

export default function Home() {
  return (
    <div className="min-h-full flex flex-col">
      <header className="border-b border-neutral-200 dark:border-neutral-800 px-6 py-4">
        <h1 className="text-base font-semibold tracking-tight">CorpusAI</h1>
        <p className="text-xs text-neutral-500">
          Multi-agent biology research assistant
        </p>
      </header>
      <main className="flex-1 px-6 py-6 max-w-7xl w-full mx-auto">
        <ModeTabs />
      </main>
      <footer className="text-xs text-neutral-400 px-6 py-3 border-t border-neutral-200 dark:border-neutral-800">
        Backend: <code>{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</code>
      </footer>
    </div>
  );
}
