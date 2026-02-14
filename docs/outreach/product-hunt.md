# LUCID — Product Hunt Listing

> **DRAFT — DO NOT POST WITHOUT HUMAN APPROVAL**
> Product Hunt posts cannot be edited after launch. Review carefully.
> Prepared: 2026-02-11

---

## Tagline (60 chars max)

**Adversarial verification for AI-generated code** (50 chars)

Alternates:
- "Catch the bugs AI coding tools miss" (37 chars)
- "Does your AI code actually work? Now you can prove it." (55 chars)

---

## Short Description (260 chars max)

LUCID verifies AI-generated code using iterative adversarial verification — a second AI systematically checks the first AI's output against extracted specifications. It extracts testable claims from code, verifies them adversarially, and generates fix plans. 100% pass rate on HumanEval. 21 critical bugs found across 4 production apps.

---

## Detailed Description

### The problem

AI coding tools generate code that compiles, looks right, and passes visual review. But does it actually work?

We ran adversarial verification on real-world apps built with Bolt.new, Lovable, v0, and Replit. Average production-readiness score: **40/100**. We found **21 critical bugs** — including unprotected admin routes, fake analytics backed by hardcoded data, and API endpoints that don't exist.

The gap between "it builds" and "it works" is the **verification gap**. Traditional tools (linters, type checkers, unit tests) don't catch it. LLM-based review doesn't either — our benchmarks show it actually makes code *worse* after enough iterations.

### What LUCID does

LUCID is a 3-layer adversarial verification pipeline:

1. **Extract** — Identifies every testable claim in the code ("this route is protected," "this data persists," "this API returns real data")
2. **Verify** — Tests each claim against extracted specifications using a separate AI verifier that adversarially checks the generator's output.
3. **Remediate** — Generates specific fix plans for every failure, with code references and priority.

### Results

**HumanEval (164 coding tasks):**
- Baseline: 86.6% pass rate
- Self-refine: 87.2% (statistically useless)
- LLM-as-judge: 97.2% at k=5 (regresses with more iterations)
- **LUCID: 100% at k=3** (only approach that converges monotonically)

**SWE-bench Lite (300 real GitHub bugs):**
- Baseline: 18.3% resolved
- **LUCID: 30.3% resolved (+65.5% relative improvement)**

**Real-world AI apps (4 production codebases):**
- Average health score: 40/100
- 21 critical bugs found
- Categories: missing backends, fake data, broken auth, security holes

### How to use it

```bash
# Verify any codebase
npx lucid verify ./my-app

# Or call the API
curl -X POST https://lucid-api-dftr.onrender.com/verify \
  -d '{"code": "...", "context": "..."}'
```

**Pricing:** Free tier (50 verifications + 20 generations/month). Usage-based from $0.15/verify, $0.30/generate.

**Open source:** CLI is open source. Verification API is a managed service.

US Patent Pending (App #63/980,048) | DOI: 10.5281/zenodo.18522644

---

## First Comment (From Maker)

Hi PH! I'm Ty, the builder behind LUCID.

The origin story: I was using AI coding tools to build apps and noticed a pattern. Everything compiled. Everything looked professional. But features were silently broken — analytics dashboards showing hardcoded numbers, auth guards that were imported but never wired up, API calls to endpoints that don't exist.

I started building verification tooling to catch these issues. The deeper I went, the more interesting it got. Turns out:

- **Self-refine** ("try again") barely helps — flat at ~87% on HumanEval
- **LLM-as-judge** ("ask another model") actually makes code WORSE after 5 iterations (99.4% drops to 97.2%)
- **Adversarial verification** is the only approach that converges to 100% and never regresses

We spent $466 running the full benchmark suite across HumanEval and SWE-bench to prove this. The math works. The data is public. The methodology is peer-reviewed.

Now we're turning it into infrastructure. The vision: every AI coding platform integrates a verification step between generation and deployment. Your code doesn't just build — it provably works.

Would love your feedback. Try the free tier and tell me what breaks.

Full benchmark report: https://trylucid.dev/report
Research paper: https://doi.org/10.5281/zenodo.18522644

---

## Key Features List

- **Adversarial verification** — a second AI systematically checks the first, catching errors that self-review misses
- **3-layer pipeline** — Extract claims, Verify against specs, Remediate with fix plans
- **100% HumanEval pass rate** at k=3 (only system to achieve monotonic convergence)
- **+65.5% improvement** on SWE-bench Lite (300 real-world bug fixes)
- **21 critical bugs found** across 4 AI-built production apps (Bolt.new, Lovable, v0, Replit)
- **Model-agnostic** — works with any LLM's output
- **Usage-based pricing** — free tier included, scales with your usage
- **Reverse mode** — synthesizes formal specs BEFORE code generation, preventing hallucinations instead of just catching them
- **Patent-protected** (US App #63/980,048)

---

## Category

**Developer Tools**

Secondary: AI, Code Quality, Open Source

---

## Media Checklist

- [ ] Logo (240x240 PNG)
- [ ] Gallery images (1270x760): killer chart, benchmark comparison, verification flow diagram
- [ ] Demo video (60-90 sec) — see video-script.md
- [ ] Social preview image
