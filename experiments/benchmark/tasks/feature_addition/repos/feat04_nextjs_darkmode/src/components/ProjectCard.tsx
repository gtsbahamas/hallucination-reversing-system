import React from "react";

interface ProjectCardProps {
  title: string;
  description: string;
  tech: string[];
}

export default function ProjectCard({ title, description, tech }: ProjectCardProps) {
  return (
    <div
      data-testid="project-card"
      style={{
        border: "1px solid #ddd",
        borderRadius: "8px",
        padding: "1.5rem",
        marginBottom: "1rem",
      }}
    >
      <h3>{title}</h3>
      <p>{description}</p>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        {tech.map((t) => (
          <span
            key={t}
            style={{
              background: "#f0f0f0",
              padding: "0.25rem 0.5rem",
              borderRadius: "4px",
              fontSize: "0.85rem",
            }}
          >
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}
