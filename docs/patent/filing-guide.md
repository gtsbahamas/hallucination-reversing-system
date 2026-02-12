# USPTO PROVISIONAL PATENT FILING GUIDE

## System and Method for Iterative Formal Verification of AI-Generated Code Using a Hallucination-Verification Loop

---

## 1. Overview

A **provisional patent application** establishes a priority date for the invention and provides a 12-month window to file a non-provisional (full) patent application. It is faster, cheaper, and simpler than a full patent filing. It is not examined and does not itself become a patent --- it secures the date from which prior art is evaluated.

**Why file now (before publishing the benchmark report):**
- Establishes priority date *before* any public disclosure of implementation details
- The architecture paper and benchmark results, once published, become prior art against any future patent filing
- 12-month window provides time to refine claims, gather additional evidence, and decide on full patent strategy
- Relatively low cost (~$1,700-3,500 depending on entity status)

---

## 2. Entity Status: Micro-Entity vs. Small Entity

### Micro-Entity Qualification (37 CFR 1.29)

To qualify as a micro-entity, ALL of the following must be true:

| Requirement | Assessment |
|-------------|------------|
| Qualifies as small entity (fewer than 500 employees) | YES --- individual inventor / small startup |
| Not named as inventor on more than 4 previously filed US patent applications | Likely YES --- verify with Ty Wells |
| Did not have gross income exceeding 3x median household income (~$225,000) in the calendar year preceding filing | Verify with Ty Wells |
| Has not assigned, granted, or conveyed (and is not obligated to do so) a license or ownership interest in the application to an entity that exceeds the income limit | Likely YES --- no assignment to large entity |

### Fee Comparison (2026 Estimates)

| Fee | Micro-Entity | Small Entity | Large Entity |
|-----|-------------|-------------|--------------|
| Provisional filing fee | ~$160 | ~$320 | ~$1,600 |
| Provisional surcharge (late filing of formal papers) | $0 | $0 | $0 |
| **Total provisional filing** | **~$160** | **~$320** | **~$1,600** |

**Recommendation:** File as micro-entity if qualified. Saves ~$160 vs. small entity.

### Patent Attorney Fees (Estimate)

| Service | Estimated Cost |
|---------|---------------|
| Review and polish provisional specification | $1,500-2,500 |
| Prepare formal claims (review our draft claims) | Included above |
| Prepare formal drawings (from our mermaid flowcharts) | $300-500 |
| File via EFS-Web | $200-400 |
| **Total with attorney** | **$2,000-3,400** |
| **Total self-filing (no attorney)** | **$160-320** |

**Recommendation:** Use a patent attorney for best protection. The specification and claims drafts in this package provide a strong starting point that will reduce attorney time.

---

## 3. Required Documents

### 3.1 Documents Included in This Package

| Document | File | Status |
|----------|------|--------|
| Specification | `provisional-specification.md` | Complete draft |
| Claims | `claims.md` | Complete draft (20 claims) |
| Flowchart descriptions | `flowcharts.md` | Complete (7 figures with mermaid) |
| Filing guide | `filing-guide.md` | This document |

### 3.2 Additional Documents Needed for Filing

| Document | Description | Status |
|----------|-------------|--------|
| **Cover sheet** (SB/16) | USPTO form identifying the application as provisional | To prepare |
| **Formal drawings** | Patent drawings rendered from our mermaid flowcharts (black-and-white line drawings per USPTO standards) | To prepare (patent illustrator) |
| **Declaration (optional for provisional)** | Inventor declaration is NOT required for provisional filing | Not needed |
| **Fee payment** | Filing fee based on entity status | At filing time |
| **Application Data Sheet** (ADS) | Inventor name, correspondence address, entity status | To prepare |

### 3.3 What Is NOT Needed for Provisional Filing

- Formal claims (included for completeness, but not examined)
- Oath or declaration
- Information disclosure statement (IDS)
- Formal specification formatting (37 CFR 1.52 format not required for provisional)

