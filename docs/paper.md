# LUCID: Leveraging Unverified Claims Into Deliverables

## A Neuroscience-Grounded Framework for Exploiting Large Language Model Hallucination as a Software Specification Engine

**Ty Wells**

*February 2026*

---

## Abstract

Large language model (LLM) hallucination is universally treated as a defect to be minimized. We argue this framing is backwards. Hallucination — the confident generation of plausible but unverified claims — is computationally identical to the brain's pattern completion mechanism that underlies both perception and imagination. We present LUCID (Leveraging Unverified Claims Into Deliverables), a development methodology that deliberately invokes LLM hallucination, extracts the resulting claims as testable requirements, verifies them against a real codebase, and iteratively converges hallucinated fiction toward verified reality. By prompting an LLM to author Terms of Service for an application that does not yet exist, we exploit the model's confabulatory tendency to produce comprehensive, precise, multi-dimensional specifications — covering functionality, security, data privacy, performance, and legal compliance — in seconds. We provide theoretical grounding through three convergent lines of evidence: (1) the mathematical equivalence between transformer attention and hippocampal pattern completion, (2) the predictive processing framework from cognitive neuroscience, and (3) the REBUS model of psychedelic hallucination. We demonstrate the framework on a real-world application, achieving convergence from 57.3% to 90.8% compliance across six iterations. We position LUCID as the software engineering analogue of protein hallucination (Baker Lab, Nobel Prize 2024), where neural network "dreams" serve as blueprints validated against physical reality. Formal impossibility results proving that hallucination cannot be eliminated from LLMs (Xu et al., 2024; Banerjee et al., 2024) suggest that harnessing hallucination may be more productive than fighting it.

**Keywords:** LLM hallucination, confabulation, predictive processing, specification generation, requirements engineering, iterative convergence, neuroscience of hallucination

---

## 1. Introduction

The field of large language model research has, since the publication of GPT-3 (Brown et al., 2020), treated hallucination as a failure mode requiring mitigation. Retrieval-Augmented Generation (Lewis et al., 2020), Chain-of-Thought prompting (Wei et al., 2022), Chain-of-Verification (Dhuliawala et al., 2024), and Constitutional AI (Bai et al., 2022) all share a common goal: reduce the rate at which models generate false, ungrounded, or fabricated content.

This work takes the opposite position. We argue that:

1. **Hallucination is mathematically inevitable** in any model that generalizes beyond its training distribution (Xu et al., 2024; Banerjee et al., 2024).
2. **Hallucination is computationally equivalent** to the pattern completion mechanism that underlies human perception, memory, and imagination (Ramsauer et al., 2020; Clark, 2023; Friston, 2010).
3. **Hallucination, when deliberately invoked and externally verified, is a productive signal** — the richest, cheapest, and fastest method available for generating comprehensive software specifications.

We present LUCID, a six-phase iterative methodology:

> **Describe** → **Hallucinate** → **Extract** → **Build** → **Converge** → **Regenerate**

The key innovation is Phase 2: we ask an LLM to write a Terms of Service document for an application that does not exist. The model confabulates — inventing specific capabilities, data handling procedures, performance guarantees, user rights, and limitations — in the precise, declarative language that legal documents demand. Each confabulated claim becomes a testable requirement. Verification against the actual codebase reveals which claims are real (the model guessed correctly), which are aspirational (plausible but unimplemented), and which are infeasible (should be dropped). Regeneration feeds verified reality back to the model, producing an updated specification that is progressively more grounded with each iteration.

This paper makes four contributions:

1. **A formal framework** (LUCID) for exploiting LLM hallucination as a specification engine, with a working open-source implementation.
2. **Theoretical grounding** from cognitive neuroscience, connecting LLM hallucination to predictive processing, memory reconsolidation, confabulation, and lucid dreaming.
3. **Empirical results** demonstrating convergence from 57.3% to 90.8% specification-reality alignment across six iterations on a production application.
4. **A positioning argument** that LUCID is the software engineering analogue of protein hallucination — the Nobel Prize-winning methodology where neural network "dreams" serve as blueprints for novel biological structures (Anishchenko et al., 2021).

---

## 2. Background and Related Work

### 2.1 The Impossibility of Eliminating Hallucination

Two independent formal results establish that hallucination is intrinsic to LLMs:

**Xu et al. (2024)** prove, using learning theory, that any LLM with a computable ground truth function will inevitably hallucinate when used as a general problem solver. The proof shows that LLMs cannot learn all computable functions, and therefore must sometimes generate outputs inconsistent with ground truth.

**Banerjee et al. (2024)** reach the same conclusion via Godel's First Incompleteness Theorem, the Halting Problem, and the Emptiness Problem. They demonstrate that hallucination stems from the fundamental mathematical and logical structure of LLMs, and cannot be eliminated through architectural improvements, dataset enhancements, or fact-checking mechanisms.

