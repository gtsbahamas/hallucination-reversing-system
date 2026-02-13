# LUCID Go-to-Market Strategy (Revised)

*Date: February 13, 2026*
*Author: Ty Wells*
*Status: Active — supersedes 2026-02-12 enterprise audit strategy*
*Revision trigger: RLVF v2 scaling results (negative scaling, quality > quantity)*

---

## Why This Revision

The February 12 strategy was built on three revenue tracks:
1. **Consulting** (enterprise audits)
2. **GitHub Action** (viral developer adoption)
3. **Training signal sales** (selling DPO pairs to frontier labs)

On February 13, RLVF v2 experiments completed with a critical finding: **more training data hurts model performance.** DPO 120 pairs (91.5%) beat DPO 2K pairs (77.4%). The "training data factory at scale" thesis is damaged.

**What changes:**
- Track 3 pivots from "volume data factory" to "curation research collaboration"
- Track 2 (GitHub Action) elevates from supporting play to primary revenue engine
- Track 1 (consulting) remains the immediate cash generator
- Timeline compresses — EU AI Act deadline is 169 days away (August 2, 2026)

**What doesn't change:**
- Runtime verification is proven (100% HumanEval, +36% SWE-bench)
- LLM-judge regression data is compelling sales ammunition
- Patent filed, benchmarks published, API deployed
- Platform outreach is still priority #1

---

## The Data We're Selling With

| Metric | Value | Source |
|--------|-------|--------|
| LUCID pass@5 on HumanEval | **100%** (164/164) | Our benchmark |
| LUCID k=1 on SWE-bench | **25.0%** (+36.4% vs baseline) | Our benchmark |
| LLM-judge regression at k=5 | **97.2%** (down from 99.4%) | Our benchmark |
| Self-refine effectiveness | **~87%** (useless) | Our benchmark |
| Live comparison win rate | **7/10 tasks** | Our experiment |
| DPO pair quality finding | **120 curated > 2K automated** | RLVF v2 |
| Cost of all experiments | **$638** | Actual spend |

---

## Revenue Architecture: Three Tracks

### Track 1: Enterprise Consulting (Immediate Cash)
**Timeline:** Revenue starts Month 1-2
**Target:** $150K-$300K Year 1

Unchanged from Feb 12 strategy. AI Code Quality Audits for CTOs/CISOs/compliance leaders. This is how we eat while building product.

**Service tiers:**

| Tier | Price | Duration | Deliverable |
|------|-------|----------|-------------|
| Spotlight | $10K-$15K | 1-2 weeks | 1 repo, 10-page report + call |
| Standard | $25K-$50K | 3-4 weeks | 3-5 repos, full audit + remediation plan |
| Enterprise | $75K-$150K | 6-8 weeks | Org-wide + EU AI Act mapping + retainer |
| Retainer | $5K-$10K/mo | Monthly | Dashboard + monthly report |

**First sale target:** Spotlight audit closed by March 15.

---

### Track 2: GitHub Action + SaaS Platform (Scalable Revenue)
**Timeline:** Ship free tier Month 1, paid tiers Month 2-3
**Target:** $100K-$500K Year 1 (accelerating in months 6-12)

This is the most important section of the revised strategy.

#### How GitHub Action Monetization Works

**The model every successful DevSecOps tool uses:**
The GitHub Action itself is **free and open source**. It's the distribution vehicle, not the revenue engine. The Action calls the LUCID API. Billing happens through trylucid.dev, not GitHub Marketplace.

This is exactly how Snyk, SonarQube, Semgrep, and CodeQL work:
- **Snyk:** Free GitHub Action → calls Snyk API → billing on snyk.io ($25/dev/month)
- **SonarCloud:** Free GitHub Action → calls SonarCloud API → billing on sonarcloud.io (€30/month for 100K LoC)
- **Semgrep:** Free GitHub Action → calls Semgrep Cloud → billing on semgrep.dev
- **CodeQL:** Free for public repos → part of GitHub Advanced Security ($49/committer/month)

**Why NOT sell through GitHub Marketplace directly:**
- GitHub Marketplace caps you at 10 pricing plans
- GitHub takes 5% of revenue
- You lose control of the billing relationship
- You can't do usage-based pricing easily
- No enterprise SSO/SAML through Marketplace

**LUCID follows the same pattern:** Free Action + paid SaaS.

#### The Product: LUCID Verify

