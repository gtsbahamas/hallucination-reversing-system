# LUCID — Production Plan (Revised 2026-02-08)

*Created: 2026-02-07, Revised: 2026-02-08*
*Supersedes: IP + Acquisition plan (pure acquisition play replaced with revenue-first approach)*
*Full strategy: `docs/plans/2026-02-08-monetization-plan.md`*
*Current Status: 8%*

---

## How To Use This Plan

**Every session start:**
1. Read this file
2. Check current phase and progress
3. Continue from `[IN PROGRESS]` or next `[ ]` item

**After completing work:**
1. Mark items `[x]` when done
2. Update `Current Status` percentage
3. Add notes if needed

**Status markers:**
- `[ ]` = Not started
- `[IN PROGRESS]` = Currently working on
- `[x]` = Complete
- `[BLOCKED]` = Needs external input
- `[SKIP]` = Intentionally skipped (with reason)

---

## Strategic Context (Revised)

**Old strategy:** Pure IP + Acquisition play at $149/audit
**New strategy:** Revenue-first with niche positioning + compliance angle

**Core positioning:** "The only tool that verifies what AI-built software actually does versus what it claims to do"

**Why the pivot:**
- $149/audit commoditizes the value (comparable tools charge $7,500-35,000/year)
- Pure acquisition without revenue/users is the longest shot
- EU AI Act enforcement (Aug 2, 2026) creates compliance-driven demand
- Consulting generates immediate revenue while SaaS builds
- NSF SBIR could provide $305K non-dilutive funding

**What we keep from old plan:** publications, distribution, conferences
**What changes:** pricing (10-50x increase), add consulting, add compliance, users before acquisition

---

## Current Status: 28% → Target: $10K MRR

| Phase | Status | Completion |
|-------|--------|------------|
| Phase 0: Foundation (Weeks 1-2) | IN PROGRESS | 9/9 |
| Phase 1: GitHub Action MVP (Weeks 3-6) | NOT STARTED | 0/6 |
| Phase 2: SaaS Platform (Weeks 7-12) | NOT STARTED | 0/5 |
| Phase 3: Consulting Pipeline (Weeks 3-12) | NOT STARTED | 0/6 |
| Phase 4: NSF SBIR (Weeks 4-8) | NOT STARTED | 0/3 |
| Phase 5: EU AI Act Compliance (Months 3-6) | NOT STARTED | 0/5 |
| Phase 6: Growth + Data Moat (Months 6-12) | NOT STARTED | 0/6 |

---

## Phase 0: Foundation (Weeks 1-2, Feb 8-21)

**Goal:** Ship what we have, capture existing demand, update academic work

### 0.1 Publications — PARTIALLY COMPLETE
- [x] Zenodo publication with DOI (10.5281/zenodo.18522644)
- [x] CHI 2026 Tools for Thought workshop paper (4 pages, `chi-submission/`)
- [x] Submit CHI 2026 paper (submitted via Fillout form, poster PDF uploaded)
- [BLOCKED] Submit to arXiv — account registered (tywells_lucid2026), needs endorser
- [x] Update paper: add Karpowicz 2025 citation (added to both CHI and arXiv papers)
- [ ] Submit to TechRxiv, SSRN

### 0.2 Distribution — PARTIALLY COMPLETE
- [x] HN Show HN posted
- [x] LinkedIn posted
- [x] Twitter/X posted
- [x] Skool posted (4 AI communities)
- [x] Publish blog post (blog.html live on GitHub Pages)
- [BLOCKED] Post to Reddit r/MachineLearning + r/programming — Reddit blocks automated browsers, content ready in docs/distribution-content.md
- [x] Post to Dev.to (user posted manually)

### 0.3 Landing Page + Email Capture
- [x] Create landing page with waitlist signup (index.html, GitHub Pages enabled)
- [x] Position: "Verify what AI-built software actually does"
- [x] Include convergence chart, paper citation, GitHub link
- [x] Set up email capture (Formsubmit.co — activated and working)

**Completion criteria:** CHI submitted, blog live, Reddit posted, landing page capturing emails.

---

## Phase 1: GitHub Action MVP (Weeks 3-6, Feb 22 - Mar 21)

**Goal:** First usable product developers can try in < 5 minutes

