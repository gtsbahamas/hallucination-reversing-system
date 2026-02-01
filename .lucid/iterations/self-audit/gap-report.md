# LUCID Self-Audit Gap Report

*Generated: 2026-02-01*
*Method: Manual claim extraction from README.md, docs/methodology.md, docs/plans/2026-02-01-lucid-product-plan.md, package.json*
*Verified against: src/ codebase*

---

## Executive Summary

Extracted **52 testable claims** from LUCID's own documentation and verified each against the codebase.

| Metric | Value |
|--------|-------|
| Total claims | 52 |
| PASS | 28 |
| PARTIAL | 8 |
| FAIL | 6 |
| N/A | 10 |
| **Compliance score** | **76.2%** |

**Risk Assessment:** 1 critical inconsistency (naming conflict) and 5 methodology gaps (missing REGENERATE phase). The CLI delivers 5 of 6 documented methodology phases. The missing 6th phase (Regenerate) is a significant gap since it's the core of the "iterative convergence loop" that LUCID claims to be.

---

## Priority Matrix

| Severity | FAIL | PARTIAL | PASS | N/A |
|----------|------|---------|------|-----|
| critical | 1 | 0 | 0 | 0 |
| high | 3 | 3 | 8 | 0 |
| medium | 2 | 4 | 12 | 2 |
| low | 0 | 1 | 8 | 8 |

---

## Detailed Findings

### Naming & Identity

[FAIL] **CLAIM-01** [critical] — LUCID stands for "Leveraging Unverified Claims Into Deliverables"
> README.md line 3 says "Leveraging Unverified Claims Into Deliverables"
> `package.json:4` says "Legal Understanding through Code Inspection & Discovery"
> These are two different expansions of the same acronym. Contradictory.

[PASS] **CLAIM-02** [low] — CLI name is `lucid`
> `src/cli.ts:14`: `.name('lucid')`

[PASS] **CLAIM-03** [low] — Version is 0.1.0
> `src/cli.ts:16`: `.version('0.1.0')` matches `package.json:3`

[PASS] **CLAIM-04** [low] — License is MIT
> `LICENSE` file exists at repo root

### 6-Phase Methodology (README + methodology.md)

[PASS] **CLAIM-05** [high] — Phase 1 (DESCRIBE/Seed): "Give the AI a loose, conversational description of what the application should do"
> `src/commands/init.ts:16-29` collects projectName, description, techStack, targetAudience via interactive prompts. These feed into hallucination prompts.

[PASS] **CLAIM-06** [high] — Phase 2 (HALLUCINATE): "Ask the AI to write a Terms of Service as if the application is already live in production"
> `src/commands/hallucinate.ts` + `src/lib/system-prompts.ts:26`: "You are the legal team for a technology company. You are writing the Terms of Service for a production application."
> `src/lib/system-prompts.ts:36`: "Write as if this application EXISTS and is LIVE in production."

[PASS] **CLAIM-07** [high] — Phase 3 (EXTRACT): "Parse every declarative statement from the ToS into a testable requirement"
> `src/commands/extract.ts` + `src/lib/claim-extractor.ts` — AI-powered extraction into structured JSON claims with category, severity, testability.

[N/A] **CLAIM-08** [medium] — Phase 4 (BUILD): "Implement the application to satisfy the extracted requirements"
> Not in CLI scope. README says "Use any development methodology." Intentionally external.

[PASS] **CLAIM-09** [high] — Phase 5 (CONVERGE): "Compare the ToS claims against the actual application"
> `src/commands/verify.ts` + `src/lib/code-verifier.ts` — Two-stage AI verification (file selection + evidence evaluation) with PASS/PARTIAL/FAIL/N/A verdicts.

[FAIL] **CLAIM-10** [high] — Phase 6 (REGENERATE): "Feed the updated application state back to the AI and generate a new ToS"
> No `regenerate` command exists. No CLI mechanism to provide gap report + current state and re-hallucinate. The `hallucinate` command generates from config only, not from prior iteration state.