---

## 4. Filing Process via EFS-Web (USPTO Patent Center)

### Step 1: Create a USPTO Account

1. Navigate to https://patentcenter.uspto.gov
2. Click "Create Account"
3. Register with personal or business information
4. Verify email address
5. Set up two-factor authentication

### Step 2: Prepare the Filing

1. **Convert specification to PDF.** The provisional specification (`provisional-specification.md`) should be converted to PDF format. Markdown rendering with LaTeX math notation is acceptable.

2. **Prepare formal drawings.** Convert the mermaid flowcharts to formal patent drawings. Options:
   - Hire a patent illustrator ($300-500) for USPTO-compliant drawings
   - Use a tool like draw.io, Lucidchart, or Visio to create black-and-white line drawings
   - Each figure should be on its own page, numbered (FIG. 1, FIG. 2, etc.)

3. **Prepare cover sheet.** Use USPTO form SB/16 (Provisional Application for Patent Cover Sheet):
   - Title: "System and Method for Iterative Formal Verification of AI-Generated Code Using a Hallucination-Verification Loop"
   - Inventor(s): Ty Wells
   - Correspondence address
   - Entity status: Micro-entity or Small entity (as qualified)

4. **Prepare Application Data Sheet (ADS).** USPTO form with inventor details.

### Step 3: File via Patent Center

1. Log in to https://patentcenter.uspto.gov
2. Click "New Submission" > "Provisional Application"
3. Upload documents:
   - Specification (PDF)
   - Drawings (PDF)
   - Cover sheet (SB/16)
   - Application Data Sheet (ADS)
4. Pay filing fee:
   - Micro-entity: ~$160
   - Small entity: ~$320
5. Submit and save the filing receipt

### Step 4: Receive Filing Receipt

- USPTO assigns an application number and filing date
- Save the filing receipt --- the filing date is the priority date
- The priority date is the date against which all prior art will be evaluated

---

## 5. Timeline and Milestones

### Critical Dates

| Date | Event | Action |
|------|-------|--------|
| **ASAP** | File provisional application | Establishes priority date |
| Filing date + 12 months | **Deadline for non-provisional filing** | Must file full (non-provisional) patent application or the provisional expires |
| Before filing | Do NOT publish implementation details | Protect against self-created prior art |
| After filing | Safe to publish benchmark report, arXiv paper | Filing date protects against this disclosure |

### Recommended Timeline

| When | Action |
|------|--------|
| Week 1 | Review this package; engage patent attorney (optional but recommended) |
| Week 1-2 | Attorney reviews and polishes specification and claims |
| Week 2 | Patent illustrator creates formal drawings from mermaid flowcharts |
| Week 2-3 | **File provisional application** |
| Week 3+ | Publish benchmark report, arXiv paper, begin outreach (protected by filing date) |
| Month 6 | Assess commercial traction; decide on non-provisional filing strategy |
| Month 10-11 | Engage patent attorney for non-provisional application preparation |
| **Month 12** | **Deadline: file non-provisional or lose provisional priority** |

### Post-Filing Decision Matrix

At month 6-8, assess whether to file a non-provisional based on:

| Signal | Action |
|--------|--------|
| Platform pilot signed, revenue potential clear | File non-provisional (budget $8,000-15,000 with attorney) |
| Academic interest strong, commercial uncertain | Consider PCT international filing for broader protection |
| No commercial traction | Let provisional expire; publish as prior art to prevent others from patenting |
| Competitive threat (someone else filing similar claims) | File non-provisional urgently |

---

## 6. Cost Summary

### Provisional Filing (Now)

| Item | Self-File | With Attorney |
|------|-----------|---------------|
| USPTO filing fee (micro-entity) | $160 | $160 |
| USPTO filing fee (small entity) | $320 | $320 |
| Attorney review and preparation | $0 | $1,500-2,500 |
| Patent illustrator (drawings) | $0-300 | $300-500 |
| **Total (micro-entity)** | **$160-460** | **$1,960-3,160** |
| **Total (small entity)** | **$320-620** | **$2,120-3,320** |