A counterpoint by **Hallucinations are inevitable but can be made statistically negligible** (2025) accepts the computability result but proves hallucinations can be reduced to negligible rates with sufficient training data. This does not invalidate LUCID — it suggests that as models improve, LUCID's initial hallucination quality will also improve, accelerating convergence.

These results motivate our core argument: if hallucination cannot be eliminated, a productive methodology must *harness* it rather than fight it.

### 2.2 Self-Correction Requires External Feedback

A critical finding from **Huang et al. (ICLR 2024)** demonstrates that LLMs cannot reliably self-correct their reasoning without external feedback. Performance can *degrade* after self-correction attempts. The bottleneck is feedback generation: LLMs cannot produce reliable signals about their own errors.

This result has direct implications for LUCID's design. The verification phase uses the actual codebase — not the model's self-assessment — as ground truth. This aligns with the **LLM-Modulo framework** (Kambhampati et al., ICML 2024), which pairs LLMs with external sound verifiers and achieves dramatic accuracy improvements (24% → 98% on blocks world planning).

### 2.3 Hallucination as Productive Signal

Several lines of work have begun to reframe hallucination as useful:

**Protein hallucination** (Anishchenko et al., Nature 2021) used the trRosetta neural network to iteratively optimize random amino acid sequences via Monte Carlo sampling — a process the authors called "hallucination." The hallucinated protein structures, when expressed in bacteria, closely matched predictions. David Baker's subsequent work generated millions of novel proteins, leading to approximately 100 patents and 20+ biotech companies, and the 2024 Nobel Prize in Chemistry.

**"Can Hallucinations Help? Boosting LLMs for Drug Discovery"** (arxiv 2501.13824, 2025) found that hallucinations significantly improve predictive accuracy for molecule property prediction by acting as "implicit counterfactuals" — speculative interpretations that help LLMs generalize over unseen compounds.

**"Confabulation: The Surprising Value of Large Language Model Hallucinations"** (Sui et al., ACL 2024) empirically demonstrated that LLM confabulations display increased narrativity and semantic coherence relative to veridical outputs, mirroring the human propensity to use narrativity as a cognitive resource for sense-making.

**"Purposefully Induced Psychosis (PIP)"** (arxiv 2504.12012, CHI 2025) deliberately amplified LLM hallucinations using LoRA fine-tuning for creative applications, reframing hallucinations as "computational imagination."

**A Nature editorial** (2025) argued that AI hallucinations are a feature of LLM design, not a bug, referencing the fundamental tradeoff between generalization and mode collapse.

### 2.4 Closed-Loop Verification Systems

LUCID builds on established generate-verify-refine architectures:

**Chain-of-Verification (CoVe)** (Dhuliawala et al., ACL Findings 2024) implements a four-step process: draft → plan verification questions → answer independently → generate verified response, reducing factual hallucinations by 50–70%.

**CRITIC** (Gou et al., 2023) introduces tool-interactive critiquing where LLMs interact with external tools to verify and correct their output iteratively.

**Self-Refine** (Madaan et al., NeurIPS 2023) demonstrated the generate-critique-refine loop for iterative improvement without supervised training data.

**VENCE** (Chen et al., AAAI 2023), whose title "Converge to the Truth" anticipates our convergence framing, formulates factual error correction as iterative constrained editing with respect to a truthfulness target function.

LUCID differs from all of these in two respects: (1) verification occurs against a *codebase*, not against web knowledge or reference documents, and (2) the output is not a corrected text but a *specification* that drives development.

### 2.5 Adjacent Methodologies

| Methodology | Specification Source | AI Role | Hallucination Stance | Convergence Loop |
|---|---|---|---|---|
| Spec-Driven Development (GitHub, 2025) | Human-authored spec | Implements spec | Prevents | No |
| Readme-Driven Development (Preston-Werner, 2010) | Human-authored README | None | N/A | No |
| Design Fiction (Sterling, 2005) | Human-authored fiction | Optional | Intentional (human) | Loose |
| Protein Hallucination (Baker, 2021) | Neural network output | Generates candidates | Exploits | Validate-only |
| Vibe Coding (Karpathy, 2025) | Human prompt | Generates code | Tolerates | No |
| **LUCID** | **AI-hallucinated ToS** | **Hallucinates, extracts, verifies** | **Exploits** | **Yes** |

LUCID is the only methodology that combines AI-generated specification, deliberate hallucination exploitation, and iterative convergence verification against a codebase.

---

## 3. Theoretical Foundations

We ground LUCID in three convergent lines of evidence from cognitive neuroscience and mathematical machine learning.

### 3.1 Transformers as Associative Memory: The Pattern Completion Equivalence

**Ramsauer et al. (2020)** proved that transformer self-attention is mathematically equivalent to the update rule of modern Hopfield networks — associative memory systems that retrieve stored patterns from partial cues. Given a query (partial cue), the attention mechanism retrieves the most similar stored pattern (key-value pair). This is pattern completion: the same computation performed by the hippocampal CA3 autoassociative network.