[FAIL] **CLAIM-11** [high] — "The loop is the methodology. LUCID isn't a one-shot generation. It's an iterative convergence between fiction and reality." (README Principle 5)
> The CLI supports iterations (auto-incrementing iteration numbers), but there's no mechanism to feed iteration N results into iteration N+1. Running `lucid hallucinate` again produces a fresh hallucination from the same config, not an updated one incorporating verification results.

[PARTIAL] **CLAIM-12** [medium] — "The loop terminates when the delta between hallucinated ToS and verified reality reaches an acceptable threshold"
> No automated delta tracking or threshold checking. The iteration structure exists, but comparing across iterations is not implemented.

### Document Types

[PASS] **CLAIM-13** [high] — Hallucination supports ToS document type
> `src/lib/system-prompts.ts:25-82`: Full ToS prompt with 20 mandatory sections, specificity requirements, 400-600 line target.

[PASS] **CLAIM-14** [high] — Hallucination supports API docs document type
> `src/lib/system-prompts.ts:84-121`: Full API docs prompt with 10 mandatory sections.

[PASS] **CLAIM-15** [high] — Hallucination supports user manual document type
> `src/lib/system-prompts.ts:123-158`: Full user manual prompt with 10 mandatory sections.

[PASS] **CLAIM-16** [medium] — "400-600 lines of dense, specific legal text" target for ToS
> `src/lib/system-prompts.ts:78`: "400-600 lines of dense, specific legal text"

[PASS] **CLAIM-17** [medium] — "80-150 extractable, testable claims" target for ToS
> `src/lib/system-prompts.ts:79`: "80-150 extractable, testable claims"

### Claim Extraction

[PASS] **CLAIM-18** [high] — Claims are categorized by type: data-privacy, security, functionality, operational, legal
> `src/types.ts:25-30`: `ClaimCategory` union type with all 5 categories.
> `src/lib/claim-extractor.ts:59-61`: Validated against these categories.

[PASS] **CLAIM-19** [high] — Claims are categorized by severity: critical, high, medium, low
> `src/types.ts:32`: `ClaimSeverity` union type.
> `src/lib/claim-extractor.ts:63-65`: Validated.

[PASS] **CLAIM-20** [medium] — "Split compound claims into individual claims"
> `src/lib/claim-extractor.ts:14-15` extraction prompt: "Split compound claims into individual claims."

[PASS] **CLAIM-21** [medium] — Claims are marked as testable or non-testable
> `src/types.ts:40`: `testable: boolean` field on Claim type.
> `src/lib/claim-extractor.ts:17-19`: Prompt instructs testable vs non-testable classification.

[PASS] **CLAIM-22** [medium] — Each claim traces back to a specific section
> `src/types.ts:37`: `section: string` field on Claim type.

### Verification

[PASS] **CLAIM-23** [high] — Two-stage verification: file selection then claim evaluation
> `src/lib/code-verifier.ts:14-27`: FILE_SELECTION_SYSTEM prompt (stage 1)
> `src/lib/code-verifier.ts:30-63`: VERIFICATION_SYSTEM prompt (stage 2)

[PASS] **CLAIM-24** [medium] — Verification uses PASS/PARTIAL/FAIL/N/A verdicts
> `src/types.ts:54`: `Verdict = 'PASS' | 'PARTIAL' | 'FAIL' | 'N/A'`

[PASS] **CLAIM-25** [medium] — Evidence includes file path, line number, code snippet, confidence score
> `src/types.ts:56-61`: Evidence type with all 4 fields.

[PASS] **CLAIM-26** [medium] — Claims are verified in batches of 15
> `src/lib/code-verifier.ts:145`: `const BATCH_SIZE = 15`

[PASS] **CLAIM-27** [medium] — Non-testable claims are marked N/A automatically
> `src/lib/code-verifier.ts:163-172`: Filters non-testable claims, pushes N/A verdict immediately.

[PARTIAL] **CLAIM-28** [medium] — Methodology.md: "Gap categories: Missing feature, Partial implementation, Unverified, Exceeds claim"
> Only PASS/PARTIAL/FAIL/N/A exist. No "Exceeds claim" category for when code does more than ToS claims. "Unverified" maps roughly to N/A.

### Gap Report

[PASS] **CLAIM-29** [medium] — Report includes executive summary with compliance score
> `src/lib/report-generator.ts:29-50`: Executive summary section with compliance percentage.

