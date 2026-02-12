"""Tests for APP-09: Kanban Board.

Evaluates: columns, cards, drag-and-drop, persistence.
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

        # Check for column labels
        columns = check_html_contains(server.base_url, "/", [
            "to do", "in progress", "done",
        ])
        score.renders = 2 if sum(columns) >= 2 else (1 if any(columns) else 0)
        score.details["renders"] = [f"Columns found: {sum(columns)}/3"]

        # Core: add card, drag-and-drop
        core = check_html_contains(server.base_url, "/", [
            "add",
            "drag",
            "card",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 2 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Core features: {passed}/3"]

        # Edge: localStorage persistence
        edge = check_html_contains(server.base_url, "/", ["localstorage", "persist"])
        score.edge = 2 if any(edge) else 1
        score.details["edge"] = ["Persistence reference found" if any(edge) else "No persistence reference"]

        # Error: stability
        stable = all(check_route(server.base_url, "/") for _ in range(3))
        score.error = 2 if stable else 1
        score.details["error"] = ["Stable" if stable else "Intermittent"]

    finally:
        server.stop()

    return score
