"""Base class every CorpusAI agent inherits from.

Wraps a PydanticAI Agent. Subclasses declare prompt_name + output_model;
the base handles agent construction (lazy), prompt loading, typed parsing,
prompt caching, per-request usage accounting, per-agent model override,
and retries on transient Anthropic failures.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from anthropic import APIStatusError, APITimeoutError, RateLimitError
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.prompts import load_prompt
from app.core.usage import get_scope

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

_log = get_logger(__name__)

_RETRYABLE: tuple[type[BaseException], ...] = (
    RateLimitError,
    APITimeoutError,
)


def _retry_on_status(exc: BaseException) -> bool:
    if isinstance(exc, _RETRYABLE):
        return True
    if isinstance(exc, APIStatusError):
        # Retry on 5xx and 429; do not retry 4xx (caller errors).
        status = getattr(exc, "status_code", None)
        return status is not None and (status >= 500 or status == 429)
    return False


class BaseAgent(ABC, Generic[InputT, OutputT]):
    prompt_name: str
    output_model: type[OutputT]
    #: Optional per-agent model override. None = use ANTHROPIC_CHAT_MODEL.
    model: str | None = None

    def __init__(self) -> None:
        self._agent: Agent | None = None

    def _get_agent(self) -> Agent:
        if self._agent is None:
            settings = get_settings()
            api_key = settings.anthropic_api_key or os.environ.get(
                "ANTHROPIC_API_KEY", ""
            )
            model_id = self.model or settings.anthropic_chat_model
            model = AnthropicModel(
                model_id,
                provider=AnthropicProvider(api_key=api_key),
            )
            model_settings = AnthropicModelSettings(
                anthropic_cache_instructions=settings.enable_prompt_cache,
            )
            self._agent = Agent(
                model,
                system_prompt=load_prompt(self.prompt_name),
                output_type=self.output_model,
                model_settings=model_settings,
            )
        return self._agent

    @abstractmethod
    def render_input(self, payload: InputT) -> str:
        """Convert the typed input into the user-message string sent to the LLM."""

    async def run(self, payload: InputT) -> OutputT:
        agent = self._get_agent()
        message = self.render_input(payload)
        result = await self._run_with_retries(agent, message)
        self._record_usage(result)
        return result.output

    @retry(
        retry=retry_if_exception_type(Exception)
        & retry_if_exception_type((RateLimitError, APITimeoutError, APIStatusError)),
        wait=wait_random_exponential(min=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    async def _run_with_retries(self, agent: Agent, message: str):
        try:
            return await agent.run(message)
        except APIStatusError as exc:
            if not _retry_on_status(exc):
                raise
            _log.warning(
                "agent_retry",
                agent=self.__class__.__name__,
                status=getattr(exc, "status_code", None),
            )
            raise

    def _record_usage(self, result: object) -> None:
        scope = get_scope()
        if scope is None:
            return
        usage_fn = getattr(result, "usage", None)
        if usage_fn is None:
            return
        try:
            usage = usage_fn()
        except Exception:  # noqa: BLE001
            return
        scope.add(
            agent_name=self.__class__.__name__,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
            cache_read_tokens=int(getattr(usage, "cache_read_tokens", 0) or 0),
            cache_write_tokens=int(getattr(usage, "cache_write_tokens", 0) or 0),
        )
        _log.debug(
            "agent_call",
            agent=self.__class__.__name__,
            input_tokens=getattr(usage, "input_tokens", 0),
            output_tokens=getattr(usage, "output_tokens", 0),
            cache_read=getattr(usage, "cache_read_tokens", 0),
        )

    def _parse(self, text: str) -> OutputT:
        block = _extract_json(text)
        return self.output_model.model_validate_json(block)


def _extract_json(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```", 2)[1]
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.rsplit("```", 1)[0]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in text: {text[:200]}")
    return stripped[start : end + 1]


_ = json
