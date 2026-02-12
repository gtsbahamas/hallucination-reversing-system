/**
 * Feature tests: Dark Mode Toggle with Persistence.
 *
 * These tests verify dark mode was correctly added.
 * They should FAIL before the feature and PASS after.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

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

// Mock matchMedia for prefers-color-scheme
Object.defineProperty(window, "matchMedia", {
  value: jest.fn().mockImplementation((query: string) => ({
    matches: query === "(prefers-color-scheme: dark)",
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// We need to import the components that include the theme toggle
// The feature should add a ThemeToggle or ThemeProvider component
let Header: any;
let ThemeToggle: any;
let ThemeProvider: any;

beforeAll(() => {
  // Try importing the theme components -- these should exist after feature is added
  try {
    ThemeToggle = require("../src/components/ThemeToggle").default;
  } catch {
    ThemeToggle = null;
  }
  try {
    ThemeProvider = require("../src/components/ThemeProvider").default;
  } catch {
    ThemeProvider = null;
  }
  Header = require("../src/components/Header").default;
});

beforeEach(() => {
  localStorageMock.clear();
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.classList.remove("dark", "light");
});

describe("Dark Mode - Feature tests", () => {
  test("ThemeToggle component exists", () => {
    expect(ThemeToggle).not.toBeNull();
  });

  test("toggle button is rendered", () => {
    if (!ThemeToggle) throw new Error("ThemeToggle component not found");

    const Wrapper = ThemeProvider
      ? ({ children }: any) => <ThemeProvider>{children}</ThemeProvider>
      : React.Fragment;

    render(
      <Wrapper>
        <ThemeToggle />
      </Wrapper>
    );

    const toggle = screen.getByRole("button", { name: /theme|dark|light|toggle|mode/i });
    expect(toggle).toBeInTheDocument();
  });

  test("clicking toggle changes theme", () => {
    if (!ThemeToggle) throw new Error("ThemeToggle component not found");

    const Wrapper = ThemeProvider
      ? ({ children }: any) => <ThemeProvider>{children}</ThemeProvider>
      : React.Fragment;

    render(
      <Wrapper>
        <ThemeToggle />
      </Wrapper>
    );

    const toggle = screen.getByRole("button", { name: /theme|dark|light|toggle|mode/i });
    fireEvent.click(toggle);

    // After click, document should have a dark theme indicator
    const hasDark =
      document.documentElement.classList.contains("dark") ||
      document.documentElement.getAttribute("data-theme") === "dark" ||
      document.body.classList.contains("dark");

    expect(hasDark).toBe(true);
  });

  test("theme preference persists in localStorage", () => {
    if (!ThemeToggle) throw new Error("ThemeToggle component not found");

    const Wrapper = ThemeProvider
      ? ({ children }: any) => <ThemeProvider>{children}</ThemeProvider>
      : React.Fragment;

    render(
      <Wrapper>
        <ThemeToggle />
      </Wrapper>
    );

    const toggle = screen.getByRole("button", { name: /theme|dark|light|toggle|mode/i });
    fireEvent.click(toggle);

    // localStorage should have the theme preference
    const stored = localStorageMock.getItem("theme") || localStorageMock.getItem("color-mode") || localStorageMock.getItem("darkMode");
    expect(stored).toBeDefined();
    expect(stored).not.toBeNull();
  });

  test("respects system preference on first visit", () => {
    if (!ThemeToggle) throw new Error("ThemeToggle component not found");

    // matchMedia is mocked to return true for prefers-color-scheme: dark
    // On first visit (no localStorage), should default to dark

    const Wrapper = ThemeProvider
      ? ({ children }: any) => <ThemeProvider>{children}</ThemeProvider>
      : React.Fragment;

    render(
      <Wrapper>
        <ThemeToggle />
      </Wrapper>
    );

    const hasDark =
      document.documentElement.classList.contains("dark") ||
      document.documentElement.getAttribute("data-theme") === "dark" ||
      document.body.classList.contains("dark");

    expect(hasDark).toBe(true);
  });

  test("toggle shows sun or moon icon", () => {
    if (!ThemeToggle) throw new Error("ThemeToggle component not found");

    const Wrapper = ThemeProvider
      ? ({ children }: any) => <ThemeProvider>{children}</ThemeProvider>
      : React.Fragment;

    render(
      <Wrapper>
        <ThemeToggle />
      </Wrapper>
    );

    const toggle = screen.getByRole("button", { name: /theme|dark|light|toggle|mode/i });
    // Should contain a sun or moon symbol/icon/emoji/svg
    const content = toggle.innerHTML.toLowerCase();
    const hasIcon =
      content.includes("sun") ||
      content.includes("moon") ||
      content.includes("☀") ||
      content.includes("🌙") ||
      content.includes("svg") ||
      content.includes("icon");
    expect(hasIcon).toBe(true);
  });
});
