"""Tests for APP-03: Markdown Previewer.

Evaluates: real-time preview, Markdown syntax support, split-pane layout.
"""

from .helpers import (
    RubricScore, build_app, check_html_contains, check_route, start_server,
)

# Markdown test snippets and expected HTML patterns
MARKDOWN_TESTS = [
    ("# Heading 1", "<h1>"),
    ("## Heading 2", "<h2>"),
    ("**bold**", "<strong>"),
    ("*italic*", "<em>"),
    ("[link](http://example.com)", "<a "),
    ("```code```", "<code>"),
    ("- item 1", "<li>"),
    ("1. item 1", "<li>"),
    ("![alt](img.png)", "<img"),
    ("> blockquote", "<blockquote>"),
]


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
            "textarea",  # editor pane
        ])
        score.renders = 2 if all(found) else 1
        score.details["renders"] = ["Textarea found" if all(found) else "No textarea found"]

        # Core: check for markdown rendering library presence
        md_checks = check_html_contains(server.base_url, "/", [
            "textarea",
            "preview",
        ])
        passed = sum(md_checks)
        score.core = 2 if passed == len(md_checks) else (1 if passed > 0 else 0)
        score.details["core"] = [f"Markdown elements: {passed}/{len(md_checks)}"]

        # Edge: code block syntax highlighting
        code_checks = check_html_contains(server.base_url, "/", ["highlight", "prism", "hljs"])
        score.edge = 2 if any(code_checks) else 1
        score.details["edge"] = ["Syntax highlighting library detected" if any(code_checks) else "No syntax highlighting detected"]

        # Error: stability
        stable = all(check_route(server.base_url, "/") for _ in range(3))
        score.error = 2 if stable else 1
        score.details["error"] = ["Stable across reloads" if stable else "Intermittent failures"]

    finally:
        server.stop()

    return score
