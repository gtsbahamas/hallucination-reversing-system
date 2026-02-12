"""Cursor adapter for cross-platform benchmark.

Cursor offers both IDE-based generation and an agent mode.
For HumanEval (Track 1), we use the completion API.
For SWE-bench (Track 2) and Feature Addition (Track 4), we use agent mode.

NOTE: Cursor does not have a public REST API as of 2026-02. This adapter
supports two modes:
  1. API mode: Uses the underlying model (Claude/GPT) directly via Anthropic/OpenAI API
     with Cursor-style system prompts. This tests the model, not Cursor's orchestration.
  2. Manual mode: Records results from manual Cursor IDE sessions.

For the benchmark, we default to API mode for reproducibility and automation,
with manual mode available for verifying that results match real Cursor behavior.
"""

import os
import time
from typing import Optional

from .base import PlatformAdapter, GenerationResult, ManualResultAdapter
from ..cost_tracker import BenchmarkCostTracker


# System prompts that approximate Cursor's behavior
CURSOR_FUNCTION_SYSTEM = """You are an expert programmer. Complete the function implementation based on the provided signature and docstring. Return ONLY the function code, no markdown fences or explanations."""

CURSOR_PATCH_SYSTEM = """You are an expert software engineer working in an IDE. Given a bug report and the relevant source files, generate a unified diff patch that fixes the issue. Output ONLY the patch in unified diff format."""

CURSOR_FEATURE_SYSTEM = """You are an expert software engineer working in an IDE. Given a feature request and the existing codebase, generate the necessary code changes as a unified diff patch. Output ONLY the patch."""


class CursorAdapter(PlatformAdapter):
    """Cursor platform adapter using direct API calls.

    Approximates Cursor's code generation by calling the underlying
    model (Claude Sonnet by default) with IDE-context-style prompts.
    """

    def __init__(
        self,
        tracker: BenchmarkCostTracker,
        model: str = "claude-sonnet-4-5-20250929",
        **kwargs,
    ):
        super().__init__(name="cursor", tracker=tracker, **kwargs)
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy-init the LLM client."""
        if self._client is None:
            from ...common.llm_client import LLMClient
            from ...common.cost_tracker import CostTracker
            # Use a lightweight tracker; actual costs go through BenchmarkCostTracker
            self._inner_tracker = CostTracker(budget_limit=99999)
            self._client = LLMClient(model=self.model, tracker=self._inner_tracker)
        return self._client

    def get_version(self) -> str:
        return f"cursor-api-{self.model}"

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        self._rate_limit()
        client = self._get_client()
        start = time.time()
        try:
            user_msg = f"Complete this function:\n\n{prompt}"
            if context:
                user_msg = f"{context}\n\n{user_msg}"

            code = client.complete(
                system=CURSOR_FUNCTION_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=2048,
                task_id="",
                condition="cursor",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000

            # Track in benchmark tracker
            self.tracker.record(
                platform="cursor",
                track="humaneval",
                task_id="",
                role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )

            return GenerationResult(
                platform="cursor",
                task_id="",
                track="humaneval",
                code=code,
                success=True,
                duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="cursor",
                task_id="",
                track="humaneval",
                code="",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        self._rate_limit()
        client = self._get_client()
        start = time.time()
        try:
            files_context = ""
            for filepath, content in source_files.items():
                truncated = content[:15000] if len(content) > 15000 else content
                files_context += f"\n### {filepath}\n```\n{truncated}\n```\n"

            user_msg = f"## Bug Report\n{issue}\n\n## Source Files\n{files_context}"

            patch = client.complete(
                system=CURSOR_PATCH_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=4096,
                task_id="",
                condition="cursor",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000

            self.tracker.record(
                platform="cursor",
                track="swebench",
                task_id="",
                role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )

            return GenerationResult(
                platform="cursor",
                task_id="",
                track="swebench",
                code=patch,
                success=True,
                duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="cursor",
                task_id="",
                track="swebench",
                code="",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )

    def generate_app(self, spec: str) -> GenerationResult:
        # Cursor is not an app generation platform
        return GenerationResult(
            platform="cursor",
            task_id="",
            track="app_gen",
            code="",
            success=False,
            error="Cursor does not support full app generation (Track 3)",
        )

    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        self._rate_limit()
        client = self._get_client()
        start = time.time()
        try:
            files_context = ""
            for filepath, content in list(codebase.items())[:10]:  # Limit files
                truncated = content[:10000] if len(content) > 10000 else content
                files_context += f"\n### {filepath}\n```\n{truncated}\n```\n"

            user_msg = f"## Feature Request\n{feature_request}\n\n## Existing Codebase\n{files_context}"

            patch = client.complete(
                system=CURSOR_FEATURE_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=4096,
                task_id="",
                condition="cursor",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000

            self.tracker.record(
                platform="cursor",
                track="feature",
                task_id="",
                role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )

            return GenerationResult(
                platform="cursor",
                task_id="",
                track="feature",
                code=patch,
                success=True,
                duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="cursor",
                task_id="",
                track="feature",
                code="",
                success=False,
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )
