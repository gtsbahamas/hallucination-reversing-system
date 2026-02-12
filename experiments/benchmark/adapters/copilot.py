"""GitHub Copilot adapter for cross-platform benchmark.

Copilot primarily does code completion (Track 1) and feature addition (Track 4).
Like Cursor, Copilot doesn't have a direct REST API for code generation.

This adapter uses GPT-4o (Copilot's underlying model) via the OpenAI API
with Copilot-style prompts to approximate behavior. For true Copilot results,
use manual mode and record results from the VS Code extension.
"""

import time
from typing import Optional

from .base import PlatformAdapter, GenerationResult
from ..cost_tracker import BenchmarkCostTracker


COPILOT_FUNCTION_SYSTEM = """You are GitHub Copilot, an AI pair programmer. Complete the function based on the signature and docstring. Return ONLY the function implementation, no explanations."""

COPILOT_FEATURE_SYSTEM = """You are GitHub Copilot Workspace. Given a feature request and existing code, generate the necessary changes as a unified diff. Return ONLY the diff."""


class CopilotAdapter(PlatformAdapter):
    """GitHub Copilot adapter using OpenAI API (GPT-4o)."""

    def __init__(
        self,
        tracker: BenchmarkCostTracker,
        model: str = "gpt-4o-2024-11-20",
        **kwargs,
    ):
        super().__init__(name="copilot", tracker=tracker, **kwargs)
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            from ...common.llm_client import LLMClient
            from ...common.cost_tracker import CostTracker
            self._inner_tracker = CostTracker(budget_limit=99999)
            self._client = LLMClient(model=self.model, tracker=self._inner_tracker)
        return self._client

    def get_version(self) -> str:
        return f"copilot-api-{self.model}"

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        self._rate_limit()
        client = self._get_client()
        start = time.time()
        try:
            user_msg = f"Complete this function:\n\n{prompt}"
            if context:
                user_msg = f"{context}\n\n{user_msg}"
            code = client.complete(
                system=COPILOT_FUNCTION_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=2048,
                task_id="",
                condition="copilot",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000
            self.tracker.record(
                platform="copilot", track="humaneval", task_id="", role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )
            return GenerationResult(
                platform="copilot", task_id="", track="humaneval",
                code=code, success=True, duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="copilot", task_id="", track="humaneval",
                code="", success=False, error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        return GenerationResult(
            platform="copilot", task_id="", track="swebench",
            code="", success=False,
            error="Copilot does not support autonomous bug fixing (Track 2)",
        )

    def generate_app(self, spec: str) -> GenerationResult:
        return GenerationResult(
            platform="copilot", task_id="", track="app_gen",
            code="", success=False,
            error="Copilot does not support full app generation (Track 3)",
        )

    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        self._rate_limit()
        client = self._get_client()
        start = time.time()
        try:
            files_context = ""
            for filepath, content in list(codebase.items())[:10]:
                truncated = content[:10000] if len(content) > 10000 else content
                files_context += f"\n### {filepath}\n```\n{truncated}\n```\n"
            user_msg = f"## Feature Request\n{feature_request}\n\n## Existing Code\n{files_context}"
            patch = client.complete(
                system=COPILOT_FEATURE_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=4096,
                task_id="",
                condition="copilot",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000
            self.tracker.record(
                platform="copilot", track="feature", task_id="", role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )
            return GenerationResult(
                platform="copilot", task_id="", track="feature",
                code=patch, success=True, duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="copilot", task_id="", track="feature",
                code="", success=False, error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
