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
