"""Tests for APP-05: Color Palette Generator.

Evaluates: color generation, hex codes, copy, lock mechanism.
"""

import re

import httpx

from .helpers import (
    RubricScore, build_app, check_html_contains, check_route, start_server,
)

HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{6}")


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

        resp = httpx.get(server.base_url, timeout=10)
        html = resp.text

        # Check for hex codes in the rendered page
        hex_codes = HEX_PATTERN.findall(html)
        has_swatches = len(hex_codes) >= 5

        score.renders = 2 if has_swatches else (1 if len(hex_codes) > 0 else 0)
        score.details["renders"] = [f"Found {len(hex_codes)} hex codes (need 5)"]

        # Core: generate button, swatches
        core_checks = check_html_contains(server.base_url, "/", [
            "generate",
            "button",
        ])
        has_hex = len(hex_codes) >= 5
        core_score_items = list(core_checks) + [has_hex]
        passed = sum(core_score_items)
        score.core = 2 if passed == len(core_score_items) else (1 if passed > 0 else 0)
        score.details["core"] = [f"Core checks: {passed}/{len(core_score_items)}"]

        # Edge: lock mechanism
        lock_checks = check_html_contains(server.base_url, "/", ["lock"])
        score.edge = 2 if any(lock_checks) else 1
        score.details["edge"] = ["Lock mechanism found" if any(lock_checks) else "Lock not found"]

        # Error: all hex codes valid
        valid = all(len(h) == 7 for h in hex_codes)
        score.error = 2 if valid and hex_codes else 1
        score.details["error"] = [f"All {len(hex_codes)} hex codes valid" if valid else "Invalid hex codes"]

    finally:
        server.stop()

    return score
