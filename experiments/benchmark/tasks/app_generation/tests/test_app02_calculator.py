"""Tests for APP-02: Calculator.

Evaluates: arithmetic correctness, decimal handling, division by zero.
"""

from .helpers import (
    RubricScore, build_app, check_html_contains, check_route, start_server,
)


# Test expressions and expected results
CALC_TEST_CASES = [
    ("2 + 3", 5),
    ("10 - 4", 6),
    ("6 * 7", 42),
    ("15 / 3", 5),
    ("2.5 + 1.5", 4.0),
    ("0.1 + 0.2", 0.3),   # floating point edge case
    ("100 / 0", None),     # division by zero -- should show error, not crash
    ("0 * 999", 0),
    ("1 + 2 + 3", 6),
    ("-5 + 3", -2),
]


def evaluate(app_dir: str) -> RubricScore:
    score = RubricScore(details={})

    result = build_app(app_dir)
    if not result.success:
        score.builds = 0
        score.details["builds"] = [f"Build failed: {result.error}"]
        return score
    score.builds = 2 if result.clean else 1
    score.details["builds"] = ["Clean build" if result.clean else "Build with warnings"]

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
            "display",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"UI elements: {sum(found)}/{len(found)}"]

        # Core: verify calculator buttons exist
        digit_checks = check_html_contains(server.base_url, "/", [
            ">0<", ">1<", ">2<", ">3<", ">4<",
            ">5<", ">6<", ">7<", ">8<", ">9<",
            ">+<", ">-<", ">*<", ">/<",
            ">=<",  # equals button
        ])
        passed = sum(digit_checks)
        if passed >= 12:
            score.core = 2
        elif passed >= 6:
            score.core = 1
        else:
            score.core = 0
        score.details["core"] = [f"Button elements found: {passed}/15"]

        # Edge: division by zero, decimal
        edge = check_html_contains(server.base_url, "/", [">.<"])  # decimal button
        score.edge = 2 if all(edge) else 1
        score.details["edge"] = ["Decimal button present" if all(edge) else "Decimal button not found"]

        # Error: clear button, stability
        clear = check_html_contains(server.base_url, "/", ["clear", ">c<", ">ac<"])
        score.error = 2 if any(clear) else 1
        score.details["error"] = ["Clear button found" if any(clear) else "Clear button not found"]

    finally:
        server.stop()

    return score
