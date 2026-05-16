import { ModeHero } from "@/components/ModeHero";
import { NHMRCView } from "@/components/nhmrc/NHMRCView";
import { TopNav } from "@/components/TopNav";

export default function NHMRCPage() {
  return (
    <main className="flex-1 flex flex-col">
      <TopNav />
      <ModeHero
        eyebrow="Pipeline 3"
        title="NHMRC Grant"
        subtitle="Topic → NHMRC application"
        description="Burden of Disease, Aims & Hypotheses, Research Plan, Consumer & Community Involvement, Impact, and Plain-Language Synopsis. All NHMRC schemes supported."
      />
      <section className="flex-1 max-w-7xl w-full mx-auto px-6 pb-12">
        <div className="surface rounded-lg p-6">
          <NHMRCView />
        </div>
      </section>
    </main>
  );
}
