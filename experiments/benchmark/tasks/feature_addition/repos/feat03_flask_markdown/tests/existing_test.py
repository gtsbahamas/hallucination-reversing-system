"""Existing tests for the Flask blog API.
These must continue to pass after Markdown support is added.
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_list_posts(client):
    resp = client.get("/api/posts")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_single_post(client):
    resp = client.get("/api/posts/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Hello World"


def test_create_post(client):
    resp = client.post(
        "/api/posts",
        json={"title": "New Post", "content": "Some content", "author": "tester"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "New Post"
    assert data["id"] is not None


def test_create_post_requires_fields(client):
    resp = client.post("/api/posts", json={"title": "No Content"})
    assert resp.status_code == 400


def test_get_missing_post(client):
    resp = client.get("/api/posts/99999")
    assert resp.status_code == 404
