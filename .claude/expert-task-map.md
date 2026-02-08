# LUCID — FrankLabs Expert Task Map

*Created: 2026-02-07*
*Client Workspace: lucid*
*Source Plan: .claude/production-plan.md*

---

## Expert Roster (LUCID Client)

| Expert | Role | Assigned Phases | Task Count |
|--------|------|-----------------|------------|
| **Sam** | SDR | 1.3, 3.8, 5.1-5.5 | 11 |
| **Jordan** | Marketing / Content | 2.1-2.6, 3.6, 4.1-4.5 | 16 |
| **Riley** | Engineering / Security | 1.1-1.2, 1.4-1.5, 3.1-3.5, 3.7 | 14 |
| **Taylor** | Operations / Chief of Staff | All phases (coordination) | 8 |
| **Alex** | Sales Lead | 5.1-5.5 | 8 |
| **Drew** | Finance / Billing | 3.5 | 3 |
| **Morgan** | Onboarding | 3.8 | 3 |
| **Casey** | Support | 3.8 (post-launch) | 2 |

**Total tasks: 65** (expanded from 31 plan items into actionable expert proposals)

---

## Dependency Chain

```
Phase 1 (Publication)
  ├─ 1.1 Zenodo ──────────────────────┐
  ├─ 1.2 TechRxiv                     │
  ├─ 1.3 arXiv Endorser (parallel)    ├──▶ Phase 2 (Distribution)
  ├─ 1.4 IP.com                       │      needs DOI from 1.1
  └─ 1.5 SSRN                         │
                                       │
Phase 2 (Distribution) ◀──────────────┘
  ├─ 2.1 Blog Post ───────────────────┐
  ├─ 2.2 HN (needs 2.1) ◀────────────┤
  ├─ 2.3 LinkedIn                     ├──▶ Phase 3 (SaaS)
  ├─ 2.4 Dev.to                       │      needs audience signal
  ├─ 2.5 Twitter/X                    │
  └─ 2.6 TDS                          │
                                       │
Phase 3 (SaaS MVP) ◀──────────────────┘
  ├─ 3.1 Architecture ────▶ 3.2-3.5 (all depend on 3.1)
  ├─ 3.2 Auth + GitHub
  ├─ 3.3 Audit Pipeline
  ├─ 3.4 Dashboard
  ├─ 3.5 Stripe ──────────▶ 3.7 Deploy
  ├─ 3.6 Landing Page
  ├─ 3.7 Deploy ──────────▶ 3.8 First Customers
  └─ 3.8 First 10 Customers

Phase 4 (Conferences) — runs parallel to Phase 3
  ├─ 4.1 CHI 2026 (URGENT: Feb 12 deadline)
  ├─ 4.2 ICML (Apr 24)
  ├─ 4.3 ACL (Mar 14)
  ├─ 4.4 NeurIPS (~May)
  └─ 4.5 ICSE 2027

Phase 5 (Acquirer Visibility) — after Phase 3 launch
  ├─ 5.1-5.4 (parallel outreach campaigns)
  └─ 5.5 Network building (ongoing)
```

---

## Phase 1: Publication & Defensive IP

### TASK-1.1: Zenodo Publication
**Owner:** Riley (Engineering)
**Priority:** critical
**Timeline:** Day 1
**Depends on:** Nothing (first task)
**Blocks:** 2.1, 2.2, 2.3, 2.4, 2.5, 2.6 (all distribution needs DOI)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.1a | Create Zenodo account for Ty Wells | Riley | `ops.account_setup` | 0.90 | Needs Ty's email — propose with instructions |
| 1.1b | Upload PDF to Zenodo | Riley | `ops.document_publish` | 0.95 | File: arxiv-submission/main.pdf |
| 1.1c | Fill metadata (title, abstract, keywords, CC-BY-4.0) | Riley | `ops.document_publish` | 0.95 | Pull from main.tex frontmatter |
| 1.1d | Publish and record DOI | Riley | `ops.document_publish` | 0.95 | Record DOI back to production-plan.md |

**Approval level:** Copilot (human approves account creation + publication)
**Deliverable:** DOI string recorded in plan

---

