/**
 * Existing tests for the Express API.
 * These must continue to pass after the feature is added.
 */
const request = require("supertest");
const app = require("../src/app");

describe("Express API - Existing functionality", () => {
  test("GET /health returns 200 with status ok", async () => {
    const res = await request(app).get("/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
  });

  test("GET /api/items returns array of items", async () => {
    const res = await request(app).get("/api/items");
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
    expect(res.body.length).toBeGreaterThanOrEqual(3);
  });

  test("POST /api/items creates a new item", async () => {
    const res = await request(app)
      .post("/api/items")
      .send({ name: "Test Item", price: 12.50 });
    expect(res.status).toBe(201);
    expect(res.body.name).toBe("Test Item");
    expect(res.body.price).toBe(12.50);
    expect(res.body.id).toBeDefined();
  });

  test("POST /api/items rejects missing fields", async () => {
    const res = await request(app)
      .post("/api/items")
      .send({ name: "No Price" });
    expect(res.status).toBe(400);
  });

  test("GET /api/items/:id returns 404 for missing item", async () => {
    const res = await request(app).get("/api/items/99999");
    expect(res.status).toBe(404);
  });
});
