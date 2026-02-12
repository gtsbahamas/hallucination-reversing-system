# LUCID: Hallucination as Computational Primitive — Sections 6-8

*Continuation of the architecture paper. Sections 1-5 cover Problem Statement, Neuroscience Foundations, Architecture, Mathematical Framework, and Experimental Evaluation.*

---

## 6. Comparison to Existing Approaches

The AI field is independently converging on the generate-verify pattern from multiple directions. No existing system, however, unifies all five properties that LUCID integrates: unconstrained generation, formal verification, iterative self-improvement, neuroscience grounding, and the explicit treatment of hallucination as a productive computational primitive. This section provides a detailed comparison.

### 6.1 AlphaEvolve (DeepMind, 2025)

AlphaEvolve [1] represents the most industrially validated generate-verify system to date. Using Gemini as a generator and automated evaluators as verifiers, it improved upon Strassen's matrix multiplication algorithm for the first time in 56 years and recovered an estimated 0.7% of Google's global compute through data center optimizations.

**What AlphaEvolve gets right.** The system demonstrates that unconstrained generation followed by rigorous evaluation produces results that neither component achieves alone. Its evolutionary selection mechanism allows the generator to explore freely while the evaluator enforces correctness. The self-referential improvement loop --- where AlphaEvolve improved its own pipeline components --- validates the compounding dynamics central to LUCID's thesis.

**What AlphaEvolve is missing.** AlphaEvolve has no theoretical framework explaining *why* the generate-verify loop works. It treats hallucination as a byproduct of stochastic generation, not as a productive signal. The evaluators are automated but domain-specific; there is no unified verification framework. Most critically, AlphaEvolve lacks a neuroscience grounding that would explain its convergent behavior with biological intelligence or suggest principled extensions to new domains.

**LUCID's relationship.** LUCID provides the theoretical framework that AlphaEvolve lacks. AlphaEvolve's success is *predicted* by the free energy minimization interpretation: unconstrained generation maximizes the entropy of the hypothesis space, while evaluation minimizes prediction error against ground truth. LUCID formalizes this as $\mathcal{F} = D_{KL}[q(\theta) \| p(\theta)] - \mathbb{E}_q[\ln p(y|\theta)]$, where AlphaEvolve's evolutionary selection is an instance of variational inference on program space.

### 6.2 Propose, Solve, Verify (Wilf et al., December 2025)

PSV [2] is architecturally the closest existing system to LUCID. It decomposes mathematical problem-solving into three stages --- proposing subproblems, solving them, and formally verifying solutions in Lean 4 --- achieving a 9.6x improvement over baselines on miniF2F. The authors describe formal verification as "the essential ingredient."

**What PSV gets right.** PSV validates LUCID's core claim that formal verification provides a qualitatively different training signal than learned reward models. The 9.6x improvement over baselines that use the same generator but lack formal verification is direct evidence that the verification modality, not the generation capability, is the binding constraint on performance. PSV also demonstrates hierarchical decomposition (proposing subproblems maps to LUCID's claim extraction stage).

**What PSV is missing.** PSV is restricted to mathematical theorem proving. It has no mechanism for generalizing its verification framework to code, natural language, or other domains. The system treats verification as an external check rather than as a training signal that shapes generation. There is no iterative refinement --- failed proofs are discarded rather than used to guide regeneration. The hallucination-as-feature perspective is absent; divergent generations are treated as waste.

**LUCID's relationship.** LUCID generalizes PSV's core insight. Where PSV uses Lean 4 proofs as a binary pass/fail signal, LUCID uses the *structure* of the specification gap --- which claims failed, how they failed, what the delta is between expected and actual behavior --- as a rich signal that drives targeted remediation. This is analogous to the difference between a loss function that returns a scalar and one that returns a gradient.

### 6.3 Darwin Godel Machine (Sakana AI, 2025)

The Darwin Godel Machine (DGM) [3] demonstrates compounding self-improvement through an evolutionary loop: an AI agent modifies its own codebase, evaluates modifications on benchmarks, and retains beneficial mutations. Starting from a 20% baseline on SWE-bench, DGM achieved 50% through self-modification alone.