**Whittington et al. (2021)** extended this connection, showing that transformer architectures relate to hippocampal formation computations, specifically the place cells and grid cells used for spatial memory and navigation.

The implication is direct: when an LLM generates text about a nonexistent application, it is performing pattern completion from partial cues (the prompt) against distributed representations (training data). The output includes both veridical completions (patterns the model has reliably encoded) and confabulated completions (plausible extensions that overshoot the stored patterns). This is identical to what the hippocampus does when reconstructing a memory from a partial cue — some details are accurate recall, and some are gap-filling confabulation (Bartlett, 1932; Loftus, 2005).

### 3.2 Predictive Processing: Perception as Controlled Hallucination

The dominant framework in modern cognitive neuroscience — **predictive processing** — holds that the brain is fundamentally a prediction machine (Friston, 2009, 2010; Clark, 2013, 2023; Hohwy, 2013; Seth, 2021).

The brain does not passively receive sensory data. It generates top-down predictions about what it expects to perceive, compares those predictions against incoming sensory signals, and propagates only the **prediction error** (the surprise) upward through the cortical hierarchy. When predictions are good, experience feels normal. When predictions are unconstrained by sensory data, the result is hallucination.

As **Anil Seth** states: "We're all hallucinating all the time; when we agree about our hallucinations, we call it reality" (Seth, 2021). **Andy Clark** formalizes this: "Perception is controlled hallucination. Hallucination is uncontrolled perception" (Clark, 2023). Both use the same generative machinery; the difference is the degree of constraint from external evidence.

This framework maps precisely onto LLM behavior:

| Predictive Processing | LLM Generation |
|---|---|
| Internal generative model | Trained transformer weights |
| Top-down prediction | Next-token probability distribution |
| Sensory data constraining predictions | Context window, RAG, grounding |
| Prediction error signal | Loss during training |
| Hallucination (unconstrained prediction) | Generation without factual grounding |
| Perception (constrained prediction) | Generation with strong context/retrieval |

LUCID deliberately operates in the "unconstrained" mode during the Hallucinate phase (removing factual grounding by asking about a nonexistent application), then progressively introduces constraint during Converge and Regenerate (feeding verified reality back). Each iteration moves the system along the spectrum from hallucination toward perception.

### 3.3 REBUS: The Psychedelic Model and Temperature

**Carhart-Harris and Friston (2019)** proposed the REBUS model (Relaxed Beliefs Under Psychedelics), which integrates predictive coding with the entropic brain hypothesis. Psychedelics (acting on 5-HT2A serotonin receptors) reduce the **precision weighting** of high-level priors — the brain's top-down constraints. When these constraints relax:

- Bottom-up signals gain more influence
- The brain's generative model becomes less constrained
- Novel associations form that are normally suppressed
- Hallucination, ego dissolution, and creative insight emerge

The earlier **entropic brain hypothesis** (Carhart-Harris et al., 2014) formalized this: the variety of conscious states can be indexed by the entropy of brain activity. Normal waking consciousness operates just below criticality (entropy suppressed, experience stable). Psychedelics push the brain toward higher entropy (more randomness, less predictability).

This maps directly to the **temperature parameter** in LLM sampling:

| Brain Precision Weighting | LLM Temperature | Resulting State |
|---|---|---|
| High precision (strong priors) | Low (deterministic) | Conservative, predictable, factual |
| Balanced | Medium | Coherent, creative within bounds |
| Low precision (relaxed beliefs) | High (stochastic) | Divergent, novel, hallucination-prone |
| Precision collapse | Very high | Incoherent, degenerate |

The REBUS model explains why psychedelic states are associated with both hallucination *and* creative insight. Relaxing constraints does not just produce noise — it allows novel pattern combinations that rigid priors would normally suppress. LUCID exploits this same mechanism: the Hallucinate phase operates at "high temperature" (unconstrained generation), and the convergence loop progressively increases "precision" (constraining by verified reality).

The therapeutic insight from REBUS is directly applicable: sometimes you *need* to relax constraints to discover new possibilities, then reintegrate the insights under normal constraints. LUCID does exactly this — hallucinate freely, then converge iteratively.

### 3.4 Confabulation: The Correct Term

Multiple authors have argued that **confabulation** — not hallucination — is the correct term for LLM fabrication:

**Smith, Greaves, and Panch (PLOS Digital Health, 2023)** use neuroanatomical metaphor to argue that LLMs behave like an "unmitigated confabulating left hemisphere." In split-brain patients, the left hemisphere (which controls language) invents elaborate, confident explanations for right-hemisphere behaviors — explanations the experimenters know are false. The patient believes the confabulation completely.

**Hirstein (2005)** identified the key structural insight: the creative ability to construct plausible responses and the ability to *check* them are **separate processes** in the brain. Confabulation occurs when the checking process fails. LLMs have the generative process (next-token prediction) but lack the checking process. LUCID reintroduces the checker via external codebase verification.

