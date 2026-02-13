# LUCID Verified Reconstruction (LVR)

*Created: 2026-02-13*
*Status: Strategy Document — Pre-Pilot*

---

## Executive Summary

LUCID Verified Reconstruction (LVR) is a methodology for taking existing, working applications — particularly those built iteratively with AI tools — and regenerating them as clean, verified codebases while preserving the existing database, infrastructure, and user base.

The core innovation: applying the LUCID verification loop not just to code generation, but to the entire reconstruction pipeline — requirements extraction, architecture design, and code generation — with a concrete verification oracle at every stage.

**Target customer:** Companies that shipped working products using AI tools (Bolt, Lovable, Cursor, Replit, Claude) and now face unmaintainable codebases that engineers refuse to touch.

**Value proposition:** Same app. Same database. Same features. Clean, verified code. Bugs found and eliminated during the process, not after.

---

## The Problem

AI-assisted development tools have created a new class of technical debt. Applications built iteratively over dozens of AI sessions accumulate:

- Hundreds of status/handoff files documenting session-to-session context loss
- Contradictory implementations where later sessions overwrite earlier decisions
- Scaffolded features (empty handlers, TODO comments, mock data) claimed as complete
- Permission models with inconsistent role naming across tables
- Dead code paths from abandoned approaches
- Duplicated logic that diverged over time

The application works. Customers use it. Revenue flows. But:

- New engineers refuse to maintain the codebase (or charge premium rates)
- Every new feature introduces regressions
- Bug fixes create new bugs
- The original AI-assisted approach no longer works because context is too large

**Traditional rewrite is not an option** — it takes months, risks losing features, and the database/user migration is complex. What's needed is a verified reconstruction that preserves everything that works while replacing the code that doesn't.

---

## The Three-Loop Methodology

LVR applies the LUCID verification loop at three stages. Each stage has a concrete oracle — something real to verify against — so nothing is trusted on assertion alone.

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   LOOP 1: REQUIREMENTS EXTRACTION & VERIFICATION        │
│   Oracle: Existing codebase + database + running app    │
│                                                         │
│   AI reads code ──► generates requirements ──►          │
│   LUCID extracts claims ──► verifies against oracle     │
│   ──► failures feed back ──► loop until verified        │
│                                                         │
│   Output: Verified Requirements Specification           │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   LOOP 2: ARCHITECTURE DESIGN & VERIFICATION            │
│   Oracle: Verified requirements + existing infra        │
│                                                         │
│   AI designs system ──► generates architecture ──►      │
│   LUCID extracts claims ──► verifies against oracle     │
│   ──► failures feed back ──► loop until verified        │
│                                                         │
│   Output: Verified Architecture Document                │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   LOOP 3: CODE GENERATION & VERIFICATION                │
│   Oracle: Verified architecture + real database         │
│                                                         │
│   AI generates code ──► LUCID extracts claims ──►       │
│   verifies against oracle + real infrastructure         │
│   ──► failures feed back ──► loop until verified        │
│                                                         │
│   Output: Verified Application Code                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

Each loop eliminates a class of errors before the next loop begins. By the time code is generated, the specification it builds from has already been verified against reality.

---

## Loop 1: Requirements Extraction & Verification

### Input
- Existing application source code
- Database schema (tables, columns, types, constraints, foreign keys)
- RLS policies and permission model
- Auth configuration (roles, providers, session handling)
- Edge functions / API routes
- Running application (for behavioral verification)

### Process

**Step 1: Automated Inventory**

Scan the codebase to produce a raw inventory:

| Category | What to extract | Source |
|----------|----------------|--------|
| Routes | Every navigable page with its component | Router config, `App.tsx`, route definitions |
| Components | Every UI component and what it renders | `src/components/`, page components |
| Database queries | Every Supabase/API call with table, columns, filters | `supabase.from()`, `fetch()`, RPC calls |
| Permissions | Every role check, RLS policy, route guard | Auth context, middleware, RLS SQL |
| Business logic | Calculations, validations, state machines | Service functions, hooks, utilities |
| External integrations | Third-party APIs, webhooks, email triggers | API calls, edge functions |

**Step 2: AI Generates Requirements**

For each route/feature, the AI generates a structured requirement:

```
REQUIREMENT: INV-001 — Invoice List Page

ROUTE: /accounting/invoices
ROLES: admin, accountant, cashier (read-only)
DATABASE: invoices table, joined with customers, line_items
FILTERS: business_id (from auth context), optional date range, status

BEHAVIOR:
- Displays paginated list of invoices for current business
- Columns: invoice number, customer name, date, total, status
- Clicking a row navigates to /accounting/invoices/:id
- "New Invoice" button visible to admin and accountant only
- Filters persist across page navigation

PERMISSIONS:
- RLS: invoices filtered by business_id matching auth.jwt().business_id
- cashier role: read-only (no create/edit/delete buttons)
- admin/accountant: full CRUD

DATA DEPENDENCIES:
- customers table (for customer name display)
- line_items table (for total calculation)
- business_settings (for currency/tax configuration)
```

**Step 3: LUCID Verification**

For each generated requirement, LUCID extracts claims and verifies:

| Claim | Verification method |
|-------|-------------------|
| Route `/accounting/invoices` exists | Grep router config for path match |
| Component renders invoice data | Read component, confirm it queries `invoices` table |
| Filters by `business_id` | Check query code for `.eq('business_id', ...)` AND check RLS policy |
| Cashier is read-only | Check component for role-based conditional rendering |
| "New Invoice" button exists | Grep component for button/link to create route |
| Joins with `customers` table | Check query for `.select('*, customers(*)')` or equivalent |
| Total is calculated from `line_items` | Trace calculation logic in component or query |

**Step 4: Failure Categories**

| Failure type | What it means | Action |
|--------------|--------------|--------|
| Claim contradicts code | AI hallucinated a requirement | Correct requirement to match reality |
| Claim contradicts schema | Code references non-existent table/column | Flag as existing bug — document it |
| Claim contradicts RLS | Permission model inconsistent | Flag as security bug — document it |
| Missing coverage | Routes/features exist but no requirement generated | Generate missing requirements, re-verify |
| Contradictory requirements | Two requirements conflict | Flag for human review — business decision needed |

**Step 5: Iteration**

Loop until:
- Every route has a verified requirement
- Every database table is referenced by at least one requirement
- Every RLS policy is accounted for in permissions
- Zero unresolved contradictions (all flagged for human decision)

### Output

**Verified Requirements Specification** — a structured document where every requirement has been verified against the existing codebase and database. Contradictions and bugs discovered during extraction are documented separately as a **Bug Discovery Report**.

### Bug-Finding Capability

Loop 1 catches bugs that are invisible in code but visible as contradictions in requirements:

| Bug type | How it surfaces |
|----------|----------------|
| Permission gaps | RLS says one thing, component checks another |
| Dead features | Route exists but component is empty/scaffolded |
| Data inconsistency | Query references columns that don't exist in schema |
| Role confusion | Different role names used in different parts of the app |
| Missing validation | Database has constraints the UI doesn't enforce |
| Orphaned tables | Tables exist with no code referencing them |

---

## Loop 2: Architecture Design & Verification

### Input
- Verified Requirements Specification (from Loop 1)
- Existing infrastructure inventory (database, auth, storage, edge functions)
- Technology constraints (framework, hosting, etc.)

### Process

**Step 1: AI Generates Architecture**

From the verified requirements, the AI designs:

| Artifact | Contents |
|----------|----------|
| **Component tree** | Page components, shared components, layout hierarchy |
| **Data layer** | Queries, mutations, real-time subscriptions, caching strategy |
| **Auth model** | Roles, permissions, route guards, RLS alignment |
| **API contracts** | Edge function signatures, request/response types |
| **State management** | What's local, what's global, what's server state |
| **Type definitions** | Domain types, API types, form types, error types |

**Step 2: LUCID Verification**

Verify the architecture against the verified requirements:

| Claim | Verification |
|-------|-------------|
| Every requirement maps to a component | Cross-reference requirement IDs to component tree |
| Every database table has typed queries | Check data layer covers all tables in requirements |
| Permission model matches requirements | Compare auth model to requirement permission specs |
| All API contracts have types for request and response | Check type definitions cover all edge functions |
| No requirement is unaccounted for | Coverage matrix — requirements vs architecture elements |

**Step 3: Infrastructure Compatibility**

