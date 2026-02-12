"""Tests for APP-17: Payment Flow (Stripe Test Mode).

Evaluates: product selection, Stripe checkout, success/cancel handling.
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
        if not check_route(server.base_url, "/"):
            score.renders = 0
            score.details["renders"] = ["Root returned error"]
            return score

        found = check_html_contains(server.base_url, "/", [
            "product",
            "price",
            "checkout",
        ])
        score.renders = 2 if sum(found) >= 2 else (1 if any(found) else 0)
        score.details["renders"] = [f"Payment UI: {sum(found)}/3"]

        # Core: Stripe integration
        core = check_html_contains(server.base_url, "/", [
            "stripe",
            "checkout",
            "payment",
        ])
        passed = sum(core)
        score.core = 2 if passed >= 2 else (1 if passed >= 1 else 0)
        score.details["core"] = [f"Stripe features: {passed}/3"]

        # Check for success/cancel pages
        success = check_route(server.base_url, "/success")
        cancel = check_route(server.base_url, "/cancel")
        score.edge = 2 if success and cancel else (1 if success or cancel else 0)
        score.details["edge"] = [f"Success page: {success}, Cancel page: {cancel}"]

        # Error: API endpoint for checkout session
        checkout_endpoints = ["/api/checkout", "/api/create-checkout-session",
                            "/create-checkout-session"]
        api_found = any(
            check_api_json(server.base_url, "POST", ep, body={})[0]
            or check_api_json(server.base_url, "POST", ep, body={})[1] is not None
            for ep in checkout_endpoints
        )
        score.error = 2 if api_found else 1
        score.details["error"] = ["Checkout API endpoint found" if api_found else "No checkout API"]

    finally:
        server.stop()

    return score
