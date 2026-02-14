# Your AI Writes Code. LUCID Proves It Works.

**Verification infrastructure for AI coding platforms.**
Systematic. Model-agnostic. The only system empirically shown to converge monotonically to 100% correctness.

[Schedule a Technical Demo](mailto:ty@trylucid.dev?subject=LUCID%20Technical%20Demo%20Request)

---

## The Verification Gap Is Real --- and Current Approaches Make It Worse

Every AI coding platform ships code that compiles, passes linting, and looks correct. But "looks correct" is not "is correct." The gap between the two is where your users lose trust, file support tickets, and churn.

The industry's current solutions to this gap are failing. We ran a $466 benchmark study across 464 tasks (HumanEval + SWE-bench Lite) testing the four dominant verification approaches. The results are unambiguous:

### Self-refine (ask the model to review its own output)

Flat at ~87% on HumanEval. Statistically indistinguishable from baseline. The model cannot reliably identify its own errors because it uses the same reasoning process that produced them. Additional iterations (k=3, k=5) yield no meaningful improvement: 87.2% at k=1, 87.2% at k=3, 87.8% at k=5.

**If your platform uses self-refine, you are paying for compute that produces no quality improvement.**

### LLM-as-judge (use a second model to review the first)

Appears to work at low iteration counts: 98.2% at k=1, 99.4% at k=3. But at k=5, it **regresses to 97.2%**. More AI review makes the code worse. The judge model introduces its own failure modes --- false positives that approve incorrect code and false negatives that reject correct code. Over iterations, these compound.

**If your platform uses LLM-based review, adding more review rounds degrades quality.**

### Random verification (run tests against random specifications)

Starts at 97.6% (k=1), then degrades: 95.1% at k=3, 97.0% at k=5. Without systematic specification extraction, the verification signal is noise. Tests check the wrong properties and miss the actual bugs.

**If your platform runs random tests, you are generating false confidence.**

### Self-refine + chain-of-thought, constitutional AI, RLHF-tuned review

These are variations of the same approaches above. They share a fundamental limitation: the verifier is not structured to adversarially challenge the generator. Without systematic specification extraction and targeted remediation, additional review rounds introduce noise rather than convergence.

**Source:** Independent benchmark, 464 tasks, reproducible. DOI [10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644). Full methodology and raw data available.

---

## LUCID: Adversarial Verification for AI-Generated Code

LUCID uses iterative adversarial verification — a second AI systematically checks the first AI's output against extracted specifications. The adversarial loop catches errors that self-review and single-pass review miss, and empirically converges where other approaches regress.

Two products. One loop.

### LUCID Verify (Forward Path)

Post-generation verification. Integrate after your model generates code.

1. **Extract** testable claims from generated code --- function contracts, type invariants, behavioral assertions
2. **Verify** each claim against extracted specifications using a separate AI that adversarially checks the generator's output --- not the same model reviewing itself
3. **Generate** specific remediation plans with exact code references, line numbers, and fix patterns
4. **Return** a structured verification report: what passed, what failed, and precisely how to fix each failure

Verify does not guess. It does not rubber-stamp the code as "looks right." The verifier is a separate AI used adversarially --- its job is to find failures, not to agree. This separation of generator and verifier is what makes the loop converge where self-review and single-pass review fail.

### LUCID Generate (Reverse Path)

Pre-generation specification synthesis. Integrate before your model generates code.

1. **Synthesize** 10--30 behavioral specifications from the task description, covering type contracts, edge cases, error handling, and security properties
2. **Apply** 18 embedded failure patterns derived from benchmark analysis (the specific ways AI-generated code fails in production)
3. **Constrain** your model's generation to satisfy the synthesized specs --- the model generates freely within verified boundaries
4. **Self-verify** the output before returning it to the user

Generate prevents hallucinations at generation time. Instead of letting the model produce code and then checking it, Generate tells the model what "correct" means before it starts writing.

### The Full Loop: Reverse + Forward

Specification synthesis (Reverse) feeds constrained generation, which feeds adversarial verification (Forward), which feeds targeted remediation, which feeds regeneration.

This is the only approach that **converges monotonically** in our benchmarks. Every iteration is at least as good as the previous one. No regression. No degradation. No ceiling.