- [ ] Build GitHub Action that runs LUCID on any repo
- [ ] Free tier: 5 scans/month, public repos only
- [ ] Action comments on PRs with specification gap findings
- [ ] "Powered by LUCID" badge with upgrade link
- [ ] List on GitHub Marketplace (free)
- [ ] Diff-based scanning (changed files only) to manage LLM costs

**Completion criteria:** Any developer adds LUCID to repo in < 5 min, sees results on PR.

---

## Phase 2: SaaS Platform (Weeks 7-12, Mar 22 - May 2)

**Goal:** Paid product with recurring revenue

- [ ] Web dashboard: connect repo, view history, track compliance
- [ ] Stripe: Free → Team ($99/mo) → Org ($249/mo)
- [ ] Team features: shared dashboard, scheduling, notifications
- [ ] API endpoint for programmatic access
- [ ] CI/CD integration docs (GitHub Actions, GitLab CI, CircleCI)

**Completion criteria:** Users can sign up, connect repos, pay, get ongoing verification.

---

## Phase 3: Consulting Pipeline (Parallel, Weeks 3-12)

**Goal:** Generate revenue immediately while building SaaS

- [ ] Create "AI Software Specification Audit" service page
- [ ] Reach out to interested Skool/LinkedIn contacts
- [ ] Price: $2,000-5,000 per engagement
- [ ] Deliver: LUCID run + expert analysis + remediation report
- [ ] Position around EU AI Act (Aug 2026 deadline)
- [ ] Target: 2-3 consulting engagements by end of Month 3

**Completion criteria:** First paid consulting engagement completed.

---

## Phase 4: NSF SBIR Application (Weeks 4-8)

**Goal:** $305K non-dilutive funding

- [ ] Research NSF SBIR Phase I requirements and timeline
- [ ] Draft application (published paper + DOI + working tool)
- [ ] Submit Phase I application

**Completion criteria:** Application submitted.

---

## Phase 5: EU AI Act Compliance (Months 3-6)

**Goal:** Capture compliance-driven demand before Aug 2026 enforcement

- [ ] Add compliance reporting features to SaaS
- [ ] Generate EU AI Act-formatted documentation from scans
- [ ] Create "EU AI Act Compliance" landing page
- [ ] Target compliance buyers (Legal, CISO, VP Eng)
- [ ] Price: $5,000-15,000 per readiness assessment

**Completion criteria:** First compliance engagement.

---

## Phase 6: Growth + Data Moat (Months 6-12)

**Goal:** Build defensible position through data and community

- [ ] 500+ free tier users, 1,000+ GitHub stars
- [ ] Benchmarking data from 1,000+ scans
- [ ] "Your spec coverage vs. industry" premium feature
- [ ] Enterprise pilot with 1-2 companies
- [ ] Present at 2+ conferences beyond CHI
- [ ] Evaluate acquisition interest based on actual traction

**Completion criteria:** $10K+ MRR, meaningful user base, data moat forming.

---

## Key Metrics

| Metric | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| GitHub stars | 200+ | 500+ | 1,000+ |
| Free users | 50+ | 200+ | 500+ |
| Paying customers | 3-5 | 15-25 | 50-100 |
| MRR | $500-1K | $3-5K | $10K+ |
| Consulting revenue (cumulative) | $2-5K | $10-15K | $30K+ |

---

## Progress Log

| Date | Session | Work Done | New % |
|------|---------|-----------|-------|
| 2026-02-07 | Initial | Research, paper, LaTeX, old plan created | 5% |
| 2026-02-08 | Research | Deep-dive research (3 agents), new plan created | 8% |
| 2026-02-08 | Execution | Landing page, Karpowicz citation, poster content, monetization plan | 15% |

---

## Notes

- Old plan (IP + Acquisition) archived — approach was valid but acquisition without revenue is unrealistic
- Old product plan ($149/audit, $49/month) archived — massively underpriced
- CHI 2026 deadline: Feb 12 AoE (4 days)
- EU AI Act enforcement: Aug 2, 2026 (6 months)
- NSF SBIR Phase I: up to $305K, retain full IP
- Tessl ($125M funded) is closest competitor but philosophically opposite (prevents hallucination vs. harnesses it)
