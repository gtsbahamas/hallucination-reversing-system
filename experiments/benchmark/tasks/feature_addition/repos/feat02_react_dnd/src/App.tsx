import React, { useState, useEffect } from "react";
import "./App.css";

interface Todo {
  id: number;
  text: string;
  completed: boolean;
}

const STORAGE_KEY = "todos";

function loadTodos(): Todo[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveTodos(todos: Todo[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
}

export default function App() {
  const [todos, setTodos] = useState<Todo[]>(loadTodos);
  const [input, setInput] = useState("");

  useEffect(() => {
    saveTodos(todos);
  }, [todos]);

  const addTodo = () => {
    const text = input.trim();
    if (!text) return;
    setTodos((prev) => [
      ...prev,
      { id: Date.now(), text, completed: false },
    ]);
    setInput("");
  };

  const toggleTodo = (id: number) => {
    setTodos((prev) =>
      prev.map((t) => (t.id === id ? { ...t, completed: !t.completed } : t))
    );
  };

  const deleteTodo = (id: number) => {
    setTodos((prev) => prev.filter((t) => t.id !== id));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") addTodo();
  };

  const remaining = todos.filter((t) => !t.completed).length;

  return (
    <div className="app">
      <h1>Todo App</h1>
      <div className="input-row">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add a todo..."
          data-testid="todo-input"
        />
        <button onClick={addTodo} data-testid="add-btn">
          Add
        </button>
      </div>
      <p data-testid="remaining">{remaining} items remaining</p>
      <ul data-testid="todo-list">
        {todos.map((todo) => (
          <li key={todo.id} data-testid={`todo-${todo.id}`}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
              data-testid={`toggle-${todo.id}`}
            />
            <span
              style={{
                textDecoration: todo.completed ? "line-through" : "none",
              }}
            >
              {todo.text}
            </span>
            <button
              onClick={() => deleteTodo(todo.id)}
              data-testid={`delete-${todo.id}`}
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
