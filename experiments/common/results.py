"""Result storage and loading for benchmark experiments."""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class TaskResult:
    task_id: str
    condition: str
    max_iterations: int
    model: str
    final_passed: bool
    final_test_output: dict
    iterations: list[dict]
    ablation: Optional[str] = None
    solution: Optional[str] = None


class ResultStore:
    """Manages saving and loading experiment results."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _result_path(self, task_id: str, condition: str, max_iter: int, ablation: Optional[str] = None) -> Path:
        suffix = f"_{ablation}" if ablation else ""
        safe_id = task_id.replace("/", "_")
        return self.output_dir / f"{safe_id}_{condition}_k{max_iter}{suffix}.json"

    def save(self, result: TaskResult) -> None:
        path = self._result_path(result.task_id, result.condition, result.max_iterations, result.ablation)
        path.write_text(json.dumps(asdict(result), indent=2))

    def exists(self, task_id: str, condition: str, max_iter: int, ablation: Optional[str] = None) -> bool:
        return self._result_path(task_id, condition, max_iter, ablation).exists()

    def load(self, task_id: str, condition: str, max_iter: int, ablation: Optional[str] = None) -> Optional[TaskResult]:
        path = self._result_path(task_id, condition, max_iter, ablation)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return TaskResult(**data)

    def load_all(self) -> list[TaskResult]:
        results = []
        for path in self.output_dir.glob("*.json"):
            if path.name == "cost_tracker.json":
                continue
            try:
                data = json.loads(path.read_text())
                results.append(TaskResult(**data))
            except (json.JSONDecodeError, TypeError):
                continue
        return results

    def load_by_condition(self, condition: str) -> list[TaskResult]:
        return [r for r in self.load_all() if r.condition == condition]

    def load_by_iterations(self, max_iter: int) -> list[TaskResult]:
        return [r for r in self.load_all() if r.max_iterations == max_iter]
