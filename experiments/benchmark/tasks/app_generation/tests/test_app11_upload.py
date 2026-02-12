"""Tests for APP-11: File Upload and Preview.

Evaluates: upload, preview, file type validation, size limits.
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
            "input",
            "upload",
            "file",
        ])
        score.renders = 2 if sum(found) >= 2 else (1 if any(found) else 0)
        score.details["renders"] = [f"Upload UI: {sum(found)}/3"]

        # Core: file input, drag-and-drop zone, preview
        core = check_html_contains(server.base_url, "/", [
            "type=\"file\"",
            "drag",
            "drop",
            "preview",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Core features: {passed}/4"]

        # Edge: file type restrictions, size limit
        edge = check_html_contains(server.base_url, "/", [
            "accept",
            "5mb",
            "size",
            "jpg",
            "png",
            "pdf",
        ])
        score.edge = 2 if sum(edge) >= 3 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Validation features: {sum(edge)}/6"]

        # Error: rejection messages
        error = check_html_contains(server.base_url, "/", ["error", "invalid", "too large"])
        score.error = 2 if any(error) else 1
        score.details["error"] = ["Error messages found" if any(error) else "No error messages"]

    finally:
        server.stop()

    return score
