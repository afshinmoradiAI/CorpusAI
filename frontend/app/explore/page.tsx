import { ExploreView } from "@/components/explore/ExploreView";
import { ModeHero } from "@/components/ModeHero";
import { TopNav } from "@/components/TopNav";

export default function ExplorePage() {
  return (
    <main className="flex-1 flex flex-col">
      <TopNav />
      <ModeHero
        eyebrow="Pipeline 1"
        title="Proposal"
        subtitle="Topic → research proposal"
        description="Surveys the literature, identifies the gap, proposes a novel idea, designs a method, and writes a discussion paragraph. Optionally ground it in your own reference PDFs."
      />
      <section className="flex-1 max-w-7xl w-full mx-auto px-6 pb-12">
        <div className="surface rounded-lg p-6">
          <ExploreView />
        </div>
      </section>
    </main>
  );
}