### TASK-1.2: TechRxiv Publication
**Owner:** Riley (Engineering)
**Priority:** high
**Timeline:** Day 1-2
**Depends on:** Nothing (parallel to 1.1)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.2a | Create TechRxiv account | Riley | `ops.account_setup` | 0.90 | IEEE-affiliated preprint server |
| 1.2b | Upload PDF with metadata | Riley | `ops.document_publish` | 0.95 | Category: CS → Software Engineering / AI |
| 1.2c | Submit for moderation | Riley | `ops.document_publish` | 0.90 | ~4 business day turnaround |

**Approval level:** Copilot
**Deliverable:** Submission confirmation, then DOI when accepted

---

### TASK-1.3: arXiv Endorser Outreach
**Owner:** Sam (SDR)
**Priority:** high
**Timeline:** Days 1-21 (parallel)
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.3a | Research endorser candidates from cited papers | Sam | `lead.research` | 0.85 | Check cs.SE endorser list, match against references.bib authors |
| 1.3b | Enrich contact info for 5 candidates | Sam | `lead.enrich` | 0.80 | University email addresses, Google Scholar profiles |
| 1.3c | Draft professional outreach email | Jordan | `content.draft` | 0.90 | Include paper abstract, explain endorsement request |
| 1.3d | Send outreach to 3-5 candidates | Sam | `email.send` | 0.85 | Personalized per recipient |
| 1.3e | Follow up after 7 days if no response | Sam | `email.send` | 0.85 | Polite follow-up sequence |
| 1.3f | Submit to arXiv once endorsed | Riley | `ops.document_publish` | 0.90 | Category: cs.SE, cross-list cs.AI + cs.CL |

**Approval level:** Copilot (all emails need human review)
**Deliverable:** arXiv submission ID or documented rejection reasons

---

### TASK-1.4: IP.com Defensive Publication
**Owner:** Riley (Engineering)
**Priority:** medium
**Timeline:** Days 2-5
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.4a | Create IP.com account | Riley | `ops.account_setup` | 0.85 | Requires purchase of publishing voucher |
| 1.4b | Purchase publishing voucher | Drew | `invoice.create` | 0.80 | Cost TBD — propose with price for approval |
| 1.4c | Upload paper to IP.com PAD | Riley | `ops.document_publish` | 0.90 | Prior Art Database publication |
| 1.4d | Confirm indexing by patent examiners | Riley | `ops.document_publish` | 0.85 | Verify searchable in PAD |

**Approval level:** Copilot (payment requires approval)
**Deliverable:** IP.com publication confirmation

---

### TASK-1.5: SSRN Publication
**Owner:** Riley (Engineering)
**Priority:** medium
**Timeline:** Days 2-5
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.5a | Upload to SSRN CS Research Network | Riley | `ops.document_publish` | 0.90 | Standard preprint upload |
| 1.5b | Confirm indexing | Riley | `ops.document_publish` | 0.85 | 1-3 business days |

**Approval level:** Copilot
**Deliverable:** SSRN paper URL

---

### Phase 1 Coordination
**Owner:** Taylor (Operations)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 1.C1 | Create Phase 1 tracker with deadlines | Taylor | `ops.daily_summary` | 0.95 | Track all 5 publication outlets |
| 1.C2 | Daily status report on publication progress | Taylor | `report.generate` | 0.95 | Until all 5 are submitted |

---

## Phase 2: Distribution Blitz

### TASK-2.1: Blog Post — Narrative Version
**Owner:** Jordan (Marketing)
**Priority:** critical
**Timeline:** Week 2 (after DOI from 1.1)
**Depends on:** 1.1 (needs DOI link)
**Blocks:** 2.2 (HN needs blog URL)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.1a | Draft blog post: "I Built a Tool That Treats AI Hallucination as a Feature" | Jordan | `content.draft` | 0.90 | Source: docs/paper.md sections 1, 3, 5, 6 |
| 2.1b | Create convergence chart visual (57.3% → 90.8%) | Jordan | `content.draft` | 0.85 | Data from paper Table 1 |
| 2.1c | Write accessible neuroscience parallel section | Jordan | `content.draft` | 0.85 | Simplify paper Section 3 for general audience |
| 2.1d | Write protein hallucination / Nobel Prize hook | Jordan | `content.draft` | 0.90 | The "Baker Lab did this for proteins" angle |
| 2.1e | Add DOI link + GitHub repo link | Jordan | `content.draft` | 0.95 | From Zenodo DOI + repo URL |
| 2.1f | Publish on Medium (or personal site) | Jordan | `content.publish` | 0.85 | Propose final draft for approval before publish |

