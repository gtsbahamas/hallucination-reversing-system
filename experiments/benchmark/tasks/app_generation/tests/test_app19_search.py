"""Tests for APP-19: Search with Autocomplete.

Evaluates: debounced search, dropdown, keyboard navigation, highlighting.
"""

from .helpers import (
    RubricScore, build_app, check_api_json, check_html_contains,
    check_route, start_server,
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
            "search",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Search UI: {sum(found)}/2"]

        # Core: search input, results area, API endpoint
        core = check_html_contains(server.base_url, "/", [
            "input",
            "search",
            "result",
        ])
        # Check for search API
        api_ok, data = check_api_json(server.base_url, "GET", "/api/search?q=test")
        api_ok2, data2 = check_api_json(server.base_url, "GET", "/search?q=test")
        has_api = api_ok or api_ok2

        passed = sum(core) + (1 if has_api else 0)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Search features: {passed}/4"]

        # Edge: debounce, keyboard nav, highlighting
        edge = check_html_contains(server.base_url, "/", [
            "debounce",
            "highlight",
            "keyboard",
            "arrow",
        ])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Advanced features: {sum(edge)}/4"]

        # Error: empty query handling
        score.error = 2 if has_api else 1
        score.details["error"] = ["API responds to search" if has_api else "No search API"]

    finally:
        server.stop()

    return score
