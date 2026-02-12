"""Feature tests: Markdown Support for Posts.

These tests verify that Markdown rendering was correctly added.
They should FAIL before the feature and PASS after.
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_post_with_heading_renders_h1(client):
    """Markdown headings should render as HTML h1 tags."""
    resp = client.post(
        "/api/posts",
        json={"title": "MD Test", "content": "# This is a heading"},
    )
    assert resp.status_code == 201
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    # The response should include rendered HTML
    assert "content_html" in data or "html" in data or "<h1>" in data.get("content", "")
    html_content = data.get("content_html") or data.get("html") or data.get("content", "")
    assert "<h1>" in html_content


def test_post_with_bold_renders_strong(client):
    """Bold markdown should render as <strong> tags."""
    resp = client.post(
        "/api/posts",
        json={"title": "Bold Test", "content": "This is **bold** text"},
    )
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    html_content = data.get("content_html") or data.get("html") or data.get("content", "")
    assert "<strong>" in html_content


def test_post_with_link_renders_anchor(client):
    """Links should render as <a> tags."""
    resp = client.post(
        "/api/posts",
        json={"title": "Link Test", "content": "Visit [Example](http://example.com)"},
    )
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    html_content = data.get("content_html") or data.get("html") or data.get("content", "")
    assert "<a " in html_content
    assert "http://example.com" in html_content


def test_post_with_code_block_renders_code(client):
    """Code blocks should render as <code> or <pre> tags."""
    content = "Here is code:\n```\nprint('hello')\n```"
    resp = client.post(
        "/api/posts",
        json={"title": "Code Test", "content": content},
    )
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    html_content = data.get("content_html") or data.get("html") or data.get("content", "")
    assert "<code>" in html_content or "<pre>" in html_content


def test_raw_markdown_preserved_in_content_field(client):
    """The raw content field should still contain the original Markdown."""
    resp = client.post(
        "/api/posts",
        json={"title": "Raw MD", "content": "# Heading\n**bold**"},
    )
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    # Either content still has raw MD, or there's a separate raw field
    raw = data.get("content_raw") or data.get("content", "")
    assert "# Heading" in raw or "**bold**" in raw


def test_xss_prevention_in_rendered_html(client):
    """Script tags in Markdown should be sanitized."""
    resp = client.post(
        "/api/posts",
        json={"title": "XSS Test", "content": "<script>alert('xss')</script>"},
    )
    post_id = resp.get_json()["id"]

    resp = client.get(f"/api/posts/{post_id}")
    data = resp.get_json()
    html_content = data.get("content_html") or data.get("html") or data.get("content", "")
    # The rendered HTML should NOT contain raw script tags
    assert "<script>" not in html_content
