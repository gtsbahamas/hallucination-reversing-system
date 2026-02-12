# Cross-Platform AI Code Quality Benchmark

*Created: 2026-02-10*
*Companion to: `2026-02-10-platform-integration-strategy.md`*
*Status: Design phase*

---

## Purpose

Produce a credible, reproducible benchmark comparing the code correctness of major AI coding platforms, and measure LUCID's improvement on each. The output is:

1. **A public report** — "State of AI Code Quality 2026"
2. **Platform-specific scorecards** — used in outreach
3. **LUCID improvement data** — proof that the API works across platforms

---

## Design Principles

| Principle | Why |
|-----------|-----|
| **Use established benchmarks** | HumanEval and SWE-bench are recognized. Custom tasks can be dismissed as cherry-picked. |
| **Test what each platform actually does** | Don't test an app builder on function generation. Match task type to platform capability. |
| **Reproducible methodology** | Publish exact prompts, evaluation criteria, and scoring. Invite platforms to challenge results. |
| **Fair comparison** | Same prompts, same evaluation, same hardware. No platform-specific tuning. |
| **Measure both baseline and LUCID-enhanced** | The story is the delta, not just the raw score. |

---

## Platform Categories

Different platforms do different things. The benchmark needs task categories that map to each platform's actual use case.

### Category A: Code Completion / Function Generation

**Platforms:** Cursor, Windsurf, GitHub Copilot, Tabnine, JetBrains AI
**What they do:** Generate code from context, complete functions, implement from docstrings
**Benchmark:** HumanEval (164 tasks) — industry standard for this exact capability

### Category B: Autonomous Bug Fixing

**Platforms:** Cursor (agent mode), Devin, Replit Agent, GitHub Copilot Workspace
**What they do:** Take a bug report or issue, modify existing code to fix it
**Benchmark:** SWE-bench Lite (300 tasks) — industry standard for this capability

### Category C: Full Application Generation

**Platforms:** Bolt.new, Lovable, Replit Agent, v0
**What they do:** Generate entire working applications from natural language prompts
**Benchmark:** Custom task set (see Section: App Generation Tasks below) — no established benchmark exists for this, so we define one

### Category D: Feature Addition

**Platforms:** Cursor, Windsurf, Devin, Replit Agent
**What they do:** Add a feature to an existing codebase
**Benchmark:** Custom task set derived from real GitHub PRs (see Section: Feature Addition Tasks below)

---

## Benchmark Suite

### Track 1: HumanEval (Category A platforms)

**Tasks:** 164 function-level programming problems from OpenAI's HumanEval dataset
**We already have:** Full results for baseline, self-refine, LLM-judge, and LUCID

**Per platform, run:**
1. Present the function signature + docstring as prompt
2. Collect generated code (pass@1, pass@3)
3. Run against HumanEval test cases
4. Run LUCID verification loop (k=1, k=3)
5. Re-run test cases on LUCID-verified code

**Evaluation:**
- pass@1: correctness on first attempt
- pass@3: best of 3 attempts
- LUCID pass@1: correctness after LUCID verification (k=1)
- LUCID pass@3: correctness after LUCID verification (k=3)

**Cost estimate:** ~$5-15 per platform (164 tasks x ~$0.03-0.10 per generation)
**Time estimate:** 2-4 hours per platform (automated)

### Track 2: SWE-bench Lite (Category B platforms)

**Tasks:** 300 real GitHub issues from major Python projects (django, flask, sympy, scikit-learn, etc.)
**We already have:** Full results for baseline and LUCID

**Per platform, run:**
1. Present the issue description + relevant source files
2. Collect generated patch
3. Run SWE-bench Docker evaluation (test suite verification)
4. Run LUCID verification loop on the patch
5. Re-run Docker evaluation on LUCID-verified patch

**Evaluation:**
- Resolve rate: % of issues correctly resolved
- Patch quality: % of patches that apply cleanly
- LUCID resolve rate: after verification
- Improvement delta: platform + LUCID vs platform alone

