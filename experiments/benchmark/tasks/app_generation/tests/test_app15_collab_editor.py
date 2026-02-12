"""Tests for APP-15: Collaborative Text Editor.

Evaluates: rich text editing, real-time sync, cursor presence, conflict resolution.
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
            "contenteditable",
            "editor",
        ])
        score.renders = 2 if any(found) else 0
        score.details["renders"] = [f"Editor element: {sum(found)}/2"]

        # Core: formatting, websocket
        core = check_html_contains(server.base_url, "/", [
            "bold",
            "italic",
            "underline",
            "websocket",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Editor features: {passed}/4"]

        # Edge: cursor presence, CRDT/OT
        edge = check_html_contains(server.base_url, "/", [
            "cursor",
            "crdt",
            "operational transform",
        ])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Collaboration features: {sum(edge)}/3"]

        # Error: auto-save, undo
        error = check_html_contains(server.base_url, "/", ["save", "undo"])
        score.error = 2 if all(error) else (1 if any(error) else 0)
        score.details["error"] = [f"Persistence: {sum(error)}/2"]

    finally:
        server.stop()

    return score
