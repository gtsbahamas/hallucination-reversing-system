"""Tests for APP-13: Multi-step Form Wizard.

Evaluates: step navigation, validation, data persistence, review step.
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
            "button",
            "step",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Wizard UI: {sum(found)}/3"]

        # Core: form fields, navigation
        core = check_html_contains(server.base_url, "/", [
            "name",
            "email",
            "next",
            "step 1",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Form elements: {passed}/4"]

        # Edge: back button, progress indicator
        edge = check_html_contains(server.base_url, "/", [
            "back",
            "previous",
            "progress",
        ])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Navigation: {sum(edge)}/3"]

        # Error: validation
        error = check_html_contains(server.base_url, "/", [
            "required",
            "valid",
            "submit",
        ])
        score.error = 2 if sum(error) >= 2 else (1 if any(error) else 0)
        score.details["error"] = [f"Validation: {sum(error)}/3"]

    finally:
        server.stop()

    return score