**What DGM gets right.** DGM validates the self-improvement dynamics that LUCID predicts from the free energy framework. Each iteration reduces specification gap (measured as benchmark performance), and the improvements compound because each refined agent generates better mutations in subsequent rounds. The evolutionary framing naturally accommodates hallucination: most mutations are deleterious (hallucinations), but the selection mechanism retains productive ones.

**What DGM is missing.** DGM's evaluation is benchmark-driven, not formally verified. This creates a reward-hacking risk: the agent can overfit to benchmark structure without genuine capability improvement. There is no formal guarantee that retained mutations are correct --- only that they improve aggregate performance on a finite test set. The system also lacks the neuroscience grounding that would explain its convergent behavior with biological learning or guide principled architectural decisions.

**LUCID's relationship.** LUCID addresses DGM's reward-hacking vulnerability by replacing benchmark evaluation with formal verification. A formally verified improvement cannot be a reward hack --- it is provably correct within its specification domain. LUCID also provides the theoretical framework (free energy minimization) that explains why DGM's evolutionary loop works and predicts the conditions under which it will fail (specification incompleteness, degenerate fitness landscapes).

### 6.4 DeepSeek-R1 (DeepSeek, 2025)

DeepSeek-R1 [4] demonstrated that reinforcement learning on chain-of-thought reasoning, without supervised fine-tuning, produces emergent self-verification behavior. The model spontaneously learned to check its own reasoning steps, backtrack on errors, and allocate more computation to harder problems.

**What DeepSeek-R1 gets right.** The emergence of self-verification from pure RL is significant evidence for LUCID's thesis. It suggests that the predict-verify loop is not merely a useful engineering pattern but a *convergent* computational strategy --- one that arises spontaneously when systems are optimized for correctness. DeepSeek-R1's variable compute allocation (spending more time on harder problems) mirrors the precision-weighting mechanism in predictive processing, where the brain allocates more processing to surprising (high-prediction-error) inputs.

**What DeepSeek-R1 is missing.** The self-verification is *emergent and uncontrolled*. There is no formal guarantee that the model's self-checks are correct --- it uses the same model for generation and verification, inheriting shared failure modes. The system cannot verify claims against an external ground truth; it can only check internal consistency. This is analogous to a brain that can detect inconsistencies in its own predictions but has no sensory input to ground those predictions against reality.

**LUCID's relationship.** LUCID provides what DeepSeek-R1's emergent verification lacks: an external, formally grounded verifier that cannot share the generator's failure modes. In the predictive processing analogy, LUCID adds the sensory input that grounds top-down predictions. The combination of DeepSeek-R1-style emergent reasoning with LUCID-style external verification would create a system with both internal coherence checking and external ground truth --- the computational analog of a brain with both top-down predictions and bottom-up sensory correction.

### 6.5 Constitutional AI (Anthropic, 2022-2025)

Constitutional AI (CAI) [5] uses self-critique guided by constitutional principles to align model outputs. The model generates a response, critiques it against a set of rules, and revises the output. RLAIF (RL from AI Feedback) trains future generations on these self-critiques.

**What CAI gets right.** CAI implements the generate-critique-revise loop that is structurally similar to LUCID's generate-verify-remediate cycle. The constitutional principles serve as a weak form of specification. The iterative refinement process demonstrates that self-correction improves output quality.

**What CAI is missing.** The critical weakness is that the critic shares the generator's knowledge and failure modes. A model that does not know a fact is wrong will not critique that fact. Constitutional principles are expressed in natural language, making them ambiguous and subject to the same interpretation failures as the original generation. The verification is *semantic* (does this seem right?) rather than *formal* (is this provably correct?). This distinction is fundamental: semantic verification degrades with task complexity, while formal verification does not.

**LUCID's relationship.** LUCID replaces CAI's semantic self-critique with formal verification against executable specifications. Where CAI asks "does this seem aligned?", LUCID asks "does this provably satisfy the specification?" The formal verifier is a separate system from the generator, eliminating shared failure modes. This is the difference between a student grading their own essay and submitting it to a compiler that either accepts or rejects it with a precise error trace.