```
Developer pushes PR → GitHub Action triggers → LUCID API verifies code →
Results posted as PR comment + status check → Badge on PR
```

**What the Action does on every PR:**
1. Extracts testable claims from changed code (what does this code claim to do?)
2. Generates formal verification tests
3. Runs verification against claims
4. Posts results as a PR comment with pass/fail per claim
5. Sets GitHub status check (blocks merge if critical failures)
6. Generates a "LUCID Verified" badge

**The viral mechanic:** The badge and PR comment are visible to every reviewer. Every verified PR is an ad for LUCID.

#### Pricing Tiers

Modeled on Snyk ($25/dev/mo) and SonarCloud (LoC-based), but positioned between them:

| Tier | Price | Includes | Target |
|------|-------|----------|--------|
| **Free** | $0 | 3 public repos, 100 verifications/month, PR comments | Individual developers, OSS projects |
| **Pro** | $29/month | Unlimited repos (public + private), 500 verifications/month, priority API, email support | Solo devs, freelancers |
| **Team** | $19/user/month (min 5) | Everything in Pro + team dashboard, org-level policies, custom rules, 2,000 verifications/month | Startup eng teams (5-50 devs) |
| **Enterprise** | Custom ($49/user/month typical) | Everything in Team + SSO/SAML, compliance reports (EU AI Act), SLA, dedicated support, unlimited verifications, self-hosted option | Enterprise (50+ devs) |

**Why this pricing works:**

| Comparison | Their price | LUCID price | LUCID advantage |
|------------|------------|-------------|-----------------|
| Snyk Team | $25/dev/month | $19/user/month | Cheaper + different value (semantic verification vs dependency scanning) |
| SonarCloud Team | €30/month (100K LoC) | $29/month (500 verifications) | Similar price, but LUCID catches what SonarQube misses |
| GitHub Advanced Security | $49/committer/month | $19/user/month | 60% cheaper for Team tier |
| CodeRabbit (AI review) | $12/user/month | $19/user/month | More expensive but formally verified, not AI-reviewing-AI |

**Key positioning:** LUCID is not competing with SAST/DAST (Snyk, SonarQube). It's complementary. LUCID catches **semantic correctness** bugs — code that compiles and passes linting but doesn't do what it claims. This is the gap AI-generated code creates that no existing tool fills.

#### Revenue Projections (Conservative)

| Month | Free users | Pro | Team (users) | Enterprise | MRR |
|-------|-----------|-----|-------------|-----------|-----|
| 1-2 | 50 | 5 | 0 | 0 | $145 |
| 3 | 200 | 20 | 25 | 0 | $1,055 |
| 4 | 500 | 40 | 60 | 0 | $2,300 |
| 5 | 1,000 | 60 | 100 | 10 | $4,130 |
| 6 | 2,000 | 80 | 200 | 25 | $7,345 |
| 8 | 5,000 | 120 | 500 | 50 | $15,430 |
| 10 | 10,000 | 200 | 1,000 | 100 | $29,700 |
| 12 | 20,000 | 300 | 2,000 | 200 | **$57,500** |

**Year 1 total from SaaS:** ~$200K-$500K (heavily back-loaded as adoption compounds)

**Break-even for SaaS:** Month 6-8 (API costs ~$2K-$5K/month, infrastructure ~$500/month)

#### Build Plan

| Week | Milestone | Effort |
|------|-----------|--------|
| 1 | GitHub Action MVP — runs on PR, posts comment with verification results | 3-4 days |
| 2 | Free tier on trylucid.dev — API key registration, usage tracking | 2-3 days |
| 3 | Publish to GitHub Marketplace (free Action, links to trylucid.dev for paid) | 1 day |
| 4 | Pro tier — Stripe billing, private repo support | 2-3 days |
| 5-6 | Team tier — org management, team dashboard, Supabase multi-tenant | 1 week |
| 8-10 | Enterprise tier — SSO, compliance reports, SLA | 2 weeks |

**Total build: ~4-6 weeks for free + Pro, 8-10 weeks for full tier stack.**

#### Distribution Strategy

**Week 1-2: Seed users**
- Post LUCID Action to Hacker News ("Show HN: Formal verification for AI-generated code")
- Post to r/programming, r/coding, r/devops
- Tweet/post from LUCID account with benchmark data
- Add to awesome-github-actions lists

