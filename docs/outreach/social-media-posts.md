# Social Media Posts -- LUCID Launch
> **DRAFT -- DO NOT POST WITHOUT HUMAN APPROVAL**
> Prepared: 2026-02-14
> Carousel slides: docs/outreach/slides/slide-01.png through slide-09.png

---

## 1. Twitter/X Thread (Launch Thread)

> Attach carousel slides as noted. First tweet is the hook -- make it count.

**Tweet 1/7** (hook)
> Attach: slide-01.png (39/100 score)

We ran adversarial verification on AI-generated code from 4 production apps.

Average production-readiness score: 39/100.

The code compiled. It linted clean. It looked polished.

It was broken. Here's what we found:

---

**Tweet 2/7**
> Attach: slide-03.png (features that don't exist)

Finding #1: Features that don't exist.

Frontend calls API endpoints that were never built. Analytics dashboards backed by hardcoded arrays. Buttons with empty onClick handlers.

The app appears to work. Core functionality is fake.

---

**Tweet 3/7**
> Attach: slide-04.png (security that isn't there)

Finding #2: Security that isn't there.

Admin routes with zero authentication. IDOR vulnerabilities -- any user can access any other user's data by changing the ID in the URL.

In a healthcare app we tested, these aren't bugs. They're HIPAA violations.

---

**Tweet 4/7**
> Attach: slide-06.png (self-refine/LLM-judge chart)

We benchmarked every verification approach on HumanEval (164 tasks).

Self-refine: plateaus at ~87%. Useless.
LLM-as-judge: REGRESSES at k=5 (99.4% -> 97.2%). More AI review = worse code.

The standard approach to AI code quality actually degrades it.

---

**Tweet 5/7**
> Attach: slide-07.png (LUCID converges to 100%)

LUCID uses adversarial AI-based verification -- a second LLM trained to break code, not review it.

Results:
- HumanEval: 100% pass@5 (164/164)
- SWE-bench: +65.5% over baseline
- Real-world pilot: 354 claims verified, 23 bugs found in one ERP codebase

Only method that never regresses.

---

**Tweet 6/7**
> Attach: slide-08.png (verification gap diagram)

There's no step between "it builds" and "it works" in the AI coding pipeline.

Linters check syntax. Type checkers check types. Nothing checks if the code actually does what it claims.

LUCID fills that gap. GitHub Action, MCP server, or CLI. 5-minute setup.

---

**Tweet 7/7** (CTA)

Full benchmark report: trylucid.dev/report
Paper: doi.org/10.5281/zenodo.18522644
GitHub: github.com/gtsbahamas/hallucination-reversing-system
Patent: US App #63/980,048

Free tier: 100 verifications/month. Try it on your own codebase.

#AIcoding #DevTools #CodeQuality #LLM #OpenSource

---

## 2. Twitter/X Standalone Tweets (5 variations)

### 2a. Data finding

We benchmarked LLM-as-judge on HumanEval.

It peaks at 99.4% (k=3), then drops to 97.2% (k=5).

More AI review = worse code. False positives cause the generator to "fix" working code.

trylucid.dev/report

---

### 2b. Contrarian take

Hot take: "Ask the AI to review its own code" is the wrong approach.

Self-refine plateaus at 87%. LLM-as-judge regresses after 5 iterations.

Adversarial verification -- using a second AI trained to BREAK code -- hits 100%.

Stop reviewing. Start attacking.

---

### 2c. Builder story

I kept shipping bugs my AI coding assistant hallucinated into existence.

So I built a tool that catches them. Ran it on 4 production apps. Average health score: 39/100.

The code compiled. The code linted clean. The code was broken.

trylucid.dev

---

### 2d. Technical insight

We tried training verification directly into an LLM (RLVF).

More training data made the model WORSE. 120 curated pairs outperformed 2,000 automated ones.

Verification can't be baked into models. It has to be a separate adversarial pass.

---

### 2e. Provocation

Your AI code passes TypeScript. Passes ESLint. Passes code review.

It has admin routes with no auth, API endpoints that don't exist, and analytics backed by hardcoded arrays.

Nobody checks if the code does what it claims. We do.

trylucid.dev

---

## 3. LinkedIn Post

> Attach: carousel slides 1-9 as a document/carousel. LinkedIn supports multi-image posts.

I spent the last 3 months building something because I kept running into the same problem.

AI coding tools generate code that compiles, lints clean, and looks professional. But when you dig deeper, features are quietly broken. Analytics dashboards backed by hardcoded arrays. Auth guards that are imported but never connected. API endpoints that the frontend calls but the backend never implements.

I call it the "verification gap" -- the space between code that looks right and code that is right. No existing tool catches it. Linters check syntax. Type checkers check types. Nothing checks if the code actually does what it claims.

So I built LUCID -- an adversarial AI-based verification system. Instead of asking an AI to review its own output (which plateaus at ~87%), LUCID uses a second AI trained to break code. Think red team for AI-generated code.

I wanted data, not opinions. So I ran real benchmarks:

-- HumanEval (164 coding tasks): Baseline 86.6% -> LUCID 100% pass@5
-- SWE-bench (300 real GitHub bugs): Baseline 18.3% -> LUCID 30.3% (+65.5%)
-- Real-world pilot (25-page ERP system): 354 claims verified, 23 bugs found including 2 critical

The most surprising finding: LLM-as-judge -- the standard approach everyone uses for AI code quality -- actually REGRESSES after 5 iterations (99.4% -> 97.2%). More AI review produces worse code because false positives cause the generator to "fix" working code.

LUCID is the only approach in our benchmarks that converges monotonically. Every iteration makes the code better, never worse.

It ships as a GitHub Action (verify every PR), MCP server (works inside Claude Code, Cursor, Windsurf), or CLI. Patent filed (App #63/980,048). Published research (DOI: 10.5281/zenodo.18522644).

If you're shipping AI-generated code to production -- or reviewing PRs that contain it -- the verification gap is real and it's invisible to traditional tooling.

Full benchmark report: https://trylucid.dev/report
GitHub: https://github.com/gtsbahamas/hallucination-reversing-system

Happy to run a free verification audit on any codebase. DM me a repo link.

---

## 4. Skool Community Post

> For developer/AI builder communities. Casual, peer-to-peer, lead with curiosity.

**Title:** I found something weird about AI code review -- more review makes the code WORSE

---

Hey everyone. I've been deep in AI coding tools for the past few months and I stumbled on something that contradicts the standard advice.

Everyone says: "Just have the AI review its own code." Or "Use a second model as a judge."

So I benchmarked it properly. HumanEval, 164 coding tasks, controlled conditions.

Here's what happened:

**Self-refine** (ask the AI to try again): Plateaus at ~87%. Doesn't matter how many iterations you run. It just... stops improving.

**LLM-as-judge** (have a second model review the code): Starts great -- 98.2% at k=1, 99.4% at k=3. Then it DROPS to 97.2% at k=5.

Read that again. More AI review produced worse code.

Why? The judge starts hallucinating false positives. It flags correct code as buggy. The generator dutifully "fixes" working code and breaks it.

The only approach that didn't regress: adversarial verification. Instead of asking an AI to *review* code, you use a second AI trained to *break* code. Think red team, not code review.

Results:
- HumanEval: 100% pass@5 (164/164 problems solved)
- SWE-bench (real GitHub bugs): +65.5% over baseline
- Real production apps: average health score 39/100 -- admin routes with no auth, API endpoints that don't exist, "real-time" dashboards backed by static arrays

I also tried training the verification signal directly into the model (RLVF -- reinforcement learning from verification feedback). More training data made the model worse. 120 carefully curated training pairs outperformed 2,000 automated ones. Verification genuinely can't be baked in. It has to be external and adversarial.

Built this into a tool called LUCID. GitHub Action, MCP server (works in Claude Code / Cursor / Windsurf), and CLI. Patent filed, benchmarks published with a DOI.

**Free offer:** I'll run adversarial verification on your codebase for free. You get a claim-by-claim breakdown of what's verified vs. what's broken, with specific fix suggestions. Takes about 5 minutes. DM me a repo link or drop it in the comments.

Full data: trylucid.dev/report
GitHub: github.com/gtsbahamas/hallucination-reversing-system

Curious if anyone else has noticed the LLM-as-judge regression pattern. Are you reviewing AI-generated code differently than human-written code? What's your process?

---

## Posting Notes

### Platform-Specific Guidelines

| Platform | Timing | Notes |
|----------|--------|-------|
| Twitter/X | Tue-Thu, 8-10am ET | Thread first, standalones spread across the week |
| LinkedIn | Tue-Wed, 7-9am ET | Single post with carousel. Engage comments for 2 hours. |
| Skool | Any weekday | Check community rules on self-promotion first |

### General Rules

- Lead with data and findings, not with the product
- Offer free audits as genuine helpfulness
- Respond to every comment with substance, not marketing
- If someone challenges methodology, point to DOI and raw data in the repo
- Never overstate: say "adversarial AI-based verification" not "formal verification" (the verifier is an LLM, not a mathematical proof engine)
- Never say "deterministic" -- the system uses LLMs which are inherently stochastic
- All benchmark numbers are real, validated by running actual test suites, and reproducible from the repo

### Carousel Slide Reference

| Slide | Content | Best paired with |
|-------|---------|------------------|
| slide-01 | Hook: 39/100 average score | Thread tweet 1, LinkedIn header |
| slide-02 | Problem: compiles, lints clean, broken | Thread tweet 1 alt |
| slide-03 | Finding: features that don't exist | Thread tweet 2 |
| slide-04 | Finding: security that isn't there | Thread tweet 3 |
| slide-05 | Finding: scaffolding as features | LinkedIn carousel |
| slide-06 | Data: self-refine/LLM-judge regression | Thread tweet 4, standalone 2a |
| slide-07 | Data: LUCID converges to 100% | Thread tweet 5 |
| slide-08 | The verification gap diagram | Thread tweet 6 |
| slide-09 | CTA: trylucid.dev/report | Thread tweet 7, all CTAs |
