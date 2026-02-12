"""Tests for APP-16: OAuth Integration.

Evaluates: OAuth flow, session management, protected routes, logout.
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
        # Check login page exists
        login_routes = ["/login", "/auth", "/"]
        login_found = None
        for r in login_routes:
            if check_route(server.base_url, r):
                login_found = r
                break

        score.renders = 2 if login_found else 0
        score.details["renders"] = [f"Login route: {login_found or 'not found'}"]

        if login_found:
            # Core: OAuth button, session endpoints
            core = check_html_contains(server.base_url, login_found, [
                "google",
                "github",
                "sign in",
                "login",
                "oauth",
            ])
            passed = sum(core)
            score.core = 2 if passed >= 2 else (1 if passed >= 1 else 0)
            score.details["core"] = [f"OAuth elements: {passed}/5"]

            # Check callback route exists
            callback_routes = ["/auth/callback", "/api/auth/callback",
                             "/auth/google/callback", "/auth/github/callback"]
            callback_found = any(
                check_route(server.base_url, r) for r in callback_routes
            )

            # Edge: CSRF, session security
            edge = check_html_contains(server.base_url, login_found, [
                "csrf",
                "token",
                "session",
            ])
            score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) or callback_found else 0)
            score.details["edge"] = [f"Security features: {sum(edge)}/3, callback: {callback_found}"]

            # Error: protected routes redirect
            protected = ["/profile", "/dashboard", "/protected"]
            redirected = 0
            for p in protected:
                if check_route(server.base_url, p):
                    redirected += 1
            score.error = 2 if redirected == 0 else (1 if redirected < len(protected) else 0)
            score.details["error"] = [f"Protected routes accessible: {redirected}/{len(protected)}"]
        else:
            score.core = 0
            score.edge = 0
            score.error = 0

    finally:
        server.stop()

    return score