**Week 3-4: Developer content**
- Blog post: "We ran formal verification on 164 HumanEval problems. Here's what AI gets wrong."
- Blog post: "Why AI code review makes AI code worse" (LLM-judge regression data)
- Dev.to + Hashnode cross-posts

**Month 2-3: Integration partnerships**
- Approach Cursor, Bolt, Lovable, Replit to bundle LUCID verification
- Pitch: "Your users generate code. LUCID verifies it. Ship a 'Verified by LUCID' badge."
- Revenue share: 20-30% of LUCID subscription revenue from their referred users

**Month 3-6: Conference presence**
- Submit talks to QCon, StrangeLoop, DevSecCon
- Lightning talks at local meetups with live demo

**Month 6+: Enterprise sales**
- Inbound from free tier usage (developer convinces their company to buy Team/Enterprise)
- Bottom-up adoption: one developer uses free → team adopts → org buys Enterprise
- This is exactly how Snyk grew to $300M ARR

---

### Track 3: Verification-Guided Curation (Research Revenue)
**Timeline:** First partnership Month 4-6
**Target:** $50K-$200K Year 1

#### The Pivot: Quality Over Quantity

**Old pitch (damaged):** "We produce 400x cheaper preference pairs at scale."
**New pitch (data-backed):** "Our experiments prove 120 curated pairs beat 2,000 automated pairs by 15 percentage points. We have the only system that can identify *which* pairs actually improve models."

**Why this is more defensible:**
- Scale AI, Surge AI sell volume. Commodity market, race to bottom.
- LUCID sells *signal quality*. Nobody else has verification data on which pairs help vs hurt.
- The negative scaling result is publishable — it positions LUCID as the team that understands training data quality at a scientific level.

#### Offering

| Product | Price | Deliverable |
|---------|-------|-------------|
| Research collaboration pilot | $25K-$50K | 100-500 maximally informative pairs per domain + analysis report |
| Domain-specific curation | $50K-$100K/domain | Verified preference pairs for specific capability (math, security, systems) |
| Quality audit of existing training data | $25K-$75K | Run LUCID verification on a lab's existing DPO pairs, identify pairs that hurt |

**Target customers:**
- Mistral (most likely — smaller, more agile, would value external verification research)
- Cohere (enterprise-focused, would value quality-over-quantity message)
- Together AI / Fireworks AI (fine-tuning platforms, need better DPO data for customers)

**Approach:** Position as research collaboration, not commodity data sale. Lead with the negative scaling paper.

---

## Consolidated Timeline

### Phase 1: Foundation (Weeks 1-4, Feb 13 - Mar 13)

| Week | Action | Track | Expected Outcome |
|------|--------|-------|------------------|
| 1 | Ship GitHub Action MVP (free, public repos) | T2 | Action live on Marketplace |
| 1 | Publish benchmark report on trylucid.dev/report | T1,T2 | Lead generation asset |
| 1 | Begin outreach to 15 target contacts (LinkedIn + email) | T1 | Pipeline building |
| 2 | Publish "State of AI Code Quality 2026" on HN, Reddit, Dev.to | T2 | First 50 free users |
| 2 | Create SOW template, engagement letter template | T1 | Sales collateral ready |
| 2 | Build API key registration + usage tracking on trylucid.dev | T2 | Free tier operational |
| 3 | Launch Pro tier ($29/month) with Stripe billing | T2 | First paying SaaS users |
| 3 | Deliver first mini-audit (free, for conversion) | T1 | Pipeline to paid engagement |
| 4 | Close first Spotlight audit ($10K-$15K) | T1 | **FIRST REVENUE** |
| 4 | Begin platform outreach (Cursor, Bolt, Lovable, Replit) | T2 | Partnership conversations |

### Phase 2: First Revenue (Months 2-3, Mar 13 - May 13)

| Action | Track | Expected Outcome |
|--------|-------|------------------|
| Ship Team tier ($19/user/month) | T2 | Team adoption begins |
| Close first Standard audit ($25K-$50K) | T1 | Reference customer |
| Deliver 2-3 mini-audits | T1 | Pipeline growth |
| Write negative scaling paper (RLVF v2 findings) | T3 | Research credibility |
| Approach Mistral with curation pilot proposal | T3 | Partnership pipeline |
| Publish 4-6 LinkedIn thought leadership posts | T1,T2 | Inbound leads |
| Submit conference talk proposals (QCon, DevSecCon) | T2 | Brand building |
| 100+ free GitHub Action users | T2 | Community growth |

**Revenue target: $25K-$75K cumulative**

