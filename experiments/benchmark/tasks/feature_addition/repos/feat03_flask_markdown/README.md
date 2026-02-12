# Flask Blog API

A simple Flask REST API for blog posts.

## Routes

- `GET /api/posts` -- List all posts
- `GET /api/posts/<id>` -- Get a single post
- `POST /api/posts` -- Create post (body: `{title, content, author}`)
- `PUT /api/posts/<id>` -- Update post
- `DELETE /api/posts/<id>` -- Delete post

## Running

```bash
pip install -r requirements.txt
python app.py          # Start server on port 5000
pytest tests/          # Run tests
```