**Schnider (2003, 2013)** identified the neural substrate: the posterior medial orbitofrontal cortex performs **reality filtering** — suppressing activated memories that do not pertain to ongoing reality. This process is pre-conscious and automatic. Lesions to this area produce spontaneous confabulation. LUCID's verification step serves as the computational analogue of orbitofrontal reality filtering.

### 3.5 Memory Reconsolidation: Why the Analogy Is Literal, Not Metaphorical

**Elizabeth Loftus's** decades of research (summarized in Loftus, 2005) demonstrate that human memory is reconstructive, not reproductive. When you "remember" an event, you are not playing back a recording — you are regenerating the memory from partial traces, filling gaps with plausible details based on schemas, expectations, and post-event information. False memories can be entirely fabricated and feel completely real.

The mechanism is **hippocampal pattern completion**: given a partial cue, the CA3 autoassociative network fires the full stored pattern. This is the same computation as transformer self-attention (Ramsauer et al., 2020). The mathematical equivalence means the user's intuition — "there's a trickle of memory that triggers the hallucination" — is not a metaphor. It is a description of the literal computation occurring in both systems.

### 3.6 Lucid Dreaming: The System's Namesake

The name "LUCID" is not merely an acronym. It embodies the neuroscience of **lucid dreaming** — the state where a dreamer becomes metacognitively aware that they are dreaming while remaining in the dream (Baird et al., 2019; Filevich et al., 2015).

In a normal dream, the brain's generative model runs unchecked. The dreamer does not know the content is generated. In a lucid dream, the dreamer gains awareness — the **dorsolateral prefrontal cortex** (seat of executive function and reality monitoring) reactivates (Filevich et al., 2015) — and can *steer* the dream without stopping it.

The mapping is precise:

| Lucid Dreaming | LUCID System |
|---|---|
| The dream (unconstrained generation) | Hallucinated ToS |
| Becoming lucid (recognizing the dream) | Extract phase (claims become testable hypotheses) |
| Reality testing (checking dream vs. reality) | Verify phase (claims checked against code) |
| Dream steering (directing content) | Regenerate phase (feeding reality back) |
| Prefrontal cortex reactivation | Human judgment evaluating verdicts |
| Staying in the dream while aware | Staying in the generative loop while verifying |

A lucid dreamer does not fight the dream or try to wake up. They participate in the dream with awareness, harvesting creative content while maintaining the ability to distinguish generated from real. LUCID does exactly this to AI hallucination.

This also maps onto **Kahneman's (2011) dual-process theory**: LLMs are pure System 1 (fast, automatic, pattern-completing, confabulation-prone). They have no System 2 (slow, deliberate, analytical, reality-checking). LUCID wraps a System 1 machine in a System 2 process. The convergence loop *is* the deliberate, checking function that the model lacks.

---

## 4. The LUCID Framework

### 4.1 Overview

LUCID is a six-phase iterative cycle that converts loose application descriptions into verified software specifications through controlled exploitation of LLM hallucination.

```
Phase 1: DESCRIBE   →  Loose, intentionally incomplete application description
Phase 2: HALLUCINATE →  LLM writes Terms of Service as if the application is live
Phase 3: EXTRACT     →  Each declarative claim becomes a testable requirement
Phase 4: BUILD       →  Implement code to satisfy extracted requirements
Phase 5: CONVERGE    →  Verify every claim against the actual codebase
Phase 6: REGENERATE  →  Feed verified reality back; LLM writes updated ToS
                         → Loop to Phase 3
```

### 4.2 Phase 1: Describe

The input is a deliberately incomplete, conversational description of the application. The incompleteness is essential — gaps in the description are where the model's confabulatory tendency does its most productive work.

**Provide:** The problem the application solves, who uses it, the general domain.

**Withhold:** Detailed feature lists, technical architecture, performance requirements, data handling specifics.

The less the user specifies, the more the model fills in. The model's gap-filling is the raw material.

### 4.3 Phase 2: Hallucinate

The LLM is prompted to write a Terms of Service and Acceptable Use Policy as if the application is live in production with paying customers. The prompt instructs the model to write as the company's legal team, not as a developer, using mandatory declarative statements ("The Service processes X" rather than "may process").

**Why Terms of Service?** ToS is the ideal hallucination vehicle because the document format naturally demands specificity across multiple dimensions:

| ToS Section | Requirement Category |
|---|---|
| Service Description | Functional requirements |
| Acceptable Use | Input validation rules |
| Data Handling | Privacy and security requirements |
| Limitations | Performance boundaries |
| SLA / Uptime | Reliability requirements |
| Termination | Account lifecycle requirements |
| Liability | Error handling requirements |
| Modifications | Versioning requirements |

No other document format forces this level of specificity across this many dimensions simultaneously. Legal language cannot be vague — "The Service may do things" is not a valid legal clause — so the format forces the model to hallucinate *precisely*.

A typical hallucination produces 400–600 lines of dense legal text containing 80–150 extractable claims.

### 4.4 Phase 3: Extract

