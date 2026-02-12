# LUCID North Star

*Last updated: 2026-02-11*
*Owner: Ty Wells*
*This document is the single source of truth for LUCID's strategy. All autonomous agents, plans, and decisions derive from this.*

---

## Mission

LUCID makes AI-generated code trustworthy through formal verification. We are the only system mathematically proven to converge on correctness — every other approach (self-refine, LLM-as-judge, random verification) either plateaus, regresses, or actively degrades quality. We exist because hallucination is permanent, proven by three independent impossibility theorems, and the industry needs infrastructure that works *with* that reality instead of pretending it will go away.

---

## Current Position (Ground Truth)

Everything below is verified fact, not aspiration.

### Intellectual Property
- **Provisional patent filed:** App #63/980,048 (Feb 11, 2026)
- **Claims cover:** extraction-verification-remediation loop, monotonic convergence property, formal test case generation from LLM output
- **Non-provisional deadline:** February 11, 2027
- **Published paper:** DOI 10.5281/zenodo.18522644
- **CHI 2026 Tools for Thought:** Submitted (notification ~Feb 25)

### Benchmark Results (Definitive)
| Benchmark | Baseline | LUCID Best | Improvement |
|-----------|----------|------------|-------------|
| HumanEval (164 tasks) | 86.6% | **100%** (k=3) | +15.5% absolute |
| SWE-bench Lite (300 tasks) | 18.3% | **30.3%** (best) | +65.5% relative |
| AI Platform Health (4 apps) | 40/100 avg | 21 critical bugs found | — |

### What Self-Refine and LLM-Judge Actually Do
- Self-refine: flat at ~87%, statistically useless
- LLM-judge: **regresses at k=5** (99.4% → 97.2%) — more iterations make code WORSE
- Random verification: **degrades** (97.6% → 95.1%)
- LUCID: monotonically converges to 100%. This is the only approach that does.

### Live Assets
| Asset | Status | Location |
|-------|--------|----------|
| CLI tool | Working | `dist/cli.js` (8 commands) |
| API | Live | https://lucid-api-dftr.onrender.com |
| Website | Live | gtsbahamas.github.io/hallucination-reversing-system |
| GitHub | Public | github.com/gtsbahamas/hallucination-reversing-system |
| Architecture paper | Draft complete | `docs/architecture-paper/` (~20K words, 5 theorems) |
| Benchmark report | Written | `docs/benchmark-report/state-of-ai-code-quality-2026.md` |
| Pitch materials | Complete | `docs/pitch/` (one-pager, deck, 14-question FAQ) |

### Distribution (Completed)
- Hacker News (Show HN), LinkedIn, Twitter/X, Skool (4 communities), Dev.to
- Blog post live on GitHub Pages
- Email capture active (Formsubmit.co → tyclaude@snapperland.com)

### What We Don't Have Yet
- Zero revenue
- Zero paying customers
- Zero platform integrations
- No npm package published
- No GitHub Action on Marketplace
- No API documentation site

---

## Core Thesis (The Why That Never Changes)

1. **Hallucination is mathematically permanent.** Three independent proofs (Xu 2024, Banerjee 2024, Karpowicz 2025) prove this from different angles. The industry spending billions to suppress it is fighting mathematics.

