import Link from "next/link";
import { LandingHeader } from "@/components/LandingHeader";

interface Mode {
  href: string;
  title: string;
  tagline: string;
  description: string;
  icon: string;
  highlight: string;
}

const MODES: Mode[] = [
  {
    href: "/explore",
    title: "Proposal",
    tagline: "Topic → research proposal",
    description:
      "Give it a topic and optional reference PDFs. It surveys the literature, identifies the gap, proposes a novel idea, designs a method, and writes a discussion.",
    icon: "🔬",
    highlight: "Proposal",
  },
  {
    href: "/write",
    title: "Paper",
    tagline: "References → full paper",
    description:
      "Upload up to 100 reference PDFs. It drafts Abstract, Introduction, Methods, Results, Discussion, formats citations, and runs a 3-way peer review.",
    icon: "📄",
    highlight: "Scientific paper",
  },
  {
    href: "/nhmrc",
    title: "NHMRC",
    tagline: "Topic → NHMRC application",
    description:
      "Generates Burden of Disease, Aims, Methods, Consumer Involvement, Impact, and Plain-Language Synopsis. Supports every NHMRC scheme.",
    icon: "⚕️",
    highlight: "Grant",
  },
  {
    href: "/arc",
    title: "ARC",
    tagline: "Topic → ARC application",
    description:
      "Generates Significance, Innovation, Aims, Approach & Methodology, National Benefit, and Project Description. All ARC schemes supported.",
    icon: "🎓",
    highlight: "Grant",
  },
  {
    href: "/thesis",
    title: "Thesis",
    tagline: "Title + chapters → full thesis",
    description:
      "Define 1–15 chapters with optional per-chapter notes, reference PDFs, and figures. Each chapter is drafted in turn, then the abstract is synthesised.",
    icon: "📚",
    highlight: "Long-form",
  },
];

