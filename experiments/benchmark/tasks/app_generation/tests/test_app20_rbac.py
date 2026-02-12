"""Tests for APP-20: Role-Based Access Control.

Evaluates: role assignment, admin/user dashboards, permission enforcement.
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
        # Check for login/dashboard routes
        routes = {"/": False, "/login": False, "/admin": False, "/dashboard": False}
        for r in routes:
            routes[r] = check_route(server.base_url, r)

        responding = sum(routes.values())
        score.renders = 2 if responding >= 2 else (1 if responding >= 1 else 0)
        score.details["renders"] = [f"Routes responding: {routes}"]

        # Core: role-based elements
        core_elements = []
        for path, ok in routes.items():
            if ok:
                found = check_html_contains(server.base_url, path, [
                    "admin",
                    "user",
                    "role",
                    "login",
                ])
                core_elements.extend(found)

        passed = sum(core_elements)
        total = len(core_elements)
        score.core = 2 if total > 0 and passed >= total * 0.5 else (1 if passed > 0 else 0)
        score.details["core"] = [f"RBAC elements: {passed}/{total}"]

        # Edge: admin-only functionality
        admin_api = ["/api/admin/users", "/api/users", "/admin/users"]
        admin_found = any(
            check_api_json(server.base_url, "GET", ep)[0]
            or check_api_json(server.base_url, "GET", ep)[1] is not None
            for ep in admin_api
        )
        score.edge = 2 if admin_found else 1
        score.details["edge"] = ["Admin API found" if admin_found else "No admin API"]

        # Error: unauthenticated access to admin blocked
        admin_blocked = not check_route(server.base_url, "/admin")
        score.error = 2 if admin_blocked else 1
        score.details["error"] = ["Admin route blocked" if admin_blocked else "Admin route accessible"]

    finally:
        server.stop()

    return score
