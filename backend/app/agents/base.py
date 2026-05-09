"""Base class every CorpusAI agent inherits from.

Wraps Microsoft Agent Framework's Agent + AnthropicClient. Subclasses only
declare the prompt name and the input/output Pydantic models — the base
handles client construction, prompt loading, and JSON parsing of the reply.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from agent_framework import Agent
from agent_framework_anthropic import AnthropicClient
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.prompts import load_prompt

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseAgent(ABC, Generic[InputT, OutputT]):
    prompt_name: str
    output_model: type[OutputT]

    def __init__(self) -> None:
        settings = get_settings()
        self._agent = Agent(
            client=AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_chat_model,
            ),
            instructions=load_prompt(self.prompt_name),
            name=self.__class__.__name__,
        )

    @abstractmethod
    def render_input(self, payload: InputT) -> str:
        """Convert the typed input into the user-message string sent to the LLM."""

    async def run(self, payload: InputT) -> OutputT:
        response = await self._agent.run(self.render_input(payload))
        return self._parse(response.text)

    def _parse(self, text: str) -> OutputT:
        block = _extract_json(text)
        return self.output_model.model_validate_json(block)


def _extract_json(text: str) -> str:
    """Pull a JSON object out of an LLM reply, tolerating ```json fences."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```", 2)[1]
        if stripped.startswith("json"):
            stripped = stripped[4:]
        stripped = stripped.rsplit("```", 1)[0]
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in agent reply: {text[:200]}")
    return stripped[start : end + 1]