**Cost estimate:** ~$50-100 per platform (300 tasks, heavier LLM usage)
**Time estimate:** 8-16 hours per platform (Docker evaluation is slow)

**Infrastructure:** EC2 c5.9xlarge or similar (we already have the harness and experience from v2 run)

### Track 3: App Generation (Category C platforms) — NEW

**Tasks:** 20 full-application generation tasks, carefully designed to be:
- Unambiguous (clear spec, testable requirements)
- Representative (common app types developers actually build)
- Graduated difficulty (easy → hard)
- Verifiable (automated test suites for each task)

#### App Generation Task Set (20 tasks)

**Tier 1: Simple (5 tasks) — Single-page, minimal logic**

| ID | Task | Key requirements | Verification criteria |
|----|------|-----------------|----------------------|
| APP-01 | Todo list app | Add, complete, delete, persist to localStorage | CRUD operations work, data persists on reload |
| APP-02 | Calculator | Basic arithmetic, decimal handling, clear | Correct results for 20 test expressions |
| APP-03 | Markdown previewer | Real-time preview, common Markdown syntax | Renders 10 test Markdown snippets correctly |
| APP-04 | Timer / stopwatch | Start, stop, reset, lap times | Timing accurate within 100ms, all controls work |
| APP-05 | Color palette generator | Generate harmonious colors, copy hex values | Valid hex codes, copy-to-clipboard works |

**Tier 2: Medium (8 tasks) — Multi-page, data management, API integration**

| ID | Task | Key requirements | Verification criteria |
|----|------|-----------------|----------------------|
| APP-06 | Weather dashboard | Fetch from API, display forecast, search by city | API calls work, data renders, error handling for invalid city |
| APP-07 | Blog with auth | User signup/login, create/edit/delete posts, public view | Auth flow works, CRUD on posts, unauthorized access blocked |
| APP-08 | E-commerce product page | Product listing, cart, quantity management, checkout form | Cart math correct, form validation works, responsive |
| APP-09 | Kanban board | Drag-and-drop cards, columns, persist state | Drag works, state persists, cards move between columns |
| APP-10 | Chat interface with WebSocket | Real-time messaging, multiple users, message history | Messages deliver in real-time, history loads, handles disconnection |
| APP-11 | File upload + preview | Upload images/PDFs, preview, delete, size limits | Upload works, preview renders, size validation enforced |
| APP-12 | Data table with sort/filter/paginate | Load dataset, column sort, text filter, pagination | Sort correct for all types, filter matches, page navigation works |
| APP-13 | Multi-step form wizard | 3+ steps, validation per step, review + submit | Validation fires per step, back navigation preserves data, submit collects all fields |

**Tier 3: Hard (7 tasks) — Complex logic, real-world patterns**

| ID | Task | Key requirements | Verification criteria |
|----|------|-----------------|----------------------|
| APP-14 | Dashboard with charts | Fetch data, render 3+ chart types, responsive | Charts render with real data, responsive layout, legends correct |
| APP-15 | Collaborative text editor | Real-time co-editing, cursor presence, conflict resolution | Two users can edit simultaneously, changes merge correctly |
| APP-16 | OAuth integration | Google/GitHub OAuth, session management, protected routes | Full OAuth flow works, session persists, protected routes redirect |
| APP-17 | Payment flow (Stripe test mode) | Product selection, Stripe checkout, success/failure handling | Checkout session creates, redirects work, handles declined cards |
| APP-18 | REST API + database | CRUD endpoints, validation, error responses, pagination | All endpoints return correct status codes, validation rejects invalid input |
| APP-19 | Search with autocomplete | Debounced search, result ranking, keyboard navigation | Results appear on type, debounce works, arrow keys navigate |
| APP-20 | Role-based access control | Admin/user roles, different views per role, permission enforcement | Admin sees admin features, user doesn't, direct URL access blocked |

#### App Generation Evaluation Framework

Each generated app is evaluated on a 5-point rubric:

| Criterion | Weight | Scoring |
|-----------|--------|---------|
| **Builds** | 20% | 0 = won't install/compile, 1 = builds with warnings, 2 = clean build |
| **Renders** | 15% | 0 = blank/error page, 1 = partial render, 2 = full render |
| **Core functionality** | 35% | 0 = nothing works, 1 = partial, 2 = all requirements met |
| **Edge cases** | 15% | 0 = crashes on edge input, 1 = handles some, 2 = handles all defined |
| **Error handling** | 15% | 0 = unhandled errors, 1 = some handling, 2 = graceful handling |

**Automated verification:**
For each task, we write a test suite (Playwright for UI, API tests for backend) that produces a score. This removes subjectivity.

**Manual spot-check:** 20% of results are manually reviewed to validate the automated scoring.

### Track 4: Feature Addition (Category D platforms) — NEW

**Tasks:** 15 feature-addition tasks based on real open-source repositories.

**Structure:** Each task provides:
- An existing small codebase (50-200 files)
- A feature request (as a GitHub issue)
- A test suite that passes BEFORE the feature (regression) and includes tests for the NEW feature (currently failing)

**Success = all tests pass (old + new) after the platform generates the changes.**

#### Feature Addition Task Set (15 tasks)

| ID | Base repo | Feature request | Complexity |
|----|-----------|----------------|------------|
| FEAT-01 | Express API (5 routes) | Add rate limiting middleware | Low |
| FEAT-02 | React todo app | Add drag-and-drop reordering | Low |
| FEAT-03 | Flask blog | Add Markdown support to posts | Low |
| FEAT-04 | Next.js portfolio | Add dark mode toggle with persistence | Medium |
| FEAT-05 | Django REST API | Add JWT authentication | Medium |
| FEAT-06 | React dashboard | Add CSV export for data tables | Medium |
| FEAT-07 | Express + Postgres API | Add full-text search endpoint | Medium |
| FEAT-08 | Vue.js e-commerce | Add product filtering (price, category, rating) | Medium |
| FEAT-09 | FastAPI + SQLAlchemy | Add pagination with cursor-based navigation | Medium |
| FEAT-10 | React + Firebase app | Add real-time notifications | Hard |
| FEAT-11 | Django multi-tenant app | Add per-tenant billing with Stripe | Hard |
| FEAT-12 | Next.js SaaS | Add team invitation flow with email | Hard |
| FEAT-13 | Express + Redis | Add job queue with retry and dead-letter | Hard |
| FEAT-14 | React + GraphQL | Add optimistic UI updates with rollback | Hard |
| FEAT-15 | Full-stack app | Add end-to-end encryption for messages | Hard |

