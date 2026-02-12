"""Lovable adapter for cross-platform benchmark.

Lovable is a browser-based app generation platform similar to Bolt.new.
It does not have a public API, so this adapter operates in MANUAL mode only.

To use this adapter:
1. Open lovable.dev in a browser
2. Paste the benchmark prompt
3. Let Lovable generate the application
4. Export the generated code
5. Save it to: results/benchmark/manual/lovable/app_gen/{task_id}/run_1.json

The JSON file should contain:
{
    "code": "<full source code or path to exported project>",
    "success": true,
    "duration_ms": 60000,
    "metadata": {
        "lovable_version": "2026-02",
        "follow_up_prompts": 0,
        "export_format": "github"
    }
}
"""

from pathlib import Path

from .base import ManualResultAdapter, GenerationResult
from ..cost_tracker import BenchmarkCostTracker


class LovableAdapter(ManualResultAdapter):
    """Lovable adapter — manual mode only.

    Lovable generates full applications from natural language prompts.
    It only supports Track 3 (App Generation).
    """

    def __init__(
        self,
        tracker: BenchmarkCostTracker,
        results_dir: Path = Path("results/benchmark/manual"),
        **kwargs,
    ):
        super().__init__(
            name="lovable",
            tracker=tracker,
            results_dir=results_dir,
            **kwargs,
        )

    def get_version(self) -> str:
        return "lovable-manual-2026-02"

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        return GenerationResult(
            platform="lovable", task_id="", track="humaneval",
            code="", success=False,
            error="Lovable does not support function generation (Track 1)",
        )

    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        return GenerationResult(
            platform="lovable", task_id="", track="swebench",
            code="", success=False,
            error="Lovable does not support bug fixing (Track 2)",
        )

    def generate_app(self, spec: str) -> GenerationResult:
        return self._not_recorded("app_gen", "unknown")

    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        return GenerationResult(
            platform="lovable", task_id="", track="feature",
            code="", success=False,
            error="Lovable does not support feature addition (Track 4)",
        )
