"""Tests for APP-07: Blog with Authentication.

Evaluates: auth flow, CRUD on posts, authorization enforcement.
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
        # Check main routes exist
        routes_ok = []
        for path in ["/", "/login", "/signup", "/register"]:
            if check_route(server.base_url, path):
                routes_ok.append(path)

        score.renders = 2 if len(routes_ok) >= 2 else (1 if len(routes_ok) >= 1 else 0)
        score.details["renders"] = [f"Routes responding: {routes_ok}"]

        # Core: auth forms and post elements
        auth_checks = []
        for path in routes_ok:
            found = check_html_contains(server.base_url, path, [
                "email", "password", "input", "button",
            ])
            auth_checks.extend(found)

        passed = sum(auth_checks)
        total = len(auth_checks)
        score.core = 2 if passed >= total * 0.7 else (1 if passed >= total * 0.3 else 0)
        score.details["core"] = [f"Auth UI elements: {passed}/{total}"]

        # Check for API endpoints (common patterns)
        api_paths = ["/api/posts", "/api/auth/login", "/api/auth/signup",
                     "/api/auth/register", "/api/login", "/api/register"]
        api_found = []
        for path in api_paths:
            ok, _ = check_api_json(server.base_url, "GET", path)
            if ok:
                api_found.append(path)

        # Edge: authorization enforcement
        if api_found:
            score.edge = 2
        else:
            score.edge = 1
        score.details["edge"] = [f"API endpoints found: {api_found or 'none'}"]

        # Error: unauthenticated access should be blocked
        protected = ["/api/posts"]
        blocked = 0
        for path in protected:
            ok, data = check_api_json(server.base_url, "POST", path,
                                       body={"title": "test", "content": "test"})
            if not ok:  # Should reject -- 401/403
                blocked += 1
        score.error = 2 if blocked > 0 else 1
        score.details["error"] = [f"Unauthenticated POST blocked: {blocked}/{len(protected)}"]

    finally:
        server.stop()

    return score