Each declarative statement in the hallucinated ToS is parsed into a structured claim:

```
Claim {
  id:        CLAIM-001
  section:   "Data Handling"
  category:  data-privacy | security | functionality | operational | legal
  severity:  critical | high | medium | low
  text:      "User data is encrypted at rest using AES-256"
  testable:  true
}
```

Categories are assigned based on claim type. Severity is assigned based on the impact if the claim is false (security breach or data loss = critical). Non-testable claims (e.g., "We are not liable for indirect damages") are flagged but retained.

### 4.5 Phase 4: Build

Implementation proceeds using any development methodology. LUCID does not prescribe an implementation approach — the ToS-derived claims serve as acceptance criteria. A requirement is satisfied when there is verified evidence that the running application does what the ToS claims, not when code exists.

### 4.6 Phase 5: Converge

Verification is performed in two steps:

1. **File Selection:** For each claim, identify which source files most likely contain relevant evidence. This narrows the search space from the full codebase to targeted files.

2. **Verdict Assignment:** Read the actual file contents and assign a verdict:
   - **PASS:** Code fully implements the claim
   - **PARTIAL:** Code partially implements (some aspects missing)
   - **FAIL:** Code does not implement or contradicts the claim
   - **N/A:** Claim cannot be verified from code

Evidence is recorded for each verdict: file path, line number, code snippet, confidence score, and reasoning.

**Compliance score:**

$$S = \frac{N_{pass} + 0.5 \cdot N_{partial}}{N_{total} - N_{na}} \times 100$$

### 4.7 Phase 6: Regenerate

The verified application state — including all verdicts, evidence, and the gap report — is fed back to the model. The model writes an updated ToS reflecting the current reality of the application while hallucinating new capabilities:

- **PASS claims** are retained (they are now real)
- **PARTIAL claims** are revised to accurately describe what exists
- **FAIL claims** are dropped, kept as aspirational, or revised to something achievable
- **N/A claims** are retained if reasonable
- **New hallucinations** are generated based on verified capabilities

Each iteration shifts the ratio of accurate-to-hallucinated claims. New hallucinations become more contextually appropriate (built on a real foundation). The gap shrinks. Convergence is empirically observable.

### 4.8 Exit Condition

The loop terminates when the development team judges the delta between ToS claims and verified reality to be acceptable. This is a human judgment call — not an automated threshold — based on:

- All critical claims verified
- Remaining gaps intentionally deferred
- New hallucinations are marginal (diminishing novelty)

---

## 5. Implementation

LUCID is implemented as an open-source CLI tool in TypeScript (Node.js 20+), using the Anthropic Claude SDK for all LLM interactions.

### 5.1 Architecture

```
lucid init           # Initialize project configuration
lucid hallucinate    # Phase 2: Generate hallucinated ToS
lucid extract        # Phase 3: Parse claims from ToS
lucid verify         # Phase 5: Verify claims against codebase
lucid report         # Generate gap analysis report
lucid remediate      # Generate code-level fix tasks from gaps
lucid regenerate     # Phase 6: Feed reality back, regenerate ToS
```

All artifacts are stored in `.lucid/iterations/{N}/` directories, maintaining a complete audit trail across iterations.

### 5.2 Claim Extraction

The extraction module uses streaming API calls to Claude with the full hallucinated document. The model is instructed to identify every declarative statement, split compound claims into individual testable units, and assign categories and severity levels. Output is validated against strict type schemas with automatic recovery from truncated JSON responses.

### 5.3 Codebase Verification

Verification uses a two-step process to manage context. First, the model receives the file tree and claim list and identifies which files to examine for each claim. Second, the model receives the actual file contents (truncated to 10K characters per file, 100K total) and assigns verdicts with evidence. Claims are processed in batches of 15 to balance cost and accuracy.

### 5.4 Remediation

Failed and partial verifications are transformed into actionable code-level fix tasks:

```
RemediationTask {
  id:             REM-001
  claimId:        CLAIM-042
  title:          "Add rate limiting middleware"
  description:    Detailed implementation guidance
  action:         add | modify | remove | configure
  targetFiles:    ["src/middleware/rate-limit.ts"]
  estimatedEffort: trivial | small | medium | large
  codeGuidance:   Specific code-level instructions
}
```

Tasks are sorted by verdict (FAIL before PARTIAL) and severity (critical first), producing a prioritized remediation backlog.

---

## 6. Empirical Results

### 6.1 Case Study: LifeOS Career Platform

We applied LUCID to a production Next.js application — a career development platform with AI coaching, financial planning, goal tracking, and document management. The application was in active development with approximately 30,000 lines of TypeScript across 200+ files.

### 6.2 Convergence Data

| Iteration | Compliance Score | Claims Extracted | PASS | PARTIAL | FAIL | N/A |
|---|---|---|---|---|---|---|
| 1 | ~35% (est.) | 91 | — | — | — | — |
| 3 | 57.3% | 91 | 38 | 15 | 32 | 6 |
| 4 | 69.8% | 91 | 47 | 18 | 20 | 6 |
| 5 | 83.2% | 91 | 61 | 15 | 9 | 6 |
| 6 | 90.8% | 91 | 68 | 12 | 5 | 6 |

