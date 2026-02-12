# Express REST API

A simple Express REST API with CRUD operations on items.

## Routes

- `GET /health` -- Health check
- `GET /api/items` -- List all items
- `GET /api/items/:id` -- Get item by ID
- `POST /api/items` -- Create item (body: `{name, price}`)
- `PUT /api/items/:id` -- Update item
- `DELETE /api/items/:id` -- Delete item

## Running

```bash
npm install
npm start        # Start server on port 3000
npm test         # Run tests
```
