# LUCID Product Plan

*Created: 2026-02-01*

---

## What LUCID Is

A self-serve web app that verifies whether a codebase delivers what its legal documents promise. Customer connects a repo, uploads their ToS or privacy policy, and gets a verified gap report — no humans involved.

## Revenue Model

| Tier | Trigger | Price | Value |
|------|---------|-------|-------|
| Single Audit | Customer-initiated | $149 | One repo + one document verified, full report |
| Continuous Monitoring | Push / schedule | $49/month per repo | Ongoing re-audits, alerts on new failures |

Continuous monitoring ships in Phase 2. Phase 1 is single audits only.

## Cost Per Audit

Anthropic API tokens: ~$2-5 per audit (based on Frank Labs test: 91 claims).
At $149/audit, gross margin is ~96%.
At $49/month with weekly re-audits (~4/month), cost is ~$8-20/month per customer. Margin ~60-85%.

---

## Architecture

```
+----------------------------------+
|  Web App (Next.js on Vercel)     |  Auth, dashboard, reports, billing
+----------------------------------+
|  Pipeline Engine (Inngest)       |  Clone repo, extract claims, verify, report
+----------------------------------+
|  Data Layer (Supabase)           |  Users, audits, claims, verdicts, corpus
+----------------------------------+
```

**Repo:** Separate from the CLI repo. New repo: `lucid-app`.
**CLI repo** (`hallucination-reversing-system`): stays as-is. Core logic (extract, verify, report) gets extracted into importable functions that the web app calls.

### Why Inngest

LUCID audits take minutes (clone repo, call Anthropic per claim batch). Vercel serverless functions timeout at 60s (hobby) or 300s (pro). Inngest runs multi-step functions with retries, no infra to manage, scales to zero.

### Repo Access

GitHub App. Customer installs it, grants access to specific repos. LUCID clones on demand into temp storage, runs the pipeline, deletes after. No persistent code storage.

---

## Data Model

```
users
  +-- organizations
        +-- repositories (via GitHub App)
        +-- documents (uploaded ToS, policies)
        +-- audits (one audit = one document vs one repo)
              +-- claims (extracted from document)
                    +-- verdicts (PASS/PARTIAL/FAIL/N/A + evidence)
```

### Tables

| Table | Key Fields |
|-------|------------|
| `users` | id, email, github_id, stripe_customer_id |
| `organizations` | id, name, owner_id |
| `repositories` | id, org_id, github_installation_id, full_name, default_branch |
| `documents` | id, org_id, type, version, content_hash, raw_text |
| `audits` | id, org_id, repo_id, document_id, status, trigger, started_at, completed_at |
| `claims` | id, audit_id, section, category, severity, text, taxonomy_key |
| `verdicts` | id, claim_id, audit_id, verdict, confidence, evidence (jsonb), reasoning |

### Design Decisions

- **Documents are versioned**, not overwritten. New ToS = new document row. Enables drift tracking.
- **Verdicts store structured evidence**: file path, line number, code snippet, confidence score.
- **taxonomy_key on claims** maps to the corpus. Similar claims across customers get the same key. This is how the moat accumulates.
- **No customer code persisted.** Cloned, analyzed, deleted. Evidence snippets (short excerpts) stored in verdicts only.

---

## User Journey

### First Audit

1. Land on marketing page
2. Sign up (GitHub OAuth)
3. Install LUCID GitHub App, select repos
4. Upload document (paste text or provide URL)
5. Stripe checkout ($149)
6. Pipeline runs (progress shown in dashboard)
7. Report delivered (dashboard + PDF + email notification)

### Converting to Subscriber (Phase 2)

8. Enable monitoring on a repo+document pair
9. Choose trigger (push / daily / weekly / monthly)
10. Subscribe ($49/month)
11. Dashboard shows audit history, trends, alerts on new failures

---

## Build Phases

### Phase 1: Single Audit MVP (Launch)

Goal: First paying customer.