**Approval level:** Copilot (all content reviewed before publication)
**Deliverable:** Published blog URL

---

### TASK-2.2: Hacker News — Show HN
**Owner:** Jordan (Marketing) + Sam (SDR)
**Priority:** high
**Timeline:** Week 2, Wednesday ~8am EST
**Depends on:** 2.1 (needs blog URL)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.2a | Craft HN title with contrarian hallucination-as-feature angle | Jordan | `content.draft` | 0.85 | A/B test 3 title options, propose best |
| 2.2b | Submit to HN as Show HN | Jordan | `social.post` | 0.80 | Wednesday 8am EST optimal timing |
| 2.2c | Monitor comments and flag questions needing Ty's response | Sam | `support.monitor` | 0.85 | Real-time monitoring for first 6 hours |
| 2.2d | Draft response suggestions for technical questions | Jordan | `content.draft` | 0.80 | Ty approves before posting |
| 2.2e | Track upvotes + referral traffic | Taylor | `report.generate` | 0.90 | Hourly updates for first day |

**Approval level:** Copilot (HN posts are high-stakes, human writes final comments)
**Deliverable:** HN post URL + engagement metrics

---

### TASK-2.3: LinkedIn Article
**Owner:** Jordan (Marketing)
**Priority:** high
**Timeline:** Week 2
**Depends on:** 1.1 (needs DOI)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.3a | Write business-framed article (market gap + acquirer value) | Jordan | `content.draft` | 0.85 | Focus: $4.5B market, GitHub/AWS gap, LUCID fills it |
| 2.3b | Identify AI/dev tools leaders to tag | Sam | `lead.research` | 0.80 | LinkedIn profiles of GitHub, Anthropic, AWS people |
| 2.3c | Publish article | Jordan | `content.publish` | 0.85 | Ty's LinkedIn account |
| 2.3d | Share in relevant LinkedIn groups | Jordan | `social.post` | 0.80 | AI, Dev Tools, Software Engineering groups |
| 2.3e | Track engagement metrics | Taylor | `report.generate` | 0.90 | Views, reactions, comments, shares |

**Approval level:** Copilot
**Deliverable:** LinkedIn article URL + engagement report

---

### TASK-2.4: Dev.to Developer Tutorial
**Owner:** Jordan (Marketing)
**Priority:** medium
**Timeline:** Week 2-3
**Depends on:** 1.1 (needs DOI)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.4a | Write hands-on tutorial: "How to Use AI Hallucination to Generate Your Software Spec" | Jordan | `content.draft` | 0.85 | Include CLI code examples from README.md |
| 2.4b | Include installation + usage walkthrough | Jordan | `content.draft` | 0.90 | npm install, lucid audit, lucid verify |
| 2.4c | Add tags: #ai #machinelearning #softwareengineering #devtools | Jordan | `content.publish` | 0.95 | Dev.to tag format |
| 2.4d | Publish on Dev.to | Jordan | `content.publish` | 0.85 | Propose final for approval |

**Approval level:** Copilot
**Deliverable:** Dev.to tutorial URL

---

### TASK-2.5: Twitter/X Thread
**Owner:** Jordan (Marketing)
**Priority:** high
**Timeline:** Week 2
**Depends on:** 1.1 (needs DOI)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.5a | Draft visual thread (8-12 tweets) with convergence data | Jordan | `content.draft` | 0.85 | Key data points from paper |
| 2.5b | Identify researchers to tag (cited paper authors) | Sam | `lead.research` | 0.80 | Twitter handles for Friston, Clark, Carhart-Harris, etc. |
| 2.5c | Post thread | Jordan | `social.post` | 0.80 | Optimal timing for AI/tech audience |
| 2.5d | Track engagement + retweets | Taylor | `report.generate` | 0.90 | Impressions, engagements, profile visits |

