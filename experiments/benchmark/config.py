"""Configuration for cross-platform AI code quality benchmark.

Defines platforms, tracks, evaluation settings, and execution parameters.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Track(Enum):
    """Benchmark tracks matching platform capabilities."""
    HUMANEVAL = "humaneval"        # Track 1: Function-level code generation
    SWEBENCH = "swebench"         # Track 2: Autonomous bug fixing
    APP_GENERATION = "app_gen"    # Track 3: Full application generation
    FEATURE_ADDITION = "feature"  # Track 4: Feature addition to existing codebase


class AdapterMode(Enum):
    """How the platform adapter operates."""
    API = "api"          # Fully automated via API
    MANUAL = "manual"    # Manual operation, results recorded after the fact
    HYBRID = "hybrid"    # API where possible, manual fallback


@dataclass
class PlatformConfig:
    """Configuration for a single platform."""
    name: str
    adapter: str  # Adapter class name (e.g., "cursor", "bolt", "copilot")
    mode: AdapterMode = AdapterMode.API
    tracks: list[Track] = field(default_factory=list)
    api_key_env: Optional[str] = None  # Environment variable for API key
    base_url: Optional[str] = None
    model: Optional[str] = None  # Underlying model if configurable
    timeout_seconds: int = 600  # Per-task timeout
    max_retries: int = 3
    rate_limit_rpm: int = 60  # Requests per minute


@dataclass
class TrackConfig:
    """Configuration for a single benchmark track."""
    track: Track
    task_dir: Optional[Path] = None  # Directory with task definitions
    dataset_name: Optional[str] = None  # For HumanEval/SWE-bench
    num_runs: int = 3  # Number of runs per task for statistical significance
    lucid_k_values: list[int] = field(default_factory=lambda: [1, 3])
    time_limit_seconds: int = 600  # Per-task time limit


@dataclass
class BenchmarkConfig:
    """Top-level benchmark configuration."""
    name: str = "State of AI Code Quality 2026"
    output_dir: Path = Path("results/benchmark")
    platforms: list[PlatformConfig] = field(default_factory=list)
    tracks: list[TrackConfig] = field(default_factory=list)
    model: str = "claude-sonnet-4-5-20250929"  # Default model for LUCID verification
    budget: float = 2000.0
    resume: bool = False
    dry_run: bool = False
    lucid_api_url: str = "https://lucid-api-dftr.onrender.com"
    chunk_id: str = ""

    @classmethod
    def default(cls) -> "BenchmarkConfig":
        """Create a default configuration with all platforms and tracks."""
        platforms = [
            PlatformConfig(
                name="Cursor",
                adapter="cursor",
                mode=AdapterMode.HYBRID,
                tracks=[Track.HUMANEVAL, Track.SWEBENCH, Track.FEATURE_ADDITION],
                timeout_seconds=600,
            ),
            PlatformConfig(
                name="Bolt.new",
                adapter="bolt",
                mode=AdapterMode.MANUAL,
                tracks=[Track.APP_GENERATION],
                base_url="https://bolt.new",
                timeout_seconds=300,
            ),
            PlatformConfig(
                name="Lovable",
                adapter="lovable",
                mode=AdapterMode.MANUAL,
                tracks=[Track.APP_GENERATION],
                base_url="https://lovable.dev",
                timeout_seconds=300,
            ),
            PlatformConfig(
                name="Replit Agent",
                adapter="replit",
                mode=AdapterMode.HYBRID,
                tracks=[Track.SWEBENCH, Track.APP_GENERATION, Track.FEATURE_ADDITION],
                api_key_env="REPLIT_API_KEY",
                timeout_seconds=1800,
            ),
            PlatformConfig(
                name="GitHub Copilot",
                adapter="copilot",
                mode=AdapterMode.HYBRID,
                tracks=[Track.HUMANEVAL, Track.FEATURE_ADDITION],
                timeout_seconds=300,
            ),
        ]

        tracks = [
            TrackConfig(
                track=Track.HUMANEVAL,
                dataset_name="HumanEval",
                num_runs=3,
                lucid_k_values=[1, 3],
                time_limit_seconds=120,
            ),
            TrackConfig(
                track=Track.SWEBENCH,
                dataset_name="SWE-bench_Lite",
                num_runs=1,  # SWE-bench is expensive, 1 run
                lucid_k_values=[1, 3],
                time_limit_seconds=1800,
            ),
            TrackConfig(
                track=Track.APP_GENERATION,
                task_dir=Path("experiments/benchmark/tasks/app_generation"),
                num_runs=1,
                lucid_k_values=[1, 3],
                time_limit_seconds=3600,
            ),
            TrackConfig(
                track=Track.FEATURE_ADDITION,
                task_dir=Path("experiments/benchmark/tasks/feature_addition"),
                num_runs=1,
                lucid_k_values=[1, 3],
                time_limit_seconds=1800,
            ),
        ]

        return cls(platforms=platforms, tracks=tracks)

    def platforms_for_track(self, track: Track) -> list[PlatformConfig]:
        """Get all platforms that support a given track."""
        return [p for p in self.platforms if track in p.tracks]

    def track_config(self, track: Track) -> Optional[TrackConfig]:
        """Get configuration for a specific track."""
        for tc in self.tracks:
            if tc.track == track:
                return tc
        return None
