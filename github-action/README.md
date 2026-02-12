# LUCID Verify - GitHub Action

**Automated AI code verification for every pull request.** LUCID extracts testable claims about your codebase (security, privacy, functionality) and verifies each one against the actual code. Results are posted as a PR comment with pass/fail verdicts and evidence.

## What it does

1. **Extracts claims** -- LUCID generates testable compliance claims from your codebase structure (or from a document you provide, like your Terms of Service)
2. **Verifies each claim** -- Every claim is checked against the actual source code with evidence
3. **Posts results** -- A detailed PR comment shows pass/fail counts, critical failures, and a compliance score

## Quick Start (< 5 minutes)

### 1. Add your Anthropic API key as a repository secret

Go to **Settings > Secrets and variables > Actions** and add:

- Name: `ANTHROPIC_API_KEY`
- Value: your Anthropic API key (starts with `sk-ant-`)

### 2. Create the workflow file

Create `.github/workflows/lucid-verify.yml`:

```yaml
name: LUCID Verify

on:
  pull_request:
    types: [opened, synchronize, reopened]

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

That's it. Every PR will now get a LUCID verification report as a comment.

## Configuration

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `anthropic-api-key` | Yes | -- | Anthropic API key for Claude |
| `scan-mode` | No | `changed` | `changed` = only PR files, `full` = entire codebase |
| `fail-threshold` | No | `0` | Minimum compliance score (0-100). Action fails below this. |
| `doc-source` | No | -- | URL to a document to verify against (ToS, Privacy Policy) |
| `comment-on-pr` | No | `true` | Post results as a PR comment |
| `working-directory` | No | `.` | Subdirectory to analyze |

### Outputs

| Output | Description |
|--------|-------------|
| `compliance-score` | Score as percentage (0-100) |
| `total-claims` | Number of claims extracted |
| `pass-count` | Claims that passed |
| `fail-count` | Claims that failed |
| `partial-count` | Claims partially passing |
| `report-path` | Path to full JSON report |

## Examples

### Verify against your Terms of Service

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    doc-source: 'https://example.com/terms-of-service'
```

### Fail the build below 80% compliance

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    fail-threshold: '80'
```

### Full codebase scan (not just changed files)

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    scan-mode: 'full'
```

### Use outputs in subsequent steps

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  id: lucid
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

- name: Check results
  run: |
    echo "Score: ${{ steps.lucid.outputs.compliance-score }}%"
    echo "Failed: ${{ steps.lucid.outputs.fail-count }} claims"
```

### Monorepo -- scan a subdirectory

```yaml
- uses: gtsbahamas/hallucination-reversing-system/github-action@main
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
    working-directory: 'packages/api'
```

## What the PR comment looks like

The action posts a comment with:

- **Compliance score badge** (color-coded: green/yellow/orange/red)
- **Summary table** with pass/partial/fail/N/A counts
- **Critical failures** highlighted at the top
- **Top issues** table with severity and reasoning
- **Passing claims** (collapsed)
- **Category breakdown** by security, privacy, functionality, etc.

Previous LUCID comments on the same PR are automatically replaced to avoid clutter.

## How it works

LUCID uses Claude to:

1. **Analyze your codebase structure** to understand what the code does
2. **Generate testable claims** about security, privacy, and functionality (or extract them from a document you provide)
3. **Select relevant source files** for each claim
4. **Verify each claim** against the actual code with evidence

This is the same technology behind the [LUCID research paper](https://trylucid.dev), which achieved 100% on HumanEval (k=3) and +36% improvement on SWE-bench.

## Cost

The action uses Claude Sonnet for verification. Typical cost per run:

| Codebase size | Claims | Approximate cost |
|---------------|--------|------------------|
| Small (< 50 files) | 15-20 | ~$0.05-0.10 |
| Medium (50-200 files) | 20-30 | ~$0.10-0.25 |
| Large (200+ files) | 25-30 | ~$0.15-0.40 |

With `scan-mode: changed` (default), only PR-changed files are prioritized, keeping costs low.

## Claim categories

| Category | What it checks |
|----------|---------------|
| `security` | Auth, encryption, input validation, CSRF, XSS |
| `data-privacy` | Data handling, storage, retention, consent |
| `functionality` | Core features, error handling, edge cases |
| `operational` | Logging, monitoring, rate limiting |
| `legal` | Compliance-related code requirements |

## Severity levels

| Level | Meaning |
|-------|---------|
| `critical` | Security vulnerabilities, data exposure risks |
| `high` | Significant gaps in claimed functionality |
| `medium` | Partial implementations, missing edge cases |
| `low` | Minor improvements, best practice suggestions |

## Troubleshooting

### Action fails with "ANTHROPIC_API_KEY is not set"

Make sure you added the secret in **Settings > Secrets and variables > Actions**, not in environment variables.

### No claims extracted

This usually means the codebase is too small or doesn't have recognizable patterns. Try `scan-mode: full` or provide a `doc-source`.

### Comment not posted

Ensure the workflow has `pull-requests: write` permission:

```yaml
permissions:
  contents: read
  pull-requests: write
```

## License

MIT -- see [LICENSE](../LICENSE)

---

*Built by [FrankLabs](https://franklabs.io) | [trylucid.dev](https://trylucid.dev)*
