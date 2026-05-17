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

      {/* ARCHITECTURE — the impressive stack section */}
      <section className="px-6 py-24">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <p className="eyebrow mb-3">Under the hood</p>
            <h2 className="font-display text-3xl md:text-4xl font-semibold mb-4">
              A team of <span className="text-gold-gradient">26 specialists</span> working in concert
            </h2>
            <p className="text-base md:text-lg text-neutral-300 max-w-3xl mx-auto">
              Every agent owns one job, one prompt, and one structured output —
              orchestrated by five purpose-built workflows.
            </p>
          </div>

          {/* Big stats bar */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-14">
            <StatBlock value="26" label="Specialised agents" />
            <StatBlock value="5" label="Coordinated pipelines" />
            <StatBlock value="3-way" label="Peer review + synthesis" />
            <StatBlock value="2" label="Claude models, smart-routed" />
          </div>

          {/* Agent roster by role */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5 mb-14">
            <AgentGroup
              count={17}
              title="Writers"
              colour="gold"
              agents={[
                "5 paper sections",
                "6 NHMRC sections",
                "6 ARC sections",
                "Thesis chapters + abstract",
              ]}
            />
            <AgentGroup
              count={4}
              title="Peer reviewers"
              colour="emerald"
              agents={[
                "Biology reviewer",
                "Statistics reviewer",
                "Gap reviewer",
                "Review synthesiser",
              ]}
            />
            <AgentGroup
              count={4}
              title="Analysts"
              colour="sky"
              agents={[
                "Topic analyser",
                "Gap finder",
                "Idea generator",
                "Method designer",
              ]}
            />
            <AgentGroup
              count={3}
              title="Support"
              colour="rose"
              agents={[
                "Paper summariser",
                "Reference formatter",
                "Discussion writer",
              ]}
            />
          </div>

          {/* Engineering highlights */}
          <div className="grid md:grid-cols-3 gap-5">
            <TechCard
              tag="Multi-model"
              title="Sonnet 4.6 + Haiku 4.5"
              body="Writing and reasoning run on Sonnet. Keyword expansion, structured extraction, and citation formatting run on Haiku — faster, cheaper, just as accurate."
            />
            <TechCard
              tag="Type-safe I/O"
              title="Pydantic everywhere"
              body="Every agent returns a validated Pydantic model. No regex parsing, no hallucinated fields — the schema is enforced before the next agent sees it."
            />
            <TechCard
              tag="Resilience"
              title="Cached prompts, retried calls"
              body="System prompts are cached across runs. Transient 429s and 5xx errors retry automatically with exponential backoff."
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

function StatBlock({ value, label }: { value: string; label: string }) {
  return (
    <div className="surface rounded-xl p-6 text-center border border-[color:var(--gold-line)]">
      <div className="font-display text-4xl md:text-5xl font-semibold text-gold-gradient mb-1">
        {value}
      </div>
      <div className="text-xs md:text-sm uppercase tracking-widest text-neutral-400">
        {label}
      </div>
    </div>
  );
}

const GROUP_COLOURS: Record<
  string,
  { badge: string; accent: string; border: string }
> = {
  gold: {
    badge: "bg-[color:var(--gold)] text-black",
    accent: "text-[color:var(--gold-bright)]",
    border: "border-[color:var(--gold-line)]",
  },
  emerald: {
    badge: "bg-emerald-400 text-black",
    accent: "text-emerald-300",
    border: "border-emerald-500/30",
  },
  sky: {
    badge: "bg-sky-400 text-black",
    accent: "text-sky-300",
    border: "border-sky-500/30",
  },
  rose: {
    badge: "bg-rose-400 text-black",
    accent: "text-rose-300",
    border: "border-rose-500/30",
  },
};

function AgentGroup({
  count,
  title,
  colour,
  agents,
}: {
  count: number;
  title: string;
  colour: keyof typeof GROUP_COLOURS;
  agents: string[];
}) {
  const c = GROUP_COLOURS[colour];
  return (
    <div className={`surface rounded-xl p-6 border ${c.border}`}>
      <div className="flex items-center gap-3 mb-4">
        <span
          className={`inline-flex items-center justify-center w-12 h-12 rounded-full text-xl font-bold ${c.badge}`}
        >
          {count}
        </span>
        <h4 className={`font-display text-xl font-semibold ${c.accent}`}>
          {title}
        </h4>
      </div>
      <ul className="space-y-1.5 text-sm text-neutral-300">
        {agents.map((a) => (
          <li key={a} className="flex items-start gap-2">
            <span className={`mt-1 ${c.accent}`}>›</span>
            <span>{a}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TechCard({
  tag,
  title,
  body,
}: {
  tag: string;
  title: string;
  body: string;
}) {
  return (
    <div className="surface rounded-xl p-6 border border-[color:var(--gold-line)]">
      <span className="inline-block text-xs uppercase tracking-widest text-[color:var(--gold)] px-2.5 py-1 rounded-full border border-[color:var(--gold-line)] bg-black/30 mb-4">
        {tag}
      </span>
      <h4 className="font-display text-xl font-semibold text-[color:var(--gold-bright)] mb-2">
        {title}
      </h4>
      <p className="text-sm text-neutral-300 leading-relaxed">{body}</p>
    </div>
  );
}