**Evaluation:** Binary pass/fail per task (all tests pass or they don't), plus partial credit for passing subset of new tests.

---

## Execution Plan

### Phase 1: Preparation (Week 1)

| Task | Time | Cost |
|------|------|------|
| Set up accounts on all target platforms | 2 hours | Free tier where possible |
| Prepare HumanEval prompts per platform's interface | 4 hours | $0 |
| Prepare SWE-bench prompts per platform's interface | 4 hours | $0 |
| Write app generation test suites (20 apps) | 16 hours | $0 |
| Write feature addition base repos + test suites (15 tasks) | 16 hours | $0 |
| Set up EC2 for SWE-bench Docker evaluation | 1 hour | ~$5 |
| Total | ~43 hours | ~$5 |

### Phase 2: Baseline Collection (Week 2)

Run each platform on all applicable tracks WITHOUT LUCID.

| Platform | Track 1 (HumanEval) | Track 2 (SWE-bench) | Track 3 (App Gen) | Track 4 (Feature) | Est. cost |
|----------|---------------------|---------------------|-------------------|--------------------|-----------|
| Cursor | Yes | Yes | No | Yes | $80-120 |
| Bolt.new | No | No | Yes | No | $40-60 |
| Lovable | No | No | Yes | No | $40-60 |
| Replit Agent | No | Yes (subset) | Yes | Yes | $80-120 |
| Windsurf | Yes | Yes | No | Yes | $80-120 |
| v0 | No | No | Yes (UI only) | No | $20-40 |
| Devin | Yes | Yes | No | Yes | $100-150 |
| Copilot | Yes | No | No | Yes | $40-60 |

**Total baseline cost estimate: $480-730**
**Total baseline time estimate: 40-60 hours (parallelizable across platforms)**

**Note on platform costs:** Some platforms charge per message/generation. Budget $200-400 for platform subscription fees during the benchmark period.

### Phase 3: LUCID Verification (Week 3)

Run LUCID verification on ALL baseline outputs.

| Track | Tasks | LUCID calls per task | Est. cost |
|-------|-------|---------------------|-----------|
| Track 1 (HumanEval) | 164 x ~5 platforms | k=1 and k=3 | $50-80 |
| Track 2 (SWE-bench) | 300 x ~4 platforms | k=1 and k=3 | $200-400 |
| Track 3 (App Gen) | 20 x ~4 platforms | k=1 and k=3 | $30-60 |
| Track 4 (Feature) | 15 x ~5 platforms | k=1 and k=3 | $30-50 |

**Total LUCID verification cost: $310-590**
**Total verification time: 20-40 hours (parallelizable)**

### Phase 4: Analysis & Report (Week 4)

| Task | Time |
|------|------|
| Aggregate all results into unified dataset | 4 hours |
| Generate charts and visualizations | 8 hours |
| Write report narrative | 8 hours |
| Platform-specific scorecards | 4 hours |
| Peer review / sanity check | 4 hours |
| Design report layout (PDF + web) | 4 hours |
| Total | ~32 hours |

### Total Budget

| Category | Low | High |
|----------|-----|------|
| Platform subscriptions | $200 | $400 |
| Baseline generation (LLM costs) | $480 | $730 |
| LUCID verification (Anthropic API) | $310 | $590 |
| EC2 for SWE-bench Docker | $20 | $50 |
| **Total** | **$1,010** | **$1,770** |

**Time: 4 weeks, ~150 hours of work (much parallelizable with automation)**

---

## Methodology Details

### Prompt Standardization

Each platform has a different interface. To ensure fairness:

**For IDE-based platforms (Cursor, Windsurf, Copilot):**
- Create a new file with the function signature and docstring
- Use the platform's autocomplete/generate feature
- No additional context beyond what HumanEval provides
- Record the FIRST generation (no manual re-prompting)

**For agent-based platforms (Devin, Replit Agent, Cursor Agent):**
- Provide the task as a natural language prompt matching the issue description
- Allow the agent to run its full pipeline (planning, coding, testing if it does that)
- Record the final output after the agent reports "done"
- Time-box: 10 minutes per HumanEval task, 30 minutes per SWE-bench task, 60 minutes per app/feature task

**For app builders (Bolt.new, Lovable, v0):**
- Provide the task description as the initial prompt
- Allow up to 3 follow-up prompts for clarification (record all prompts)
- Record the final generated application
- Export/download the full source code for evaluation

### Evaluation Integrity

| Measure | How |
|---------|-----|
| Blind evaluation | Automated test suites don't know which platform generated the code |
| Reproducibility | All prompts, responses, and test results saved and publishable |
| Multiple runs | Track 1 and Track 2: 3 runs per task per platform (report mean + stdev) |
| Version pinning | Record exact platform version/date for each run |
| No cherry-picking | ALL results reported, including tasks where LUCID makes things worse |

### LUCID Verification Protocol

For each platform's output, LUCID verification follows the same protocol:

1. **Input:** Platform's generated code + original task description
2. **LUCID k=1:** Single extraction → verification → remediation pass
3. **LUCID k=3:** Up to 3 iterations of the verification loop
4. **Output:** Verified code
5. **Evaluation:** Same test suite as baseline, applied to verified code
6. **Record:** Baseline score, LUCID k=1 score, LUCID k=3 score, cost per verification

---

## Report Structure: "State of AI Code Quality 2026"

### Executive Summary
- Overall findings in 3 bullet points
- Hero chart: all platforms, baseline vs LUCID-enhanced
- Key insight: "Current verification approaches degrade with iteration. Formal verification converges."

### Section 1: Methodology
- Benchmark design, platform list, evaluation criteria
- Reproducibility statement
- Limitations and caveats

### Section 2: Function-Level Code Generation (Track 1)
- HumanEval results per platform
- Chart: pass@1 and pass@3 comparison
- LUCID improvement per platform
- Finding: which platforms benefit most from verification

### Section 3: Bug Fixing (Track 2)
- SWE-bench results per platform
- Chart: resolve rate comparison
- LUCID improvement per platform
- Analysis: which bug categories each platform handles best/worst

### Section 4: Full Application Generation (Track 3)
- App generation results per platform
- Chart: rubric scores by difficulty tier
- LUCID improvement per platform
- Gallery: example apps generated (screenshots)

### Section 5: Feature Addition (Track 4)
- Feature addition results per platform
- Chart: pass rate by complexity
- LUCID improvement per platform

### Section 6: Cross-Cutting Analysis
- Which platforms improve most with LUCID verification?
- Which task categories have the largest correctness gaps?
- Cost analysis: platform cost + LUCID cost vs. manual fix cost
- The convergence finding: why iterative verification only works with formal methods

### Section 7: Recommendations
- For developers: how to choose a platform based on your use case
- For platforms: how to integrate verification into your pipeline
- For enterprises: how to evaluate AI coding tool risk

### Appendix
- Full results tables
- Per-task breakdowns
- Platform version information
- Prompt templates used

---

## Platform-Specific Scorecards

For each platform, produce a 1-page scorecard:

```
┌─────────────────────────────────────────────┐
│  [PLATFORM NAME] — AI Code Quality Report   │
│  State of AI Code Quality 2026              │
├─────────────────────────────────────────────┤
│                                             │
│  Overall Score: [X]/100                     │
│  Rank: [N] of [total platforms]             │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  Track scores (bar chart)           │    │
│  │  Baseline vs LUCID-enhanced         │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Strengths:                                 │
│  - [Strength 1]                             │
│  - [Strength 2]                             │
│                                             │
│  Weaknesses:                                │
│  - [Weakness 1]                             │
│  - [Weakness 2]                             │
│                                             │
│  LUCID Improvement: +[X]% overall           │
│  Best improvement area: [category]          │
│                                             │
│  Contact: hello@lucid.dev                   │
├─────────────────────────────────────────────┤
│  lucid.dev/benchmark/2026                   │
└─────────────────────────────────────────────┘
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Platform blocks automated access | Use manual operation where needed; document the limitation |
| Platform updates during benchmark period | Pin versions; run all platforms within same 2-week window |
| Results are too close to differentiate | Focus on task categories where differences are meaningful |
| Platform claims benchmark is unfair | Publish full methodology; offer to re-run on their chosen tasks |
| LUCID makes things worse on some platform | Report honestly — credibility is worth more than perfect numbers |
| Platform rate-limits or costs explode | Budget caps per platform; reduce task count if needed |
| App generation tasks are too subjective | Automated test suites remove subjectivity; manual review is spot-check only |

---

## Deliverables

| Deliverable | Format | Audience |
|-------------|--------|----------|
| Full report | PDF + web page | Public (developers, press, platforms) |
| Platform scorecards | 1-page PDFs | Outreach to specific platforms |
| Raw data | GitHub repo (CSV/JSON) | Researchers, platforms wanting to verify |
| Executive summary | 1-page PDF | CTOs, VPs of Engineering |
| Blog post | Web | Developer audience, social sharing |
| Charts (standalone) | PNG/SVG | Social media, presentations |

---

## Timeline

| Week | Activity | Output |
|------|----------|--------|
| Week 1 | Preparation: accounts, prompts, test suites, infra | Ready to run |
| Week 2 | Baseline collection across all platforms | Raw results per platform |
| Week 3 | LUCID verification on all outputs + analysis | Full dataset |
| Week 4 | Report writing, charts, scorecards | "State of AI Code Quality 2026" |
| Week 5 | Publication + outreach begins | Report live, first emails sent |
