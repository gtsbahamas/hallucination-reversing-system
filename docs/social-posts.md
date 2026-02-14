# LUCID Social Media Posts

---

## Twitter/X Thread

**Tweet 1 (Hook):**

I built an AI tool using Claude. Then I ran my tool on the code Claude wrote.

It found 24 bugs — including a critical security vulnerability that would have let anyone read any file on your computer.

The code compiled clean. TypeScript passed. Every check said "ship it."

Thread:

**Tweet 2 (Problem):**

Three independent papers have proven that AI hallucination is mathematically inevitable.

You can't fine-tune it away (we tried — more training data made it WORSE).
You can't prompt it away.
You can't test it away — the tests pass because the AI hallucinates those too.

**Tweet 3 (Solution):**

So I built LUCID — a verification layer that extracts the implicit claims AI makes about code ("this handles null input," "this is injection-safe") and verifies each one against the actual implementation.

It catches what the AI is confident about but wrong on.

**Tweet 4 (Results):**

Results on standard benchmarks:

HumanEval: 86.6% → 100% (164/164 problems — perfect score)
SWE-bench: 18.3% → 30.3% (+65% more real-world bugs fixed)

LLM-as-judge actually gets WORSE at higher attempts. It hallucinates false positives. Formal verification doesn't.

**Tweet 5 (Dogfooding):**

The best proof: I used Claude to build LUCID's MCP server. Then ran LUCID on it.

24 issues found across 48 claims (50% issue rate):
- 1 CRITICAL: path traversal (read any file on disk)
- 8 HIGH: no timeouts, unbounded input, unsafe casts
- 10 MEDIUM: no graceful shutdown, brittle error handling

All fixed. Published v0.1.1.

**Tweet 6 (CTA):**

LUCID is free for 100 verifications/month.

One line to add it to Claude Code:

npx lucid-mcp

Paper: doi.org/10.5281/zenodo.18522644
Code: github.com/gtsbahamas/hallucination-reversing-system
Dashboard: trylucid.dev

---

## LinkedIn Post

Three independent research papers have proven that AI hallucination is mathematically inevitable. You cannot train it away, prompt it away, or test it away.

I decided to stop fighting thermodynamics and build a verification layer instead.

LUCID extracts the implicit claims AI makes about code — "this handles null input," "this is injection-safe," "this handles concurrent access" — and verifies each one against the actual implementation. You get a report showing exactly what would have shipped to production without verification.

Results on standard coding benchmarks:

- HumanEval: 86.6% baseline → 100% with LUCID (164/164 — perfect score)
- SWE-bench: 18.3% → 30.3% (+65% more real-world bugs fixed)
- LLM-as-judge actually performs worse at higher attempts — it hallucinates false positives

But the real proof came from dogfooding.

I used Claude to build LUCID's own MCP server — a plugin that gives Claude Code, Cursor, and Windsurf real-time verification. Then I ran LUCID on the code Claude wrote.

It found 24 bugs across 48 claims. A 50% issue rate.

Including a critical security vulnerability that would have let any user read any file on your computer — passwords, SSH keys, environment secrets. The code compiled clean. TypeScript was happy. Every automated check said "ship it."

LUCID caught it. Fixed in v0.1.1 before a single user was affected.

We also tried the opposite approach: fine-tuning models to hallucinate less. We ran RLVF (Reinforcement Learning from Verification Feedback) experiments on StarCoder2. The result? More training data made the model WORSE. 120 curated pairs outperformed 2,000 automated pairs. At 2K pairs on the 3B model, performance collapsed entirely.

This confirms the thesis: you cannot bake verification into the model. It must remain an external layer. Which means every AI-generated line of code needs verification — permanently.

The neuroscience angle: LUCID is based on predictive processing theory (Karl Friston, Anil Seth). Hallucination and perception are the same generative process under different constraint levels. LUCID deliberately operates unconstrained during generation, then progressively constrains through verification — the same loop the brain uses. The name comes from lucid dreaming: maintaining metacognitive awareness while remaining inside the generative process.

LUCID is free for developers (100 verifications/month). One config line adds it to Claude Code:

npx lucid-mcp

Paper: https://doi.org/10.5281/zenodo.18522644
Code: https://github.com/gtsbahamas/hallucination-reversing-system
Get a free API key: https://trylucid.dev

I'm building this as a solo founder. If you're working on AI code generation, developer tools, or AI safety — I'd love to connect.

#AI #DeveloperTools #CodeVerification #LLM #AISafety #OpenSource

---

## School Community Post

Hey everyone — I wanted to share something I've been working on.

If you've used ChatGPT, Claude, or Copilot to help write code, you've probably noticed they sometimes get things wrong. They sound confident, the code looks right, it compiles and runs — but there's a subtle bug hiding in it. Researchers call this "hallucination," and three independent papers have now proven it's mathematically inevitable. No matter how much better AI models get, they will always hallucinate.

