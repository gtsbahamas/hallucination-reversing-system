"""Tests for APP-10: Chat Interface with WebSocket.

Evaluates: real-time messaging, username, typing indicator.
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
            "send",
            "message",
        ])
        score.renders = 2 if all(found) else (1 if any(found) else 0)
        score.details["renders"] = [f"Chat UI: {sum(found)}/3"]

        # Core: message input, send, username
        core = check_html_contains(server.base_url, "/", [
            "username",
            "message",
            "send",
            "websocket",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Core features: {passed}/4"]

        # Edge: typing indicator
        edge = check_html_contains(server.base_url, "/", ["typing", "is typing"])
        score.edge = 2 if any(edge) else 1
        score.details["edge"] = ["Typing indicator found" if any(edge) else "No typing indicator"]

        # Error: disconnect handling
        error = check_html_contains(server.base_url, "/", ["disconnect", "reconnect", "connection"])
        score.error = 2 if any(error) else 1
        score.details["error"] = ["Connection handling found" if any(error) else "No connection handling"]

    finally:
        server.stop()

    return score