Verify the architecture works with existing infrastructure:

| Check | How |
|-------|-----|
| Schema compatibility | Architecture queries reference actual columns/types |
| RLS alignment | New auth model produces same JWT claims existing RLS expects |
| Edge function compatibility | New API contracts match existing edge function signatures |
| Storage compatibility | File upload/download paths match existing bucket structure |
| Auth provider compatibility | Login flow produces tokens the database expects |

### Output

**Verified Architecture Document** — a system design where every component traces to a verified requirement, and every infrastructure dependency has been confirmed against the real system.

---

## Loop 3: Code Generation & Verification

### Input
- Verified Architecture Document (from Loop 2)
- Verified Requirements Specification (from Loop 1)
- Real database (connected, queryable)
- Existing infrastructure (auth, storage, edge functions)

### Process

**Step 1: Generation Order**

Generate in dependency order:

```
1. Type definitions (domain types, API types)
2. Database layer (queries, mutations, subscriptions)
3. Auth layer (context, guards, role checks)
4. Shared components (layout, navigation, common UI)
5. Feature pages (one per requirement group)
6. Integration layer (edge functions, webhooks)
7. App shell (routing, providers, error boundaries)
```

Each stage is independently verified before the next begins.

**Step 2: Per-Component LUCID Loop**

For each generated component:

1. AI generates code from architecture spec + requirements
2. LUCID extracts claims:
   - "This component queries the `invoices` table filtered by `business_id`"
   - "The create button is hidden for `cashier` role"
   - "Form validation requires non-empty customer_id"
3. Verification runs:
   - Type check (TypeScript compiler)
   - Lint (ESLint)
   - Query verification (run against real database, confirm results match)
   - Permission verification (simulate role-based access)
   - Behavioral comparison (does new component produce same output as old for same data?)
4. Failures feed back to AI with specific error
5. Loop until all claims verified

**Step 3: Integration Verification**

After all components pass individually:

- Full build (`npm run build`) — zero errors
- Route-level smoke test — every page loads without console errors
- Data flow verification — queries return expected data for test scenarios
- Permission matrix — every role/route combination checked
- Behavioral comparison — side-by-side with original app on same database

### Output

**Verified Application Code** — a complete, building, working application that:
- Passes all verification at generation time
- Runs against the existing database unchanged
- Preserves all features from the verified requirements
- Has zero scaffolding (no empty handlers, no TODO comments, no mock data)

---

## Tooling: What Exists vs What Needs to Be Built

### Exists Today

| Tool | Status | Used In |
|------|--------|---------|
| LUCID verification loop (claim extraction + formal verify) | Proven (HumanEval 100%, SWE-bench +65%) | Loop 3 |
| GitHub Action (PR-level verification) | Shipped (commit `4d39eb2`) | Post-reconstruction ongoing verification |
| LUCID API (`api.trylucid.dev`) | Live | Loop 3 (per-file verification) |
| Benchmark methodology | Proven across 3 benchmarks | Quality measurement |

### Needs to Be Built

| Tool | Purpose | Used In | Priority |
|------|---------|---------|----------|
| **Codebase Inventory Scanner** | Automated extraction of routes, components, queries, permissions from arbitrary codebases | Loop 1 | Critical |
| **Requirements Generator** | AI pipeline that reads inventory and produces structured requirements | Loop 1 | Critical |
| **Requirements Verifier** | LUCID-style claim extraction and verification for requirements against code/schema | Loop 1 | Critical |
| **Architecture Generator** | AI pipeline that reads verified requirements and produces system design | Loop 2 | High |
| **Architecture Verifier** | Cross-references architecture against requirements + infrastructure | Loop 2 | High |
| **Behavioral Comparator** | Side-by-side comparison of old app vs new app on same data | Loop 3 | Medium |
| **Coverage Matrix** | Tracks which requirements have been verified at which loop | All loops | Medium |

### Build Order

```
Phase 1 (pilot): Manual process with AI assistance
  → Run loops manually using Claude, document the methodology
  → Validates the approach before building tooling

Phase 2 (tooling): Automate the critical path
  → Codebase Inventory Scanner (generic, works on any React/Supabase app)
  → Requirements Generator + Verifier (the core Loop 1 pipeline)
  → Coverage Matrix (tracking and reporting)

Phase 3 (product): Package for self-service
  → Web interface: connect repo, connect database, run LVR
  → Automated architecture generation + verification
  → Behavioral comparator for final validation
```

