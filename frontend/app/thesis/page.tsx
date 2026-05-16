import { ModeHero } from "@/components/ModeHero";
import { ThesisView } from "@/components/thesis/ThesisView";
import { TopNav } from "@/components/TopNav";

export default function ThesisPage() {
  return (
    <main className="flex-1 flex flex-col">
      <TopNav />
      <ModeHero
        eyebrow="Pipeline 5"
        title="Thesis"
        subtitle="Title + chapters → full thesis"
        description="Define 1–15 chapters with optional notes, reference PDFs, and figures per chapter. Chapters draft sequentially, then the abstract synthesises last. Figures embed inline in both the preview and the .docx."
      />
      <section className="flex-1 max-w-7xl w-full mx-auto px-6 pb-12">
        <div className="surface rounded-lg p-6">
          <ThesisView />
        </div>
      </section>
    </main>
  );
}