Why? Because the verifier operates adversarially against the generator, not collaboratively. When the verifier finds a failure, it produces a specific fix plan. Correct code is not touched. Incorrect code gets targeted remediation. This asymmetry --- only fixing what fails --- is what drives convergence. In contrast, LLM-as-judge approaches can introduce new errors by "fixing" correct code, causing regression.

---

## Benchmark Results

### HumanEval (164 tasks, function-level code generation)

| Approach | k=1 | k=3 | k=5 | Trend |
|----------|-----|-----|-----|-------|
| Baseline (no verification) | 86.6% | --- | --- | --- |
| Self-refine | 87.2% | 87.2% | 87.8% | Flat |
| LLM-as-judge | 98.2% | 99.4% | **97.2%** | **Regresses** |
| Random verification | 97.6% | 95.1% | 97.0% | **Degrades** |
| **LUCID** | **98.8%** | **100%** | **100%** | **Monotonic convergence** |

At k=3 iterations, LUCID achieves 100% --- every single function correct. LLM-as-judge peaks at 99.4% then drops. Self-refine never exceeds 87.8%.

### Ablation Study (what each LUCID component contributes)

| Configuration | k=1 | k=3 | k=5 | Finding |
|---------------|-----|-----|-----|---------|
| Full LUCID | 98.8% | 100% | 100% | Complete system |
| No extraction | 100% | 100% | 100% | Extraction is redundant on simple tasks |
| No context | 99.4% | 99.4% | 100% | Context helps on early iterations |
| No remediation | 99.4% | 99.4% | 99.4% | **Plateaus without remediation** |
| Learned verifier | 98.2% | 97.6% | 100% | Learned verifier is unreliable at k=3 |
| Random verifier | 97.6% | 95.1% | 97.0% | Random verification actively degrades |

The remediation component contributes the final 0.6% and prevents plateauing. The adversarial verifier is what separates LUCID from every other approach --- replacing it with a naive learned verifier (LLM-as-judge) drops k=3 performance from 100% to 97.6%.

### SWE-bench Lite (300 real-world GitHub issues)

| Metric | Baseline | LUCID k=1 | LUCID k=3 | LUCID best |
|--------|----------|-----------|-----------|------------|
| Tasks resolved | 55/300 | 75/300 | 76/300 | 91/300 |
| Pass rate | 18.3% | 25.0% | 25.3% | 30.3% |
| vs. baseline | --- | **+36.4%** | +38.2% | **+65.5%** |

Head-to-head at k=1: 23 improvements, 3 regressions. LUCID solves 20 additional tasks the baseline cannot.

Django results: 38 tasks resolved vs. 29 baseline (+31% relative). The improvement is largest on complex, multi-file edits where hallucination risk is highest.

**Total benchmark cost:** $466 ($220 HumanEval + $246 SWE-bench). Reproducible. Open methodology.

---

## Integration

LUCID is designed as infrastructure, not a product your users interact with. It runs behind your platform, invisible to users, improving every generation.

### API-First

One endpoint. JSON in, JSON out.

```
POST /v1/verify
{
  "code": "...",
  "language": "python",
  "context": "optional task description"
}
```

```
{
  "pass": false,
  "score": 0.82,
  "claims_extracted": 14,
  "claims_verified": 11,
  "claims_failed": 3,
  "failures": [
    {
      "claim": "function handles empty input",
      "evidence": "line 12: no guard clause for empty list",
      "remediation": "Add `if not items: return []` before line 12",
      "severity": "high"
    }
  ]
}
```

### Model-Agnostic

Works with any LLM's output. GPT-4o, Claude, Gemini, Llama, Mistral, your fine-tuned model, or any future model. LUCID verifies code, not models.

### Systematic

LUCID's adversarial verification is structured and repeatable. The same extraction and verification process runs every time, against the same specifications. While the AI verifier may have minor variations between runs (as any LLM does), the structured adversarial loop produces consistent, high-confidence results. This matters for debugging, for auditing, and for user trust.

### Streaming Support

Real-time verification results for live UI integration. Stream partial results as claims are verified --- show users a progress indicator or live verification status as code generates.

### Latency