---

## Pilot: Island Biz

### Why Island Biz Is the Ideal First Target

| Factor | Island Biz | Why it matters |
|--------|-----------|----------------|
| Built with AI | Yes (dozens of Claude sessions) | Exact target customer profile |
| Working product | Yes (users, real data) | Not a toy project — real stakes |
| Codebase size | Large (~200+ components, 50+ routes) | Proves methodology scales |
| Technical debt | Severe (200+ status files, multiple audit reports) | Clear before/after story |
| Database | Supabase (schema, RLS, edge functions) | Infrastructure preservation is testable |
| Accessible | Same machine, full access | No customer coordination for pilot |

### Pilot Scope

**Phase 1: Loop 1 Only (Requirements Extraction)**
- Duration: 1-2 sessions
- Goal: Extract and verify requirements from Island Biz
- Deliverable: Verified Requirements Specification + Bug Discovery Report
- Success criteria: Every route accounted for, contradictions documented, at least 3 bugs discovered that exist in the original app

**Phase 2: Loop 2 (Architecture)**
- Duration: 1 session
- Goal: Design verified architecture from requirements
- Deliverable: Verified Architecture Document
- Success criteria: 100% requirement coverage, infrastructure compatibility confirmed

**Phase 3: Loop 3 (Code Generation)**
- Duration: 3-5 sessions (largest phase)
- Goal: Regenerate application through LUCID loop
- Deliverable: Working application on same database
- Success criteria: All features functional, zero scaffolding, build passes, behavioral comparison matches original

**Phase 4: Comparison & Case Study**
- Duration: 1 session
- Goal: Quantify improvement
- Deliverable: Before/after case study with metrics
- Metrics:
  - Lines of code (expect reduction)
  - Number of files (expect significant reduction)
  - Scaffolding patterns found in old vs new (expect zero in new)
  - Bugs discovered during Loop 1 (expect 5-20)
  - TypeScript strict mode compliance (expect 100% in new)
  - Build warnings (expect zero in new)

### Expected Outcomes

1. **Bug discovery:** Loop 1 requirements extraction will surface 5-20 bugs in the existing Island Biz app (permission inconsistencies, dead features, data access issues)
2. **Code reduction:** Regenerated codebase will be 40-60% smaller (no status files, no duplicated logic, no dead code)
3. **Quality improvement:** Zero scaffolding patterns, strict TypeScript, consistent patterns
4. **Case study:** Publishable before/after comparison for marketing

---

## Go-to-Market

### Pricing Model

| Tier | Scope | Price | Margin |
|------|-------|-------|--------|
| **Assessment** | Loop 1 only — requirements extraction, bug discovery report | $2,500-$5,000 | ~80% |
| **Full Reconstruction** | All 3 loops — verified requirements + architecture + code | $10,000-$50,000 (based on app complexity) | ~60-70% |
| **Ongoing Verification** | GitHub Action subscription post-reconstruction | $29-99/mo | ~80% |

**Assessment tier is the wedge.** Low commitment, immediate value (bug discovery), leads to full reconstruction. Even if the customer doesn't proceed to full reconstruction, they get a verified spec of their own app — which has standalone value.

### Customer Acquisition Funnel

```
1. Content marketing: "Your AI-built app has bugs you don't know about"
   → Blog posts, Show HN, Twitter threads, case study from Island Biz pilot

2. Free assessment teaser: Automated codebase scan (scaffolding detection,
   dead code, permission inconsistencies) — delivered as report
   → trylucid.dev/assess (connect GitHub repo, get report)

3. Paid assessment: Full Loop 1 — verified requirements + bug discovery
   → $2,500-$5,000

4. Full reconstruction: All 3 loops
   → $10,000-$50,000

5. Ongoing: GitHub Action subscription
   → $29-99/mo
```

### Target Customer Segments

