# LUCID — Technical One-Pager

**Adversarial AI-Based Verification for AI-Generated Code**

Your AI writes code. LUCID proves it works.

---

## The Problem

AI coding tools (Copilot, Cursor, Windsurf) generate code that compiles, lints clean, and looks correct. But "looks correct" isn't "is correct."

**The verification gap:** Code passes all traditional checks but has structural bugs that only appear in production.

**Examples we've found:**
- Admin routes with no auth guards (any user can access admin panels)
- API endpoints the frontend calls that don't exist (app shows "loading" forever)
- "Real-time" dashboards backed by hardcoded static data (charts look real, data is fake)
- IDOR vulnerabilities (role checked, ownership not verified)
- Path traversal bugs (happy path validated, edge cases missed)

**Traditional tools miss these:**
- Linters check style, not behavior
- SAST checks syntax, not logic
- Type checkers verify types, not contracts
- LLM-as-judge regresses at high iteration counts (99.4% at k=3 → 97.2% at k=5)

LUCID closes the gap with adversarial AI-based verification.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: AI-Generated Code + Task Context                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ EXTRACTION: Parse testable claims from code                    │
│ • Function contracts ("handles empty input")                   │
│ • Type invariants ("user.id is always a number")               │
│ • Security assertions ("admin route requires auth")            │
│ • Persistence claims ("settings saved to database")            │
│ Result: 10-30 formal specifications per file                   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ ADVERSARIAL VERIFICATION: Second LLM attacks each claim        │
│ • NOT self-review (same model can't find its own bugs)         │
│ • NOT random testing (misses systematic failures)              │
│ • Adversarial LLM trained to find security/logic violations    │
│ • Deterministic checks (type, test execution, static analysis) │
│ Result: PASS/FAIL + evidence for each claim                    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ REMEDIATION: Generate specific fix plans for failures          │
│ • File path, line number, exact issue                          │
│ • Code snippet showing the bug                                 │
│ • Suggested fix with explanation                               │
│ • Severity level (critical/high/medium/low)                    │
│ Result: Actionable repair instructions                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: Verification Report                                    │
│ • Health score (0-100): ratio of verified to failing claims    │
│ • Claim-by-claim results (PASS/FAIL with evidence)             │
│ • Remediation plans for each failure                           │
│ • Structured JSON for automation                               │
└─────────────────────────────────────────────────────────────────┘
```

**Key insight:** Use a second LLM adversarially (trained to break code), not cooperatively (reviewing its own output). Self-review plateaus at ~87%. Adversarial verification reaches 100%.

---

## Benchmark Comparison

### HumanEval (164 function-level tasks)

| Approach | k=1 | k=3 | k=5 | Trend |
|----------|-----|-----|-----|-------|
| Baseline (no verification) | 86.6% | — | — | — |
| Self-refine | 87.2% | 87.2% | 87.8% | Flat (plateaus) |
| LLM-as-judge | 98.2% | 99.4% | **97.2%** | **Regresses** |
| Random verification | 97.6% | 95.1% | 97.0% | Degrades |
| SAST tools (traditional) | N/A | N/A | N/A | Can't verify behavior |
| **LUCID** | **98.8%** | **100%** | **100%** | **Monotonic** |

**Key finding:** LUCID is the only approach that doesn't plateau or regress. 100% at k=3 and maintains it.

### SWE-bench Lite (300 real-world GitHub issues)

| Condition | Resolved | Pass Rate | vs. Baseline |
|-----------|----------|-----------|--------------|
| Baseline k=1 | 55/300 | 18.3% | — |
| LUCID k=1 | 75/300 | 25.0% | **+36.4%** |
| LUCID k=3 | 76/300 | 25.3% | +38.2% |
| LUCID best | 91/300 | 30.3% | **+65.5%** |

**Key finding:** LUCID solves 20 additional tasks at k=1. 36 additional tasks at best-of-5.

### Real-World Codebases (LVR Pilot)

| Metric | Island Biz Accounting (25 pages, 26 tables) |
|--------|---------------------------------------------|
| Claims extracted | 354 |
| Verified | 310 (87.6%) |
| Partial | 8 (2.3%) |
| Falsified | 28 (7.9%) |
| Bugs found | 23 (2 critical, 6 high, 10 medium, 5 low) |
| Headline bug | Permission system broken — 4 roles locked out |

**Key finding:** Large, complex codebase with 23 production-blocking bugs that passed all traditional checks.

---

## Products

### 1. PR-Gate Verification (GitHub Action)

**What it does:**
- Runs on every pull request
- Extracts claims from the diff
- Verifies each claim adversarially
- Blocks merge if critical failures found
- Posts verification report as PR comment

**Integration:** 5 minutes. Add `.github/workflows/lucid.yml` to your repo.

**Pricing:**
- Free for open source
- $29/team/month (1-10 developers)
- $79/team/month (11-50 developers)
- $99/team/month (51+ developers)
- Enterprise: custom pricing

**Use case:** Teams using Copilot, Cursor, or any AI coding tool. Prevents AI-generated bugs from reaching production.

### 2. LVR (LUCID Verified Reconstruction)

**What it does:**
- Loop 1: Extract requirements from existing codebase, verify each claim, find bugs
- Loop 2: Extract architecture, verify against requirements, find design flaws
- Loop 3: Regenerate code based on verified requirements and architecture (all bugs fixed)

**Pricing:**
- Consulting service: $5K-$25K per project (depends on codebase size)
- Self-service API: Coming Q2 2026

**Use case:** Legacy codebases with unknown quality. Pre-acquisition tech audits. Compliance verification.

---

## Integration Options

| Method | Depth | Latency | Use Case |
|--------|-------|---------|----------|
| **MCP Server** | Deep | Real-time | IDE integration (Claude Code, Cursor, etc.) |
| **GitHub Action** | Medium | Per-PR (1-5 min) | CI/CD pipeline, gate merges |
| **CLI** | Medium | On-demand | Local development, pre-commit hooks |
| **API** | Shallow | 1-4s per call | Custom workflows, platform integration |

### MCP Server (Model Context Protocol)

```bash
# Install
npm install -g @lucid/mcp-server

# Configure in Claude Code
cat >> ~/.claude/config.json <<EOF
{
  "mcpServers": {
    "lucid": {
      "command": "lucid-mcp",
      "args": ["--api-key", "$LUCID_API_KEY"]
    }
  }
}
EOF
```

**What it enables:**
- Real-time verification as you type (via IDE)
- Inline suggestions for verification failures
- Claim extraction without leaving the editor

### GitHub Action

```yaml
# .github/workflows/lucid.yml
name: LUCID Verification
on: [pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gtsbahamas/hallucination-reversing-system/github-action@main
        with:
          lucid_api_key: ${{ secrets.LUCID_API_KEY }}
          fail_on_critical: true
```

**What it does:**
- Verifies changed files in every PR
- Posts report as PR comment
- Fails CI if critical bugs found (configurable)

### CLI

```bash
# Install
npm install -g @lucid/cli

# Verify a file
lucid verify src/auth.ts

# Verify entire codebase
lucid verify .

# Generate verification report
lucid verify . --report report.json
```

### API

```bash
curl -X POST https://api.trylucid.dev/v1/verify \
  -H "Authorization: Bearer $LUCID_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def admin_route(): ...",
    "language": "python",
    "context": "Admin dashboard route"
  }'
```

**Response:**

```json
{
  "pass": false,
  "score": 0.75,
  "claims_extracted": 4,
  "claims_verified": 3,
  "claims_failed": 1,
  "failures": [
    {
      "claim": "Admin route requires authentication",
      "evidence": "No @login_required decorator found",
      "remediation": "Add @login_required before line 1",
      "severity": "critical"
    }
  ]
}
```

---

## Platform Vendor Integration

If you build an AI coding platform (Cursor, GitHub, Windsurf, etc.), LUCID integrates as post-generation verification:

**Three depths:**

1. **Shallow (backend filter):**
   - Run LUCID after code generation
   - Filter out obvious failures before showing to users
   - Zero UI changes

2. **Medium (verification UI):**
   - Stream LUCID results into your UI
   - Show users which features are verified (✓) vs. need attention (⚠)
   - Builds trust

3. **Deep (RLVF training signal):**
   - Use LUCID's verification as model training signal
   - Correct code = reward, incorrect code = penalty + specific fix
   - Fine-tune your model on verified feedback
   - Each generation cycle improves quality

**Pricing for platforms:**
- $0.06/call (Verify only)
- $0.15/call (Generate with specs)
- $0.20/call (Full loop: spec + generate + verify + remediate)
- Annual contracts: $60K-$500K

**Pilot:** 3 months free, 50K calls, dedicated integration support.

---

## Competitive Positioning

| Capability | LUCID | SAST (Snyk, SonarQube) | LLM-as-Judge | Linters |
|------------|-------|------------------------|--------------|---------|
| Syntax errors | ❌ | ✓ | ✓ | ✓ |
| Type errors | ❌ | ✓ | ✓ | ✓ |
| Code style | ❌ | Partial | ✓ | ✓ |
| Known CVEs | ❌ | ✓ | ❌ | ❌ |
| Behavioral bugs | ✓ | ❌ | Partial | ❌ |
| Missing auth | ✓ | ❌ | Partial | ❌ |
| Logic errors | ✓ | ❌ | Partial | ❌ |
| Scaffolding detection | ✓ | ❌ | ❌ | ❌ |
| Fake backends | ✓ | ❌ | ❌ | ❌ |
| AI-specific bugs | ✓ | ❌ | Partial | ❌ |
| Monotonic convergence | ✓ | N/A | ❌ | N/A |

**Key differentiator:** LUCID verifies behavior (does auth actually block unauthorized users?), not syntax (is the auth function defined?).

**Complementary, not competitive:** Use SAST + linters + LUCID together. They check different things.

---

## Success Stories

### Dogfooding (LUCID's own codebase)

**Bug caught:** Path traversal vulnerability in file handling
- Generated by Claude Sonnet 4 (one of the best models)
- Passed linting, type checking, manual review
- LUCID flagged it: "File path not sanitized before read"
- Fix applied before production deployment

**Lesson:** Even the best AI models miss edge cases. Adversarial verification catches them.

### Island Biz ERP (LVR Pilot)

**Codebase:** 25 pages, 26 database tables, 3 permission systems, ~10K LOC
- Loop 1: 354 claims extracted, 23 bugs found
- Loop 2: Architecture verified, 4 additional design flaws found
- Loop 3: 57 files regenerated with all bugs fixed

**Headline bug:** Permission system broken — 4 accounting roles locked out of all pages
- RLS policies contradicted route guards
- Hard-coded overrides in middleware
- No single source of truth

**Result:** Unified permission system, all bugs fixed, 100% React Query data layer, zero scaffolding.

---

## Technical Specifications

**Supported languages:** Python, TypeScript, JavaScript, Go, Rust, Java, C#, Ruby, PHP
**Deployment:** Cloud API (api.trylucid.dev) or self-hosted (Docker)
**Latency:** Median 1.2s per function (p99 <4s)
**Scalability:** 1M+ verifications/day (tested)
**Uptime:** 99.9% SLA (enterprise contracts)

**Security:**
- SOC2 Type II certified (Q2 2026 target)
- Code never stored (processed in-memory, discarded after verification)
- API keys rotatable, scoped by project
- Audit logs for all verification runs

---

## Credentials

**Published research:** DOI [10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644)
**Patent:** US Provisional App #63/980,048 (filed Feb 11, 2026)
**Benchmark:** $638 total cost, 464 tasks (HumanEval + SWE-bench), reproducible methodology
**Open source:** CLI + core engine at [github.com/gtsbahamas/hallucination-reversing-system](https://github.com/gtsbahamas/hallucination-reversing-system)

---

## Contact

**Website:** https://trylucid.dev
**Email:** ty@trylucid.dev
**GitHub:** https://github.com/gtsbahamas/hallucination-reversing-system
**Report:** https://trylucid.dev/report

**Schedule demo:** [ty@trylucid.dev](mailto:ty@trylucid.dev?subject=LUCID%20Technical%20Demo%20Request)

We'll run LUCID on your code (real or sample) and show you the verification results live. 30 minutes. No slides. Just data.

---

**Last updated:** 2026-02-13
**Version:** 1.0