### Non-Provisional Filing (12 months from now, if decided)

| Item | Estimated Cost |
|------|---------------|
| USPTO filing fee (micro-entity) | ~$400 |
| USPTO search fee (micro-entity) | ~$200 |
| USPTO examination fee (micro-entity) | ~$200 |
| Patent attorney preparation | $5,000-10,000 |
| Patent illustrator (updated drawings) | $500-1,000 |
| **Total (micro-entity)** | **~$6,300-11,800** |

### Optional Future: PCT International Filing

| Item | Estimated Cost |
|------|---------------|
| PCT filing fee | ~$3,000-4,000 |
| PCT search fee | ~$2,000-3,000 |
| Attorney preparation | $3,000-5,000 |
| National phase entries (per country, after 30 months) | $3,000-8,000 each |
| **Total PCT filing** | **~$8,000-12,000** |
| **Per-country national phase** | **$3,000-8,000 each** |

---

## 7. Prior Art Considerations

### Known Prior Art to Disclose

The following prior art should be disclosed in the Information Disclosure Statement (IDS) when filing the non-provisional application:

| Reference | Relevance | How LUCID Differs |
|-----------|-----------|-------------------|
| AlphaEvolve (DeepMind, 2025) | Generate-evaluate loop for code | No formal verification; no convergence guarantee; no neuroscience grounding |
| Propose, Solve, Verify (Wilf et al., 2025) | Formal verification in generate-verify loop | Math domain only; no iterative remediation; no specification gap |
| Darwin Godel Machine (Sakana AI, 2025) | Self-improving code generation | Benchmark-based evaluation, not formal verification; reward hacking risk |
| DeepSeek-R1 (2025) | Emergent self-verification in LLMs | Learned (not formal) verification; shared failure modes with generator |
| Constitutional AI (Anthropic, 2022) | Self-critique and revision | Semantic (not formal) verification; shared failure modes |
| Scaling LLM Test-Time Compute (Snell et al., 2024) | Verification-guided search at inference time | Process reward models (learned), not formal verification |
| VERSES AI AXIOM (2025) | Active inference for reinforcement learning | Different domain (games, not code); no formal verification of code |
| Xu et al. (2024) | Impossibility of hallucination elimination | Motivational prior art (establishes the problem); no solution |
| Karpowicz (2025) | Hallucination-creativity identity | Motivational prior art; no solution |
| Huang et al. (2024) | Self-correction limitations | Shows self-refinement doesn't work; motivates external verification |

### Key Differentiators from All Prior Art

1. **Formal (execution-based) verification in the iterative loop.** No prior system uses formal verification (test execution with zero noise) as the iterative feedback signal in a code generation loop.

2. **Monotonic convergence property.** No prior system demonstrates that accuracy increases monotonically with iteration count. LUCID proves this both theoretically and empirically.

3. **Explicit treatment of hallucination as a feature.** No prior system deliberately uses LLM hallucination as a generative resource to be verified rather than a defect to be suppressed.

4. **Specification gap as convergence metric.** The quantitative metric driving the loop (specification gap = 1 - pass_rate) is novel and enables precision-weighted prioritization.

5. **Model-agnostic meta-architecture.** LUCID is not a specific model but a verification layer composable with any generator.

---

## 8. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Claims too broad (rejected by examiner) | Medium | Dependent claims provide fallback positions; specification includes detailed implementation |
| Prior art found during examination | Medium | Strongest prior art already known and differentiated; formal verification + monotonic convergence is novel |
| Competitor files first | Low | File ASAP to establish priority date; provisional is fast and cheap |
| Patent attorney disagrees with claim scope | Low | This draft provides a strong starting point; attorney will refine |
| 12-month deadline missed | Low | Calendar the deadline immediately; set reminders at 6, 9, and 11 months |
| Changes to patent law | Very Low | Provisional system is well-established; unlikely to change in 12 months |