### 6.6 OpenAI o1/o3 (2024-2025)

The o1 and o3 models [6] use extended chain-of-thought reasoning with process reward models (PRMs) to verify intermediate reasoning steps. By allocating more inference-time compute to harder problems, they achieve state-of-the-art results on mathematical reasoning benchmarks.

**What o1/o3 gets right.** The inference-time scaling paradigm validates a key LUCID prediction: verification loops at inference time can substitute for parameter scaling at training time. Snell et al. [7] showed formally that a 7B model with optimal test-time compute allocation outperforms a 34B model on MATH, demonstrating that the verification loop, not the model size, is the binding constraint.

**What o1/o3 is missing.** PRMs are learned verifiers trained on human-annotated reasoning traces. They are subject to the same distribution shift, reward hacking, and approximation errors as any learned model. The verification is probabilistic, not formal --- a PRM assigns a score, not a proof. The system has no mechanism for generating *new* verification criteria or adapting its verification strategy to novel domains. There is no neuroscience grounding or theoretical framework explaining why inference-time scaling works.

**LUCID's relationship.** LUCID provides both the theoretical explanation for o1/o3's success (inference-time verification is free energy minimization with extended compute allocation) and a concrete improvement path (replacing learned PRMs with formal verifiers). The combination would yield a system with o1's adaptive compute allocation and LUCID's provably correct verification --- inference-time scaling with formal guarantees.

### 6.7 VERSES AXIOM (2025)

AXIOM [8] is the system most closely aligned with LUCID's neuroscience foundations. Built on Karl Friston's active inference framework, AXIOM uses prediction error minimization to learn environment models and select actions in reinforcement learning tasks. It outperformed DreamerV3 by up to 60% while requiring 99% less training data in the Arcade Learning Environment.

**What AXIOM gets right.** AXIOM validates the core neuroscience claim: active inference (prediction error minimization) is a viable computational architecture, not merely a theoretical framework. The 99% data efficiency improvement demonstrates the practical benefits of neuroscience-grounded architectures. AXIOM's structure-learning capability --- building causal models of the environment from interaction --- mirrors LUCID's specification extraction.

**What AXIOM is missing.** AXIOM operates in the reinforcement learning domain (games, robotics) and has not been extended to language, code generation, or formal verification. It does not treat hallucination as a productive signal --- prediction errors are minimized, not harnessed. The system uses learned prediction rather than formal verification as its ground truth, limiting its applicability to domains where formal specifications exist.

**LUCID's relationship.** LUCID and AXIOM are complementary implementations of the same theoretical framework (free energy minimization) applied to different domains. AXIOM applies active inference to perception and action in physical environments; LUCID applies it to generation and verification in code and specification spaces. A unified system would combine AXIOM's environment modeling with LUCID's formal verification, creating an architecture that minimizes free energy across both physical and logical domains.

### 6.8 JEPA / V-JEPA 2 (LeCun, Meta, 2025)

The Joint Embedding Predictive Architecture (JEPA) [9] and its video extension V-JEPA 2 [10] predict representations in embedding space rather than pixel space. LeCun positions JEPA as a path to world models that understand causal structure rather than merely pattern-matching surface statistics.

**What JEPA gets right.** JEPA's predict-in-embedding-space approach solves a key problem with pixel-level prediction: the space of valid continuations is too large to predict directly. By predicting in a learned embedding space, JEPA achieves a form of abstraction that mirrors the hierarchical prediction in predictive processing. V-JEPA 2's ability to learn visual representations without labels demonstrates that prediction error alone is a sufficient training signal.

**What JEPA is missing.** JEPA currently lacks a formal verification component. Predictions are evaluated against learned embeddings, not against formal specifications. The system does not iterate --- it makes a single forward prediction rather than engaging in the multi-step refinement that characterizes both LUCID and biological predictive processing. There is no mechanism for treating prediction errors as productive signals for generation.

**LUCID's relationship.** JEPA and LUCID address different levels of the prediction hierarchy. JEPA operates at the perceptual level (predicting embeddings from sensory input), while LUCID operates at the cognitive level (predicting code behavior from specifications). A full predictive processing architecture would stack both: JEPA-style perceptual prediction providing inputs to LUCID-style cognitive verification. This mirrors the hierarchical organization of biological cortex, where lower layers predict sensory features and higher layers predict abstract relationships.

