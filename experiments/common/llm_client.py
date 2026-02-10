"""Unified LLM client for Anthropic and OpenAI with cost tracking."""

import os
import time
from typing import Optional

import anthropic

from .cost_tracker import CostTracker


class LLMClient:
    """Wrapper around Anthropic (and optionally OpenAI) APIs with cost tracking."""

    def __init__(self, model: str, tracker: CostTracker):
        self.model = model
        self.tracker = tracker

        if model.startswith("claude"):
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._anthropic = anthropic.Anthropic(
                api_key=api_key, timeout=15 * 60
            )
            self._provider = "anthropic"
        elif model.startswith("gpt"):
            try:
                import openai
            except ImportError:
                raise ImportError("pip install openai for GPT models")
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._openai = openai.OpenAI(api_key=api_key)
            self._provider = "openai"
        else:
            raise ValueError(f"Unknown model: {model}")

    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        task_id: str = "",
        condition: str = "",
        iteration: int = 0,
        role: str = "unknown",
    ) -> str:
        start = time.time()

        if self._provider == "anthropic":
            response = self._anthropic.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            content = "".join(
                b.text for b in response.content if b.type == "text"
            )
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

        elif self._provider == "openai":
            response = self._openai.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

        duration_ms = (time.time() - start) * 1000

        self.tracker.record(
            model=self.model,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            task_id=task_id,
            condition=condition,
            iteration=iteration,
            duration_ms=duration_ms,
        )

        return content
