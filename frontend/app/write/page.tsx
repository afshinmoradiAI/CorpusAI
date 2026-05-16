import { ModeHero } from "@/components/ModeHero";
import { TopNav } from "@/components/TopNav";
import { WriteView } from "@/components/write/WriteView";

export default function WritePage() {
  return (
    <main className="flex-1 flex flex-col">
      <TopNav />
      <ModeHero
        eyebrow="Pipeline 2"
        title="Paper"
        subtitle="Reference PDFs → full paper"
        description="Upload 1–100 reference PDFs. Drafts Abstract, Introduction, Methods, Results, and Discussion grounded in your references. Formats citations and runs a three-way peer review."
      />
      <section className="flex-1 max-w-7xl w-full mx-auto px-6 pb-12">
        <div className="surface rounded-lg p-6">
          <WriteView />
        </div>
      </section>
    </main>
  );
}
