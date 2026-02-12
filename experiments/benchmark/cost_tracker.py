"""Budget and cost tracking for cross-platform benchmark.

Extends the existing CostTracker pattern with platform-level breakdown
and multi-track cost accounting.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class BenchmarkAPICall:
    """A single API call made during benchmarking."""
    timestamp: float
    platform: str
    track: str
    task_id: str
    role: str  # generate, lucid_verify, lucid_remediate, evaluate
    model: Optional[str]
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    duration_ms: float
    lucid_iteration: int = 0
    run_number: int = 1
    metadata: dict = field(default_factory=dict)


# Pricing per million tokens (as of 2026-02)
PRICING = {
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Platform-specific cost estimates (per generation, not per token)
    "cursor": {"per_request": 0.05},
    "bolt": {"per_request": 0.10},
    "lovable": {"per_request": 0.10},
    "replit": {"per_request": 0.15},
    "copilot": {"per_request": 0.03},
}


class BenchmarkCostTracker:
    """Track costs across platforms, tracks, and LUCID verification."""

    def __init__(self, budget_limit: float = 2000.0, chunk_id: str = ""):
        self.calls: list[BenchmarkAPICall] = []
        self.budget_limit = budget_limit
        self.chunk_id = chunk_id
        # Track platform subscription costs separately
        self.platform_fees: dict[str, float] = {}

    def record(
        self,
        platform: str,
        track: str,
        task_id: str,
        role: str,
        model: Optional[str] = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ms: float = 0,
        lucid_iteration: int = 0,
        run_number: int = 1,
        metadata: Optional[dict] = None,
    ) -> BenchmarkAPICall:
        """Record an API call and compute cost."""
        if model and model in PRICING and "input" in PRICING[model]:
            pricing = PRICING[model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
        elif platform in PRICING and "per_request" in PRICING.get(platform, {}):
            input_cost = PRICING[platform]["per_request"]
            output_cost = 0.0
        else:
            input_cost = 0.0
            output_cost = 0.0

        call = BenchmarkAPICall(
            timestamp=time.time(),
            platform=platform,
            track=track,
            task_id=task_id,
            role=role,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            duration_ms=duration_ms,
            lucid_iteration=lucid_iteration,
            run_number=run_number,
            metadata=metadata or {},
        )
        self.calls.append(call)
        return call

    def add_platform_fee(self, platform: str, amount: float) -> None:
        """Record a platform subscription fee."""
        self.platform_fees[platform] = self.platform_fees.get(platform, 0) + amount

    @property
    def total_api_cost(self) -> float:
        return sum(c.input_cost + c.output_cost for c in self.calls)

    @property
    def total_platform_fees(self) -> float:
        return sum(self.platform_fees.values())

    @property
    def total_cost(self) -> float:
        return self.total_api_cost + self.total_platform_fees

    def is_over_budget(self) -> bool:
        return self.total_cost > self.budget_limit

    def cost_by_platform(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for c in self.calls:
            result[c.platform] = result.get(c.platform, 0) + c.input_cost + c.output_cost
        # Add platform fees
        for plat, fee in self.platform_fees.items():
            result[plat] = result.get(plat, 0) + fee
        return result

    def cost_by_track(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for c in self.calls:
            result[c.track] = result.get(c.track, 0) + c.input_cost + c.output_cost
        return result

    def cost_by_role(self) -> dict[str, float]:
        result: dict[str, float] = {}
        for c in self.calls:
            result[c.role] = result.get(c.role, 0) + c.input_cost + c.output_cost
        return result

    def lucid_verification_cost(self) -> float:
        """Total cost of LUCID verification calls only."""
        return sum(
            c.input_cost + c.output_cost
            for c in self.calls
            if c.role.startswith("lucid_")
        )

    def summary(self) -> str:
        lines = [
            f"Total cost: ${self.total_cost:.2f} / ${self.budget_limit:.2f}",
            f"  API calls: ${self.total_api_cost:.2f} ({len(self.calls)} calls)",
            f"  Platform fees: ${self.total_platform_fees:.2f}",
            f"  LUCID verification: ${self.lucid_verification_cost():.2f}",
            "",
            "Cost by platform:",
        ]
        for plat, cost in sorted(self.cost_by_platform().items()):
            lines.append(f"  {plat}: ${cost:.2f}")
        lines.append("")
        lines.append("Cost by track:")
        for track, cost in sorted(self.cost_by_track().items()):
            lines.append(f"  {track}: ${cost:.2f}")
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
                "total_api_cost": self.total_api_cost,
                "total_platform_fees": self.total_platform_fees,
                "lucid_verification_cost": self.lucid_verification_cost(),
                "total_calls": len(self.calls),
                "cost_by_platform": self.cost_by_platform(),
                "cost_by_track": self.cost_by_track(),
                "cost_by_role": self.cost_by_role(),
                "budget_limit": self.budget_limit,
            },
            "platform_fees": self.platform_fees,
            "calls": [asdict(c) for c in self.calls],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "BenchmarkCostTracker":
        data = json.loads(path.read_text())
        tracker = cls()
        tracker.platform_fees = data.get("platform_fees", {})
        for c in data.get("calls", []):
            tracker.calls.append(BenchmarkAPICall(**c))
        return tracker