#### 1. Supabase Schema
- Create project
- All 7 tables with RLS (users see only their org's data)

#### 2. Auth + Onboarding
- Next.js app on Vercel
- GitHub OAuth via Supabase Auth
- Auto-create org on first login
- Empty-state dashboard: "Run your first audit"

#### 3. GitHub App Integration
- Register GitHub App
- Installation flow from within dashboard
- Store installation ID + accessible repos
- Handle install/uninstall webhooks

#### 4. Document Upload
- Paste raw text (launch)
- URL scrape (launch if straightforward)
- PDF/DOCX (defer to Phase 1.5)
- Content hashing for dedup

#### 5. Pipeline (Inngest)
- Three-step function:
  1. Clone repo (shallow, via GitHub App token) + extract claims
  2. Verify claims in batches (10 per step)
  3. Store verdicts, generate report, mark audit complete
- Wraps existing CLI logic as library functions
- Progress updates via polling or SSE

#### 6. Stripe Checkout
- Single product: LUCID Audit $149
- Checkout session after repo + document selection
- `checkout.session.completed` webhook triggers pipeline
- No subscriptions yet

#### 7. Report Dashboard
- Audit list: date, repo, document, status, verdict summary
- Audit detail: claim-by-claim with verdicts, evidence, code snippets
- PDF export
- Email notification on completion

### Phase 2: Subscriptions + Monitoring

Goal: Recurring revenue.

- Stripe subscription billing ($49/month per repo)
- GitHub push webhook triggers re-audit
- Scheduled triggers via Inngest cron
- Audit history per repo
- Diff view: "2 new failures since last audit"
- Alert emails on regression

### Phase 3: Corpus + Moat

Goal: Defensibility.

- Taxonomy mapping (automatic on every audit)
- Accuracy calibration from accumulated data
- Industry benchmarks ("better than 72% of SaaS apps")
- GitHub Action: `lucid-audit` in CI, block PRs that break legal promises
- Annual "State of ToS Compliance" report

---

## Explicitly Cut From Phase 1

| Feature | Reason | Returns In |
|---------|--------|------------|
| Subscriptions / recurring billing | Validate single-audit demand first | Phase 2 |
| GitHub webhook monitoring | Requires subscription model | Phase 2 |
| Scheduled re-audits | Requires subscription model | Phase 2 |
| Trend dashboard / diff view | Need 2+ audits per customer | Phase 2 |
| Taxonomy mapping | Need volume first | Phase 3 |
| GitHub Action (CI/CD) | Power feature, not launch feature | Phase 3 |
| PDF/DOCX upload | Text paste + URL covers 90% of cases | Phase 1.5 |
| GitLab / Bitbucket | GitHub first | Phase 2+ |
| Team features | Solo buyer is first customer | Phase 2+ |
| API access | No one needs it before using the product | Phase 3 |
| Sales pipeline / contact forms | Self-serve product. Checkout IS the pipeline. | Never (unless enterprise) |

---

## Moat Strategy

The moat is not the technology (LLM + code analysis). The moat is three things compounding together:

### 1. Verification Corpus
Every audit produces structured claim-to-verdict data. Anonymized patterns accumulate. After 1,000 audits, you have accuracy benchmarks and failure-rate data nobody else has. Every customer makes the product better for the next one.

### 2. Claim Taxonomy
Structured categories with specific verification strategies and measured false-positive rates. This is domain expertise encoded as data. Takes years of real audits to build. Cannot be replicated by throwing an LLM at the problem.

### 3. CI/CD Embedding
Once LUCID runs on every PR blocking merges that violate legal commitments, ripping it out is painful. This is the Snyk/SonarQube playbook. Deep integration = high switching cost.

None of these require anything special at launch. They build silently as customers use the product.

---

## Risks

| Risk | Mitigation |
|------|------------|
| LUCID itself hallucinating during verification | Multi-pass verification, confidence scoring, evidence requirements. Phase 3 accuracy calibration. |
| Thin moat at launch | Expected. Corpus + taxonomy + embedding compound over time. Race to accumulate audits. |
| Anthropic API cost spikes | Token usage monitoring, claim batching, caching repeated patterns |
| GitHub App security / trust | No persistent code storage, shallow clones, delete after audit, SOC 2 later |
| Larger player copies the concept | Speed to market + corpus advantage. If Snyk builds this in 2027, you have 1,000 audits of data they don't. |
