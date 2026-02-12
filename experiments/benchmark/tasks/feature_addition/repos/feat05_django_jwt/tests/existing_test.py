"""Existing tests for the Django REST API.
These must continue to pass after JWT auth is added.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestItemsAPI:
    def test_list_items(self, api_client):
        resp = api_client.get("/api/items/")
        assert resp.status_code == 200

    def test_create_item(self, api_client):
        resp = api_client.post(
            "/api/items/",
            {"name": "Widget", "price": "9.99"},
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["name"] == "Widget"

    def test_get_single_item(self, api_client):
        create = api_client.post(
            "/api/items/",
            {"name": "Gadget", "price": "24.99"},
            format="json",
        )
        item_id = create.data["id"]
        resp = api_client.get(f"/api/items/{item_id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == "Gadget"

    def test_update_item(self, api_client):
        create = api_client.post(
            "/api/items/",
            {"name": "Old Name", "price": "5.00"},
            format="json",
        )
        item_id = create.data["id"]
        resp = api_client.put(
            f"/api/items/{item_id}/",
            {"name": "New Name", "price": "7.50"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["name"] == "New Name"

    def test_delete_item(self, api_client):
        create = api_client.post(
            "/api/items/",
            {"name": "Delete Me", "price": "1.00"},
            format="json",
        )
        item_id = create.data["id"]
        resp = api_client.delete(f"/api/items/{item_id}/")
        assert resp.status_code == 204