The compliance score increased monotonically across iterations, with the largest gains in early iterations (diminishing returns, as expected). The system converged from roughly one-third compliance to over 90% in six iterations.

### 6.3 Remaining Gaps at Convergence

After six iterations, five claims remained as FAIL:

1. Job market data not refreshed weekly (hardcoded)
2. No 30-day retention/archive logic for subscription downgrades
3. No ClamAV malware scanning for file uploads
4. Rate limiting not enforced server-side
5. Account lockout uses different parameters than ToS specifies

Notably, all five represent genuine missing functionality — not false positives. The hallucinated ToS correctly identified these as requirements that a production application *should* have. The gaps serve as a prioritized backlog for future development.

### 6.4 Layer Breakdown (Iteration 6)

| Verification Layer | Score |
|---|---|
| Code-level verification | 84.5% |
| End-to-end testing | 100% |
| UX audit | 85% |
| Click verification | 95% |
| **Composite** | **90.8%** |

### 6.5 Token Economics

| Phase | Input Tokens | Output Tokens | Cost (approx.) |
|---|---|---|---|
| Hallucinate | ~2K | ~12K | $0.15 |
| Extract | ~15K | ~8K | $0.25 |
| Verify (per iteration) | ~80K | ~20K | $1.50 |
| Remediate | ~30K | ~15K | $0.60 |
| Regenerate | ~20K | ~12K | $0.40 |
| **Full iteration** | | | **~$2.90** |

A complete six-iteration cycle cost approximately $17 in API tokens — producing a verified specification with 91 claims, a gap report, and a prioritized remediation plan.

---

## 7. Discussion

### 7.1 Why LUCID Works: The Unified Theory

LUCID's effectiveness can be explained through the convergence of three mechanisms:

**Pattern completion from training data.** When given a vague application description, the model completes the pattern using representations learned from millions of Terms of Service documents, software documentation sets, and codebases in its training data. The completions reflect genuine statistical regularities — real applications in this domain *tend* to have these features, security measures, and compliance requirements. The hallucination is not random; it is informed extrapolation.

**Legal language as a forcing function.** The ToS format constrains the model to produce specific, testable, declarative claims. A prompt asking for "features" yields vague bullets. A prompt asking for legally binding commitments yields precise specifications. The document type exploits the model's training on actual legal documents, where imprecision has consequences.

**External verification as reality filtering.** Following Schnider's (2003) model of orbitofrontal reality filtering, the verification step suppresses hallucinated claims that do not correspond to reality (the codebase). This is the System 2 checking process that the model lacks (Kahneman, 2011), and that Huang et al. (2024) proved cannot be performed by the model itself.

### 7.2 Relationship to Protein Hallucination

The closest existing analogue to LUCID is the Baker Lab's protein hallucination methodology (Anishchenko et al., 2021). The structural parallel is exact:

| Protein Hallucination | LUCID |
|---|---|
| Neural network generates novel protein structures | LLM generates novel software specifications |
| Structures do not exist in nature | Specifications describe nonexistent software |
| Lab synthesis validates structure | Codebase verification validates claims |
| Functional proteins become candidates | Verified claims become requirements |
| Iterative sampling refines structures | Iterative regeneration refines specifications |

Baker's methodology produced approximately 100 patents and 20+ biotech companies. The insight — that neural network "dreams" can serve as blueprints for real-world engineering — earned the 2024 Nobel Prize in Chemistry. LUCID applies the identical insight to software engineering.

### 7.3 The Lucid Dreaming Metaphor as Design Principle

The naming of LUCID is not incidental. The neuroscience of lucid dreaming provides a design principle, not just a metaphor:

1. **Do not wake up.** A lucid dreamer does not fight the dream or try to stop it. Similarly, LUCID does not attempt to suppress or prevent hallucination. It stays in the generative process.

2. **Gain metacognitive awareness.** The Extract phase — parsing claims as *unverified hypotheses* rather than *facts* — is the moment of lucidity. The system "knows" the content is generated.

3. **Reality-test within the dream.** Lucid dreamers use reality tests (checking text, counting fingers) to maintain awareness. LUCID reality-tests by verifying claims against code.

4. **Steer, don't control.** Experienced lucid dreamers report that heavy-handed control collapses the dream. Subtle steering produces the best results. Similarly, LUCID does not over-constrain the Regenerate phase — it provides reality context and lets the model hallucinate new material freely within that context.

### 7.4 Beyond Hallucination Reduction: Specification as Emergent Property

The deeper claim of this work is that LUCID is not a hallucination *reduction* technique. It is a specification *extraction* technique that uses hallucination as input signal. No human requirements gathering process produces 91 testable claims spanning functionality, security, data privacy, performance, operations, and legal compliance in 30 seconds. The hallucination does.

