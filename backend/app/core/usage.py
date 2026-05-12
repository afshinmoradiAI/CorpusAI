"""Per-request usage tracking and spend cap.

Workflows enter `usage_scope()` at the start; each agent call adds tokens
to the active scope. If the scope's max_tokens is exceeded, the next agent
call raises SpendCapExceeded — the workflow surfaces this as an SSE error.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Iterator


class SpendCapExceeded(RuntimeError):
    """Raised when the per-request token budget is exhausted."""


_SONNET_INPUT_PER_M = 3.0
_SONNET_OUTPUT_PER_M = 15.0
_CACHE_READ_DISCOUNT = 0.1  # Anthropic cached reads ≈ 10% of input price


@dataclass
class UsageScope:
    max_tokens: int
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    requests: int = 0
    agent_breakdown: dict[str, int] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimated_cost_usd(self) -> float:
        """Rough USD estimate (Sonnet pricing; Haiku is ~5× cheaper but we
        report worst-case so users aren't surprised)."""
        cached = self.cache_read_tokens * _SONNET_INPUT_PER_M * _CACHE_READ_DISCOUNT
        fresh = (self.input_tokens - self.cache_read_tokens) * _SONNET_INPUT_PER_M
        out = self.output_tokens * _SONNET_OUTPUT_PER_M
        return round((cached + fresh + out) / 1_000_000, 4)

    def summary(self) -> dict[str, int | float | dict[str, int]]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "requests": self.requests,
            "estimated_cost_usd": self.estimated_cost_usd(),
            "agent_breakdown": dict(self.agent_breakdown),
        }

    def add(
        self,
        *,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
    ) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.cache_read_tokens += cache_read_tokens
        self.cache_write_tokens += cache_write_tokens
        self.requests += 1
        self.agent_breakdown[agent_name] = (
            self.agent_breakdown.get(agent_name, 0) + input_tokens + output_tokens
        )
        if self.total_tokens > self.max_tokens:
            raise SpendCapExceeded(
                f"Token budget exceeded: {self.total_tokens} > {self.max_tokens}"
            )


_current_scope: ContextVar[UsageScope | None] = ContextVar(
    "usage_scope", default=None
)


def get_scope() -> UsageScope | None:
    return _current_scope.get()


@contextmanager
def usage_scope(max_tokens: int) -> Iterator[UsageScope]:
    scope = UsageScope(max_tokens=max_tokens)
    token = _current_scope.set(scope)
    try:
        yield scope
    finally:
        _current_scope.reset(token)
