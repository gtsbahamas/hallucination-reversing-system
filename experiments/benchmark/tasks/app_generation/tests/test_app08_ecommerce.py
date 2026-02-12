"""Tests for APP-08: E-commerce Product Page.

Evaluates: product listing, cart operations, checkout form.
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
            "product",
            "price",
            "cart",
            "add",
        ])
        score.renders = 2 if sum(found) >= 3 else (1 if any(found) else 0)
        score.details["renders"] = [f"E-commerce elements: {sum(found)}/4"]

        # Core: product listing, cart, checkout
        core = check_html_contains(server.base_url, "/", [
            "$",           # price display
            "add to cart",
            "quantity",
            "checkout",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 3 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Core features: {passed}/4"]

        # Edge: quantity controls
        edge = check_html_contains(server.base_url, "/", [
            "increase", "decrease", "+", "-",
        ])
        score.edge = 2 if sum(edge) >= 2 else (1 if any(edge) else 0)
        score.details["edge"] = [f"Quantity controls: {sum(edge)}/4"]

        # Error: form validation
        checkout_routes = ["/checkout", "/cart"]
        checkout_found = any(check_route(server.base_url, r) for r in checkout_routes)
        score.error = 2 if checkout_found else 1
        score.details["error"] = ["Checkout route exists" if checkout_found else "No checkout route"]

    finally:
        server.stop()

    return score
