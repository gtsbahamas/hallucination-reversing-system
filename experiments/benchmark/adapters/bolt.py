"""Bolt.new adapter for cross-platform benchmark.

Bolt.new is a browser-based app generation platform. It does not have a
public API, so this adapter operates in MANUAL mode only.

To use this adapter:
1. Open bolt.new in a browser
2. Paste the benchmark prompt
3. Let Bolt generate the application
4. Export/download the generated code
5. Save it to: results/benchmark/manual/bolt/app_gen/{task_id}/run_1.json

The JSON file should contain:
{
    "code": "<full source code or path to exported project>",
    "success": true,
    "duration_ms": 45000,
    "metadata": {
        "bolt_version": "2026-02",
        "follow_up_prompts": 0,
        "export_format": "zip"
    }
}
"""

from pathlib import Path

from .base import ManualResultAdapter, GenerationResult
from ..cost_tracker import BenchmarkCostTracker


class BoltAdapter(ManualResultAdapter):
    """Bolt.new adapter — manual mode only.

    Bolt.new generates full applications from natural language prompts.
    It only supports Track 3 (App Generation).
    """

    def __init__(
        self,
        tracker: BenchmarkCostTracker,
        results_dir: Path = Path("results/benchmark/manual"),
        **kwargs,
    ):
        super().__init__(
            name="bolt",
            tracker=tracker,
            results_dir=results_dir,
            **kwargs,
        )

    def get_version(self) -> str:
        return "bolt-manual-2026-02"

    def generate_function(self, prompt: str, context: str = "") -> GenerationResult:
        return GenerationResult(
            platform="bolt", task_id="", track="humaneval",
            code="", success=False,
            error="Bolt.new does not support function generation (Track 1)",
        )

    def generate_patch(self, issue: str, source_files: dict[str, str]) -> GenerationResult:
        return GenerationResult(
            platform="bolt", task_id="", track="swebench",
            code="", success=False,
            error="Bolt.new does not support bug fixing (Track 2)",
        )

    def generate_app(self, spec: str) -> GenerationResult:
        # In manual mode, this just returns a not-recorded placeholder.
        # The actual results are loaded via load_result() during benchmark execution.
        return self._not_recorded("app_gen", "unknown")

    def add_feature(self, feature_request: str, codebase: dict[str, str]) -> GenerationResult:
        return GenerationResult(
            platform="bolt", task_id="", track="feature",
            code="", success=False,
            error="Bolt.new does not support feature addition (Track 4)",
        )