### 6.9 Synthesis: The Convergence Argument

The comparison reveals a striking pattern. Eight independent research programs, developed by different teams with different goals and different theoretical motivations, are converging on the same computational structure:

1. **Generate** outputs from a stochastic model (all eight systems)
2. **Verify** outputs against some form of ground truth (all eight systems)
3. **Iterate** based on verification signal (six of eight --- CAI, o1/o3 are single-pass)
4. **Ground in neuroscience** (two of eight --- AXIOM, JEPA)
5. **Treat hallucination as feature** (zero of eight)

LUCID is the only system that integrates all five properties. More importantly, LUCID provides the theoretical framework --- rooted in the free energy principle and predictive processing --- that *explains* why all eight systems work and *predicts* how they should be unified.

The convergence is not coincidental. It reflects a deep computational truth: the predict-verify loop is the minimal architecture for reliable intelligence under uncertainty. This is the architecture the brain converged on through 500 million years of evolution. It is the architecture the AI field is converging on through 70 years of research. LUCID is the first system to articulate this convergence explicitly and build on it systematically.

**Table 1: Comprehensive Comparison of Generate-Verify Architectures**

| System | Free Generation | Formal Verification | Self-Improvement | Neuroscience-Grounded | Hallucination-as-Feature | Theoretical Framework |
|--------|:-:|:-:|:-:|:-:|:-:|:-:|
| AlphaEvolve | Yes | Automated evaluators | Yes (evolutionary) | No | No | None |
| PSV | Yes | Yes (Lean 4) | No (single-pass) | No | No | None |
| DGM | Yes | Benchmark eval | Yes (evolutionary) | No | Implicit | None |
| DeepSeek-R1 | Yes | Emergent self-check | Yes (RL) | No | No | None |
| Constitutional AI | Yes | Self-critique (weak) | Yes (RLAIF) | No | No | Constitutional principles |
| o1/o3 | Yes (CoT) | Process reward models | Yes (RL) | No | No | None |
| VERSES AXIOM | Yes | Prediction error | Yes (belief updating) | **Yes** | No | Free Energy Principle |
| JEPA/V-JEPA 2 | Yes | Embedding prediction | Limited | Partial | No | World models |
| **LUCID** | **Yes** | **Yes (code-level formal)** | **Yes (iterative)** | **Yes** | **Yes** | **Free Energy Principle + Predictive Processing** |

---

## 7. Implications and Future Work

### 7.1 The Inference-Time Scaling Revolution

The dominant paradigm in AI scaling --- larger models trained on more data --- faces diminishing returns. Training compute has increased by approximately $10^4$ over three years (GPT-3 to GPT-4-class models), yet benchmark improvements on reasoning tasks have been incremental. Snell et al. [7] demonstrated that optimal allocation of test-time compute to verification yields larger performance gains than equivalent investment in model scale.

LUCID's architecture is natively positioned for the inference-time scaling paradigm. Each iteration of the generate-verify-remediate loop allocates additional compute at inference time, with the formal verifier providing a precise signal for where that compute should be directed. This has three implications:

**First, verification loops decouple capability from parameter count.** A smaller model paired with a formal verifier can match or exceed a larger model without verification, because the verifier compensates for the generator's errors through iterative correction. This suggests a new scaling law: capability scales with the product of model capacity and verification iterations, not with model capacity alone.

**Second, the compute economics favor verification.** Formal verification of code properties is O(n) in program length for most decidable properties, while model inference is O(n^2) or higher due to attention mechanisms. Adding verification iterations is computationally cheaper than scaling model parameters. For code generation tasks, doubling the number of LUCID iterations costs approximately 2x the compute; doubling model parameters costs approximately 4x (due to quadratic attention scaling) and requires retraining.

**Third, verification enables *adaptive* compute allocation.** Not all outputs require the same number of iterations. Simple, well-specified tasks converge in 1-2 iterations; complex, ambiguous tasks may require 5-10. LUCID's specification gap metric provides a natural stopping criterion: iterate until the gap falls below a threshold. This mirrors the brain's allocation of attentional resources, where surprising inputs receive more processing than expected ones.