---

## 9. Immediate Action Items

1. **Verify micro-entity eligibility** with Ty Wells (income and prior patent history)
2. **Decide: self-file or engage patent attorney**
   - Self-file: Cheapest, fastest, but weaker protection
   - Attorney: More expensive, better claims, stronger protection
3. **Convert specification to PDF** (from markdown)
4. **Create formal patent drawings** from mermaid flowcharts
5. **Create USPTO Patent Center account** if not already done
6. **File the provisional application**
7. **Calendar the 12-month deadline** for non-provisional filing
8. **After filing: publish benchmark report and arXiv paper** (protected by filing date)

---

## 10. Patent Attorney Recommendations

If engaging a patent attorney, look for one with experience in:

- **Software patents / computer-implemented methods** (35 U.S.C. 101 eligibility under Alice)
- **AI/ML patents** (growing specialty area)
- **Provisional-to-non-provisional conversion**

The Alice/101 risk (patent eligibility for software methods) is the main legal concern. The specification addresses this by emphasizing:
- The *technical improvement* (monotonic convergence, zero-noise verification)
- The *specific technical implementation* (sandboxed execution, test generation, structured remediation)
- The *concrete, measurable results* (100% on HumanEval, +65.5% on SWE-bench)
- The *unconventional approach* (treating hallucination as a feature, not a defect)

A patent attorney experienced in Alice analysis can further strengthen the claims against 101 rejections.

---

## Appendix A: Key Statistics for Patent Application

These numbers should be referenced in the specification:

| Metric | Value | Source |
|--------|-------|--------|
| HumanEval LUCID k=3 accuracy | 100% (164/164) | Benchmark experiments |
| HumanEval Self-Refine k=5 accuracy | 87.8% (144/164) | Benchmark experiments |
| HumanEval LLM-Judge k=5 accuracy | 97.0% (159/164) | Benchmark experiments |
| LLM-Judge regression (k=3 to k=5) | -2.4 pp (99.4% to 97.0%) | Benchmark experiments |
| SWE-bench baseline accuracy | 18.3% (55/300) | Benchmark experiments |
| SWE-bench LUCID best accuracy | 30.3% (91/300) | Benchmark experiments |
| SWE-bench relative improvement | +65.5% | Computed |
| Improvement-to-regression ratio (SWE-bench k=1) | 7.7:1 (23:3) | Benchmark experiments |
| Random-verify divergence | 97.6% to 95.1% (k=1 to k=3) | Ablation study |
| Total benchmark cost | ~$472 | Cost tracking |
| Cost per verification call | $0.005-0.008 | Cost tracking |
| Production codebase convergence | 57.3% to 90.8% (iterations 3-6) | Case study |
| Production codebase size | 30,000 lines TypeScript, 200+ files, 91 claims | Case study |

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **LUCID** | Leveraging Unverified Claims Into Deliverables. The name of the system and method described in this application. |
| **Specification gap** | A quantitative metric equal to 1 minus the fraction of applicable claims that pass formal verification. |
| **Formal verification** | Execution-based verification that produces exact (zero-noise) verdicts within its decidable domain, as distinguished from learned verification. |
| **Learned verification** | Verification performed by a machine learning model (LLM-as-judge, reward model, discriminator), which produces noisy verdicts subject to approximation error. |
| **Monotonic convergence** | The property that accuracy never decreases with additional iterations. |
| **Claim** | A decidable predicate about an expected behavior of source code. |
| **Remediation** | The process of generating targeted code modifications to address specific verification failures. |
| **Regeneration** | The process of producing updated source code incorporating remediation, with full context from prior iterations. |
| **Hallucination** | The generation by an LLM of plausible but potentially incorrect content. Treated as a generative resource in this invention. |
| **Meta-architecture** | A system that is composable with any generative model, functioning as an additional layer rather than a replacement. |
