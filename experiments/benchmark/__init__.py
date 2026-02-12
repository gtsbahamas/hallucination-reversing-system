"""Cross-platform AI code quality benchmark suite.

Harness modules:
  - config: BenchmarkConfig, PlatformConfig, TrackConfig
  - runner: Main benchmark runner (run_benchmark)
  - evaluator: Unified evaluation for all 4 tracks
  - lucid_verify: LUCID verification integration
  - cost_tracker: Budget and cost tracking
  - adapters/: Platform-specific adapters (cursor, copilot, bolt, lovable, replit)
"""