### 7.2 Implications for AI Safety

The AI safety community has focused primarily on alignment --- ensuring that model outputs conform to human values and intentions. LUCID suggests a complementary approach: *verification* rather than *alignment*.

**The alignment approach** attempts to shape the generator's distribution so that harmful outputs are unlikely. This is fundamentally probabilistic: no amount of RLHF can guarantee that a model will never produce a harmful output, because the output distribution has non-zero probability density everywhere in the output space (a consequence of the impossibility theorems).

**The verification approach** does not attempt to prevent harmful outputs. Instead, it formally verifies that outputs satisfy specifications before they are deployed. This provides provable guarantees within the specification domain: if the specification captures the safety requirement, and the verifier confirms satisfaction, then the output is safe by construction.

The two approaches are complementary, not competing. Alignment reduces the frequency of harmful generations (making the generate-verify loop more efficient by reducing the number of iterations needed). Verification provides formal guarantees that alignment alone cannot. The combination --- aligned generation followed by formal verification --- offers both probabilistic and formal safety guarantees.

This has immediate practical implications for the EU AI Act, which takes effect August 2, 2026. The Act requires "high-risk" AI systems to demonstrate conformity with essential requirements including accuracy, robustness, and cybersecurity. LUCID's specification gap metric provides a quantitative, auditable measure of conformity. The iterative verification loop generates an audit trail showing what was generated, what was verified, what failed, and how it was remediated. This is precisely the documentation regulators will require.

### 7.3 The Hallucination-Creativity Connection

Karpowicz [11] proved that hallucination and creativity arise from the same mathematical mechanism in transformer architectures: the Log-Sum-Exp approximation in softmax attention. Suppressing hallucination necessarily suppresses creativity; enhancing creativity necessarily increases hallucination. They are not independent axes that can be optimized separately.

This result has a profound implication: **systems that hallucinate more, but verify better, should be more creative than systems that hallucinate less.** By decoupling generation from verification, LUCID allows the generator to operate at maximum creative capacity --- exploring the full space of possible outputs including novel, unexpected, and "hallucinatory" ones --- while the verifier ensures that only correct outputs are retained.

This is precisely how biological creativity works. Divergent thinking (brainstorming, free association, dreaming) generates a wide space of candidates, many of which are incorrect, impossible, or absurd. Convergent thinking (evaluation, testing, criticism) selects the viable candidates. The most creative individuals are not those who generate fewer wrong ideas; they are those who generate more ideas overall and have better selection mechanisms [12].

LUCID operationalizes this insight computationally. Future work should explore whether increasing the generator's temperature (encouraging more diverse, more "hallucinatory" outputs) combined with formal verification produces more novel solutions than conservative generation. Preliminary evidence from AlphaEvolve supports this: the system's most impactful discoveries came from mutations that would have been filtered out by any reasonable prior, but survived because the evaluator confirmed their correctness.

### 7.4 Path to General Intelligence via Predictive Processing

Karl Friston has argued that the free energy principle provides a unified account of perception, action, and cognition --- and that any system that minimizes free energy will exhibit intelligent behavior [13]. LUCID's mapping onto this framework raises a speculative but important question: does the LUCID architecture, if generalized beyond code, provide a path to artificial general intelligence?

We state this possibility with appropriate caveats. The following claims are *speculative* and require significant research to validate:

**The generalization hypothesis.** LUCID currently operates on code, where formal verification is well-defined. If formal verification can be extended to other domains --- natural language via logical consistency checking, mathematics via proof assistants, physical systems via simulation --- then the LUCID loop could operate across the full range of cognitive tasks. The generator provides the "imagination" (top-down prediction); the verifier provides the "reality check" (bottom-up correction); the iterative loop provides learning.

**The efficiency hypothesis.** Predictive processing achieves biological intelligence with approximately 20 watts of power. Current AI systems require megawatts. If the efficiency gap is due to architectural differences --- specifically, the brain's use of prediction error as a sparse, targeted signal versus AI's use of dense gradient updates --- then a native LUCID architecture could achieve significant efficiency improvements. VERSES' AXIOM result (99% less training data) provides preliminary evidence in bounded domains.

