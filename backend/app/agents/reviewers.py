"""Peer-review agents — three subject-matter reviewers + a synthesiser.

Reviewers each receive the assembled paper markdown and return structured
feedback. They run in parallel; the synthesiser merges their reports into
an executive summary and a prioritised revision list.
"""

from __future__ import annotations

from app.agents.base import BaseAgent
from app.schemas.paper import (
    BiologyReview,
    GapReview,
    ReviewerInput,
    ReviewSynthesis,
    ReviewSynthesisInput,
    StatisticsReview,
)


def _render_paper(payload: ReviewerInput) -> str:
    return (
        f"Paper topic: {payload.topic}\n\n"
        f"--- BEGIN PAPER ---\n{payload.paper_markdown}\n--- END PAPER ---"
    )


class BiologyReviewer(BaseAgent[ReviewerInput, BiologyReview]):
    prompt_name = "biology_reviewer"
    output_model = BiologyReview

    def render_input(self, payload: ReviewerInput) -> str:
        return _render_paper(payload)


class StatisticsReviewer(BaseAgent[ReviewerInput, StatisticsReview]):
    prompt_name = "statistics_reviewer"
    output_model = StatisticsReview

    def render_input(self, payload: ReviewerInput) -> str:
        return _render_paper(payload)


class GapReviewer(BaseAgent[ReviewerInput, GapReview]):
    prompt_name = "gap_reviewer"
    output_model = GapReview

    def render_input(self, payload: ReviewerInput) -> str:
        return _render_paper(payload)


class ReviewSynthesiser(BaseAgent[ReviewSynthesisInput, ReviewSynthesis]):
    prompt_name = "review_synthesiser"
    output_model = ReviewSynthesis

    def render_input(self, payload: ReviewSynthesisInput) -> str:
        bio_issues = "\n".join(
            f"- [{i.severity}] ({i.section}) {i.comment}" for i in payload.biology.issues
        ) or "(none)"
        stat_issues = "\n".join(
            f"- [{i.severity}] ({i.section}) {i.comment}"
            for i in payload.statistics.issues
        ) or "(none)"
        gaps = "\n".join(f"- {g}" for g in payload.gap.unaddressed_gaps) or "(none)"

        return (
            f"Topic: {payload.topic}\n\n"
            f"=== Biology review (score {payload.biology.overall_score}/5) ===\n"
            f"{payload.biology.summary}\nIssues:\n{bio_issues}\n\n"
            f"=== Statistics review (score {payload.statistics.overall_score}/5) ===\n"
            f"{payload.statistics.summary}\nIssues:\n{stat_issues}\n\n"
            f"=== Gap review ===\n{payload.gap.summary}\n"
            f"Unaddressed gaps:\n{gaps}"
        )
