# Django REST API

A simple Django REST Framework API with CRUD operations on items.

## Endpoints

- `GET /api/items/` -- List all items
- `POST /api/items/` -- Create item (body: `{name, description, price}`)
- `GET /api/items/<id>/` -- Get item by ID
- `PUT /api/items/<id>/` -- Update item
- `DELETE /api/items/<id>/` -- Delete item

## Running

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver    # Start server on port 8000
pytest tests/                 # Run tests
```
