# Show HN Draft

**Title:** Show HN: LUCID – Catch hallucinations in AI-generated code before they ship

**URL:** https://github.com/gtsbahamas/hallucination-reversing-system

---

**Body:**

Hi HN, I'm Ty. I built LUCID because I kept shipping bugs that my AI coding assistant hallucinated into existence.

Three independent papers have proven that LLM hallucination is mathematically inevitable (Xu et al. 2024, Banerjee et al. 2024, Karpowicz 2025). You can't train it away. You can't prompt it away. So I built a verification layer instead.

**How it works:** LUCID extracts implicit claims from AI-generated code (e.g., "this function handles null input," "this query is injection-safe," "this handles concurrent access"), then uses a second, adversarial AI pass to verify each claim against the actual implementation. You get a report showing exactly what would have shipped to production without verification.

**"But can't the verifier hallucinate too?"** Yes — and that's the right question. The benchmarks below were validated by running real test suites, not by trusting LUCID's judgment. The value is that structured claim extraction + adversarial verification catches bugs that a single generation pass misses. The architecture also supports swapping LLM verification for formal methods (SMT solvers, property-based testing) per claim type as those integrations mature.

**Benchmarks:**

- HumanEval: 86.6% baseline → 100% pass@5 with LUCID (164/164 problems)
- SWE-bench: 18.3% baseline → 30.3% with LUCID (+65.5%)
- Both benchmarks were validated by running actual test suites, not by LLM judgment
- LLM-as-judge actually performs worse at higher k values — it hallucinates false positives

**Three ways to use it:**

1. **MCP Server** (Claude Code, Cursor, Windsurf) — one config line, verification as a native tool:
   ```json
   { "mcpServers": { "lucid": { "command": "npx", "args": ["-y", "lucid-mcp"], "env": { "LUCID_API_KEY": "your_key" } } } }
   ```

2. **GitHub Action** — automated verification on every PR with inline comments

3. **CLI** — `npx lucid verify --repo /path/to/code`

Free tier: 100 verifications/month. Get a key at https://trylucid.dev

The neuroscience angle: LUCID is based on predictive processing (Friston, Seth). Hallucination and perception are the same generative process under different constraint levels. LUCID deliberately operates unconstrained during generation, then progressively constrains through verification — just as the brain does. The name comes from lucid dreaming: maintaining metacognitive awareness while remaining inside the generative process.

Curious what HN thinks about the approach. The conventional wisdom is to suppress hallucination. We think that's fighting thermodynamics. And yes, we know the verifier is also an LLM — the roadmap includes plugging in real formal methods for specific claim types. The structured claim extraction is the foundation that makes that possible.

Code: https://github.com/gtsbahamas/hallucination-reversing-system
Paper: https://doi.org/10.5281/zenodo.18522644
Dashboard: https://trylucid.dev