**Approval level:** Copilot
**Deliverable:** Thread URL + engagement metrics

---

### TASK-2.6: Towards Data Science Submission
**Owner:** Jordan (Marketing)
**Priority:** medium
**Timeline:** Week 2-3
**Depends on:** 1.1 (needs DOI)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.6a | Write TDS-formatted article (practitioner-focused) | Jordan | `content.draft` | 0.80 | MUST be human-quality, not AI-generated style |
| 2.6b | Submit via TDS submission form | Jordan | `content.publish` | 0.75 | ~1 week editorial review |
| 2.6c | Track editorial response | Taylor | `ops.daily_summary` | 0.90 | Follow up if no response in 10 days |

**Approval level:** Copilot (TDS has high editorial bar)
**Deliverable:** TDS acceptance or documented rejection

---

### Phase 2 Coordination
**Owner:** Taylor (Operations)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 2.C1 | Create content calendar for all 6 distribution channels | Taylor | `ops.daily_summary` | 0.95 | Sequence: Blog → HN → LinkedIn → Dev.to → Twitter → TDS |
| 2.C2 | Weekly distribution metrics report | Taylor | `report.generate` | 0.95 | Aggregate all channel performance |
| 2.C3 | Coordinate Jordan + Sam handoffs | Taylor | `ops.daily_summary` | 0.90 | Sam researches leads/contacts, Jordan writes content |

---

## Phase 3: SaaS MVP

### TASK-3.1: Architecture & Design
**Owner:** Riley (Engineering)
**Priority:** critical
**Timeline:** Week 3
**Depends on:** Nothing (can start parallel to Phase 2)
**Blocks:** 3.2, 3.3, 3.4, 3.5, 3.6, 3.7

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.1a | Define tech stack document (Next.js + Supabase + Inngest + Stripe) | Riley | `ops.document_publish` | 0.95 | Architecture decision record |
| 3.1b | Design database schema (users, orgs, repos, audits, claims, verdicts) | Riley | `ops.document_publish` | 0.90 | Type-first: types before tables |
| 3.1c | Design API routes (REST contract) | Riley | `ops.document_publish` | 0.90 | OpenAPI-style route map |
| 3.1d | Type-first contract design (TypeScript interfaces) | Riley | `ops.document_publish` | 0.90 | Domain types, result types, error states |

**Approval level:** Copilot (architecture requires human sign-off)
**Deliverable:** Approved architecture document with types

---

### TASK-3.2: Authentication & GitHub Integration
**Owner:** Riley (Engineering)
**Priority:** high
**Timeline:** Week 3-4
**Depends on:** 3.1

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.2a | Implement GitHub OAuth signup | Riley | `code.implement` | 0.85 | Supabase Auth + GitHub provider |
| 3.2b | Create GitHub App for repo access | Riley | `ops.account_setup` | 0.80 | Needs repo read permissions |
| 3.2c | Wire Supabase Auth integration | Riley | `code.implement` | 0.90 | RLS policies, session management |

**Approval level:** Copilot
**Deliverable:** Working auth flow with GitHub repo access

---

### TASK-3.3: Audit Pipeline
**Owner:** Riley (Engineering)
**Priority:** critical
**Timeline:** Week 4-5
**Depends on:** 3.1, 3.2

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.3a | Build Inngest pipeline: clone → extract → verify → report | Riley | `code.implement` | 0.80 | Wrap existing CLI logic |
| 3.3b | Wrap CLI claim-extractor in serverless function | Riley | `code.implement` | 0.85 | src/lib/claim-extractor.ts |
| 3.3c | Wrap CLI verifier in serverless function | Riley | `code.implement` | 0.85 | src/lib/verifier.ts |
| 3.3d | Handle long-running operations (15+ min audits) | Riley | `code.implement` | 0.75 | Inngest step functions for timeout handling |

**Approval level:** Copilot
**Deliverable:** End-to-end audit pipeline running on Inngest

---

