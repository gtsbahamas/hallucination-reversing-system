"""Tests for APP-18: REST API with Database.

Evaluates: CRUD endpoints, validation, status codes, pagination, search.
"""

from .helpers import (
    RubricScore, build_app, check_api_json, check_route, start_server,
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
        # For API apps, "renders" means the server responds
        api_paths = ["/api/products", "/products", "/api/v1/products"]
        api_root = None
        for path in api_paths:
            ok, data = check_api_json(server.base_url, "GET", path)
            if ok or data is not None:
                api_root = path
                break

        score.renders = 2 if api_root else 0
        score.details["renders"] = [f"API root: {api_root or 'not found'}"]

        if not api_root:
            return score

        # Core: CRUD operations
        crud_results = []

        # CREATE
        ok, data = check_api_json(
            server.base_url, "POST", api_root,
            body={"name": "Test Product", "price": 9.99, "description": "Test"},
            expect_status=201,
        )
        crud_results.append(("CREATE", ok))
        created_id = None
        if data and isinstance(data, dict):
            created_id = data.get("id") or data.get("_id")

        # READ list
        ok, data = check_api_json(server.base_url, "GET", api_root)
        crud_results.append(("READ_LIST", ok))

        # READ single
        if created_id:
            ok, data = check_api_json(server.base_url, "GET", f"{api_root}/{created_id}")
            crud_results.append(("READ_SINGLE", ok))

            # UPDATE
            ok, data = check_api_json(
                server.base_url, "PUT", f"{api_root}/{created_id}",
                body={"name": "Updated Product", "price": 19.99},
            )
            crud_results.append(("UPDATE", ok))

            # DELETE
            ok, data = check_api_json(server.base_url, "DELETE", f"{api_root}/{created_id}")
            crud_results.append(("DELETE", ok))

        passed = sum(1 for _, ok in crud_results if ok)
        total = len(crud_results)
        score.core = 2 if passed >= 4 else (1 if passed >= 2 else 0)
        score.details["core"] = [f"CRUD: {passed}/{total} - {crud_results}"]

        # Edge: pagination
        ok, data = check_api_json(server.base_url, "GET", f"{api_root}?page=1&limit=10")
        pagination_ok = ok and data is not None
        # Search
        ok, data = check_api_json(server.base_url, "GET", f"{api_root}?search=test")
        search_ok = ok and data is not None

        score.edge = 2 if pagination_ok and search_ok else (1 if pagination_ok or search_ok else 0)
        score.details["edge"] = [f"Pagination: {pagination_ok}, Search: {search_ok}"]

        # Error: validation (400 on invalid input), 404 on missing
        ok_400, _ = check_api_json(
            server.base_url, "POST", api_root,
            body={},  # Missing required fields
            expect_status=400,
        )
        ok_404, _ = check_api_json(
            server.base_url, "GET", f"{api_root}/nonexistent-id-99999",
            expect_status=404,
        )
        error_checks = sum([ok_400, ok_404])
        score.error = 2 if error_checks == 2 else (1 if error_checks >= 1 else 0)
        score.details["error"] = [f"400 on invalid: {ok_400}, 404 on missing: {ok_404}"]

    finally:
        server.stop()

    return score
