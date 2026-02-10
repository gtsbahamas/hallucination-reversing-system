"""Token and cost tracking for benchmark experiments."""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# Pricing per million tokens (as of 2026-02)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.0},
}


@dataclass
class APICall:
    timestamp: float
    model: str
    role: str  # generate, extract, verify, remediate, regenerate
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    task_id: str
    condition: str
    iteration: int
    duration_ms: float


@dataclass
class CostTracker:
    calls: list[APICall] = field(default_factory=list)
    budget_limit: float = 500.0  # Phase 1 budget

    def record(
        self,
        model: str,
        role: str,
        input_tokens: int,
        output_tokens: int,
        task_id: str,
        condition: str,
        iteration: int,
        duration_ms: float,
    ) -> APICall:
        pricing = PRICING.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        call = APICall(
            timestamp=time.time(),
            model=model,
            role=role,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            task_id=task_id,
            condition=condition,
            iteration=iteration,
            duration_ms=duration_ms,
        )
        self.calls.append(call)
        return call

    @property
    def total_cost(self) -> float:
        return sum(c.input_cost + c.output_cost for c in self.calls)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    def cost_by_condition(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for c in self.calls:
            result[c.condition] = result.get(c.condition, 0) + c.input_cost + c.output_cost
        return result

    def cost_by_role(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for c in self.calls:
            result[c.role] = result.get(c.role, 0) + c.input_cost + c.output_cost
        return result

    def is_over_budget(self) -> bool:
        return self.total_cost > self.budget_limit

    def summary(self) -> str:
        lines = [
            f"Total cost: ${self.total_cost:.2f} / ${self.budget_limit:.2f}",
            f"Total calls: {len(self.calls)}",
            f"Total tokens: {self.total_input_tokens:,} in / {self.total_output_tokens:,} out",
            "",
            "Cost by condition:",
        ]
        for cond, cost in sorted(self.cost_by_condition().items()):
            lines.append(f"  {cond}: ${cost:.2f}")
        lines.append("")
        lines.append("Cost by role:")
        for role, cost in sorted(self.cost_by_role().items()):
            lines.append(f"  {role}: ${cost:.2f}")
        return "\n".join(lines)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "summary": {
                "total_cost": self.total_cost,
                "total_calls": len(self.calls),
                "total_input_tokens": self.total_input_tokens,
                "total_output_tokens": self.total_output_tokens,
                "cost_by_condition": self.cost_by_condition(),
                "cost_by_role": self.cost_by_role(),
            },
            "calls": [asdict(c) for c in self.calls],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "CostTracker":
        data = json.loads(path.read_text())
        tracker = cls()
        for c in data.get("calls", []):
            tracker.calls.append(APICall(**c))
        return tracker