### TASK-3.4: Dashboard & Reports
**Owner:** Riley (Engineering) + Jordan (Marketing)
**Priority:** high
**Timeline:** Week 5-6
**Depends on:** 3.3

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.4a | Build audit results dashboard (verdicts, evidence, compliance score) | Riley | `code.implement` | 0.85 | React components for verdict display |
| 3.4b | Build gap report viewer | Riley | `code.implement` | 0.85 | Show what's missing between docs and code |
| 3.4c | Implement PDF export | Riley | `code.implement` | 0.80 | Generate shareable audit reports |

**Approval level:** Copilot
**Deliverable:** Working dashboard with report generation

---

### TASK-3.5: Stripe Integration
**Owner:** Riley (Engineering) + Drew (Finance)
**Priority:** high
**Timeline:** Week 5-6
**Depends on:** 3.1

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.5a | Create Stripe product: Single Audit ($149) | Drew | `invoice.create` | 0.90 | Product + price in Stripe dashboard |
| 3.5b | Implement checkout flow | Riley | `code.implement` | 0.85 | Stripe Checkout session → redirect |
| 3.5c | Implement webhook handling for payment confirmation | Riley | `code.implement` | 0.80 | checkout.session.completed → trigger audit |

**Approval level:** Copilot (payment flow requires human verification)
**Deliverable:** Working payment → audit trigger flow

---

### TASK-3.6: Landing Page
**Owner:** Jordan (Marketing) + Riley (Engineering)
**Priority:** high
**Timeline:** Week 5-6
**Depends on:** 1.1 (needs DOI for citation)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.6a | Write hero copy: "Does your code actually do what your docs claim?" | Jordan | `content.draft` | 0.90 | Value prop + pain point |
| 3.6b | Design convergence chart component (social proof) | Jordan | `content.draft` | 0.85 | 57.3% → 90.8% visual |
| 3.6c | Write paper citation section (credibility) | Jordan | `content.draft` | 0.90 | Zenodo DOI + author info |
| 3.6d | Write CTA copy and pricing section | Jordan | `content.draft` | 0.85 | $149/audit, clear value prop |
| 3.6e | Implement landing page in Next.js | Riley | `code.implement` | 0.85 | From Jordan's approved copy |

**Approval level:** Copilot
**Deliverable:** Published landing page at lucid domain

---

### TASK-3.7: Deploy
**Owner:** Riley (Engineering)
**Priority:** critical
**Timeline:** Week 6-7
**Depends on:** 3.2, 3.3, 3.4, 3.5, 3.6

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.7a | Deploy to Vercel | Riley | `code.deploy` | 0.90 | Standard Next.js deployment |
| 3.7b | Configure custom domain | Riley | `ops.account_setup` | 0.85 | DNS + Vercel domain settings |
| 3.7c | Set production environment variables | Riley | `code.deploy` | 0.85 | Supabase, Stripe, Anthropic keys |

**Approval level:** Copilot
**Deliverable:** Live SaaS at custom domain

---

### TASK-3.8: First 10 Customers
**Owner:** Sam (SDR) + Morgan (Onboarding)
**Priority:** critical
**Timeline:** Week 7-8
**Depends on:** 3.7

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.8a | Draft Product Hunt launch copy | Jordan | `content.draft` | 0.85 | Tagline, description, screenshots |
| 3.8b | Launch on Product Hunt | Jordan | `social.post` | 0.80 | Tuesday launch for max visibility |
| 3.8c | Identify 20 open-source projects for free audits | Sam | `lead.research` | 0.85 | High-star repos with docs claims |
| 3.8d | Send free audit offers to maintainers | Sam | `email.send` | 0.80 | Personalized per project |
| 3.8e | Run free audits and deliver results | Riley | `ops.document_publish` | 0.85 | LUCID CLI → PDF report |
| 3.8f | Onboard paying customers from inbound | Morgan | `onboarding.guide` | 0.85 | Setup, first audit, results review |
| 3.8g | Collect testimonials from satisfied users | Morgan | `content.draft` | 0.80 | Quote + permission for marketing use |
| 3.8h | Set up support inbox for customer issues | Casey | `support.ticket_create` | 0.90 | Triage bugs vs. feature requests |

