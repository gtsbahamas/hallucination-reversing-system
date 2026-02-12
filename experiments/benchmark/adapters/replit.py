"""Replit Agent adapter for cross-platform benchmark.

Replit Agent can generate full applications (Track 3), fix bugs in
existing code (Track 2 subset), and add features (Track 4).

As of 2026-02, Replit provides a Model API that can be used for
programmatic code generation. For full Agent behavior (planning,
multi-file edits, testing), manual mode is required.

This adapter supports:
  - API mode: Uses Replit's code generation model for function/patch tasks
  - Manual mode: Records results from Replit Agent sessions for app generation

To record manual results:
1. Open replit.com and create a new Repl
2. Use Replit Agent with the benchmark prompt
3. Once the agent completes, export the project
4. Save to: results/benchmark/manual/replit/{track}/{task_id}/run_1.json
"""

import time
from pathlib import Path
from typing import Optional

from .base import PlatformAdapter, ManualResultAdapter, GenerationResult
from ..cost_tracker import BenchmarkCostTracker


REPLIT_PATCH_SYSTEM = """You are Replit Agent, an AI coding assistant. Given a bug report and source files, generate a unified diff patch to fix the issue. Output ONLY the patch."""

REPLIT_FEATURE_SYSTEM = """You are Replit Agent, an AI coding assistant. Given a feature request and existing code, generate a unified diff patch with the necessary changes. Output ONLY the patch."""

REPLIT_APP_SYSTEM = """You are Replit Agent, an AI coding assistant. Given an application specification, generate the complete source code for the application. Include all necessary files with clear file path markers."""


class ReplitAdapter(PlatformAdapter):
    """Replit Agent adapter — hybrid API/manual mode.

    Uses Anthropic API (Claude Sonnet) with Replit-style prompts for
    automated tracks. Falls back to manual result loading for app generation.
    """

    def __init__(
        self,
        tracker: BenchmarkCostTracker,
        model: str = "claude-sonnet-4-5-20250929",
        manual_results_dir: Path = Path("results/benchmark/manual"),
        **kwargs,
    ):
        super().__init__(name="replit", tracker=tracker, **kwargs)
        self.model = model
        self.manual_results_dir = manual_results_dir
        self._client = None
        self._manual = ManualResultAdapter(
            name="replit", tracker=tracker, results_dir=manual_results_dir,
        )

    def _get_client(self):
        if self._client is None:
            from ...common.llm_client import LLMClient
            from ...common.cost_tracker import CostTracker
            self._inner_tracker = CostTracker(budget_limit=99999)
            self._client = LLMClient(model=self.model, tracker=self._inner_tracker)
        return self._client

    def get_version(self) -> str:
        return f"replit-hybrid-{self.model}"

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        # Replit doesn't focus on function-level generation
        return GenerationResult(
            platform="replit", task_id="", track="humaneval",
            code="", success=False,
            error="Replit Agent is not designed for function completion (Track 1). Use Track 2-4.",
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
                system=REPLIT_PATCH_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=4096,
                task_id="",
                condition="replit",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000
            self.tracker.record(
                platform="replit", track="swebench", task_id="", role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )
            return GenerationResult(
                platform="replit", task_id="", track="swebench",
                code=patch, success=True, duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="replit", task_id="", track="swebench",
                code="", success=False, error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )

    def generate_app(self, spec: str) -> GenerationResult:
        # App generation requires full Replit Agent — use manual mode
        return self._manual._not_recorded("app_gen", "unknown")

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
                system=REPLIT_FEATURE_SYSTEM,
                user=user_msg,
                temperature=0.7,
                max_tokens=4096,
                task_id="",
                condition="replit",
                role="generate",
            )
            duration_ms = (time.time() - start) * 1000
            self.tracker.record(
                platform="replit", track="feature", task_id="", role="generate",
                model=self.model,
                input_tokens=self._inner_tracker.calls[-1].input_tokens if self._inner_tracker.calls else 0,
                output_tokens=self._inner_tracker.calls[-1].output_tokens if self._inner_tracker.calls else 0,
                duration_ms=duration_ms,
            )
            return GenerationResult(
                platform="replit", task_id="", track="feature",
                code=patch, success=True, duration_ms=duration_ms,
            )
        except Exception as e:
            return GenerationResult(
                platform="replit", task_id="", track="feature",
                code="", success=False, error=str(e),
                duration_ms=(time.time() - start) * 1000,
            )
