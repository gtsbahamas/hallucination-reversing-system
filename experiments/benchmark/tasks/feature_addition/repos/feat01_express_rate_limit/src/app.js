const express = require("express");

const app = express();
app.use(express.json());

// In-memory data store
const items = [
  { id: 1, name: "Widget", price: 9.99 },
  { id: 2, name: "Gadget", price: 24.99 },
  { id: 3, name: "Doohickey", price: 4.99 },
];
let nextId = 4;

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// List all items
app.get("/api/items", (req, res) => {
  res.json(items);
});

// Get single item
app.get("/api/items/:id", (req, res) => {
  const item = items.find((i) => i.id === parseInt(req.params.id));
  if (!item) return res.status(404).json({ error: "Item not found" });
  res.json(item);
});

// Create item
app.post("/api/items", (req, res) => {
  const { name, price } = req.body;
  if (!name || price === undefined) {
    return res.status(400).json({ error: "name and price are required" });
  }
  const item = { id: nextId++, name, price: parseFloat(price) };
  items.push(item);
  res.status(201).json(item);
});

// Update item
app.put("/api/items/:id", (req, res) => {
  const item = items.find((i) => i.id === parseInt(req.params.id));
  if (!item) return res.status(404).json({ error: "Item not found" });
  if (req.body.name) item.name = req.body.name;
  if (req.body.price !== undefined) item.price = parseFloat(req.body.price);
  res.json(item);
});

// Delete item
app.delete("/api/items/:id", (req, res) => {
  const idx = items.findIndex((i) => i.id === parseInt(req.params.id));
  if (idx === -1) return res.status(404).json({ error: "Item not found" });
  items.splice(idx, 1);
  res.status(204).send();
});

// Only start server if this file is run directly
if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => console.log(`Server on port ${PORT}`));
}

module.exports = app;
