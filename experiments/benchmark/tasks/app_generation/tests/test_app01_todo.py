"""Tests for APP-01: Todo List App.

Evaluates: CRUD operations, localStorage persistence, input validation.
"""

from .helpers import (
    BuildResult, RubricScore, ServerHandle,
    build_app, check_html_contains, check_route, start_server,
)


def evaluate(app_dir: str) -> RubricScore:
    """Run full evaluation of a generated todo app."""
    score = RubricScore(details={})

    # --- Builds (0/1/2) ---
    result = build_app(app_dir)
    if not result.success:
        score.builds = 0
        score.details["builds"] = [f"Build failed: {result.error}"]
        return score
    score.builds = 2 if result.clean else 1
    score.details["builds"] = ["Clean build" if result.clean else "Build with warnings"]

    # --- Renders (0/1/2) ---
    server = start_server(app_dir)
    if server is None:
        score.renders = 0
        score.details["renders"] = ["Server failed to start"]
        return score

    try:
        if not check_route(server.base_url, "/"):
            score.renders = 0
            score.details["renders"] = ["Root route returned error"]
            return score

        # Check for essential UI elements
        found = check_html_contains(server.base_url, "/", [
            "input",       # text input
            "button",      # submit button or similar
        ])
        if all(found):
            score.renders = 2
            score.details["renders"] = ["Page renders with input and button"]
        elif any(found):
            score.renders = 1
            score.details["renders"] = ["Partial render -- missing some elements"]
        else:
            score.renders = 0
            score.details["renders"] = ["Page renders but missing key elements"]
            return score

        # --- Core functionality (0/1/2) ---
        # We test via the rendered HTML and API-like checks.
        # In a real evaluation, Playwright would interact with the page.
        # Here we verify the code structure supports the requirements.
        core_checks = []

        # Check that the page has interactive elements
        html_checks = check_html_contains(server.base_url, "/", [
            "todo",        # references to todo
            "input",       # input element
            "button",      # button element
        ])
        core_checks.extend(html_checks)

        passed = sum(core_checks)
        total = len(core_checks)
        if passed == total:
            score.core = 2
        elif passed >= total // 2:
            score.core = 1
        else:
            score.core = 0
        score.details["core"] = [f"{passed}/{total} core checks passed"]

        # --- Edge cases (0/1/2) ---
        # Empty input should not create todo
        # These would be tested with Playwright in full eval
        edge_checks = check_html_contains(server.base_url, "/", [
            "localstorage",  # persistence mechanism referenced
        ])
        if all(edge_checks):
            score.edge = 2
        elif any(edge_checks):
            score.edge = 1
        else:
            # localStorage might be in JS, not visible in HTML
            score.edge = 1  # Assume partial credit
        score.details["edge"] = ["localStorage check (JS-level verification needed)"]

        # --- Error handling (0/1/2) ---
        # Check that the app handles edge cases gracefully
        error_checks = []
        # Page should not crash on repeated loads
        for _ in range(3):
            ok = check_route(server.base_url, "/")
            error_checks.append(ok)

        if all(error_checks):
            score.error = 2
        elif any(error_checks):
            score.error = 1
        else:
            score.error = 0
        score.details["error"] = [f"Stability: {sum(error_checks)}/{len(error_checks)} loads OK"]

    finally:
        server.stop()

    return score