### Phase 3: Scale (Months 4-6, May 13 - Aug 2)

| Action | Track | Expected Outcome |
|--------|-------|------------------|
| Ship Enterprise tier (SSO, compliance reports) | T2 | Enterprise-ready |
| Close 2-3 more consulting engagements | T1 | Revenue growth |
| First curation research pilot with a frontier lab | T3 | $25K-$50K |
| EU AI Act compliance package launched | T1,T2 | Deadline-driven urgency |
| 1,000+ free users, 50+ paid users | T2 | Product-market fit signal |
| Convert audit customers to retainers ($5K-$10K/mo) | T1 | Recurring revenue |
| Hire first contractor (if monthly revenue > $30K) | All | Scale capacity |

**Revenue target: $100K-$200K cumulative**

### Phase 4: Compound (Months 7-12, Aug - Feb 2027)

| Action | Track | Expected Outcome |
|--------|-------|------------------|
| Platform integration live (at least 1 of Cursor/Bolt/Lovable/Replit) | T2 | Distribution moat |
| Enterprise sales from bottom-up adoption | T2 | $49/user/month contracts |
| Continuous monitoring SaaS ($2K-$10K/month retainers) | T1,T2 | MRR growth |
| Second research collaboration | T3 | Recurring research revenue |
| Submit NSF SBIR with negative scaling as preliminary data | T3 | $305K non-dilutive (if awarded) |
| Evaluate fundraise need based on traction | All | Strategic decision |
| Non-provisional patent assessment (month 8-10) | All | IP decision point |

**Revenue target: $300K-$700K cumulative**

---

## Year 1 Financial Summary

### Revenue Projection (Conservative)

| Quarter | Track 1 (Consulting) | Track 2 (SaaS) | Track 3 (Research) | Total |
|---------|---------------------|-----------------|-------------------|-------|
| Q1 (Feb-Apr) | $15K-$30K | $1K-$3K | $0 | $16K-$33K |
| Q2 (May-Jul) | $50K-$80K | $10K-$25K | $25K-$50K | $85K-$155K |
| Q3 (Aug-Oct) | $40K-$70K | $30K-$60K | $25K-$50K | $95K-$180K |
| Q4 (Nov-Jan) | $40K-$70K | $60K-$120K | $25K-$50K | $125K-$240K |
| **Year 1** | **$145K-$250K** | **$101K-$208K** | **$75K-$150K** | **$321K-$608K** |

### Cost Structure

| Item | Monthly | Annual |
|------|---------|--------|
| Claude API (verification engine) | $2K-$5K | $24K-$60K |
| Infrastructure (Vercel, Supabase, Upstash) | $100-$300 | $1.2K-$3.6K |
| Stripe fees (2.9% + $0.30) | ~$200-$500 | $2.4K-$6K |
| LinkedIn Sales Navigator | $100 | $1.2K |
| Legal (SOW, NDA, patent assessment) | varies | $5K-$15K |
| Conferences (2-3/year) | — | $5K-$10K |
| Contractor (from month 6) | $5K-$10K | $30K-$60K |
| **Total** | | **$69K-$156K** |

### Net Margin

**Year 1 net income (conservative): $165K-$452K**
**Gross margin: 75-85%** (consulting + SaaS combined)

---

## Decision Gates

### Gate 1: Month 3 (May 13) — "Is the business working?"

| Metric | Go | No-Go |
|--------|-----|-------|
| Revenue | >$30K cumulative | <$15K cumulative |
| Pipeline | >$100K qualified | <$50K pipeline |
| GitHub Action users | >200 free | <50 free |
| Benchmark report published | Yes | No |

**If Go:** Hire contractor, expand to Team tier, begin EU AI Act package
**If No-Go:** Double down on consulting, pause SaaS build, reduce burn

### Gate 2: Month 6 (August 2 — EU AI Act deadline) — "Which track leads?"

| Metric | SaaS-led | Consulting-led | Pivot |
|--------|----------|---------------|-------|
| MRR | >$5K and growing | <$2K | SaaS not working, focus consulting |
| Consulting revenue | <$50K cumulative | >$100K cumulative | Consulting is the business |
| Platform partnership | 1+ signed | 0 | Self-serve distribution only |
| Research collaboration | 1+ closed | 0 | Drop Track 3, focus T1+T2 |

### Gate 3: Month 10 (December 2026) — "What are we building?"

