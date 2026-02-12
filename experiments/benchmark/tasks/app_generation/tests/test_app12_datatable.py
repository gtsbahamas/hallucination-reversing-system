"""Tests for APP-12: Data Table with Sort/Filter/Paginate.

Evaluates: column sort, text filter, pagination, page size.
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
            "<table",
            "<th",
            "<td",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Table elements: {sum(found)}/3"]

        # Core: sort, filter, pagination
        core = check_html_contains(server.base_url, "/", [
            "sort",
            "filter",
            "search",
            "page",
            "next",
            "previous",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 4 else (1 if passed >= 2 else 0)
        score.details["core"] = [f"Table features: {passed}/6"]

        # Edge: page size selector, row count
        edge = check_html_contains(server.base_url, "/", [
            "10", "25", "50",
            "showing",
        ])
        score.edge = 2 if sum(edge) >= 3 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Pagination details: {sum(edge)}/4"]

        # Error: stability with repeated loads
        stable = all(check_route(server.base_url, "/") for _ in range(3))
        score.error = 2 if stable else 1
        score.details["error"] = ["Stable" if stable else "Intermittent"]

    finally:
        server.stop()

    return score