**Approval level:** Copilot (outreach + customer interactions need review)
**Deliverable:** 10+ paying customers with testimonials

---

### Phase 3 Coordination
**Owner:** Taylor (Operations)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 3.C1 | Weekly engineering sprint report | Taylor | `report.generate` | 0.95 | Track Riley's progress against plan |
| 3.C2 | Coordinate Riley ↔ Jordan handoffs (landing page) | Taylor | `ops.daily_summary` | 0.90 | Copy approved → implementation |
| 3.C3 | Track deployment checklist | Taylor | `ops.daily_summary` | 0.95 | Pre-launch verification |

---

## Phase 4: Conference Pipeline

### TASK-4.1: CHI 2026 Tools for Thought Workshop
**Owner:** Jordan (Marketing)
**Priority:** URGENT (Feb 12 deadline — 5 days)
**Timeline:** Days 1-5
**Depends on:** Nothing (parallel, time-critical)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 4.1a | Check if CHI 2026 Tools for Thought deadline is still open | Jordan | `lead.research` | 0.90 | Verify Feb 12 is still accepting |
| 4.1b | Adapt paper for HCI angle (tools-for-thought framing) | Jordan | `content.draft` | 0.75 | Reframe: LUCID as cognitive tool, not just SE tool |
| 4.1c | Submit to CHI workshop | Jordan | `content.publish` | 0.70 | Requires specific format compliance |

**Approval level:** Copilot (academic submission needs human review)
**Deliverable:** CHI submission confirmation or documented decision to skip

---

### TASK-4.2: ICML 2026 Workshops
**Owner:** Jordan (Marketing) + Taylor (Operations)
**Priority:** medium
**Timeline:** March-April
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 4.2a | Monitor accepted workshops (announced ~March 20) | Taylor | `ops.daily_summary` | 0.90 | Set calendar reminder |
| 4.2b | Identify relevant workshops (AI reliability, SE, hallucination) | Jordan | `lead.research` | 0.85 | Match LUCID themes |
| 4.2c | Adapt paper for workshop format + submit by April 24 | Jordan | `content.draft` | 0.80 | Workshop papers are typically shorter |

**Approval level:** Copilot
**Deliverable:** ICML workshop submission

---

### TASK-4.3: ACL 2026 via Rolling Review
**Owner:** Jordan (Marketing)
**Priority:** high
**Timeline:** March
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 4.3a | Prepare ACL Rolling Review submission (March cycle) | Jordan | `content.draft` | 0.75 | NLP/CL angle: legal language forcing |
| 4.3b | Submit to ARR by March 14 | Jordan | `content.publish` | 0.70 | Commit to ACL 2026 or EMNLP 2026 |

**Approval level:** Copilot
**Deliverable:** ARR submission confirmation

---

### TASK-4.4: NeurIPS 2026
**Owner:** Jordan (Marketing) + Taylor (Operations)
**Priority:** medium
**Timeline:** March-May
**Depends on:** Nothing

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 4.4a | Monitor call for papers (~March 2026) | Taylor | `ops.daily_summary` | 0.90 | Set monitoring schedule |
| 4.4b | Prepare main paper or workshop submission | Jordan | `content.draft` | 0.75 | Decide main vs. workshop based on reviewer feedback |

**Approval level:** Copilot
**Deliverable:** NeurIPS submission

---

### TASK-4.5: ICSE 2027
**Owner:** Taylor (Operations)
**Priority:** low (long timeline)
**Timeline:** Month 4-6
**Depends on:** Conference feedback from 4.1-4.4

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 4.5a | Monitor ICSE 2027 call for papers | Taylor | `ops.daily_summary` | 0.90 | SE conference — core venue for LUCID |
| 4.5b | Prepare submission with empirical results | Jordan | `content.draft` | 0.70 | Include SaaS customer data if available |

**Approval level:** Copilot
**Deliverable:** ICSE submission plan

---

## Phase 5: Acquirer Visibility

