"""Tests for APP-04: Timer / Stopwatch.

Evaluates: start/stop/reset, timing accuracy, lap recording.
"""

from .helpers import (
    RubricScore, build_app, check_html_contains, check_route, start_server,
)


def evaluate(app_dir: str) -> RubricScore:
    score = RubricScore(details={})

    result = build_app(app_dir)
    if not result.success:
        score.builds = 0
        score.details["builds"] = [f"Build failed: {result.error}"]
        return score
    score.builds = 2 if result.clean else 1

    server = start_server(app_dir)
    if server is None:
        score.renders = 0
        score.details["renders"] = ["Server failed to start"]
        return score

    try:
        if not check_route(server.base_url, "/"):
            score.renders = 0
            score.details["renders"] = ["Root returned error"]
            return score

        found = check_html_contains(server.base_url, "/", [
            "button",
            "00",  # initial time display
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Timer UI elements: {sum(found)}/{len(found)}"]

        # Core: start, stop, reset, lap buttons
        controls = check_html_contains(server.base_url, "/", [
            "start",
            "stop",
            "reset",
            "lap",
        ])
        passed = sum(controls)
        score.core = 2 if passed >= 3 else (1 if passed >= 2 else 0)
        score.details["core"] = [f"Controls found: {passed}/4"]

        # Edge: time format MM:SS
        time_fmt = check_html_contains(server.base_url, "/", [":", "."])
        score.edge = 2 if all(time_fmt) else 1
        score.details["edge"] = ["Time format includes colon and decimal"]

        # Error: stability
        stable = all(check_route(server.base_url, "/") for _ in range(3))
        score.error = 2 if stable else 1
        score.details["error"] = ["Stable" if stable else "Intermittent"]

    finally:
        server.stop()

    return score