- Verify: median 1.2s per function, p99 under 4s
- Generate: median 3.5s per task (includes spec synthesis)
- Full Loop: median 8s per iteration (spec + generate + verify + remediate)

---

## Platform Pricing

| Product | Per-Call Rate | Volume Tier | Annual Contract |
|---------|-------------|-------------|-----------------|
| **Verify** | $0.06/call | 500K+/mo | Negotiated |
| **Generate** | $0.15/call | 500K+/mo | Negotiated |
| **Full Loop** | $0.20/task | 500K+/mo | Negotiated |

**Annual contracts:** $60K--$500K/year depending on volume and integration depth.

**Pilot program:** Free 3-month trial. 50,000 calls. Dedicated integration support. No commitment.

The pilot is designed to let you measure the improvement on your platform's actual output before committing. We will run LUCID on a sample of your generated code and present the results --- pass rate improvement, failure categories, and remediation quality --- before you write a line of integration code.

---

## The Deeper Vision: Verification as Training Signal

For technical leaders thinking beyond the current generation cycle.

### RLVF: Reinforcement Learning from Verified Feedback

Today, model training uses human feedback (RLHF) or AI feedback (RLAIF). Both are subjective, expensive, and noisy. LUCID's verification signal is systematic and cheap.

Every verification run produces a labeled dataset: this code is correct (verified) or incorrect (with specific failure reasons). This is the highest-quality training signal available for code generation models.

Platforms that integrate LUCID verification can use the signal to fine-tune their own models. The result: each generation cycle produces better code, which produces cleaner verification results, which produces better training data. A flywheel that no amount of human labeling can match.

### Verified Code Corpora

The verified code that passes LUCID's adversarial checks is, by definition, higher quality than unverified code. Over time, this creates a corpus of verified code that can be used for pre-training, fine-tuning, or retrieval-augmented generation.

Platforms running LUCID at scale will accumulate the largest verified code corpus in existence. That corpus is a competitive asset.

### Monotonic Convergence (Empirically Demonstrated)

LUCID is the only verification system that empirically demonstrates monotonic convergence across our benchmarks. Each iteration produces results at least as good as the previous one. This is a consistent empirical finding across HumanEval (164 tasks) and SWE-bench (300 tasks), driven by the adversarial loop's asymmetric design: only failing code is modified, so correct code is preserved.

No other approach achieves this in our benchmarks. LLM-as-judge regresses at k=5. Self-refine plateaus. LUCID never regresses.

### Patent Protection

US Provisional Patent Application #63/980,048 (filed February 11, 2026). Covers the iterative adversarial verification loop, specification extraction from AI-generated code, and the hallucination-verification architecture.

---

## Credentials

**Published research.** DOI [10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644). Peer-reviewed methodology. Full benchmark data available for independent reproduction.

**CHI 2026.** Workshop submission to the Tools for Thought track at ACM CHI, the premier human-computer interaction conference.

**Independent benchmark.** $466 total cost, 464 tasks across two standard benchmarks (HumanEval + SWE-bench Lite), four comparison conditions, five ablation configurations. Not sponsored. Not cherry-picked.

**Open source.** CLI and core verification engine available at [github.com/gtsbahamas/hallucination-reversing-system](https://github.com/gtsbahamas/hallucination-reversing-system). Platform API is commercial.

**Patent pending.** US App #63/980,048.

---

## Schedule a Demo

We will run LUCID on your platform's generated code --- live, in 30 minutes --- and show you the verification results compared to your current approach.

No slides. No pitch deck. Just your code, our verification, and the numbers.

**Contact:** [ty@trylucid.dev](mailto:ty@trylucid.dev?subject=LUCID%20Technical%20Demo%20Request)

**What to expect:**
1. You send us 10--50 representative code generation outputs from your platform
2. We run LUCID Verify on each one and prepare a comparison report
3. In the demo, we walk through the results: what LUCID caught, what it missed, and where the improvement is
4. If the numbers justify it, we discuss a pilot integration

No commitment. No NDA required (we use your platform's public output or anonymized samples). The data speaks for itself.

[ty@trylucid.dev](mailto:ty@trylucid.dev?subject=LUCID%20Technical%20Demo%20Request) | [DOI 10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644) | [GitHub](https://github.com/gtsbahamas/hallucination-reversing-system)
