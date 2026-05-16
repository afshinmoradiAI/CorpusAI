import { ARCView } from "@/components/arc/ARCView";
import { ModeHero } from "@/components/ModeHero";
import { TopNav } from "@/components/TopNav";

export default function ARCPage() {
  return (
    <main className="flex-1 flex flex-col">
      <TopNav />
      <ModeHero
        eyebrow="Pipeline 4"
        title="ARC Grant"
        subtitle="Topic → ARC application"
        description="Significance, Innovation, Aims, Approach & Methodology, National Benefit, and Project Description. Discovery, Linkage, Laureate, DECRA, Future, Centre — all supported."
      />
      <section className="flex-1 max-w-7xl w-full mx-auto px-6 pb-12">
        <div className="surface rounded-lg p-6">
          <ARCView />
        </div>
      </section>
    </main>
  );
}