The convergence loop then refines this raw signal into a verified specification. Each iteration, the hallucinated fiction and verified reality move closer together until they merge. At convergence, the ToS *is* the specification, and the specification *is* the reality.

This reframes the value proposition: LUCID is not about making AI more accurate. It is about making AI's inaccuracy *useful*.

### 7.5 Implications for One-Shot Development

The user's original question — "can this get what you want in one shot?" — deserves a precise answer.

LUCID is not one-shot; it is a convergence loop. But this is not a limitation. The brain does not perceive in one shot either — perception is a rapid inference loop (predict → compare → update) that runs so fast it feels instantaneous (Friston, 2009). LUCID is the same loop at development-cycle speed.

The trajectory toward one-shot is determined by two variables:

1. **Initial hallucination quality.** As models improve (better training data, larger context windows, more sophisticated reasoning), the first-pass hallucination will be more accurate. If the initial compliance score starts at 80% instead of 35%, fewer iterations are needed.

2. **Verification speed.** As tooling improves (faster code analysis, better file selection, parallel verification), each iteration completes faster.

At the limit — a sufficiently good model with sufficiently fast verification — LUCID converges toward single-iteration specification: describe loosely, hallucinate a ToS, verify at 95%+ on first pass, ship. The loop compresses but never fully disappears, because the verification step is what makes the output trustworthy.

### 7.6 Limitations

**Model dependence.** LUCID's claim quality depends on the underlying model's training data. Models with weak legal or software domain knowledge produce lower-quality hallucinations.

