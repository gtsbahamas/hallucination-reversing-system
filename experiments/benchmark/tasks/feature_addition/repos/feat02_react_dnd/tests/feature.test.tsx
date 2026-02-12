/**
 * Feature tests: Drag-and-Drop Reordering.
 *
 * These tests verify drag-and-drop was correctly added.
 * They should FAIL before the feature and PASS after.
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

function addTodo(text: string) {
  const input = screen.getByTestId("todo-input");
  const addBtn = screen.getByTestId("add-btn");
  fireEvent.change(input, { target: { value: text } });
  fireEvent.click(addBtn);
}

beforeEach(() => {
  localStorageMock.clear();
});

describe("Drag-and-Drop Reordering - Feature tests", () => {
  test("todo items have draggable attribute", () => {
    render(<App />);
    addTodo("First");
    addTodo("Second");

    const list = screen.getByTestId("todo-list");
    const items = list.querySelectorAll("li");
    items.forEach((item) => {
      expect(item.getAttribute("draggable")).toBe("true");
    });
  });

  test("todo items have drag event handlers", () => {
    render(<App />);
    addTodo("First");
    addTodo("Second");

    const list = screen.getByTestId("todo-list");
    const firstItem = list.children[0] as HTMLElement;

    // Should not throw when drag events are fired
    expect(() => {
      fireEvent.dragStart(firstItem);
      fireEvent.dragOver(list.children[1] as HTMLElement);
      fireEvent.drop(list.children[1] as HTMLElement);
      fireEvent.dragEnd(firstItem);
    }).not.toThrow();
  });

  test("dragged item gets visual feedback class", () => {
    render(<App />);
    addTodo("First");
    addTodo("Second");

    const list = screen.getByTestId("todo-list");
    const firstItem = list.children[0] as HTMLElement;

    fireEvent.dragStart(firstItem);
    // After drag start, the item should have a "dragging" class or style
    expect(
      firstItem.classList.contains("dragging") ||
      firstItem.style.opacity === "0.5" ||
      firstItem.getAttribute("data-dragging") === "true"
    ).toBe(true);
  });

  test("reorder persists to localStorage", () => {
    render(<App />);
    addTodo("First");
    addTodo("Second");
    addTodo("Third");

    const list = screen.getByTestId("todo-list");
    const firstItem = list.children[0] as HTMLElement;
    const thirdItem = list.children[2] as HTMLElement;

    // Simulate drag from first to third position
    fireEvent.dragStart(firstItem);
    fireEvent.dragOver(thirdItem);
    fireEvent.drop(thirdItem);
    fireEvent.dragEnd(firstItem);

    // Check localStorage was updated
    const stored = JSON.parse(localStorageMock.getItem("todos") || "[]");
    expect(stored.length).toBe(3);
    // Order should have changed
    expect(stored.map((t: any) => t.text)).not.toEqual(["First", "Second", "Third"]);
  });

  test("completed items can also be dragged", () => {
    render(<App />);
    addTodo("Complete me");
    addTodo("Keep me");

    // Complete the first item
    const checkbox = screen.getAllByRole("checkbox")[0];
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();

    // The completed item should still be draggable
    const list = screen.getByTestId("todo-list");
    const completedItem = list.children[0] as HTMLElement;
    expect(completedItem.getAttribute("draggable")).toBe("true");
  });
});