That got me thinking: if you can't stop AI from making things up, can you at least catch it?

That's what LUCID does. It's a verification layer that sits between AI-generated code and production. Instead of asking "is this code correct?" (which another AI would just hallucinate an answer to), LUCID extracts every implicit claim the code makes — things like "this function handles empty input" or "this query is safe from injection attacks" — and formally verifies each one.

I tested it on two standard coding benchmarks:
- HumanEval: improved from 86.6% to a perfect 100% (164 out of 164 problems)
- SWE-bench (real GitHub bugs): +65% more bugs fixed

But my favorite result came from eating my own cooking.

I used Claude to build LUCID's plugin for coding tools. Then I ran LUCID on the code Claude wrote for me. It found 24 bugs — including a critical security vulnerability that would have let anyone read any file on your computer. Passwords, SSH keys, everything. The code compiled perfectly. No warnings. Every normal check passed.

That's the whole point of LUCID: catching the bugs that look like correct code.

I also ran an experiment trying to train the hallucination out of AI models directly. More training data actually made the model worse — confirming that verification has to stay external. You can't solve this inside the model.

The project is open source and free for developers. If anyone is interested in AI safety, developer tools, or just wants to see the research, I'm happy to talk about it:

- GitHub: github.com/gtsbahamas/hallucination-reversing-system
- Paper: doi.org/10.5281/zenodo.18522644
- Try it: trylucid.dev

---

## Carousel Slide Descriptions (for Banana Squad)

Use these as prompts in Banana Squad. Each slide should be a clean, modern infographic style — dark background (deep navy or charcoal), bold white/cyan text, minimal design, data-forward. Think Linear or Vercel aesthetic.

### Slide 1: Hook
**Prompt:** "Modern dark infographic slide with large bold text reading 'AI wrote code. Then I verified it.' Below in smaller text: '24 bugs found. 1 critical security vulnerability.' Minimal design, dark navy background, white and cyan text, no imagery, clean sans-serif typography, 1080x1080 square format"

### Slide 2: The Problem
**Prompt:** "Dark infographic slide with headline 'AI Hallucination is Mathematically Inevitable' with three citation cards below showing 'Xu et al. 2024', 'Banerjee et al. 2024', 'Karpowicz 2025' each with a small checkmark. Below the cards: 'You can't train it away. You can't prompt it away.' Minimal design, dark charcoal background, white and amber accent text, clean typography, 1080x1080"

### Slide 3: What LUCID Does
**Prompt:** "Dark infographic slide showing a simple three-step flow diagram: 'AI generates code' (arrow right) 'LUCID extracts claims' (arrow right) 'Each claim verified'. The middle step is highlighted in cyan. Below: 'Not a linter. Not tests. Verification of what AI thinks is true.' Dark navy background, glowing cyan accent, minimal geometric design, 1080x1080"

### Slide 4: HumanEval Results
**Prompt:** "Dark data visualization slide with a large progress bar going from 86.6% (labeled 'Baseline') to 100% (labeled 'LUCID', glowing cyan). Big text above: 'HumanEval: Perfect Score'. Below: '164 out of 164 problems solved. 0 errors remaining.' Dark background, white text, cyan highlight on the 100%, clean minimal style, 1080x1080"

### Slide 5: SWE-bench Results
**Prompt:** "Dark infographic slide with two horizontal bars comparing results. Top bar: '18.3% — Baseline' in muted gray. Bottom bar: '30.3% — With LUCID' in bright cyan, 1.65x longer. Large text: '+65% more real-world bugs fixed'. Subtitle: '300 real GitHub issues tested'. Dark charcoal background, clean data visualization style, 1080x1080"

### Slide 6: The Dogfooding Story
**Prompt:** "Dark infographic slide with a circular diagram showing 'Claude builds LUCID' (arrow) 'LUCID verifies Claude's code' (arrow) 'Finds 24 bugs' with the center showing '50% issue rate'. A red alert icon next to 'CRITICAL: Path traversal vulnerability'. Dark navy background, red and cyan accents, clean typography, 1080x1080"

### Slide 7: Training Can't Fix This
**Prompt:** "Dark infographic slide with a downward trending line graph. X-axis: '120 pairs, 500, 1K, 2K'. Y-axis shows accuracy declining from 91.5% down to 77.4%. Title: 'More Training Data Made It Worse'. Subtitle: 'Verification must stay external — permanently.' Dark background, red declining line, white text, minimal chart style, 1080x1080"

### Slide 8: CTA
**Prompt:** "Dark infographic slide with centered text: 'One line. Free for developers.' Below in a code-style monospace box: 'npx lucid-mcp'. Below that, three links styled as buttons: 'GitHub', 'Paper', 'trylucid.dev'. Dark navy background, cyan code box glow, white text, clean terminal aesthetic, 1080x1080"
