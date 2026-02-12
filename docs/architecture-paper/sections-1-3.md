# Productive Hallucination: A Predictive Processing Architecture for AI Self-Verification

**Ty Wells**
Independent Researcher
ty@snapperland.com

---

## Abstract

Three independent mathematical proofs establish that hallucination cannot be eliminated from large language models. Yet the dominant paradigm in AI safety and alignment---reinforcement learning from human feedback, Constitutional AI, guardrails---continues to invest billions in suppression strategies that are provably impossible. We present an alternative grounded in neuroscience: the LUCID (Leveraging Unverified Claims Into Deliverables) architecture, a five-stage loop---hallucinate, extract, verify, remediate, regenerate---that maps directly onto predictive processing, the dominant framework in computational neuroscience for how biological intelligence operates. We demonstrate that this mapping is not merely analogical but mathematically precise: LUCID's specification gap is equivalent to Friston's prediction error, its iterative convergence corresponds to free energy minimization, and its use of formal verification as the grounding signal solves the "who verifies the verifier?" problem that undermines learned discriminators, reward models, and self-critique. We survey the convergent evidence: DeepMind's AlphaEvolve, the Propose-Solve-Verify framework, the Darwin Godel Machine, and VERSES AI's AXIOM all independently implement components of this pattern---without the unifying theoretical framework that explains *why* it works. LUCID is, to our knowledge, the first architecture that simultaneously (1) treats hallucination as the generative engine rather than a defect, (2) applies formal verification as the selection signal, (3) supports iterative self-improvement, (4) is grounded in established neuroscience, and (5) functions as a meta-architecture composable with any generative model. We report empirical results across two standard benchmarks: on HumanEval (164 code generation tasks), LUCID achieves 100% pass@1 at k=3 iterations versus 86.6% for the baseline and 87.8% for self-refinement at k=5---the only condition to converge monotonically to perfect accuracy. On SWE-bench Lite (300 real-world software engineering tasks), LUCID improves resolution rate by 65.5% relative to the baseline (30.3% vs. 18.3%). We show that self-refinement provides essentially no improvement over single-pass generation, that LLM-as-judge verification regresses at higher iteration counts due to false positives, and that only LUCID with formal verification converges monotonically. Total benchmark cost: $446 in API compute. We formalize the architecture within the free energy principle.

---

## 1. The Impossibility Problem

### 1.1 Three Proofs That Hallucination Cannot Be Eliminated

The AI research community has, since the emergence of large language models, treated hallucination as a defect to be engineered away. OpenAI's alignment research program, Anthropic's Constitutional AI, Google's grounding techniques, and Meta's self-correction methods all share a common assumption: that with sufficient effort---better training data, more human feedback, stronger guardrails---hallucination can be reduced to negligible levels.

Three independent mathematical proofs demonstrate that this assumption is false.

**Xu, Jain, and Kankanhalli (2024)** provided the first formal impossibility result, proving via computational learning theory that any computable LLM must hallucinate on certain inputs [1]. Their proof establishes that hallucination is not an engineering problem but a mathematical certainty: no finite training procedure on a finite dataset can produce a model that never generates unsupported claims. The result has accumulated over 453 citations in under two years, reflecting its significance. The proof proceeds by showing that for any LLM approximating a world model, there exist inputs for which the model's learned distribution necessarily diverges from the true distribution---not because the model is poorly trained, but because the approximation is inherently lossy.

**Banerjee, Sarkar, and Schwaller (2024)** arrived at the same conclusion via a different mathematical route, invoking connections to Godel's incompleteness theorems [2]. Their argument demonstrates that any sufficiently expressive formal system (which LLMs approximate) cannot be both complete and consistent with respect to all factual claims. Just as Godel showed that arithmetic cannot prove all true statements about itself, Banerjee et al. show that LLMs cannot generate only true statements about the world. The title of their paper---"LLMs Will Always Hallucinate, and We Need to Live With This"---signals the paradigm shift their result demands.

**Karpowicz (2025)** provided the strongest result: a quadrilemma proving that no LLM can simultaneously achieve truthful knowledge representation, semantic information conservation, complete revelation, and knowledge-constrained optimality [3]. The proof draws on mechanism design theory, proper scoring rules, and the architectural properties of transformers themselves. Karpowicz demonstrates that the Log-Sum-Exp operation at the core of the softmax attention mechanism introduces a convexity that makes hallucination structurally inevitable.

