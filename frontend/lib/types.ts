// TypeScript mirrors of the backend Pydantic schemas. Kept hand-written
// for now — when this drifts often, generate from FastAPI's OpenAPI.

export type SectionName =
  | "abstract"
  | "introduction"
  | "methods"
  | "results"
  | "discussion";

export const SECTION_LABELS: Record<SectionName, string> = {
  abstract: "Abstract",
  introduction: "Introduction",
  methods: "Methods",
  results: "Results",
  discussion: "Discussion",
};

export interface PaperSummary {
  title: string;
  year: number | null;
  authors: string[];
  findings: string[];
  methods: string[];
  limitations: string[];
  source_id: string | null;
}

export interface ResearchGap {
  description: string;
  evidence: string[];
}

export interface ResearchOutput {
  topic: string;
  gap: ResearchGap;
  idea: string;
  method: string;
  discussion: string;
  references: PaperSummary[];
}

export interface UploadedRef {
  ref_id: string;
  filename: string;
  page_count: number;
  char_count: number;
}

export interface RefSet {
  set_id: string;
  documents: UploadedRef[];
}

export interface FormattedReference {
  ref_id: string;
  citation: string;
}

export interface PaperDraft {
  topic: string;
  sections: Partial<Record<SectionName, string>>;
  references: FormattedReference[];
  markdown: string;
}

export type Severity = "critical" | "major" | "minor";

export interface ReviewIssue {
  severity: Severity;
  section: string;
  comment: string;
}

export interface BiologyReview {
  summary: string;
  overall_score: number;
  strengths: string[];
  issues: ReviewIssue[];
}

export type StatisticsReview = BiologyReview;

export interface GapReview {
  summary: string;
  unaddressed_gaps: string[];
  future_work: string[];
}

export interface ReviewSynthesis {
  executive_summary: string;
  top_revisions: string[];
}

export interface ReviewReport {
  biology: BiologyReview;
  statistics: StatisticsReview;
  gap: GapReview;
  synthesis: ReviewSynthesis;
}

export interface WriteResult {
  paper: PaperDraft;
  review: ReviewReport | null;
}

export interface SseEvent {
  kind: string;
  data: Record<string, unknown>;
}

// ---------- NHMRC grant pipeline ----------

export type NHMRCScheme =
  | "ideas"
  | "investigator"
  | "synergy"
  | "partnership"
  | "clinical_trial"
  | "postgraduate";

export const NHMRC_SCHEME_LABELS: Record<NHMRCScheme, string> = {
  ideas: "Ideas Grant",
  investigator: "Investigator Grant",
  synergy: "Synergy Grant",
  partnership: "Partnership Project",
  clinical_trial: "Clinical Trials and Cohort Studies",
  postgraduate: "Postgraduate Scholarship",
};

export type StudyType =
  | "clinical_trial"
  | "observational"
  | "laboratory"
  | "health_services"
  | "mixed";

export const STUDY_TYPE_LABELS: Record<StudyType, string> = {
  clinical_trial: "Clinical trial",
  observational: "Observational",
  laboratory: "Laboratory",
  health_services: "Health services",
  mixed: "Mixed methods",
};

export type NHMRCSectionName =
  | "synopsis"
  | "burden_of_disease"
  | "aims_hypotheses"
  | "methods"
  | "consumer_involvement"
  | "significance_impact";

export const NHMRC_SECTION_LABELS: Record<NHMRCSectionName, string> = {
  synopsis: "Synopsis",
  burden_of_disease: "Burden of Disease",
  aims_hypotheses: "Aims & Hypotheses",
  methods: "Research Plan / Methods",
  consumer_involvement: "Consumer Involvement",
  significance_impact: "Significance & Impact",
};

export interface NHMRCGrantDraft {
  topic: string;
  scheme: NHMRCScheme;
  study_type: StudyType;
  sections: Partial<Record<NHMRCSectionName, string>>;
  references: FormattedReference[];
  markdown: string;
}

export interface NHMRCResult {
  grant: NHMRCGrantDraft;
}

// ---------- ARC grant pipeline ----------

export type ARCScheme =
  | "discovery"
  | "linkage"
  | "laureate"
  | "decra"
  | "future"
  | "centre";

export const ARC_SCHEME_LABELS: Record<ARCScheme, string> = {
  discovery: "Discovery Project",
  linkage: "Linkage Project",
  laureate: "Laureate Fellowship",
  decra: "DECRA",
  future: "Future Fellowship",
  centre: "Centre of Excellence",
};

export type InnovationType =
  | "conceptual"
  | "methodological"
  | "empirical"
  | "integrative";

export const INNOVATION_TYPE_LABELS: Record<InnovationType, string> = {
  conceptual: "Conceptual (new framework / theory)",
  methodological: "Methodological (new technique / application)",
  empirical: "Empirical (new measurement / dataset)",
  integrative: "Integrative (combining fields / methods)",
};

export type ARCSectionName =
  | "opening_statement"
  | "aims"
  | "significance"
  | "innovation"
  | "approach_methodology"
  | "national_benefit";

export const ARC_SECTION_LABELS: Record<ARCSectionName, string> = {
  opening_statement: "Project Description",
  aims: "Aims",
  significance: "Significance",
  innovation: "Innovation",
  approach_methodology: "Approach & Methodology",
  national_benefit: "National Benefit",
};

export interface ARCGrantDraft {
  topic: string;
  scheme: ARCScheme;
  innovation_type: InnovationType;
  sections: Partial<Record<ARCSectionName, string>>;
  references: FormattedReference[];
  markdown: string;
}

export interface ARCResult {
  grant: ARCGrantDraft;
}

// ---------- Thesis pipeline ----------

export type ThesisStructure =
  | "traditional"
  | "by_publication"
  | "hybrid"
  | "masters"
  | "custom";

export const THESIS_STRUCTURE_LABELS: Record<ThesisStructure, string> = {
  traditional: "Traditional / Monograph",
  by_publication: "PhD by Publication",
  hybrid: "Hybrid",
  masters: "Masters by Research",
  custom: "Custom (describe in notes)",
};

export interface UploadedFigure {
  figure_id: string;
  filename: string;
  width_px?: number | null;
  height_px?: number | null;
}

export interface FigureRef {
  figure_id: string;
  caption?: string | null;
  // local-only fields used for UI bookkeeping
  filename?: string;
}

export interface ChapterConfig {
  title?: string | null;
  notes?: string | null;
  set_id?: string | null;
  figures: FigureRef[];
}

export interface ThesisDraft {
  title: string;
  discipline: string | null;
  structure: ThesisStructure;
  abstract: string;
  chapters: { title: string; content: string }[];
  references: FormattedReference[];
  markdown: string;
}

export interface ThesisResult {
  thesis: ThesisDraft;
}