| Signal | Path A: DevSecOps SaaS | Path B: Enterprise Consulting | Path C: Research Platform |
|--------|------------------------|-----------------------------|--------------------------|
| Revenue mix | 50%+ SaaS | 70%+ consulting | Research partnerships growing |
| Growth rate | MRR growing >30% MoM | Consulting pipeline full | Multiple lab partnerships |
| Next move | Raise seed for growth | Stay bootstrapped, hire delivery | Raise for research + platform |

---

## Platform Outreach Strategy (Priority #1)

### Why Platforms Matter Most

A single integration with Cursor (1M+ users) or Replit (25M+ users) distributes LUCID to more developers than years of organic growth. The benchmark data makes this pitch compelling:

**The pitch to platforms:**
> "Your users generate code. 45% of it fails security tests. Your competitors will solve this with AI-reviewing-AI — which we've proven regresses after 5 iterations. We're the only formal verification solution, with benchmark data showing 100% convergence. Let us add a 'Verified' badge to your generated code. We'll share revenue 70/30."

### Tier 1 Targets (Immediate — This Week)

| Platform | Users | Why They Need LUCID | Contact Strategy |
|---------|-------|-------|------|
| Cursor | 1M+ active | Generates most code, quality is their differentiator | Email eng team, reference benchmark |
| Bolt.new | Growing fast | Vibe coding = high hallucination rate | Email founders (small team) |
| Lovable | 8M users | Non-developers generating code, highest risk | LinkedIn to CEO/CTO |
| Replit | 25M+ users | Education + production, quality matters | Email partnerships team |

### Tier 2 Targets (Month 2-3)

| Platform | Why | Approach |
|---------|-----|---------|
| Windsurf (Codeium) | AI IDE, differentiation need | Partnership email |
| GitHub Copilot | Largest installed base | Feature proposal through GH relationships |
| Amazon CodeWhisperer | Enterprise AWS customers | AWS partnership program |
| Tabnine | Enterprise-focused, privacy angle | Direct outreach |

### Integration Model

```
Platform generates code → LUCID Action/API verifies →
Results returned to platform → Platform shows badge/score
```

**Revenue share:** Platform gets 20-30% of LUCID subscription revenue from their users. Platform benefits from better code quality metrics. LUCID benefits from distribution.

---

## Key Messaging Updates (Post-RLVF v2)

### For Developers (GitHub Action)
> "Every AI coding tool generates code that compiles. None generate code that's fully correct. LUCID is the formal verification layer that catches semantic bugs before they reach production."

### For CTOs (Consulting)
> "We've benchmarked AI code quality across 594 tasks. Average health score: 40/100. We found 21 critical bugs across 4 production codebases. LLM-based code review actually makes things worse after 5 iterations. We're the only solution using formal verification — and we hit 100% on HumanEval."

### For Compliance (EU AI Act)
> "Article 15 of the EU AI Act requires accuracy and robustness assurance for high-risk AI systems. LUCID generates the formal verification audit trail you need. Enforcement begins August 2, 2026. We can have your gap analysis done in 2 weeks."

### For Frontier Labs (Research)
> "Our RLVF experiments discovered that more DPO pairs hurt model performance — 120 curated pairs beat 2,000 automated pairs by 15 percentage points. We have the verification loop that identifies which training pairs actually improve your models. Let's collaborate on a curation pilot."

### For Investors (Updated)
> "Three mathematical proofs say hallucination can't be eliminated. We built the architecture that makes it productive. Our benchmarks prove it works: 100% on HumanEval, +36% on SWE-bench. Our RLVF experiments proved that quality trumps quantity in AI training data — a finding that reshapes the $4.4B training data market. Revenue starts now through enterprise audits and a GitHub Action."

---

## Competitive Moat Assessment (Honest)

