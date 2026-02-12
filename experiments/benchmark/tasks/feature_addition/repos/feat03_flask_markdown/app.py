"""Simple Flask blog application -- base repo for Markdown benchmark."""

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory post storage
posts = [
    {
        "id": 1,
        "title": "Hello World",
        "content": "This is the first post on the blog.",
        "author": "admin",
    },
    {
        "id": 2,
        "title": "Second Post",
        "content": "More content here with some details.",
        "author": "admin",
    },
]
next_id = 3


@app.route("/api/posts", methods=["GET"])
def list_posts():
    return jsonify(posts)


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404
    return jsonify(post)


@app.route("/api/posts", methods=["POST"])
def create_post():
    global next_id
    data = request.get_json()
    if not data or not data.get("title") or not data.get("content"):
        return jsonify({"error": "title and content are required"}), 400

    post = {
        "id": next_id,
        "title": data["title"],
        "content": data["content"],
        "author": data.get("author", "anonymous"),
    }
    next_id += 1
    posts.append(post)
    return jsonify(post), 201


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    post = next((p for p in posts if p["id"] == post_id), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    data = request.get_json()
    if data.get("title"):
        post["title"] = data["title"]
    if data.get("content"):
        post["content"] = data["content"]
    return jsonify(post)


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    global posts
    original_len = len(posts)
    posts = [p for p in posts if p["id"] != post_id]
    if len(posts) == original_len:
        return jsonify({"error": "Post not found"}), 404
    return "", 204


if __name__ == "__main__":
    app.run(debug=True, port=5000)
