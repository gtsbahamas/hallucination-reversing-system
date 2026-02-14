# LUCID — Indie Hackers Post

> **DRAFT — DO NOT POST WITHOUT HUMAN APPROVAL**
> Prepared: 2026-02-11

---

## Title

**I spent $466 proving that AI coding tools ship broken code — here's what I found**

---

## Post

I've been building with AI coding tools for months. Bolt.new, Lovable, Replit, Cursor — the whole stack. And I kept hitting the same problem.

**Everything compiles. Everything looks great. But features are quietly broken.**

Analytics dashboards showing hardcoded numbers. Auth guards that are imported but never connected. API endpoints that the frontend calls but the backend never implements. A README that says "FULLY OPERATIONAL" while 5 of 6 features are decorative.

I'm a developer, so I did what developers do — I built a tool to catch it.

### The verification gap

I call it the "verification gap" — the space between code that *looks right* and code that *is right*. Traditional tools don't catch it:

- **TypeScript?** Types are correct. Logic is wrong.
- **ESLint?** Style is clean. Features are missing.
- **Visual review?** The charts render beautifully. The data is fake.

So I built LUCID — an adversarial verification system that extracts every testable claim from a codebase and verifies whether it's actually true.

### The benchmark journey

I wanted data, not opinions. So I ran real benchmarks.

**Phase 1: HumanEval** (164 coding tasks, standard academic benchmark)
- Cost: $220
- Baseline: 86.6% pass rate
- With LUCID verification: **100% at k=3**

The interesting part: I also tested the approaches everyone else uses.
- "Self-refine" (just ask the AI to try again): 87.2%. Barely moves.
- "LLM-as-judge" (ask another model to review): Starts at 98.2%, then **drops to 97.2% at k=5**. More review = worse code. The judge introduces false positives, and the generator "fixes" working code.

Only adversarial verification converges monotonically. Every iteration makes it better, never worse.

**Phase 2: SWE-bench** (300 real GitHub bug-fix tasks)
- Cost: $246 (ran on EC2 — c5.9xlarge, 36 vCPUs)
- Baseline: 18.3% resolved
- With LUCID: **30.3% resolved** (+65.5% relative improvement)
- The first run on my laptop was garbage — 70-95% Docker errors. Had to re-run the whole thing on EC2 to get clean data. That was a fun $135 lesson.

**Phase 3: Real AI-built apps** (4 production codebases from GitHub)
- Cost: ~$6.50
- Average health score: **40/100**
- **21 critical bugs** across Bolt.new, Lovable, and Replit apps
- Worst finding: a healthcare app with IDOR vulnerabilities (any therapist can view any other therapist's patient data)

**Total spent on benchmarks: ~$466.** Worth every penny for the dataset.

### What I learned

1. **Simple tasks are fine.** Todo apps score 100%. The problem starts with real complexity.

2. **"Scaffolding as features" is the killer pattern.** AI generates professional-looking UI backed by nothing. Charts with hardcoded data. Buttons with empty onClick handlers. It passes every visual review.

3. **More AI review makes things worse.** This was the biggest surprise. LLM-as-judge *regresses* after 5 iterations. The industry's main approach to code quality actually degrades it.

4. **Adversarial verification is the only thing that converges.** Not because it's fancy — because the verifier is a separate AI that systematically checks the generator's output against extracted specifications. The adversarial loop catches errors that self-review misses, and empirically it converges where other approaches regress.

### Where it stands now

- **Patent filed:** App #63/980,048 (provisional, just filed today)
- **Published:** DOI 10.5281/zenodo.18522644
- **CHI 2026:** Submitted to Tools for Thought workshop
- **API:** Live at https://lucid-api-dftr.onrender.com
- **Website:** https://trylucid.dev
- **Revenue:** $0 (keeping it real)

The plan: get AI coding platforms to integrate verification into their pipelines. I'm approaching Cursor, Bolt.new, Lovable, and Replit with the benchmark data. Usage-based API pricing — free tier at 100 calls/month, starts at $0.04/call.

### The business angle

If you're building with AI coding tools, you've hit this problem. You just might not know it yet. The code looks done. The demo works. Then a user finds the feature that's actually hardcoded data, or the auth route that anyone can access.

I'm offering free verification audits for anyone who wants to try it. Send me your repo, I'll run LUCID on it and send you the report. No charge, no strings. I want the data and you want the bugs found.

Full benchmark report: https://trylucid.dev/report
GitHub: https://github.com/gtsbahamas/hallucination-reversing-system

Would love to hear from anyone else who's noticed this pattern. Is the verification gap something you've run into?