| Moat Layer | Strength | Durability |
|------------|----------|-----------|
| Patent (App #63/980,048) | Medium — provisional, not yet tested | 12 months to decide on non-provisional |
| Benchmark data (594 tasks, 6 tracks) | Strong — nobody else has this | Needs refreshing every 6 months |
| LLM-judge regression finding | Strong — empirically proven, contrarian | Could be replicated, but we published first |
| RLVF negative scaling finding | Strong — unique dataset, publishable | Supports quality-over-quantity narrative |
| Formal verification approach | Strong — structurally hard for LLM vendors to copy | Requires admitting hallucination is permanent |
| First-mover in "AI code verification" | Medium — window is 6-12 months | Someone will follow |
| EU AI Act timing | Strong — deadline creates urgency | August 2, 2026 is fixed |

**Weakest link:** No revenue yet. All moats strengthen with traction.

---

## Risks (Revised)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Long enterprise sales cycles | High | Medium | Free mini-audits + GitHub Action builds pipeline in parallel |
| GitHub Action doesn't get adoption | Medium | High | Content marketing, platform partnerships, HN/Reddit launches |
| Competitor launches similar Action | Medium | Medium | Patent, benchmark data, formal verification vs LLM-judge |
| Solo founder capacity | High | Critical | Hire at $30K MRR. Automate verification pipeline. Ruthless prioritization. |
| Platform partnerships stall | Medium | Medium | Self-serve distribution via GitHub Action doesn't depend on partnerships |
| Training signal market too small | Low | Low | Track 3 is upside, not the base case. T1+T2 sustain the business. |
| EU AI Act enforcement delayed | Low | Low | Value exists regardless — code quality is a real problem |
| API costs scale faster than revenue | Low | Medium | Free tier has hard cap (100 verifications). Paid tiers cover API costs with margin. |

---

## Immediate Next Actions (This Week, Feb 13-19)

| # | Action | Deadline | Dependency |
|---|--------|----------|-----------|
| 1 | Push 2 unpushed commits to origin | Feb 13 | None |
| 2 | Commit API code, sales assets, strategy docs | Feb 13 | #1 |
| 3 | Ship GitHub Action MVP (free, public repos) | Feb 16 | Working API |
| 4 | Publish benchmark report at trylucid.dev/report | Feb 16 | None |
| 5 | Write HN "Show HN" post for GitHub Action launch | Feb 17 | #3 |
| 6 | Draft outreach messages for Cursor, Bolt, Lovable, Replit | Feb 17 | #4 |
| 7 | Identify 15 target contacts for consulting outreach | Feb 18 | None |
| 8 | Create SOW template for Spotlight audit | Feb 19 | None |
| 9 | Begin LinkedIn thought leadership (first post) | Feb 19 | #4 |
| 10 | Set up Stripe billing for Pro tier | Feb 19 | #3 |

---

## What We're NOT Doing (Intentional)

| Activity | Why Not (Yet) |
|----------|--------------|
| Smart contract expansion (Phase 1 from multi-discipline plan) | Gate on $30K revenue first |
| IaC/Cloud expansion | Gate on $30K revenue first |
| Building domain plugin architecture | Premature — prove PMF in software first |
| Raising funding | No traction yet — would raise at bad terms |
| Hiring | Revenue must justify cost |
| More training experiments | RLVF story is complete for now |
| Non-provisional patent filing | Assess at month 6-8, deadline is Feb 2027 |
| Conference attendance | ROI unclear until we have product + paying customers |

---

## Success Criteria: Month 6 (August 2, 2026)

If we've hit these by the EU AI Act deadline, the business is working:

| Metric | Target |
|--------|--------|
| Cumulative revenue | >$100K |
| Monthly recurring revenue (SaaS) | >$5K |
| GitHub Action free users | >1,000 |
| Paid SaaS customers | >25 |
| Consulting engagements delivered | 3+ |
| Platform partnerships (signed) | 1+ |
| Case studies / testimonials | 2+ |

If we miss these, Gate 2 triggers a strategy reassessment.

---

## Sources

Research used in pricing and market analysis:
- [Snyk pricing](https://snyk.io/plans/) — $25/dev/month Team tier
- [SonarCloud pricing](https://www.sonarsource.com/plans-and-pricing/sonarcloud/) — €30/month for 100K LoC
- [GitHub Marketplace pricing plans](https://docs.github.com/en/apps/github-marketplace/selling-your-app-on-github-marketplace/pricing-plans-for-github-marketplace-apps) — free, flat-rate, per-unit models; 5% GitHub fee
- [GitHub Marketplace payment](https://docs.github.com/en/billing/concepts/third-party-payments/github-marketplace-apps) — $500 minimum payout, monthly disbursement
- [GitHub Actions 2026 pricing changes](https://resources.github.com/actions/2026-pricing-changes-for-github-actions/) — $0.002/min platform fee, free for public repos preserved
- [LinkedIn: Semgrep + CodeQL at scale](https://www.infoq.com/news/2026/02/linkedin-redesigns-sast-pipeline/) — validates CI/CD integration model