### TASK-5.1: GitHub/Microsoft Outreach
**Owner:** Alex (Sales Lead) + Sam (SDR)
**Priority:** high
**Timeline:** Month 3-4
**Depends on:** 3.7 (needs live SaaS)

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 5.1a | Research GitHub Spec Kit team members | Sam | `lead.research` | 0.80 | LinkedIn, GitHub profiles, public talks |
| 5.1b | Research Copilot team members | Sam | `lead.research` | 0.80 | Product managers, engineering leads |
| 5.1c | Enrich contact info | Sam | `lead.enrich` | 0.75 | Email, LinkedIn, mutual connections |
| 5.1d | Draft outreach: LUCID as complement to Spec Kit | Alex | `proposal.generate` | 0.80 | "You generate specs, we verify them" |
| 5.1e | Send personalized outreach | Alex | `email.send` | 0.75 | Include paper DOI + live demo link |

**Approval level:** Copilot (acquirer outreach is high-stakes)
**Deliverable:** Response from GitHub/Microsoft contact

---

### TASK-5.2: Anthropic Outreach
**Owner:** Alex (Sales Lead) + Sam (SDR)
**Priority:** high
**Timeline:** Month 3-4
**Depends on:** 3.7

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 5.2a | Identify relevant Anthropic contacts (developer relations, partnerships) | Sam | `lead.research` | 0.80 | LUCID is built on Claude SDK |
| 5.2b | Draft outreach: "reframes hallucination as feature, not bug" | Alex | `proposal.generate` | 0.85 | Natural alignment narrative |
| 5.2c | Send with paper + tool links | Alex | `email.send` | 0.75 | Personalized |

**Approval level:** Copilot
**Deliverable:** Response from Anthropic contact

---

### TASK-5.3: AWS/Kiro Team Outreach
**Owner:** Alex (Sales Lead) + Sam (SDR)
**Priority:** high
**Timeline:** Month 3-4
**Depends on:** 3.7

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 5.3a | Identify Kiro team contacts | Sam | `lead.research` | 0.75 | AWS product team for spec-driven dev |
| 5.3b | Draft outreach: LUCID as verification layer for Kiro | Alex | `proposal.generate` | 0.80 | "Kiro generates, LUCID verifies" |
| 5.3c | Send with paper + tool links | Alex | `email.send` | 0.75 | Personalized |

**Approval level:** Copilot
**Deliverable:** Response from AWS/Kiro contact

---

### TASK-5.4: Snyk/SonarSource Outreach
**Owner:** Alex (Sales Lead) + Sam (SDR)
**Priority:** medium
**Timeline:** Month 4-5
**Depends on:** 3.7

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 5.4a | Research Snyk + SonarSource M&A contacts | Sam | `lead.research` | 0.75 | BD, partnerships, product teams |
| 5.4b | Draft outreach: AI-native code quality + specification verification | Alex | `proposal.generate` | 0.80 | Code quality → spec quality extension |
| 5.4c | Send with paper + tool links | Alex | `email.send` | 0.75 | Personalized |

**Approval level:** Copilot
**Deliverable:** Response from Snyk or SonarSource contact

---

### TASK-5.5: Investor/Acquirer Network
**Owner:** Alex (Sales Lead) + Taylor (Operations)
**Priority:** medium
**Timeline:** Month 3-6 (ongoing)
**Depends on:** 3.7 + conference acceptances

| # | Action | Expert | Action Type | Confidence | Notes |
|---|--------|--------|-------------|------------|-------|
| 5.5a | Research AI meetups/events in Ty's region | Sam | `lead.research` | 0.80 | Upcoming events, speaking slots |
| 5.5b | Identify AI-focused VCs for introductions | Sam | `lead.research` | 0.80 | Firms with dev tools portfolio |
| 5.5c | Draft intro materials (one-pager, deck outline) | Alex | `proposal.generate` | 0.80 | Paper + SaaS + metrics summary |
| 5.5d | Research YC application timeline (W2027 or S2026) | Taylor | `lead.research` | 0.85 | Deadline, requirements, fit assessment |
| 5.5e | Track all acquirer conversations in pipeline | Taylor | `ops.daily_summary` | 0.90 | CRM-style tracking of relationship stage |

**Approval level:** Copilot
**Deliverable:** 2+ active acquirer conversations