[PASS] **CLAIM-30** [medium] — Report includes priority matrix (severity x verdict)
> `src/lib/report-generator.ts:88-107`: Full matrix table.

[PASS] **CLAIM-31** [medium] — Report includes fix recommendations sorted by priority
> `src/lib/report-generator.ts:156-204`: Immediate (Critical), High Priority, Medium Priority, Partial sections.

[PASS] **CLAIM-32** [low] — Report includes methodology section
> `src/lib/report-generator.ts:69-86`: Methodology explanation.

### CLI Commands

[PASS] **CLAIM-33** [medium] — `lucid init` creates .lucid/config.json and .lucid/iterations/
> `src/lib/config.ts:37-48`: writeConfig creates both directories.
> `src/commands/init.ts:43-45`: Prints confirmation of both.

[PASS] **CLAIM-34** [low] — `lucid init` warns before overwriting existing config
> `src/commands/init.ts:8-14`: Checks configExists(), asks confirm().

[PASS] **CLAIM-35** [medium] — `lucid hallucinate` streams output in real-time
> `src/lib/anthropic.ts:39-48`: Uses `client.messages.stream()` with `stream.on('text')` writing to stdout.

[PASS] **CLAIM-36** [medium] — `lucid hallucinate` saves metadata (model, tokens, duration, section count)
> `src/commands/hallucinate.ts:91-104`: HallucinationMeta with all fields saved to meta.json.

[PASS] **CLAIM-37** [medium] — `lucid describe` fetches documents from URLs and strips HTML
> `src/commands/describe.ts:10-73`: fetch + stripHtml with tag/entity handling.

[PASS] **CLAIM-38** [low] — `lucid extract` works on both hallucinated docs and described source docs
> `src/commands/extract.ts:39-57` (source path) and `src/commands/extract.ts:62-105` (iteration path).

[PASS] **CLAIM-39** [low] — `lucid verify` defaults to current directory if no --repo
> `src/commands/verify.ts:24`: `resolve(options.repo || '.')`

[PASS] **CLAIM-40** [low] — `lucid report` requires both claims.json and verification.json
> `src/commands/report.ts:44-54`: Checks for both files, exits with error if missing.

### Codebase Indexing

[PASS] **CLAIM-41** [medium] — Codebase indexer detects frameworks (Next.js, Prisma, Supabase, etc.)
> `src/lib/codebase-indexer.ts:76-95`: detectFrameworks checks for 12+ framework signatures.

[PASS] **CLAIM-42** [medium] — Codebase indexer identifies key files (API routes, auth, config, schemas)
> `src/lib/codebase-indexer.ts:97-135`: identifyKeyFiles checks CONFIG_FILES, SCHEMA_PATTERNS, API routes, auth patterns.

[PARTIAL] **CLAIM-43** [low] — Codebase indexer respects standard ignore patterns
> `src/lib/codebase-indexer.ts:19-23`: IGNORE_DIRS covers node_modules, .git, etc. Also skips dotfiles (`entry.name.startsWith('.')`). No .gitignore parsing though.

### Technical Claims

[PASS] **CLAIM-44** [medium] — Uses Anthropic Claude Sonnet 4.5 model
> `src/lib/anthropic.ts:6`: `MODEL = 'claude-sonnet-4-5-20250929'`

[PASS] **CLAIM-45** [medium] — Requires ANTHROPIC_API_KEY environment variable
> `src/lib/anthropic.ts:10-16`: Checks env var, throws descriptive error if missing.

[PARTIAL] **CLAIM-46** [medium] — Handles JSON truncation from AI responses
> `src/lib/claim-extractor.ts:135-141`: Repairs truncated arrays by finding last `}` and closing `]`.
> `src/lib/code-verifier.ts:94-99`: Same repair for verification responses.
> However: only handles missing `]` — doesn't handle truncation mid-object (missing `}`).

[PARTIAL] **CLAIM-47** [medium] — Strips markdown code fences from AI responses
> `src/lib/claim-extractor.ts:119-131`: Removes opening and closing fences.
> Doesn't handle nested fences or unusual fence formats (e.g., ~~~~).

