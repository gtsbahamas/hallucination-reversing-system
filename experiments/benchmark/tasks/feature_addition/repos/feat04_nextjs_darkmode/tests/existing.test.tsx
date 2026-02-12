/**
 * Existing tests for the Next.js portfolio.
 * These must continue to pass after dark mode is added.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import Header from "../src/components/Header";
import ProjectCard from "../src/components/ProjectCard";

describe("Portfolio - Existing functionality", () => {
  test("Header renders site title", () => {
    render(<Header />);
    expect(screen.getByText("Jane Developer")).toBeInTheDocument();
  });

  test("Header has navigation links", () => {
    render(<Header />);
    expect(screen.getByText("About")).toBeInTheDocument();
    expect(screen.getByText("Projects")).toBeInTheDocument();
    expect(screen.getByText("Contact")).toBeInTheDocument();
  });

  test("ProjectCard renders title and description", () => {
    render(
      <ProjectCard
        title="Test Project"
        description="A test description"
        tech={["React", "Node.js"]}
      />
    );
    expect(screen.getByText("Test Project")).toBeInTheDocument();
    expect(screen.getByText("A test description")).toBeInTheDocument();
  });

  test("ProjectCard renders tech tags", () => {
    render(
      <ProjectCard
        title="Test"
        description="Desc"
        tech={["React", "Node.js", "PostgreSQL"]}
      />
    );
    expect(screen.getByText("React")).toBeInTheDocument();
    expect(screen.getByText("Node.js")).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
  });
});
