/**
 * Existing tests for the React Todo app.
 * These must continue to pass after drag-and-drop is added.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "../src/App";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    clear: () => { store = {}; },
    removeItem: (key: string) => { delete store[key]; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

beforeEach(() => {
  localStorageMock.clear();
});

describe("Todo App - Existing functionality", () => {
  test("renders the todo input and add button", () => {
    render(<App />);
    expect(screen.getByTestId("todo-input")).toBeInTheDocument();
    expect(screen.getByTestId("add-btn")).toBeInTheDocument();
  });

  test("adds a new todo", () => {
    render(<App />);
    const input = screen.getByTestId("todo-input");
    const addBtn = screen.getByTestId("add-btn");

    fireEvent.change(input, { target: { value: "Buy milk" } });
    fireEvent.click(addBtn);

    expect(screen.getByText("Buy milk")).toBeInTheDocument();
  });

  test("does not add empty todo", () => {
    render(<App />);
    const addBtn = screen.getByTestId("add-btn");
    fireEvent.click(addBtn);

    const list = screen.getByTestId("todo-list");
    expect(list.children.length).toBe(0);
  });

  test("toggles todo completion", () => {
    render(<App />);
    const input = screen.getByTestId("todo-input");
    const addBtn = screen.getByTestId("add-btn");

    fireEvent.change(input, { target: { value: "Test todo" } });
    fireEvent.click(addBtn);

    const checkbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  test("shows remaining count", () => {
    render(<App />);
    expect(screen.getByTestId("remaining")).toHaveTextContent("0 items remaining");

    const input = screen.getByTestId("todo-input");
    const addBtn = screen.getByTestId("add-btn");

    fireEvent.change(input, { target: { value: "Item 1" } });
    fireEvent.click(addBtn);
    expect(screen.getByTestId("remaining")).toHaveTextContent("1 items remaining");
  });

  test("deletes a todo", () => {
    render(<App />);
    const input = screen.getByTestId("todo-input");
    const addBtn = screen.getByTestId("add-btn");

    fireEvent.change(input, { target: { value: "Delete me" } });
    fireEvent.click(addBtn);

    expect(screen.getByText("Delete me")).toBeInTheDocument();

    const deleteBtn = screen.getAllByText("Delete")[0];
    fireEvent.click(deleteBtn);

    expect(screen.queryByText("Delete me")).not.toBeInTheDocument();
  });
});
