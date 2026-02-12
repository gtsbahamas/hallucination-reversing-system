"""Tests for APP-06: Weather Dashboard.

Evaluates: search, data display, 5-day forecast, error handling.
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
            "input",      # search input
            "search",     # search label or placeholder
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Search UI: {sum(found)}/{len(found)}"]

        # Core: weather data display elements
        core = check_html_contains(server.base_url, "/", [
            "temperature",
            "humidity",
            "wind",
            "forecast",
        ])
        # Some might be rendered only after search, so be lenient
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Weather elements: {passed}/4"]

        # Edge: loading state, units
        edge = check_html_contains(server.base_url, "/", ["loading", "celsius", "fahrenheit", "°"])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Edge features: {sum(edge)}/4"]

        # Error handling: invalid city handling, network errors
        error = check_html_contains(server.base_url, "/", ["error", "not found", "try again"])
        score.error = 2 if any(error) else 1
        score.details["error"] = ["Error handling text found" if any(error) else "No error text in HTML"]

    finally:
        server.stop()

    return score
