"""Tests for APP-14: Dashboard with Charts.

Evaluates: chart rendering, data loading, responsiveness, date filter.
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

        # Check for chart library artifacts (canvas, svg, chart containers)
        found = check_html_contains(server.base_url, "/", [
            "canvas",
            "chart",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Chart rendering: {sum(found)}/2"]

        # Core: multiple chart types
        core = check_html_contains(server.base_url, "/", [
            "bar",
            "line",
            "pie",
            "legend",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Chart types: {passed}/4"]

        # Edge: date filter, tooltips
        edge = check_html_contains(server.base_url, "/", [
            "date",
            "filter",
            "tooltip",
        ])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Interactivity: {sum(edge)}/3"]

        # Error: responsive viewport
        error = check_html_contains(server.base_url, "/", [
            "viewport",
            "responsive",
        ])
        score.error = 2 if any(error) else 1
        score.details["error"] = ["Responsive meta tag found" if any(error) else "No responsive tag"]

    finally:
        server.stop()

    return score