export default function Home() {
  return (
    <main className="flex-1 flex flex-col">
      <LandingHeader />

      {/* HERO with university photo backdrop */}
      <section className="hero-photo relative pt-28 pb-32 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <p className="eyebrow mb-8">
            Multi-agent academic writing
          </p>
          <h1 className="font-display text-5xl md:text-7xl font-semibold leading-[0.92] mb-6">
            <span className="text-gold-gradient">CorpusAI</span>
          </h1>
          <p className="font-display text-2xl md:text-3xl text-neutral-50 mb-8 leading-tight max-w-5xl mx-auto">
            From a single idea to a publishable manuscript —
            <span className="text-[color:var(--gold-bright)]">
              {" "}drafted by a team of specialised AI agents.
            </span>
          </p>
          <p className="text-base md:text-lg text-neutral-200 max-w-3xl mx-auto mb-12 leading-relaxed">
            Five purpose-built pipelines for biomedical and academic research:
            proposals, scientific papers, NHMRC grants, ARC grants, and full
            theses.
          </p>

          <div className="flex flex-wrap justify-center gap-5 mb-14">
            <Link
              href="/explore"
              className="px-9 py-4 rounded-md bg-[color:var(--gold)] text-black text-lg font-semibold hover:bg-[color:var(--gold-bright)] transition shadow-xl shadow-[color:var(--gold-faint)]"
            >
              Start with a topic →
            </Link>
          </div>

          <div className="flex flex-wrap justify-center gap-x-10 gap-y-3 text-sm md:text-base text-neutral-300">
            <span className="flex items-center gap-2">
              <span className="text-[color:var(--gold)]">✦</span> 26 specialised agents
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[color:var(--gold)]">✦</span> Claude Sonnet 4.6
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[color:var(--gold)]">✦</span> Times New Roman .docx
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[color:var(--gold)]">✦</span> Live streaming output
            </span>
          </div>
        </div>
      </section>

      {/* MODE GRID */}
      <section className="px-6 pb-28">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <p className="eyebrow mb-4">
              Pipelines
            </p>
            <h2 className="font-display text-4xl md:text-5xl font-semibold mb-4">
              Choose your <span className="text-gold-gradient">workflow</span>
            </h2>
            <p className="text-base md:text-lg text-neutral-300 max-w-3xl mx-auto">
              Each pipeline is a coordinated team of agents. Pick the artefact
              you want to produce — we handle the rest.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-7">
            {MODES.map((mode) => (
              <Link
                key={mode.href}
                href={mode.href}
                className="mode-card surface rounded-xl p-8 flex flex-col gap-4 min-h-[280px]"
              >
                <div className="flex items-start justify-between">
                  <span className="text-5xl">{mode.icon}</span>
                  <span className="text-xs uppercase tracking-widest text-[color:var(--gold)] px-3 py-1 rounded-full border border-[color:var(--gold-line)] bg-black/30">
                    {mode.highlight}
                  </span>
                </div>
                <h3 className="font-display text-3xl font-semibold text-[color:var(--gold-bright)]">
                  {mode.title}
                </h3>
                <p className="text-base text-neutral-400 italic -mt-2">
                  {mode.tagline}
                </p>
                <p className="text-base text-neutral-200 leading-relaxed">
                  {mode.description}
                </p>
                <div className="mt-auto pt-3 flex items-center gap-2 text-base font-medium text-[color:var(--gold)]">
                  Open <span className="ml-0.5 text-lg">→</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* SCIENCE ACCENT — image background section */}
      <section className="academic-photo px-6 py-24 border-y border-[color:var(--gold-line)]">
        <div className="max-w-6xl mx-auto text-center">
          <p className="eyebrow mb-4">
            Built for the lab
          </p>
          <h2 className="font-display text-3xl md:text-4xl font-semibold mb-6">
            <span className="text-gold-gradient">Designed by researchers, for researchers.</span>
          </h2>
          <p className="text-base md:text-lg text-neutral-200 max-w-3xl mx-auto leading-relaxed">
            CorpusAI mirrors how a research group actually works: a topic
            analyst, a literature reviewer, a gap finder, an idea generator,
            a methods designer, section writers, and three independent peer
            reviewers — all coordinating to ship a finished manuscript.
          </p>
        </div>
      </section>

      {/* CAPABILITIES — what the agents do */}
      <section className="px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <p className="eyebrow mb-3">What the agents do</p>
            <h2 className="font-display text-3xl md:text-4xl font-semibold mb-4">
              Specialists for the hard parts of <span className="text-gold-gradient">research writing</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            <CapabilityCard
              icon="💡"
              colour="gold"
              title="Idea generation"
              body="Proposes a novel, testable research idea grounded in the surveyed literature — not a paraphrase of existing work."
            />
            <CapabilityCard
              icon="🔍"
              colour="emerald"
              title="Gap finding"
              body="Reads across papers to pinpoint exactly what hasn't been done — with explicit evidence from the corpus."
            />
            <CapabilityCard
              icon="📊"
              colour="sky"
              title="Statistical review"
              body="Independent peer reviewer that audits study design, sample size, controls, and inference for statistical soundness."
            />
            <CapabilityCard
              icon="🧬"
              colour="rose"
              title="Biology review"
              body="Independent peer reviewer that scrutinises mechanism, model choice, biological plausibility, and missing controls."
            />
          </div>
        </div>
      </section>

      {/* FEATURE STRIP */}
      <section className="px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <p className="eyebrow mb-3">What you get</p>
            <h2 className="font-display text-3xl md:text-4xl font-semibold">
              Everything an academic needs
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-7">
            <FeatureCard
              icon="⚡"
              title="Streamed output"
              description="Watch sections appear one by one as the agents draft them, with token usage and cost shown live."
            />
            <FeatureCard
              icon="📑"
              title="Times New Roman .docx"
              description="One-click download. Embedded figures, numbered citations, and consistent typography across every pipeline."
            />
            <FeatureCard
              icon="🧬"
              title="Grounded in your PDFs"
              description="Upload 1–100 reference papers — BM25 retrieval pulls the right excerpts into every section."
            />
          </div>
        </div>
      </section>

      <footer className="mt-auto border-t border-[color:var(--gold-line)] py-8 px-6">
        <div className="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3 text-sm text-neutral-400">
          <span>
            <span className="text-[color:var(--gold)] font-semibold">CorpusAI</span> — Built
            for biomedical and academic research.
          </span>
          <span>
            Backend:{" "}
            <code className="text-[color:var(--gold)]/80">
              {process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}
            </code>
          </span>
        </div>
      </footer>
    </main>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="surface rounded-xl p-7">
      <div className="text-4xl mb-3">{icon}</div>
      <h4 className="font-display text-2xl font-semibold text-[color:var(--gold-bright)] mb-2">
        {title}
      </h4>
      <p className="text-base text-neutral-200 leading-relaxed">{description}</p>
    </div>
  );
}

const CAPABILITY_COLOURS: Record<string, { accent: string; border: string }> = {
  gold: {
    accent: "text-[color:var(--gold-bright)]",
    border: "border-[color:var(--gold-line)]",
  },
  emerald: { accent: "text-emerald-300", border: "border-emerald-500/30" },
  sky: { accent: "text-sky-300", border: "border-sky-500/30" },
  rose: { accent: "text-rose-300", border: "border-rose-500/30" },
};

function CapabilityCard({
  icon,
  title,
  body,
  colour,
}: {
  icon: string;
  title: string;
  body: string;
  colour: keyof typeof CAPABILITY_COLOURS;
}) {
  const c = CAPABILITY_COLOURS[colour];
  return (
    <div className={`surface rounded-xl p-7 border ${c.border}`}>
      <div className="text-4xl mb-4">{icon}</div>
      <h4 className={`font-display text-xl font-semibold mb-2 ${c.accent}`}>
        {title}
      </h4>
      <p className="text-sm text-neutral-300 leading-relaxed">{body}</p>
    </div>
  );
}
