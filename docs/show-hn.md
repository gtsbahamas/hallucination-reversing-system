# Show HN Draft

**Title:** Show HN: LUCID – Catch hallucinations in AI-generated code before they ship

**URL:** https://github.com/gtsbahamas/hallucination-reversing-system

---

**Body:**

Hi HN, I'm Ty. I built LUCID because I kept shipping bugs that my AI coding assistant hallucinated into existence.

Three independent papers have proven that LLM hallucination is mathematically inevitable (Xu et al. 2024, Banerjee et al. 2024, Karpowicz 2025). You can't train it away. You can't prompt it away. So I built a verification layer instead.

**How it works:** LUCID extracts implicit claims from AI-generated code (e.g., "this function handles null input," "this query is injection-safe," "this handles concurrent access"), then verifies each claim against the actual implementation. You get a report showing exactly what would have shipped to production without verification.

**Benchmarks:**

- HumanEval: 86.6% baseline → 100% pass@5 with LUCID (164/164 problems)
- SWE-bench: 18.3% baseline → 30.3% with LUCID (+65.5%)
- Both benchmarks show LLM-as-judge performs worse than formal verification — it generates false positives at higher k values

**Three ways to use it:**

1. **MCP Server** (Claude Code, Cursor, Windsurf) — one config line, verification as a native tool:
   ```json
   { "mcpServers": { "lucid": { "command": "npx", "args": ["-y", "lucid-mcp"], "env": { "LUCID_API_KEY": "your_key" } } } }
   ```

2. **GitHub Action** — automated verification on every PR with inline comments

3. **CLI** — `npx lucid verify --repo /path/to/code`

Free tier: 100 verifications/month. Get a key at https://trylucid.dev

The neuroscience angle: LUCID is based on predictive processing (Friston, Seth). Hallucination and perception are the same generative process under different constraint levels. LUCID deliberately operates unconstrained during generation, then progressively constrains through verification — just as the brain does. The name comes from lucid dreaming: maintaining metacognitive awareness while remaining inside the generative process.

Curious what HN thinks about the approach. The conventional wisdom is to suppress hallucination. We think that's fighting thermodynamics.

Code: https://github.com/gtsbahamas/hallucination-reversing-system
Paper: https://doi.org/10.5281/zenodo.18522644
Dashboard: https://trylucid.dev