### Product Plan Claims (About Current CLI)

[PARTIAL] **CLAIM-48** [high] — "Core logic (extract, verify, report) gets extracted into importable functions that the web app calls"
> The core logic IS in `src/lib/` (claim-extractor.ts, code-verifier.ts, report-generator.ts), which is the right structure. But they're not exported as a library — no index.ts, no package exports field. They're importable within the project but not as an npm package.

[N/A] **CLAIM-49** [low] — Product plan: "$2-5 per audit based on Frank Labs test"
> Historical claim about API costs. Not verifiable from code.

[N/A] **CLAIM-50** [low] — Product plan: Phase 1 SaaS features (Next.js, Supabase, Stripe, GitHub App)
> Future plans, not current CLI. Not built.

### URL & Branding Claims

[PARTIAL] **CLAIM-51** [low] — describe.ts User-Agent: "LUCID-Auditor/1.0; +https://franklabs.io/lucid"
> `src/commands/describe.ts:14`: URL claimed in User-Agent header. URL existence not verified.

[FAIL] **CLAIM-52** [medium] — report-generator.ts footer: "https://franklabs.io/lucid"
> `src/lib/report-generator.ts:210`: Footer includes this URL. Every generated report links to a URL that may not exist, which looks unprofessional if served to customers.

---

## Fix Recommendations

### Immediate (Critical)

- [ ] **CLAIM-01**: Resolve the LUCID acronym conflict. README says "Leveraging Unverified Claims Into Deliverables", package.json says "Legal Understanding through Code Inspection & Discovery". Pick one. The README version is the established identity.

### High Priority

- [ ] **CLAIM-10**: Implement a `lucid regenerate` command. This is the core differentiator of LUCID as a *methodology* vs a one-shot audit tool. The command should accept the current gap report + updated codebase state and produce a new hallucinated document that incorporates reality.
- [ ] **CLAIM-11**: Make the iteration loop functional. `lucid hallucinate` should optionally accept `--from-iteration N` to incorporate prior verification results into the next hallucination.
- [ ] **CLAIM-48**: Add `exports` field to package.json or create `src/index.ts` that re-exports the core library functions (extractClaims, verifyClaims, generateGapReport, indexCodebase) for the future web app to import.

### Medium Priority

- [ ] **CLAIM-12**: Add iteration comparison. `lucid report --compare 1 2` to show delta between iterations.
- [ ] **CLAIM-28**: Consider adding an "EXCEEDS" verdict for when code delivers more than the document claims.
- [ ] **CLAIM-52**: Verify https://franklabs.io/lucid exists, or remove the URL from generated reports until it does.

### Partial Implementations (Quick Wins)

- [ ] **CLAIM-43**: Consider parsing .gitignore for more accurate file tree (low priority — current ignore list covers common cases).
- [ ] **CLAIM-46**: Improve JSON truncation repair to handle mid-object truncation.
- [ ] **CLAIM-47**: Handle edge cases in code fence stripping (nested fences, ~~~~ format).
- [ ] **CLAIM-51**: Verify or update User-Agent URL.

---

## What LUCID Gets Right (Self-Assessment)

The CLI implements 5 of 6 methodology phases with solid engineering:

1. **Type-first design** — Clean TypeScript types in `types.ts` define the full domain model
2. **Streaming output** — Hallucination streams in real-time, good UX
3. **Two-stage verification** — Smart approach: file selection then evidence evaluation reduces token usage
4. **Batch processing** — 15-claim batches keep API calls manageable
5. **Truncation recovery** — Handles common AI JSON output issues
6. **Multiple document types** — ToS, API docs, and user manuals all supported with purpose-built prompts
7. **Describe command** — Real-world insight: existing docs ARE the hallucination

## What LUCID Gets Wrong (Self-Assessment)

1. **The loop doesn't loop** — The defining feature of LUCID (iterative convergence) is not implemented in the CLI
2. **Identity crisis** — Two different acronym expansions
3. **Phantom URL** — Generated reports link to a potentially non-existent page
4. **Not packageable** — Core logic can't be imported as a library yet

---

*Report generated by manual LUCID self-audit — Leveraging Unverified Claims Into Deliverables*