**The scaling hypothesis.** Millidge et al. [14] showed that predictive coding approximates backpropagation, and muPC [15] demonstrated scaling to 128 layers. If predictive coding networks can be scaled to transformer-competitive sizes while retaining their efficiency properties, the result would be a native neural architecture for the LUCID loop --- one where prediction error minimization is not an external verification step but an intrinsic training signal at every layer.

These hypotheses require experimental validation. The immediate research agenda includes: (1) extending formal verification to natural language claims via logical consistency checking, (2) benchmarking LUCID's iterative loop against inference-time scaling approaches on standardized tasks, and (3) implementing a native predictive coding network with LUCID-loop dynamics at the architectural level.

### 7.5 Limitations and Open Problems

We identify five principal limitations of the current work:

**The specification bottleneck.** Formal verification is only as good as the specification it verifies against. For well-specified domains (code, mathematics, logic), this is not a constraint. For ill-specified domains (creative writing, ethical reasoning, aesthetic judgment), the specification itself becomes the binding problem. LUCID partially addresses this by *generating* specifications from hallucinations (the Extract stage), but the quality of extracted specifications is itself unverified.

**The decidability boundary.** Formal verification of arbitrary program properties is undecidable (Rice's theorem). LUCID operates on decidable subsets --- type checking, test execution, bounded model checking --- but this limits the space of properties that can be formally verified. Extending to richer property classes (temporal logic, information flow, probabilistic guarantees) is an open research direction.

**Sample efficiency.** The iterative generate-verify loop requires multiple passes through the generator for each verified output. In LUCID's current implementation, the median convergence requires 2-3 iterations, but worst-case tasks may require 10+. For real-time applications, this latency may be prohibitive. Reducing iteration count through better-informed remediation is an open optimization problem.

**The verifier scope.** LUCID's formal verifier operates at the code level. Extending it to verify higher-level properties --- "does this system do what the user intended?" as opposed to "does this code satisfy its specification?" --- requires bridging the gap between formal specifications and human intent. This is a known-hard problem in formal methods that LUCID does not solve.

**Evaluation.** The benchmarks presented in Section 5 evaluate LUCID on code generation and code repair tasks in Python. Extending to other programming languages (where test-based formal verification is equally applicable) and to non-code domains (mathematical reasoning with SymPy verification, natural language with logical consistency checking) is planned future work. Evaluating the broader architectural claims --- that hallucination-as-feature generalizes beyond code, that the neuroscience mapping is productive for architectural decisions, that the theoretical framework predicts convergence properties in new domains --- requires additional experimentation across diverse verification modalities.

---

## 8. Conclusion

Three independent mathematical results establish that hallucination in large language models cannot be eliminated: it is an intrinsic consequence of the computational mechanisms that make these models useful [16, 17, 11]. The AI field's dominant response --- spending billions on suppression through RLHF, guardrails, and alignment techniques --- is attempting to solve a problem that has been proven unsolvable.

This paper has argued for a different response. Rather than treating hallucination as a defect to be suppressed, LUCID treats it as a computational primitive to be harnessed. The architecture --- generate, extract, verify, remediate, regenerate --- is not a novel invention. It is the architecture that biological intelligence converged on through 500 million years of evolution, formalized by predictive processing theory as free energy minimization. It is the architecture that eight independent research programs in AI are converging on from different directions, without a unifying theoretical framework. LUCID provides that framework.

The empirical results demonstrate that the approach works across three benchmarks. On HumanEval, LUCID achieves 100% pass@1 at k=3 iterations---the only condition to converge monotonically to perfect accuracy---while self-refinement provides essentially no improvement over single-pass generation (+1.2 pp over 5 iterations) and LLM-based judgment regresses at higher iteration counts (99.4% → 97.2% from k=3 to k=5). On SWE-bench Lite, LUCID improves resolution rate by 65.5% relative to the baseline (30.3% vs. 18.3%) with a 7.7:1 improvement-to-regression ratio. On real-world AI-generated codebases from four leading platforms, LUCID's spec-less verification identifies 21 critical bugs---including unprotected admin routes, IDOR vulnerabilities, and analytics dashboards rendering fabricated data---that no compiler, linter, or visual review would catch. Average health score: 40/100 despite clean compilation. Ablation studies confirm that the formal verifier is the critical component: replacing it with random verdicts causes accuracy to *decrease* with more iterations, while replacing it with learned verification produces non-monotonic, unreliable convergence. Total experimental cost: ~$472.

The theoretical framework explains *why* it works: the LUCID loop is a variational inference algorithm that minimizes surprise by iteratively refining its generative model against formal ground truth. The zero-noise property of formal verification (Theorem 4.2) guarantees that the prediction error signal is exact, enabling the monotonic convergence that learned verifiers cannot achieve. The comparison to existing approaches shows that every successful generate-verify system in AI --- AlphaEvolve, PSV, DGM, DeepSeek-R1, o1/o3, AXIOM --- is implementing a subset of this framework. LUCID is the first system to implement it completely and articulate the theoretical basis explicitly.

The implications extend beyond engineering. If hallucination and creativity share the same mathematical basis, then systems that hallucinate more productively --- generating freely and verifying rigorously --- should be more capable, not less, than systems constrained to conservative generation. The path to more reliable AI is not less hallucination. It is *better verification of more hallucination*. This is the insight that biological intelligence has operated on for half a billion years. It is time artificial intelligence caught up.

---

## References

[1] DeepMind. AlphaEvolve: A Gemini-powered coding agent for designing advanced algorithms. arXiv:2506.13131, 2025.

[2] Wilf, A., et al. Propose, Solve, Verify: Scaling Formal Verification for Mathematical Reasoning. arXiv:2512.18160, December 2025.

[3] Sakana AI. The Darwin Godel Machine: Open-Ended Self-Improvement of AI Agents. arXiv:2505.22954, 2025.

[4] DeepSeek. DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. Nature, 2025.

[5] Bai, Y., et al. Constitutional AI: Harmlessness from AI Feedback. Anthropic, 2022.

[6] OpenAI. Learning to Reason with LLMs. Blog post, 2024.

[7] Snell, C., et al. Scaling LLM Test-Time Compute Optimally Can Be More Effective Than Scaling Model Parameters. ICLR 2025 Oral. arXiv:2408.03314.

[8] VERSES AI. AXIOM: Mastering Arcade Games in Minutes with Active Inference and Structure Learning. 2025.

[9] LeCun, Y. A Path Towards Autonomous Machine Intelligence. Meta AI, 2022.

[10] Meta AI. V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction, and Planning. arXiv:2506.09985, June 2025.

[11] Karpowicz, M. Fundamental Impossibility of Hallucination Control in Large Language Models. arXiv:2506.06382, 2025.

[12] Guilford, J.P. The Nature of Human Intelligence. McGraw-Hill, 1967.

[13] Friston, K. The free-energy principle: a unified brain theory? Nature Reviews Neuroscience, 11:127-138, 2010.

[14] Millidge, B., Tschantz, A., and Buckley, C.L. Predictive Coding Approximates Backprop Along Arbitrary Computation Graphs. arXiv:2006.04182, 2020.

[15] muPC. Scaling Predictive Coding to 100+ Layers. arXiv:2505.13124, May 2025.

[16] Xu, Z., et al. Hallucination is Inevitable: An Innate Limitation of Large Language Models. arXiv:2401.11817, 2024.

[17] Banerjee, S., et al. LLMs Will Always Hallucinate, and We Need to Live With This. arXiv:2409.05746, 2024.

[18] Clark, A. Surfing Uncertainty: Prediction, Action, and the Embodied Mind. Oxford University Press, 2016.

[19] Seth, A. Being You: A New Science of Consciousness. Penguin, 2021.

[20] Kleppmann, M. Using AI and formal verification together. Blog post, December 2025.

[21] arXiv:2601.07046. Engineering of Hallucination in Large Language Models. January 2026.

[22] arXiv:2601.15652. Predictive Coding for Hallucination Detection in LLMs. January 2026.