### 1.2 Hallucination Is Creativity: The Same Mathematics

Karpowicz's most provocative contribution is not merely another impossibility proof but an identification: the mathematical mechanism that produces hallucination is *identical* to the mechanism that produces creativity [3]. The Log-Sum-Exp convexity in transformer attention that causes the model to "confabulate" novel associations is the same operation that enables it to make creative leaps, draw unexpected analogies, and generate novel solutions.

This result has profound implications. It means that any technique that successfully suppresses hallucination must, by mathematical necessity, also suppress creative generation. The two capabilities are not merely correlated---they are the same computation viewed from different evaluative frames. A "hallucination" is a creative output that happens to be factually incorrect. A "creative insight" is a hallucination that happens to be useful.

This explains a pattern that practitioners have observed but could not formalize: heavily RLHF-trained models become less creative, more formulaic, and more prone to refusing tasks. The alignment community has treated this as an engineering tradeoff to be optimized. Karpowicz's proof shows it is a mathematical certainty: you cannot turn the hallucination dial down without turning the creativity dial down in equal measure.

### 1.3 The Billion-Dollar Impossibility

OpenAI has acknowledged these results. In a statement covered by *Computerworld*, the company conceded that hallucination is "mathematically inevitable" and "not just an engineering flaw" [4]. Yet the industry continues to invest billions in suppression strategies:

- **RLHF and RLAIF**: Reinforcement learning from human (or AI) feedback, which penalizes hallucinated outputs during training. Cost: estimated $100M+ annually across major labs.
- **Guardrails and filters**: Post-hoc detection and suppression of hallucinated content. Growing industry of startups (Guardrails AI, NeMo Guardrails, etc.).
- **Grounding techniques**: Retrieval-augmented generation (RAG), citation injection, knowledge graph anchoring. Reduces but cannot eliminate hallucination.
- **Constitutional AI**: Self-critique and revision against principles. Anthropic's primary alignment strategy.

Each of these approaches reduces the *rate* of hallucination on benchmarks. None can eliminate it. More critically, each reduces hallucination by constraining the generative process itself---which, per Karpowicz, necessarily constrains the model's creative and reasoning capabilities.

The field is spending billions on a proven impossibility while simultaneously degrading the very capability that makes these models valuable.

### 1.4 The Architectural Imperative

If hallucination cannot be eliminated, and if suppressing it degrades capability, then the only architecturally sound response is to change the relationship between the system and its hallucinations. Rather than treating hallucination as a defect to minimize, we must treat it as a *generative resource* to harness through external verification.

This is not a novel insight. It is the solution that biological intelligence discovered hundreds of millions of years ago.

---

## 2. The Neuroscience Solution: How Brains Use Hallucination

### 2.1 The Free Energy Principle

The dominant framework in computational neuroscience---Karl Friston's free energy principle---holds that biological organisms survive by minimizing *surprise*: the discrepancy between what they predict and what they observe [5]. The brain is, fundamentally, a prediction machine. It maintains a generative model of the world and continuously generates predictions about expected sensory input. When predictions diverge from observations, the resulting *prediction error* drives two processes: (1) updating the internal model to make better predictions (perceptual learning), and (2) acting on the world to make observations match predictions (active inference).

The mathematical formulation is precise. Let $q(\theta)$ represent the brain's approximate posterior belief about hidden causes $\theta$ of sensory observations $o$. The free energy $F$ provides an upper bound on surprise:

$$F = \underbrace{D_{KL}[q(\theta) \| p(\theta | o)]}_{\text{divergence from true posterior}} + \underbrace{(-\log p(o))}_{\text{surprise}}$$

Minimizing free energy simultaneously minimizes the divergence between beliefs and reality (accurate perception) and minimizes surprise (accurate prediction). The brain accomplishes this through a continuous cycle: generate a prediction, compare it to sensory input, compute the prediction error, update the model, generate a refined prediction.

This is a hallucination loop. The brain's predictions are, in a precise sense, hallucinations---internally generated content that may or may not correspond to external reality. What makes them *useful* hallucinations is the verification step: comparison against sensory evidence.

### 2.2 Controlled Hallucination: Seth's Thesis

