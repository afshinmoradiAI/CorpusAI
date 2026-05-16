export function ModeHero({
  eyebrow,
  title,
  subtitle,
  description,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  description: string;
}) {
  return (
    <section className="px-6 pt-12 pb-10">
      <div className="max-w-7xl mx-auto">
        <p className="text-sm uppercase tracking-[0.32em] text-[color:var(--gold)] mb-3 font-medium">
          {eyebrow}
        </p>
        <h1 className="font-display text-6xl md:text-7xl font-semibold mb-3">
          <span className="text-gold-gradient">{title}</span>
        </h1>
        <p className="font-display text-2xl md:text-3xl text-neutral-200 italic mb-4">
          {subtitle}
        </p>
        <p className="text-base md:text-lg text-neutral-400 max-w-3xl leading-relaxed">
          {description}
        </p>
      </div>
    </section>
  );
}
