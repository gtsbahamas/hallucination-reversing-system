"""Abstract base adapter and manual result adapter for platform benchmarking.

Each platform adapter wraps a specific AI coding platform and provides
a uniform interface for code generation across all benchmark tracks.
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..cost_tracker import BenchmarkCostTracker


@dataclass
class GenerationResult:
    """Result of a single code generation attempt."""
    platform: str
    task_id: str
    track: str
    code: str  # Generated code, patch, or app source
    success: bool  # Whether generation completed without errors
    duration_ms: float = 0
    run_number: int = 1
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "task_id": self.task_id,
            "track": self.track,
            "code": self.code,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "run_number": self.run_number,
            "tokens_used": self.tokens_used,
            "error": self.error,
            "metadata": self.metadata,
        }


class PlatformAdapter(ABC):
    """Abstract base class for platform adapters.

    Each platform adapter implements code generation for one or more
    benchmark tracks. Adapters handle rate limiting, retries, and
    cost tracking internally.
    """

    def __init__(
        self,
        name: str,
        tracker: BenchmarkCostTracker,
        max_retries: int = 3,
        rate_limit_rpm: int = 60,
        timeout_seconds: int = 600,
    ):
        self.name = name
        self.tracker = tracker
        self.max_retries = max_retries
        self.rate_limit_rpm = rate_limit_rpm
        self.timeout_seconds = timeout_seconds
        self._last_request_time = 0.0

    @abstractmethod
    def get_version(self) -> str:
        """Return the platform version string for reproducibility."""
        ...

    @abstractmethod
    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        """Generate a function from a docstring/signature (Track 1: HumanEval).

        Args:
            prompt: Function signature with docstring.
            context: Additional context (imports, helpers).

        Returns:
            GenerationResult with the generated function code.
        """
        ...

    @abstractmethod
    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        """Generate a patch to fix a bug (Track 2: SWE-bench).

        Args:
            issue: Issue description (problem statement).
            source_files: Dict of filepath -> file contents.

        Returns:
            GenerationResult with a unified diff patch.
        """
        ...

    @abstractmethod
    def generate_app(self, spec: str) -> GenerationResult:
        """Generate a full application from a spec (Track 3: App Generation).

        Args:
            spec: Natural language application specification.

        Returns:
            GenerationResult with application source code (may be multi-file).
        """
        ...

    @abstractmethod
    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        """Add a feature to an existing codebase (Track 4: Feature Addition).

        Args:
            feature_request: Feature description (as a GitHub issue).
            codebase: Dict of filepath -> file contents.

        Returns:
            GenerationResult with the modified/new files as a patch or file dict.
        """
        ...

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self.rate_limit_rpm <= 0:
            return
        min_interval = 60.0 / self.rate_limit_rpm
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()


class ManualResultAdapter(PlatformAdapter):
    """Adapter for platforms that require manual operation.

    Instead of making API calls, this adapter loads pre-recorded results
    from a results directory. Use this for platforms like Bolt.new and
    Lovable that don't have public APIs.

    Directory structure for manual results:
        results/benchmark/manual/{platform}/{track}/{task_id}/
            run_{n}.json  — with keys: code, success, duration_ms, metadata

    To record results manually:
        1. Run the platform's UI with the benchmark prompt
        2. Save the generated code to the appropriate directory
        3. Run the benchmark with --resume to evaluate the saved results
    """

    def __init__(
        self,
        name: str,
        tracker: BenchmarkCostTracker,
        results_dir: Path,
        **kwargs,
    ):
        super().__init__(name=name, tracker=tracker, **kwargs)
        self.results_dir = results_dir

    def get_version(self) -> str:
        return "manual"

    def _load_manual_result(
        self, track: str, task_id: str, run_number: int = 1
    ) -> Optional[GenerationResult]:
        """Load a manually recorded result."""
        safe_id = task_id.replace("/", "_")
        result_path = self.results_dir / self.name / track / safe_id / f"run_{run_number}.json"
        if not result_path.exists():
            return None
        data = json.loads(result_path.read_text())
        return GenerationResult(
            platform=self.name,
            task_id=task_id,
            track=track,
            code=data.get("code", ""),
            success=data.get("success", True),
            duration_ms=data.get("duration_ms", 0),
            run_number=run_number,
            metadata=data.get("metadata", {}),
        )

    def _not_recorded(self, track: str, task_id: str) -> GenerationResult:
        """Return a placeholder for a task that hasn't been recorded yet."""
        return GenerationResult(
            platform=self.name,
            task_id=task_id,
            track=track,
            code="",
            success=False,
            error=f"Manual result not recorded. Save to: {self.results_dir}/{self.name}/{track}/{task_id}/run_1.json",
        )

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        # Manual adapters don't auto-generate — they load saved results
        return self._not_recorded("humaneval", "unknown")

    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        return self._not_recorded("swebench", "unknown")

    def generate_app(self, spec: str) -> GenerationResult:
        return self._not_recorded("app_gen", "unknown")

    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        return self._not_recorded("feature", "unknown")

    def load_result(self, track: str, task_id: str, run_number: int = 1) -> GenerationResult:
        """Load a manual result, or return a not-recorded placeholder."""
        result = self._load_manual_result(track, task_id, run_number)
        if result:
            return result
        return self._not_recorded(track, task_id)