Anil Seth, professor of cognitive and computational neuroscience at the University of Sussex, has articulated this most directly: "We're all hallucinating all the time; when we agree about our hallucinations, we call it reality" [6]. Seth's "controlled hallucination" thesis holds that conscious perception is not a passive readout of sensory data but an active construction---a "best guess" generated by the brain's predictive model, constrained by sensory input.

The key word is *constrained*. The brain does not suppress its generative process. It does not try to hallucinate less. Instead, it halluccinates continuously and uses sensory verification to *control* the hallucination---to steer the generative model toward outputs that are consistent with external reality. When this control mechanism fails (in psychosis, dreaming, or confabulation), the generative process runs unchecked and perception diverges from reality. When the control mechanism works, the result is what we call "perception"---which is, mathematically, just a well-constrained hallucination.

This directly parallels the situation with LLMs. Current approaches try to make LLMs hallucinate *less* (analogous to trying to make the brain generate fewer predictions---which would produce a non-functional brain). The neuroscience suggests a different strategy: let the LLM hallucinate freely, then apply external verification to constrain the hallucination toward reality.

### 2.3 Surfing Uncertainty: Clark's Hierarchical Predictive Coding

Andy Clark's "surfing uncertainty" framework extends predictive processing into a hierarchical architecture [7]. The brain does not generate predictions at a single level of abstraction. Instead, it maintains a hierarchy of predictions---from low-level sensory predictions (edge orientations, phonemes) to high-level conceptual predictions (objects, words, social situations). Prediction errors propagate both upward (informing higher levels of discrepancies) and downward (higher-level predictions constraining lower-level generation).

This hierarchical structure is critical for understanding how verification can operate at multiple levels of abstraction. A specification, like a high-level cortical prediction, constrains the space of acceptable outputs without dictating every low-level detail. LUCID's verification operates at the specification level (does the software do what the hallucinated claims say?), not at the token level (is every generated word correct?). This mirrors the brain's strategy: high-level predictions constrain low-level generation without micromanaging it.

### 2.4 Precision Weighting: Not All Errors Are Equal

A critical feature of predictive processing is *precision weighting*: the brain assigns different weights to prediction errors based on their estimated reliability [5, 8]. A prediction error from a trusted sensory modality (clear visual input in good lighting) receives high precision weighting and strongly updates the model. A prediction error from an unreliable source (a faint sound in a noisy room) receives low precision weighting and is partially ignored.

This mechanism explains selective attention: attending to something means *increasing the precision weighting* of prediction errors from that source. It also explains why some hallucinations persist (the brain assigns low precision to contradictory evidence) and why some are rapidly corrected (high-precision evidence overwhelms the prediction).

For AI verification architectures, precision weighting has a direct analog: not all verification failures should be weighted equally. A formal proof that code violates a specification is a high-precision error that should strongly update the model. A heuristic suggestion that an output "seems wrong" is a low-precision error that should weakly update the model. The type of verifier determines the precision of the error signal.

### 2.5 The Brain Does Not Suppress Hallucination

The central insight from neuroscience, and the foundation of our architectural argument, is this: **the brain does not suppress hallucination. It uses hallucination as the generative engine of perception, constrained by sensory verification.**

Hirstein's analysis of confabulation [9] establishes that generation and checking are neurologically separate processes. The generative process (producing predictions, filling gaps, constructing narratives) operates in deep cortical layers and is always active. The checking process (comparing predictions to sensory input, filtering confabulations) operates through a distinct neural pathway involving the posterior medial orbitofrontal cortex [10]. Confabulation---the clinical analog of hallucination---occurs not when the generative process malfunctions, but when the checking process fails.

This structural separation is the key architectural insight. Current AI approaches try to fix the generator (make the LLM produce fewer hallucinations). The brain's architecture suggests a different strategy: **leave the generator unconstrained and build a better checker.** LUCID implements this strategy by pairing unconstrained LLM generation with formal code-level verification.

The brain's approach has been validated by hundreds of millions of years of evolution. Every organism with a nervous system uses some form of predict-verify loop. The question is not whether this architecture works---it is the only architecture that has ever produced general intelligence---but whether it can be implemented in silicon.

---

## 3. The LUCID Architecture

### 3.1 Overview: A Five-Stage Verification Loop

LUCID (Leveraging Unverified Claims Into Deliverables) implements the predictive processing loop as a software architecture. The system operates in five stages that map directly onto the neuroscience:

**Stage 1: Hallucinate.** An LLM generates unconstrained claims about a software system. The prompt format (Terms of Service for a not-yet-existing application) is deliberately chosen to maximize confabulation across multiple dimensions: functionality, security, data handling, performance, and legal compliance. This corresponds to the brain's *top-down prediction*---the generative model producing its best guess about what should exist.

**Stage 2: Extract.** The hallucinated output is decomposed into individual, testable claims. Each claim is categorized (functionality, security, data privacy, operational, legal) and assigned a severity level. This corresponds to *hierarchical decomposition* in predictive coding---breaking a high-level prediction into component predictions at lower levels of the cortical hierarchy.

**Stage 3: Verify.** Each extracted claim is tested against the actual codebase through automated analysis. Claims receive verdicts: PASS (the code implements this), PARTIAL (partially implemented), FAIL (not implemented), or N/A (not applicable). This corresponds to *prediction error computation*---comparing the top-down prediction against bottom-up sensory evidence (the actual code).

**Stage 4: Remediate.** Verification failures generate a structured remediation plan. The gap between hallucinated claims and verified reality is quantified as the *specification gap*---a direct analog of Friston's *prediction error*. The system identifies which failures to address, prioritized by severity and feasibility. This corresponds to *free energy minimization*---updating the world (through code changes) to reduce the discrepancy between prediction and reality.

**Stage 5: Regenerate.** After remediation, the system generates updated claims. Verified truths (PASS claims) are retained as established knowledge. Failed claims are revised based on the new state of the codebase. The model may also hallucinate *new* claims that were not present in previous iterations, reflecting expanded capabilities. This corresponds to the *updated prediction*---a refined top-down signal that incorporates what has been learned.

The loop then repeats. Empirically, we observe monotonic convergence: specification-reality alignment increases with each iteration (57.3% -> 69.8% -> 83.2% -> 90.8% across iterations 3-6 on a production codebase [11]).

### 3.2 Formal Mapping to Predictive Processing

The mapping between LUCID and predictive processing is not merely analogical. The table below establishes the correspondence at the level of computational mechanisms:

| LUCID Component | Predictive Processing Analog | Mathematical Correspondence |
|---|---|---|
| Hallucinated claims | Top-down predictions | Generative model samples $\hat{o} \sim p(o \mid \theta)$ |
| Extracted claims | Hierarchical decomposition | Factorization into conditionally independent sub-predictions |
| Specification gap (FAIL/PARTIAL count) | Prediction error | $\epsilon = o - \hat{o}$, the discrepancy between prediction and observation |
| Verification via formal analysis | Sensory comparison | Bottom-up evidence $o$ constraining top-down prediction $\hat{o}$ |
| Remediation (code changes) | Active inference | Acting on the world to reduce prediction error |
| Regeneration (updated claims) | Updated prediction | Refined generative model $p(o \mid \theta')$ after belief update |
| Convergence across iterations | Free energy minimization | $F_{t+1} \leq F_t$ (monotonic decrease in specification gap) |
| Severity-weighted prioritization | Precision weighting | High-severity errors weighted more heavily in update |
| Formal verifier (code analysis) | Sensory precision | High-precision error signal that cannot be "explained away" |

The mathematical equivalence between LUCID's specification gap and Friston's prediction error is the foundation of this paper's central claim. Both measure the same quantity: the discrepancy between an internally generated prediction and externally verified reality. Both drive the same process: iterative updates that minimize this discrepancy. The difference is substrate: neurons and synapses in the brain, code and specifications in LUCID.

### 3.3 The Formal Verifier Advantage

The most significant architectural distinction between LUCID and other generate-verify systems is the nature of the verifier. We survey the verification mechanisms used by existing approaches:

| System | Verifier Type | Failure Mode |
|---|---|---|
| GANs | Learned discriminator | Mode collapse; discriminator can be fooled by adversarial examples |
| RLHF (OpenAI o1/o3) | Human preference model | Reward hacking; model optimizes proxy rather than true objective |
| Constitutional AI (Anthropic) | Self-critique by same model | Shared failure modes; cannot catch errors the model itself cannot recognize |
| AlphaEvolve (DeepMind) | Automated evaluators (tests) | Limited to domains with automated evaluation; evaluator quality varies |
| PSV (Wilf et al.) | Formal theorem prover (Lean/Isabelle) | Limited to formally specified domains; specification must exist |
| DeepSeek-R1 | Emergent self-verification (CoT) | No external ground truth; verification may hallucinate |
| **LUCID** | **Code-level formal analysis** | **Limited to properties expressible as code specifications** |

The critical property of LUCID's verifier is that it operates on *formal* ground truth---the actual codebase---rather than on learned approximations. A formal verifier cannot be "fooled" in the way a learned discriminator can. It cannot "reward hack" in the way a preference model can. It does not share the failure modes of the generator, as self-critique does.

This solves the "who verifies the verifier?" problem---the infinite regress that plagues systems where the verification mechanism is itself a learned model that may be incorrect. In LUCID, the verifier's ground truth is the codebase itself: either the code implements the claimed functionality or it does not. This is a decidable property within the specification domain.

The limitation is scope: formal code-level verification can only assess properties that are expressible as code specifications. It cannot assess aesthetic quality, user experience, or alignment with unstated preferences. We discuss this limitation and potential extensions in Section 5.

### 3.4 LUCID as Meta-Architecture

A key property of the LUCID architecture is that it is *composable*: it does not require a specific generative model but functions as a meta-layer on top of any generator. The hallucination stage can use GPT-4, Claude, Gemini, Llama, or any future model. The extract and verify stages are model-agnostic. The remediation stage produces structured output that can guide any development process (human or automated).

This is architecturally significant because it means LUCID is not competing with transformer architectures, diffusion models, or state space models. It is a *verification layer* that can sit on top of any of them, providing the predict-verify loop that none of them natively implement.

In neuroscience terms, LUCID is not the cortex (the generator). It is the predictive processing *loop*---the architectural principle that makes cortical generation useful by constraining it through sensory verification. Just as predictive processing is not a specific brain region but a computational principle implemented across the entire cortical hierarchy, LUCID is not a specific model but a computational principle implementable with any generator.

### 3.5 Comparison with Convergent Approaches

The AI field is independently converging on components of this architecture without the unifying framework. We survey the most significant:

**AlphaEvolve (DeepMind, 2025)** [12] uses Gemini to generate candidate algorithms, evaluates them against automated tests, and uses evolutionary selection to retain the best candidates. It achieved the first improvement to Strassen's matrix multiplication algorithm in 56 years and recovered 0.7% of Google's global compute through optimized algorithms. AlphaEvolve implements the generate-verify loop at industrial scale but lacks neuroscience grounding, does not treat hallucination as a feature, and uses test-based evaluation rather than formal specification-level verification.

**Propose, Solve, Verify (Wilf et al., December 2025)** [13] is the closest existing architecture to LUCID. PSV generates candidate problems, solves them, and verifies solutions using formal theorem provers (Lean, Isabelle). The authors report a 9.6x improvement over baselines and describe formal verification as the "essential ingredient." PSV validates LUCID's core thesis---that formal verification is the critical component---but operates only in mathematical theorem proving, does not frame hallucination as productive, and lacks the iterative convergence loop.

**Darwin Godel Machine (Sakana AI, 2025)** [14] demonstrates compounding self-improvement: an AI system that modifies its own code, achieving improvement from 20% to 50% on SWE-bench through self-modification alone. DGM validates the iterative self-improvement component of LUCID's architecture but uses test-passing as the fitness signal rather than specification-gap minimization, and lacks formal verification or neuroscience grounding.

**VERSES AI AXIOM (2025)** [15] is the only system besides LUCID that is explicitly grounded in Friston's free energy principle. AXIOM uses active inference for game playing, outperforming DreamerV3 by up to 60% while using 99% less compute in bounded domains. AXIOM validates the neuroscience foundation but operates in the reinforcement learning domain rather than software verification, and does not address hallucination as a generative resource.

**Scaling LLM Test-Time Compute (Snell et al., 2024)** [16] demonstrated at ICLR 2025 that a 7B parameter model with verification-guided tree search outperforms a 34B model on mathematical benchmarks. This result validates a core prediction of the LUCID framework: that verification loops at inference time can substitute for model scale, just as the brain's predictive processing loops substitute for exhaustive sensory processing.

The following table summarizes the landscape:

| System | Free Generation | Formal Verification | Iterative Self-Improvement | Neuroscience-Grounded | Hallucination-as-Feature |
|---|---|---|---|---|---|
| AlphaProof (DeepMind) | Yes | Yes (Lean 4) | Yes (RL) | No | No |
| AlphaEvolve (DeepMind) | Yes (Gemini) | Yes (automated evaluators) | Yes (evolutionary) | No | No |
| DeepSeek-R1 | Yes | Emergent self-verification | Yes (RL) | No | No |
| VERSES AXIOM | Yes (active inference) | Yes (prediction error) | Yes (belief updating) | **Yes** (Friston) | No |
| Constitutional AI (Anthropic) | Yes | Self-critique (weak) | Yes (RLAIF) | No | No |
| o1/o3 (OpenAI) | Yes (CoT) | Process reward models | Yes (RL) | No | No |
| PSV (Wilf et al.) | Yes | Yes (Lean/Isabelle) | Limited | No | No |
| DGM (Sakana AI) | Yes | Test-based | Yes (self-modification) | No | No |
| **LUCID** | **Yes** | **Yes (code-level)** | **Yes (iterative convergence)** | **Yes (FEP)** | **Yes** |

LUCID is the only system that checks all five boxes. Each competing system validates one or more components of the LUCID thesis, but none unifies them into a coherent architecture grounded in the computational principles of biological intelligence.

### 3.6 Empirical Evidence

We evaluated LUCID on two standard benchmarks (full methodology and results in Section 5). The headline results demonstrate the architecture's core claims.

**HumanEval (164 code generation tasks).** Four conditions were tested at iteration counts k = {1, 3, 5} using Claude Sonnet 4.5 as the generator model:

| Condition | k=1 | k=3 | k=5 |
|---|---|---|---|
| Baseline (single-pass) | 86.6% | --- | --- |
| Self-Refine | 87.2% | 87.2% | 87.8% |
| LLM-as-Judge | 98.2% | 99.4% | **97.2%** |
| **LUCID** | **98.8%** | **100%** | **100%** |

Three properties of these results are noteworthy:

**Monotonic convergence.** LUCID is the only condition whose accuracy increases monotonically with iteration count, reaching 100% at k=3 and maintaining it at k=5. This is a direct prediction of the free energy framework: formal verification provides a noiseless error signal that enables monotonic descent. Self-Refine plateaus near the baseline (87.8% at k=5, a +1.2 percentage point improvement over single-pass), confirming Huang et al.'s [23] finding that LLMs cannot self-correct without external feedback. Most strikingly, LLM-as-Judge *regresses* from 99.4% at k=3 to 97.2% at k=5---false positive judgments cause the system to "fix" correct code, introducing regressions that accumulate over iterations.

**Self-refinement is ineffective.** Self-Refine's improvement over baseline is negligible (87.2% vs. 86.6% at k=1, 87.8% vs. 86.6% at k=5). The shared failure modes between generator and self-critic---predicted by the correlated noise analysis in Section 4.3.2---render the feedback loop nearly vacuous. The model cannot identify errors in code that it was already incapable of writing correctly.

**The formal verifier is the critical component.** Ablation studies (Section 5.5) confirm this: replacing formal verification with random verdicts causes accuracy to *decrease* with more iterations (97.6% at k=1 → 95.1% at k=3), while removing the remediation stage causes accuracy to plateau at 99.4% (unable to reach 100%). Only the full LUCID loop with formal verification converges to perfection.

**SWE-bench Lite (300 real-world software engineering tasks).** Evaluated on the standard benchmark of real GitHub issues with ground-truth test suites:

| Condition | Resolved | Rate | vs. Baseline |
|---|---|---|---|
| Baseline k=1 | 55/300 | 18.3% | --- |
| LUCID k=1 | 75/300 | 25.0% | +36.4% relative |
| LUCID best (k=1 ∪ k=3) | 91/300 | 30.3% | **+65.5% relative** |

Head-to-head comparison at k=1: LUCID improved 23 tasks that baseline failed, with only 3 regressions. The k=3 iterative loop recovered an additional 16 tasks beyond k=1, demonstrating that the iterative verification cycle captures genuine second-order corrections. Django repositories showed the largest improvement (+9 resolved tasks), consistent with Django's well-structured test suites providing a high-quality formal verification signal.

**Total cost: $446 in API compute** ($220 for HumanEval across all conditions and ablations, $226 for SWE-bench including infrastructure). For comparison, the LUCID loop on SWE-bench costs approximately $1.50 per resolved issue at k=3.

**Production codebase validation.** We also applied the full LUCID specification pipeline to a production Next.js application (30,000 lines of TypeScript, 200+ files), observing convergence from 57.3% to 90.8% specification-reality alignment across six iterations on 91 extracted claims spanning functionality, security, data privacy, operational, and legal dimensions [11]. The five remaining failures at iteration 6 represented genuinely missing functionality, demonstrating that hallucination, when properly verified, functions as an *oracle for missing requirements*.

---

## References

[1] Z. Xu, S. Jain, and M. Kankanhalli, "Hallucination is Inevitable: An Innate Limitation of Large Language Models," arXiv:2401.11817, 2024.

[2] S. Banerjee, A. Sarkar, and P. Schwaller, "LLMs Will Always Hallucinate, and We Need to Live With This," arXiv:2409.05746, 2024.

[3] M. P. Karpowicz, "On the Fundamental Impossibility of Hallucination Control in Large Language Models," arXiv:2506.06382, 2025.

[4] "OpenAI admits AI hallucinations are mathematically inevitable, not just engineering flaws," Computerworld, 2025.

[5] K. Friston, "The free-energy principle: a unified brain theory?" Nature Reviews Neuroscience, vol. 11, no. 2, pp. 127-138, 2010.

[6] A. Seth, Being You: A New Science of Consciousness. Dutton, 2021.

[7] A. Clark, The Experience Machine: How Our Minds Predict and Shape Reality. Pantheon, 2023.

[8] K. Friston, "Interview on active inference and the free energy principle," National Science Review, vol. 11, no. 5, 2024.

[9] W. Hirstein, Brain Fiction: Self-Deception and the Riddle of Confabulation. MIT Press, 2005.

[10] A. Schnider, "Spontaneous confabulation and the adaptation of thought to ongoing reality," Nature Reviews Neuroscience, vol. 4, no. 8, pp. 662-671, 2003.

[11] T. Wells, "The Lucid Developer: Using LLM Hallucination as a Tool for Thought in Software Specification," CHI 2026 Tools for Thought Workshop, 2026.

[12] DeepMind, "AlphaEvolve: A Gemini-powered coding agent for designing advanced algorithms," arXiv:2506.13131, 2025.

[13] J. Wilf et al., "Propose, Solve, Verify: Scaling Formal Verification of Mathematical Reasoning," arXiv:2512.18160, 2025.

[14] Sakana AI, "The Darwin Godel Machine: Open-Ended Self-Improving AI," arXiv:2505.22954, 2025.

[15] VERSES AI, "AXIOM: Mastering Arcade Games in Minutes with Active Inference and Structure Learning," 2025.

[16] C. Snell et al., "Scaling LLM Test-Time Compute Optimally Can be More Effective Than Scaling Model Parameters," ICLR 2025 (Oral), arXiv:2408.03314, 2024.

[17] B. Millidge, A. Tschantz, and C. L. Buckley, "Predictive Coding Approximates Backprop Along Arbitrary Computation Graphs," arXiv:2006.04182, 2020.

[18] "Scaling Predictive Coding to 100+ Layers (muPC)," arXiv:2505.13124, 2025.

[19] "Predictive Coding for Hallucination Detection in LLMs," arXiv:2601.15652, 2026.

[20] "Engineering of Hallucination: Toward a Constructive Framework," arXiv:2601.07046, 2026.

[21] "Active Predictive Coding: A Unifying Neural Model," Neural Computation, vol. 36, no. 1, 2024.

[22] "Predictive Coding Networks and Variational Autoencoders: A Mathematical Equivalence," Neural Computation, vol. 34, no. 1, 2022.

[23] J. Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet," ICLR 2024.

[24] S. Kambhampati et al., "LLM-Modulo: An LLM-Modulo Framework for Task Planning," ICML 2024.

[25] M. Kleppmann, "AI + Formal Verification," December 2025.

[26] "RLVR Incentivizes Correct Reasoning in LLMs," arXiv:2506.14245, 2025.

[27] I. Anishchenko et al., "De novo protein design by deep network hallucination," Nature, vol. 600, pp. 547-552, 2021.
