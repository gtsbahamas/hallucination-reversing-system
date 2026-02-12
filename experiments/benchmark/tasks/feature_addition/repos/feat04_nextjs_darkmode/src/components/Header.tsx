import React from "react";

export default function Header() {
  return (
    <header data-testid="header" style={{ padding: "1rem 2rem", borderBottom: "1px solid #eee" }}>
      <nav style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>Jane Developer</h1>
        <div style={{ display: "flex", gap: "1rem" }}>
          <a href="#about">About</a>
          <a href="#projects">Projects</a>
          <a href="#contact">Contact</a>
        </div>
      </nav>
    </header>
  );
}
