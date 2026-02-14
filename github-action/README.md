# LUCID Verify — GitHub Action

AI-powered code verification that catches what tests miss. LUCID extracts compliance claims from your codebase (security, data privacy, functionality, operational), verifies them against the actual code, and posts a detailed report as a PR comment.

## Quick Start

### Option 1: LUCID API (Recommended)

Get a free API key at [trylucid.dev](https://trylucid.dev) — 100 verifications/month free, no credit card.

```yaml
# .github/workflows/lucid-verify.yml
name: LUCID Verify
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gtsbahamas/hallucination-reversing-system/github-action@main
        with:
          lucid-api-key: ${{ secrets.LUCID_API_KEY }}
```

### Option 2: Bring Your Own Key (BYOK)

Use your own Anthropic API key. All processing runs locally in the GitHub runner — nothing leaves your CI.

```yaml
# .github/workflows/lucid-verify.yml
name: LUCID Verify
on:
  pull_request:

permissions:
  contents: read
  pull-requests: write

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: gtsbahamas/hallucination-reversing-system/github-action@main
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

## How It Works

1. **Index** — Scans your codebase structure and identifies key files (auth, API routes, config)
2. **Extract** — Generates 15-30 testable compliance claims about what the code should do
3. **Verify** — Reads the actual source code and checks each claim against the implementation
4. **Report** — Posts a PR comment with a compliance score, failures, and evidence

### LUCID API vs BYOK

| | LUCID API | BYOK |
|---|---|---|
| **Setup** | Get key at [trylucid.dev](https://trylucid.dev) | Get key at [console.anthropic.com](https://console.anthropic.com) |
| **Processing** | LUCID cloud | Your GitHub runner |
| **Cost** | 100 free/month, then metered | You pay Anthropic directly (~$0.05-0.40/run) |
| **Features** | Verification + remediation suggestions | Verification + doc-source verification |
| **Privacy** | Code sent to LUCID API | Code stays in your runner |

If both keys are provided, LUCID API takes precedence.

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `lucid-api-key` | No* | — | LUCID API key. Get one free at [trylucid.dev](https://trylucid.dev) |
| `anthropic-api-key` | No* | — | Anthropic API key for BYOK mode |
| `scan-mode` | No | `changed` | `changed` = only PR files, `full` = entire codebase |
| `fail-threshold` | No | `0` | Fail the action if compliance score is below this (0-100). `0` = never fail |
| `doc-source` | No | — | URL to verify against (BYOK only). ToS, Privacy Policy, etc. |
| `comment-on-pr` | No | `true` | Post results as a PR comment |
| `working-directory` | No | `.` | Root of the codebase to analyze |

*At least one of `lucid-api-key` or `anthropic-api-key` must be provided.

## Outputs

| Output | Description |
|--------|-------------|
| `compliance-score` | Score as a percentage (0-100) |
| `total-claims` | Total claims extracted |
| `pass-count` | Claims that passed verification |
| `fail-count` | Claims that failed verification |
| `partial-count` | Claims with partial verification |
| `report-path` | Path to the JSON report artifact |

## PR Comment

The action posts a comment on each PR with:

- **Compliance badge** — Color-coded score (green/yellow/orange/red)
- **Summary table** — Pass/Partial/Fail/N/A counts
- **Critical failures** — Always visible, with evidence and reasoning
- **Top issues** — Collapsible table of all failures and partial matches
- **Passing claims** — Collapsible list of what's verified
- **Category breakdown** — Score by category (security, data-privacy, etc.)

Previous LUCID comments are automatically replaced to keep PR threads clean.

## Examples

### Fail the build below 80% compliance

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    lucid-api-key: ${{ secrets.LUCID_API_KEY }}
    fail-threshold: '80'
```

### Full codebase scan

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    lucid-api-key: ${{ secrets.LUCID_API_KEY }}
    scan-mode: 'full'
```

### Verify against your Terms of Service (BYOK)

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    doc-source: 'https://example.com/terms-of-service'
```

### Use the compliance score in downstream steps

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  id: lucid
  with:
    lucid-api-key: ${{ secrets.LUCID_API_KEY }}

- run: |
    echo "Score: ${{ steps.lucid.outputs.compliance-score }}%"
    echo "Failures: ${{ steps.lucid.outputs.fail-count }}"
```

### Monorepo — scan a subdirectory

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    lucid-api-key: ${{ secrets.LUCID_API_KEY }}
    working-directory: 'packages/api'
```

## Supported Languages

TypeScript, JavaScript, Python, Ruby, Go, Rust, Java, C#, PHP, Swift, Kotlin, Scala, Vue, Svelte, SQL, GraphQL, and Prisma.

## Troubleshooting

### "Either lucid-api-key or anthropic-api-key must be provided"

Add one of the keys as a repository secret: **Settings > Secrets and variables > Actions**.

### No claims extracted

The codebase may be too small or doesn't have recognizable patterns. Try `scan-mode: full` or provide a `doc-source` (BYOK mode).

### Comment not posted

Ensure the workflow has `pull-requests: write` permission:

```yaml
permissions:
  contents: read
  pull-requests: write
```

### LUCID API quota exceeded

The free tier includes 100 verifications/month. Upgrade at [trylucid.dev](https://trylucid.dev) or switch to BYOK mode.

## Links

- [trylucid.dev](https://trylucid.dev) — Get a free API key
- [Benchmark Report](https://trylucid.dev/report) — LUCID achieves 100% on HumanEval and +36% on SWE-bench

---

*Built by [FrankLabs](https://franklabs.io) | [trylucid.dev](https://trylucid.dev)*