| Segment | Pain level | Willingness to pay | How to reach |
|---------|-----------|-------------------|--------------|
| **Solo founders with AI-built MVPs** | High (can't hire engineers to maintain) | $2.5K-$10K | Indie Hackers, Show HN, Twitter |
| **Small teams (2-10) post-AI-build** | Very high (blocking growth) | $10K-$25K | Direct outreach, content marketing |
| **Agencies building for clients** | Extreme (reputation risk) | $25K-$50K per client project | Agency partnerships |
| **Enterprise modernization** | Variable | $100K+ | Longer sales cycle, different positioning |

### Competitive Positioning

**LVR is not a rewrite.** A rewrite throws away the old system and builds new. LVR is a verified reconstruction — the old system is the specification, the database stays, the verification is formal.

| Approach | Risk | Duration | Bug detection | Cost |
|----------|------|----------|--------------|------|
| Traditional rewrite | High (Spolsky's law) | Months | None (new bugs likely) | $50K-$500K |
| Hire engineers to refactor | Medium | Months | Some (code review) | $30K-$200K |
| **LVR** | Low (verified at every stage) | Days to weeks | Systematic (Loop 1 bug discovery) | $10K-$50K |
| Keep patching with AI | High (debt compounds) | Ongoing | None | Ongoing time cost |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Requirements extraction misses edge cases | Medium | High — regenerated app lacks features | Behavioral comparator catches differences; coverage matrix ensures completeness |
| Pilot takes longer than expected | Medium | Low — learning, not revenue | Time-box each phase; document what slows down for tooling priorities |
| Customer apps use stacks we don't support | Medium | Medium — limits market | Start with React + Supabase (most common AI-built stack); expand based on demand |
| AI-built app market is smaller than expected | Low | High — no customers | Assessment tier works for ANY messy codebase, not just AI-built ones |
| Existing database has schema issues | Medium | Medium — blocks Loop 3 | Loop 1 catches schema issues; document as bugs, fix before Loop 3 |
| Customer expects perfection | Low | Medium — disappointment | Set expectations: LVR catches implementation and structural bugs, not wrong business rules (unless they contradict the schema) |

---

## Relationship to Existing LUCID Assets

| Asset | Role in LVR |
|-------|------------|
| **Architecture paper** | Theoretical foundation — extend Section 4 to cover multi-loop verification |
| **Provisional patent** | LVR strengthens the patent claim — verification loop applied beyond code generation |
| **HumanEval/SWE-bench results** | Proves Loop 3 works at scale |
| **RLVF negative scaling result** | Proves verification can't be baked into models — must remain a runtime process — this is why LVR needs to exist as a service |
| **GitHub Action** | Post-reconstruction ongoing verification — recurring revenue |
| **trylucid.dev** | Landing page for LVR service + assessment signup |
| **FrankLabs agents** | Sales pipeline for LVR engagements |

---

## Intellectual Property Considerations

The provisional patent (63/980,048) covers "iterative formal verification of AI-generated code using a hallucination-verification loop." LVR extends this to:

1. Iterative formal verification of AI-generated **requirements** (Loop 1)
2. Iterative formal verification of AI-generated **architecture** (Loop 2)
3. The three-loop pipeline as a unified methodology

**Recommendation:** Include LVR methodology in the non-provisional patent filing (deadline: February 11, 2027). The extension from code-only to full-lifecycle verification is a meaningful broadening of claims.

---

## Immediate Next Steps

1. **Run the Island Biz pilot** — Loop 1 first (requirements extraction)
2. **Document everything** — the pilot IS the case study
3. **Quantify bug discovery** — how many real bugs does Loop 1 find?
4. **Measure time** — how long does each loop take for a real app?
5. **Build the Assessment tier** — automated codebase scan → report → paid engagement
6. **Update trylucid.dev** — add LVR offering alongside GitHub Action
7. **Include in non-provisional patent** — extend claims to multi-loop verification

---

## Success Metrics

| Metric | Target | Measured at |
|--------|--------|-------------|
| Bugs discovered in Island Biz (Loop 1) | 5+ real bugs | End of pilot Phase 1 |
| Code size reduction | 40%+ fewer lines | End of pilot Phase 3 |
| Scaffolding in regenerated code | Zero | End of pilot Phase 3 |
| Time for full reconstruction | < 10 sessions | End of pilot |
| First paying customer | 1 assessment sold | Within 30 days of case study |
| Monthly recurring (GitHub Action) | 3 subscriptions | Within 60 days |