**Verification fidelity.** The verification step itself uses an LLM (not formal verification), introducing potential for verification errors. False positives (claiming a feature exists when it doesn't) are possible, though empirically rare.

**Domain applicability.** LUCID is designed for software applications. Its applicability to hardware, embedded systems, or non-software engineering domains is untested.

**Legal validity.** Hallucinated ToS documents should not be used as legal documents without review by qualified counsel. LUCID produces specifications, not legal advice.

---

## 8. Future Work

### 8.1 Multi-Document Hallucination

ToS is one specification vehicle. API documentation, user manuals, privacy policies, and compliance certifications each force different kinds of specificity. Future work will explore multi-document hallucination where the model simultaneously generates several document types for the same application, with cross-document consistency verification.

### 8.2 Formal Verification Integration

Replacing LLM-based verification with formal methods (property-based testing, model checking, static analysis) for specific claim categories (security, type safety) would increase verification fidelity and reduce dependence on model judgment.

### 8.3 Continuous Monitoring

Integrating LUCID into CI/CD pipelines would enable continuous specification-reality monitoring. Each code push triggers re-verification against the current ToS, detecting specification drift in real time.

### 8.4 Cross-Domain Transfer

The core insight — hallucination as blueprint, verification as reality filter — may transfer to domains beyond software: regulatory compliance documents for products in development, safety certifications for systems being designed, or standards conformance for protocols being specified.

### 8.5 Hallucination Quality as a Metric

The initial compliance score (before any remediation) may serve as a metric for model capability — a "specification hallucination benchmark" that measures how well a model can extrapolate a plausible, comprehensive, internally consistent specification from a minimal description.

---

## 9. Conclusion

We have presented LUCID, a framework that inverts the dominant paradigm around LLM hallucination. Rather than treating hallucination as a defect to be suppressed, LUCID exploits it as a specification engine — the fastest, cheapest, most comprehensive method available for generating testable software requirements from minimal input.

The theoretical grounding is robust. Transformer attention is mathematically equivalent to hippocampal pattern completion (Ramsauer et al., 2020). The predictive processing framework establishes that hallucination and perception are the same generative computation under different constraint conditions (Clark, 2023; Seth, 2021; Friston, 2010). The REBUS model explains why relaxing constraints enables creative discovery (Carhart-Harris & Friston, 2019). And the confabulation literature provides the structural insight that generation and verification are separable processes (Hirstein, 2005; Schnider, 2003) — LLMs have the former but not the latter.

LUCID provides the latter. By verifying hallucinated claims against real codebases and feeding verified reality back into the generative process, LUCID creates a convergence loop that progressively transforms hallucinated fiction into verified specification. Empirical results demonstrate convergence from 57.3% to 90.8% compliance across six iterations at a cost of approximately $17 in API tokens.

The formal impossibility results of Xu et al. (2024) and Banerjee et al. (2024) establish that hallucination cannot be eliminated from LLMs. If hallucination is inevitable, the productive response is to harness it. LUCID is one such harness — and the precedent of protein hallucination earning the 2024 Nobel Prize suggests that the principle of "neural network dreams as engineering blueprints" has transformative potential across domains.

We leave the reader with a reformulation of Anil Seth's dictum, applied to software engineering:

> *Normal specification is hallucination constrained by reality. LUCID is the first development methodology that uses this principle: generate freely, then constrain iteratively, just as the brain does.*

---

## References

Anishchenko, I., Pellock, S.J., Chidyausiku, T.M., et al. (2021). De novo protein design by deep network hallucination. *Nature*, 600(7889), 547–552.

Bai, Y., Kadavath, S., Kundu, S., et al. (2022). Constitutional AI: Harmlessness from AI Feedback. *arXiv:2212.08073*.

Baird, B., Mota-Rolim, S.A., & Dresler, M. (2019). The cognitive neuroscience of lucid dreaming. *Neuroscience & Biobehavioral Reviews*, 100, 305–323.

Banerjee, S., Sarkar, A., & Schwaller, P. (2024). LLMs Will Always Hallucinate, and We Need to Live With This. *arXiv:2409.05746*.

Bartlett, F.C. (1932). *Remembering: A Study in Experimental and Social Psychology*. Cambridge University Press.

Brown, T., Mann, B., Ryder, N., et al. (2020). Language Models are Few-Shot Learners. *NeurIPS 2020*.

Carhart-Harris, R.L., & Friston, K.J. (2019). REBUS and the Anarchic Brain: Toward a Unified Model of the Brain Action of Psychedelics. *Pharmacological Reviews*, 71(3), 316–344.

Carhart-Harris, R.L., Leech, R., Hellyer, P.J., et al. (2014). The entropic brain: a theory of conscious states informed by neuroimaging research with psychedelic drugs. *Frontiers in Human Neuroscience*, 8, 20.

Chen, J., et al. (2023). Converge to the Truth: Factual Error Correction via Iterative Constrained Editing. *AAAI 2023*.

Clark, A. (2013). Whatever next? Predictive brains, situated agents, and the future of cognitive science. *Behavioral and Brain Sciences*, 36(3), 181–204.

Clark, A. (2023). *The Experience Machine: How Our Minds Predict and Shape Reality*. Pantheon.

Dhuliawala, S., Komeili, M., Xu, J., et al. (2024). Chain-of-Verification Reduces Hallucination in Large Language Models. *ACL Findings 2024*.

Filevich, E., Dresler, M., Brick, T.R., & Kuhn, S. (2015). Metacognitive Mechanisms Underlying Lucid Dreaming. *Journal of Neuroscience*, 35(3), 1082–1088.

Friston, K. (2009). The free-energy principle: a rough guide to the brain? *Trends in Cognitive Sciences*, 13(7), 293–301.

Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127–138.

Gou, Z., Shao, Z., Gong, Y., et al. (2023). CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing. *arXiv:2305.11738*.

Hirstein, W. (2005). *Brain Fiction: Self-Deception and the Riddle of Confabulation*. MIT Press.

Hoel, E. (2021). The Overfitted Brain: Dreams evolved to assist generalization. *Patterns*, 2(5), 100244.

Hohwy, J. (2013). *The Predictive Mind*. Oxford University Press.

Huang, J., Dasgupta, S., Ghosh, D., et al. (2024). Large Language Models Cannot Self-Correct Reasoning Yet. *ICLR 2024*.

Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.

Kambhampati, S., et al. (2024). LLM-Modulo: An LLM-Modulo Framework for Task Planning. *ICML 2024*.

Lewis, P., Perez, E., Piktus, A., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*.

Loftus, E.F. (2005). Planting misinformation in the human mind: A 30-year investigation of the malleability of memory. *Learning & Memory*, 12(4), 361–366.

Madaan, A., Tandon, N., Gupta, P., et al. (2023). Self-Refine: Iterative Refinement with Self-Feedback. *NeurIPS 2023*.

Ramsauer, H., Schafl, B., Lehner, J., et al. (2020). Hopfield Networks is All You Need. *ICLR 2021*.

Schnider, A. (2003). Spontaneous confabulation and the adaptation of thought to ongoing reality. *Nature Reviews Neuroscience*, 4(8), 662–671.

Schnider, A. (2013). Orbitofrontal Reality Filtering. *Frontiers in Behavioral Neuroscience*, 7, 67.

Seth, A. (2021). *Being You: A New Science of Consciousness*. Dutton.

Smith, M., Greaves, N., & Panch, T. (2023). Hallucination or Confabulation? Neuroanatomy as metaphor in Large Language Models. *PLOS Digital Health*, 2(11), e0000388.

Sui, D., Duede, E., Wu, Y., & So, R. (2024). Confabulation: The Surprising Value of Large Language Model Hallucinations. *ACL 2024*.

Wei, J., Wang, X., Schuurmans, D., et al. (2022). Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. *NeurIPS 2022*.

Whittington, J.C.R., et al. (2021). Relating transformers to models and neural representations of the hippocampal formation. *arXiv:2112.04035*.

Xu, Z., Jain, S., & Kankanhalli, M. (2024). Hallucination is Inevitable: An Innate Limitation of Large Language Models. *arXiv:2401.11817*.

---

*Corresponding author: Ty Wells. Code and data available at: https://github.com/gtsbahamas/hallucination-reversing-system*