2. **Biology solved this 500 million years ago.** The brain hallucinates constantly — perception is active prediction, not passive recording. The predict-verify-correct loop (Friston's Free Energy Principle) is exactly what LUCID implements. We are not inventing a new paradigm; we are implementing one that evolution already validated.

3. **Formal verification is the only verifier that can't be fooled.** Learned verifiers (RLHF, Constitutional AI, LLM-as-judge) share failure modes with generators. Formal verification is deterministic — same input, same spec, same result. It terminates the infinite regress of "who verifies the verifier?"

4. **The specification is the product.** LUCID's deepest value isn't "finding bugs." It's generating formal specifications from unstructured AI output. Specifications are auditable, version-controllable, and composable. They are the artifact regulators want and enterprises need.

---

## Target Customers (Priority Order)

### Priority 1: AI Coding Platforms (B2B API Integration)
**This is the primary path. Everything else is secondary.**

| Platform | Why They Need LUCID | Size | Status |
|----------|---------------------|------|--------|
| **Cursor** | Racing Copilot on quality. Tab-complete + agent mode both need verification. | 1M+ users | No contact |
| **Bolt.new** | Code goes to production with zero human review. Highest risk. | 500K+ users | Benchmarked |
| **Lovable** | Same as Bolt. Raised $7M, needs differentiation. | 200K+ users | Benchmarked |
| **Replit** | Agent mode builds apps autonomously. Agent needs verification. | 25M+ platform | Benchmarked |
| **Windsurf** | $150M raised, racing Cursor. | Growing | No contact |
| **Devin** | $2B valuation riding on "does it work?" | Enterprise | No contact |

**What we sell them:** API integration. They send code, they get verified code back. Usage-based pricing. Black box — they never see the implementation.

**Why they'll buy:** Our benchmark proves their code averages 40/100 health scores. We have data showing their specific failure modes. We approach with data, not a pitch.

### Priority 2: EU AI Act Compliance Buyers (B2B Services)
**August 2, 2026 deadline creates urgency. 5 months away.**

- Target: Legal, CISO, VP Engineering at companies deploying AI in EU
- Offering: AI code compliance assessment ($5K-15K per engagement)
- LUCID generates the formal verification audit trail regulators require
- TAM: $13.4B by 2028

### Priority 3: Developer Teams (PLG / SaaS)
**Longer-term recurring revenue. Lower priority than platform deals.**

- GitHub Action on every PR
- Free tier → Team ($99/mo) → Org ($249/mo)
- "Powered by LUCID" badge
- PLG motion: free users → team upgrades → enterprise conversations

### Priority 4: Consulting / Audits
**Bridge revenue while building platform relationships.**

- "AI Software Specification Audit" — $2K-5K per engagement
- Run LUCID on client's AI-generated codebase, deliver gap report
- Proves value, generates case studies, funds operations
- Target: 2-3 engagements by end of March

---

## Product Strategy (What to Build, In What Order)

### Now → March 2026: Make LUCID Buyable
1. **API documentation site** — Black box API docs so platforms can evaluate integration. This is the gate to every platform conversation.
2. **Publish the benchmark report** — "State of AI Code Quality 2026." This is our sales weapon. Patent protects us.
3. **npm package** — `npx lucid` works globally. Makes individual developer adoption frictionless.

### March → May 2026: Developer Adoption Funnel
4. **GitHub Action MVP** — Runs LUCID on PRs, comments with findings. Free tier: 5 scans/month. Listed on GitHub Marketplace.
5. **Platform outreach** — Approach Tier 1 platforms with benchmark data. Goal: 3 meetings.

### May → August 2026: Revenue
6. **First platform pilot** — One signed pilot with API access and measurement.
7. **EU AI Act compliance product** — Compliance landing page, assessment offering, outreach to compliance buyers.
8. **First consulting engagements** — Use benchmark report to open conversations.

### August 2026+: Scale
9. **EU AI Act enforcement begins** — Compliance revenue kicks in.
10. **Second and third platform deals** — Leverage first as proof.
11. **NSF SBIR Phase I application** — $305K non-dilutive. Benchmark data strengthens it.

---

## Competitive Position

### What We Are
- Verification infrastructure for AI-generated code
- The only system with proven monotonic convergence
- A formal verification layer, not a linter or code quality scanner
- Model-agnostic — works with any LLM's output

### What We Are NOT
- A code quality tool (not competing with Snyk, SonarQube, Codacy)
- A spec-driven development tool (not competing with Tessl, Kiro, Spec Kit)
- An AI model company (not training foundation models)
- A general-purpose AI safety company

### Key Differentiators
| Us | Them |
|----|------|
| Bottom-up: hallucination → specification | Tessl: top-down, specification → code |
| Formal verification (deterministic) | LLM-as-judge (learned, hackable) |
| Monotonic convergence (proven) | Self-refine (flat), LLM-judge (regresses) |
| Model-agnostic | Lab-specific |
| Patent-protected | No IP protection |

### The Moat (How We Win Long-Term)
1. **Patent** — 12-month priority window (filed Feb 2026)
2. **Data moat** — Every API call builds verification corpus. After 100K calls, no one can replicate without the same volume.
3. **Inverse positioning** — Competitors can't copy without admitting hallucination is permanent, which undermines their product narrative.
4. **Integration lock-in** — Once a platform wires LUCID into their pipeline, switching costs are high.
5. **Academic credibility** — Published theory, DOI, CHI submission, architecture paper.

---

## Decision Frameworks (For Autonomous Agents)

These rules let agents make decisions without human approval for routine tradeoffs.

### Revenue Priority
**Platform deals > Compliance revenue > SaaS subscriptions > Consulting > Free tier growth**

When two activities compete for attention, the one higher on this list wins. A single platform integration is worth more than 100 individual subscribers.

### Content Priority
**Data-driven > Thought leadership > Community engagement > Brand awareness**

Always lead with numbers. "We benchmarked 4 platforms and found 21 critical bugs" beats "AI code quality matters." Benchmark data is our competitive weapon — use it in every piece of content.

### Outreach Rules
- **Never cold pitch.** Always lead with data or a useful insight for the recipient.
- **Personalize with benchmark data.** "Your platform scored X. With LUCID, that becomes Y."
- **Target engineering, not marketing.** We sell to CTOs, VP Engineering, and platform engineering leads.
- **One warm intro beats ten cold emails.**
- **Always offer a free benchmark of their code** as the entry point, not a demo of our tool.

### Pricing Rules
- **Never discount below cost.** API calls cost $0.003-0.014 each. Minimum revenue per call: $0.01.
- **Usage-based for platforms.** Per-verification pricing, not seats.
- **Monthly SaaS for teams.** $99/mo minimum. Never offer one-time audits below $2,000.
- **Free tier exists to create upgrade pressure**, not to be generous. Cap it at 5 scans/month.

### IP Protection Rules
- **Publish results (numbers, charts, comparisons).** This is marketing.
- **Never publish implementation details.** Prompt templates, verification strategies, ablation insights are trade secrets.
- **The API is a black box.** Customers send code, get verified code back. They never see how.
- **Architecture paper: publish theoretical framework only.** Implementation section stays vague on purpose.

### Brand Voice
- **Confident, not arrogant.** We have data. We let it speak.
- **Technical, not salesy.** Our audience is engineers. Respect their intelligence.
- **Contrarian, not combative.** "The industry approach doesn't work, here's why" — not "everyone else is wrong."
- **Precise claims only.** "100% on HumanEval k=3" is a fact. "Best AI verification tool" is marketing fluff — avoid it.
- **Acknowledge limitations.** LUCID works on code. It doesn't verify prose, creativity, or subjective quality. Saying this builds trust.

### What Agents Should NEVER Do Without Human Approval
- Publish pricing changes
- Send outreach to Tier 1 platform contacts (Cursor, Bolt, Lovable, Replit leadership)
- Publish or modify the benchmark report
- Make claims about the patent or IP
- Commit to delivery timelines with external parties
- Offer free pilots to platforms (the terms matter)
- Modify the architecture paper
- Post to Hacker News or Product Hunt

### What Agents CAN Do Autonomously
- Draft outreach emails (for human review before sending)
- Write blog posts and content (for human review before publishing)
- Research platform contacts and build target lists
- Monitor competitor activity and summarize findings
- Draft consulting proposals from templates
- Track and report on metrics (GitHub stars, signups, etc.)
- Update internal documentation
- Create social media content drafts
- Research EU AI Act compliance requirements
- Build API documentation

---

## Success Metrics

### 30-Day Targets (by March 13, 2026)
| Metric | Target | How to Measure |
|--------|--------|----------------|
| API documentation site | Live | URL accessible |
| Benchmark report published | Yes | Public URL |
| npm package published | Yes | `npx lucid --help` works |
| Platform outreach sent | 3+ platforms | Emails sent with data |
| Consulting conversations | 2+ | Warm leads engaged |
| GitHub stars | 50+ | github.com/gtsbahamas/hallucination-reversing-system |

### 90-Day Targets (by May 12, 2026)
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Platform meetings | 3+ | Meetings with engineering teams |
| GitHub Action on Marketplace | Yes | Listed and installable |
| First revenue | Any | First dollar from any source |
| Email waitlist | 50+ | Formsubmit.co count |
| First case study published | Yes | Blog post with real data |

### 180-Day Targets (by August 11, 2026)
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Platform pilot signed | 1+ | Signed agreement |
| MRR | $1,000+ | Recurring from any source |
| Consulting revenue (total) | $10K+ | Completed engagements |
| EU AI Act compliance offering | Live | Landing page + first engagement |
| API calls (total) | 10,000+ | Usage logs |
| NSF SBIR submitted | Yes | Application filed |

### 12-Month Vision (by February 2027)
| Metric | Target |
|--------|--------|
| Platform integrations | 2-3 |
| MRR | $10K+ |
| Non-provisional patent decision | Made |
| Conference presentations | 2+ (beyond CHI) |
| Data moat | 100K+ verification calls |

---

## Boundaries (What We Will NOT Do)

1. **We will not train foundation models.** We are a verification layer, not a model company.
2. **We will not compete on code quality scanning.** Snyk, SonarQube own that. We verify semantic correctness, not style.
3. **We will not build a full SaaS platform before getting a platform deal.** API + simple dashboard is enough. Don't overbuild.
4. **We will not pursue enterprise sales directly.** PLG first. Enterprise follows champions who used the free/team tier.
5. **We will not give away the implementation.** Open-source the CLI (adoption), protect the API internals (revenue).
6. **We will not spread across multiple markets simultaneously.** AI coding platforms first. Compliance second. Everything else after.
7. **We will not lower prices to win deals.** Our value is in the data, not the cost. Race to the bottom kills margins.

---

## Resources

| Resource | Location |
|----------|----------|
| This document | `docs/north-star.md` |
| Architecture paper | `docs/architecture-paper/` |
| Benchmark report | `docs/benchmark-report/state-of-ai-code-quality-2026.md` |
| Monetization plan | `docs/plans/2026-02-08-monetization-plan.md` |
| Platform integration strategy | `docs/plans/2026-02-10-platform-integration-strategy.md` |
| Pitch materials | `docs/pitch/` (one-pager, deck, FAQ) |
| Patent filing docs | `docs/patent/filing-ready/` |
| FrankLabs GTM sprint | `/Users/tywells/Downloads/projects/franklabs-website/docs/guidance/lucid-gtm-sprint.md` |
| HumanEval results | `results/humaneval*/` (10 directories) |
| SWE-bench v2 results | `results/swebench-v2/` |
| Experiment harness | `experiments/` |
| API (live) | https://lucid-api-dftr.onrender.com |
| Website | https://gtsbahamas.github.io/hallucination-reversing-system |
| GitHub | https://github.com/gtsbahamas/hallucination-reversing-system |
| Zenodo DOI | 10.5281/zenodo.18522644 |
| Patent app | #63/980,048 (filed 2026-02-11) |
| FrankLabs dashboard | https://franklabs.io/login |

---

## How This Document Gets Used

1. **FrankLabs agents read this document** at the start of any LUCID-related work session.
2. **All plans, tasks, and content** must align with the priorities and frameworks above.
3. **When in doubt, check the decision frameworks.** If the answer isn't there, escalate to human.
4. **This document supersedes** the monetization plan, GTM sprint, and platform strategy docs where they conflict. Those docs remain useful for tactical detail, but this is the authority.
5. **Update this document** when material facts change (new revenue, new partnerships, new benchmark data, patent status). Do not update for tactical changes — those belong in sprint docs.

---

*LUCID exists because hallucination is permanent and the industry needs infrastructure that works with that reality. We have the proof, the patent, and the product. Now we need the customers.*