---

## Execution Schedule (Week-by-Week)

| Week | Primary Focus | Experts Active | Critical Path |
|------|---------------|----------------|---------------|
| **1** | Publications (1.1-1.5) + CHI deadline (4.1) | Riley, Sam, Jordan, Taylor | Zenodo DOI + CHI submission |
| **2** | Distribution blitz (2.1-2.6) | Jordan, Sam, Taylor | Blog → HN → LinkedIn |
| **3** | SaaS architecture (3.1) + continued distribution | Riley, Jordan, Taylor | Architecture approval |
| **4** | Auth + pipeline (3.2-3.3) | Riley, Taylor | GitHub OAuth + Inngest pipeline |
| **5** | Dashboard + Stripe + landing (3.4-3.6) | Riley, Jordan, Drew, Taylor | Payment flow + landing page |
| **6** | Deploy + pre-launch (3.7) | Riley, Jordan, Taylor | Production deployment |
| **7** | Launch + first customers (3.8) | Sam, Jordan, Morgan, Casey, Taylor | Product Hunt + outreach |
| **8** | Customer acquisition + testimonials | Sam, Morgan, Casey, Taylor | 10 paying customers |
| **9-12** | Conference submissions (4.2-4.4) | Jordan, Taylor | ICML, ACL, NeurIPS |
| **12-16** | Acquirer outreach (5.1-5.5) | Alex, Sam, Taylor | GitHub, Anthropic, AWS |
| **16-24** | Sustained outreach + network | Alex, Sam, Taylor | 2+ active conversations |

---

## Expert Workload Summary

| Expert | Weeks 1-2 | Weeks 3-6 | Weeks 7-8 | Weeks 9-24 |
|--------|-----------|-----------|-----------|------------|
| **Riley** | Publications (5 platforms) | SaaS build (full-time) | Deploy + free audits | Maintenance |
| **Jordan** | CHI + blog + social content | Landing page copy + TDS | Product Hunt copy | Conference papers |
| **Sam** | Endorser outreach + lead research | Contact enrichment | Customer prospecting | Acquirer research |
| **Taylor** | Phase tracking + coordination | Sprint reports + handoffs | Launch coordination | Pipeline tracking |
| **Alex** | — | — | — | Acquirer outreach (full-time) |
| **Drew** | — | Stripe setup + IP.com purchase | — | — |
| **Morgan** | — | — | Customer onboarding | — |
| **Casey** | — | — | Support inbox | Ongoing support |

---

## Approval Queue Estimates

| Week | Expected Proposals | Review Time (est.) |
|------|--------------------|--------------------|
| 1 | 12-15 (publications + CHI) | 30 min/day |
| 2 | 18-22 (all content + social) | 45 min/day |
| 3 | 5-8 (architecture docs) | 30 min/day |
| 4-6 | 8-12/week (engineering + copy) | 20 min/day |
| 7-8 | 15-20 (launch + outreach) | 45 min/day |
| 9+ | 5-8/week (conferences + outreach) | 15 min/day |

---

## Success Metrics (Per Phase)

| Phase | Metric | Target |
|-------|--------|--------|
| 1 | DOIs minted | 3+ (Zenodo, TechRxiv, SSRN) |
| 2 | Total content reach | 10,000+ views across all channels |
| 2 | HN upvotes | 50+ (front page threshold) |
| 3 | Paying customers | 10+ |
| 3 | MRR | $1,490+ (10 x $149) |
| 4 | Conference acceptances | 1+ |
| 5 | Acquirer conversations | 2+ active |

---

## Notes

- All experts operate in **Copilot mode** (human approval for every action) until trust is established
- Jordan is the highest-utilization expert across the plan (content is the primary output)
- Riley is the critical path for Phases 1 and 3 (publications + SaaS build)
- Sam transitions from endorser outreach (Phase 1) to customer prospecting (Phase 3) to acquirer research (Phase 5)
- Alex activates late (Phase 5) but is highest-stakes — acquirer outreach requires careful human review
- Taylor runs continuously as coordination layer across all phases
- CHI 2026 deadline (Feb 12) is the most time-sensitive item — Jordan should start immediately
