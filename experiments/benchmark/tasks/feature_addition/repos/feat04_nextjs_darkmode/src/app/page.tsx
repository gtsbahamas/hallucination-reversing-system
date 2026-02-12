import React from "react";
import Header from "../components/Header";
import ProjectCard from "../components/ProjectCard";

const projects = [
  {
    title: "E-commerce Platform",
    description: "Full-stack shop with Stripe integration",
    tech: ["React", "Node.js", "PostgreSQL"],
  },
  {
    title: "Task Manager",
    description: "Kanban board with real-time collaboration",
    tech: ["Next.js", "WebSocket", "Redis"],
  },
  {
    title: "API Gateway",
    description: "Rate-limited API gateway with caching",
    tech: ["Go", "Redis", "Docker"],
  },
];

export default function Home() {
  return (
    <div data-testid="page-root">
      <Header />
      <main style={{ maxWidth: "800px", margin: "2rem auto", padding: "0 1rem" }}>
        <section id="about" data-testid="about-section">
          <h2>About Me</h2>
          <p>
            Full-stack developer with 5 years of experience building web applications.
            Passionate about clean code and great user experiences.
          </p>
        </section>

        <section id="projects" data-testid="projects-section">
          <h2>Projects</h2>
          {projects.map((p) => (
            <ProjectCard key={p.title} {...p} />
          ))}
        </section>

        <section id="contact" data-testid="contact-section">
          <h2>Contact</h2>
          <p>Email: jane@developer.com</p>
        </section>
      </main>
    </div>
  );
}
