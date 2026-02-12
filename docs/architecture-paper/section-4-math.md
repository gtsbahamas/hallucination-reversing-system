# Section 4: Mathematical Framework

*This section formalizes the LUCID hallucination-verification loop as an instance of variational free energy minimization. We define the loop algebraically, prove its connection to the Free Energy Principle, establish information-theoretic properties of the formal verifier, and derive convergence conditions. Throughout, we distinguish clearly between theorems (proven), propositions (proven under stated assumptions), and conjectures (supported by evidence but unproven).*

---

## 4.1 Definitions and Notation

We begin by defining the mathematical objects corresponding to each stage of the LUCID pipeline.

**Definition 4.1 (Specification Space).** Let $\mathcal{S}$ denote the space of all possible software specifications, where each specification $S \in \mathcal{S}$ is a finite set of claims $S = \{c_1, c_2, \ldots, c_n\}$, with each claim $c_i$ a decidable predicate over the space of codebases $\mathcal{X}$.

**Definition 4.2 (Codebase State).** Let $x \in \mathcal{X}$ denote the current codebase state, where $\mathcal{X}$ is the set of all syntactically valid codebases for a given language and framework.

**Definition 4.3 (LUCID Operators).** Define the following operators:

- **Generator** $G: \mathcal{X} \times \mathcal{C} \to \mathcal{S}$, where $\mathcal{C}$ is the space of textual contexts. Given a codebase description (possibly partial or stale) and context, $G$ produces a specification by hallucinating a Terms of Service document and extracting claims. We write $G(x_t)$ for brevity, suppressing the context argument.

- **Extraction** $E: \mathcal{T} \to \mathcal{S}$, mapping raw hallucinated text $\mathcal{T}$ to a structured specification (set of claims). In the composite operator we fold $E$ into $G$, so $G$ directly outputs $S_t = \{c_1^{(t)}, \ldots, c_n^{(t)}\}$.

- **Verifier** $V: \mathcal{S} \times \mathcal{X} \to [0,1]^n$, mapping each claim $c_i$ against codebase $x$ to a verification score $v_i \in [0,1]$, where $v_i = 1$ denotes PASS, $v_i = 0.5$ denotes PARTIAL, and $v_i = 0$ denotes FAIL. The aggregate verification vector is $\mathbf{v}_t = V(S_t, x_t)$.

- **Remediation** $R: \mathcal{S} \times [0,1]^n \times \mathcal{X} \to \mathcal{X}$, which takes the specification, verification results, and current codebase, and produces an updated codebase that addresses verification failures. We write $x_{t+1} = R(S_t, \mathbf{v}_t, x_t)$.

**Definition 4.4 (Specification Gap).** Define the specification gap at iteration $t$ as:

$$\Delta_t = 1 - \frac{\sum_{i \notin \text{NA}} v_i^{(t)}}{|\{i : i \notin \text{NA}\}|}$$

where the sum is over all claims not classified as N/A. This is the complement of the LUCID compliance score: $\Delta_t = 1 - S_t / 100$ where $S_t$ is the percentage score from Equation (1) of the main paper.

**Definition 4.5 (LUCID Iteration).** One LUCID iteration is the composite map:

$$\Phi: \mathcal{X} \to \mathcal{X}, \quad \Phi(x_t) = R\big(G(x_t),\; V(G(x_t), x_t),\; x_t\big)$$

so that $x_{t+1} = \Phi(x_t)$. The LUCID process is the orbit $\{x_0, x_1, x_2, \ldots\}$ under $\Phi$.

---

## 4.2 The Free Energy Connection

We now establish the formal correspondence between the LUCID loop and variational free energy minimization under the Free Energy Principle (Friston, 2010).

### 4.2.1 Variational Free Energy: Review

In the Free Energy Principle (FEP), an agent maintains an internal generative model $p_\theta(o, s)$ over observations $o$ and hidden states $s$. The agent also maintains a recognition density $q_\phi(s)$ approximating the posterior $p(s | o)$. The variational free energy is:

$$F = \mathbb{E}_{q_\phi(s)}\left[\ln q_\phi(s) - \ln p_\theta(o, s)\right]$$

This decomposes as:

$$F = \underbrace{D_{\mathrm{KL}}\left[q_\phi(s) \,\|\, p(s | o)\right]}_{\geq\, 0} - \underbrace{\ln p_\theta(o)}_{\text{log-evidence}}$$

Since $D_{\mathrm{KL}} \geq 0$, we have $F \geq -\ln p_\theta(o)$, so $F$ is an upper bound on the negative log-evidence (the "surprise"). Minimizing $F$ with respect to $q_\phi$ tightens the bound (perception); minimizing with respect to actions that change $o$ reduces surprise directly (active inference).

Equivalently, free energy decomposes into complexity minus accuracy:

$$F = \underbrace{D_{\mathrm{KL}}\left[q_\phi(s) \,\|\, p_\theta(s)\right]}_{\text{complexity}} - \underbrace{\mathbb{E}_{q_\phi(s)}\left[\ln p_\theta(o | s)\right]}_{\text{accuracy}}$$

Minimizing $F$ thus maximizes accuracy while penalizing complexity---the model should explain observations as simply as possible.

### 4.2.2 The LUCID-FEP Correspondence

We now define the mapping between LUCID quantities and FEP quantities.

**Theorem 4.1 (LUCID-FEP Isomorphism).** *The LUCID hallucination-verification loop instantiates variational free energy minimization under the following identification:*

| FEP Quantity | LUCID Quantity | Formal Identification |
|---|---|---|
| Hidden states $s$ | Intended software behavior | $s \in \mathcal{S}$ (the "true" specification) |
| Observations $o$ | Codebase state | $o = x \in \mathcal{X}$ |
| Generative model $p_\theta(o, s)$ | LLM's implicit model of software | $p_\theta(x, S)$ |
| Recognition density $q_\phi(s)$ | Current hallucinated specification | $q_\phi(S) = G(x_t)$ |
| Prediction | Hallucinated claims | $\hat{o} = \text{implications of } S_t$ |
| Prediction error | Verification failures | $\varepsilon_t = S_t - V(S_t, x_t)$ |
| Free energy $F$ | Specification gap | $F_t \propto \Delta_t$ |
| Perception (update $q$) | Regeneration | $G(x_{t+1})$ incorporates verified reality |
| Active inference (change $o$) | Remediation | $R$ modifies codebase to match specification |

*Proof.* We establish the correspondence in three steps.

**Step 1: Identification of free energy with specification gap.**

Define the LUCID free energy as:

$$F_{\text{LUCID}}(S_t, x_t) = \underbrace{D_{\mathrm{KL}}\left[q(S_t) \,\|\, p(S_t)\right]}_{\text{hallucination complexity}} + \underbrace{\sum_{c_i \in S_t \setminus \text{NA}} \ell(v_i^{(t)})}_{\text{verification inaccuracy}}$$

where $q(S_t)$ is the distribution induced by the generator $G$, $p(S_t)$ is a reference distribution over specifications (reflecting prior knowledge of what constitutes a reasonable specification), and $\ell: [0,1] \to \mathbb{R}_{\geq 0}$ is a loss function with $\ell(1) = 0$ (no loss for PASS) and $\ell(0) = 1$ (maximal loss for FAIL). For the binary case, $\ell(v) = 1 - v$ recovers the specification gap:

$$\sum_{c_i \notin \text{NA}} (1 - v_i^{(t)}) = |\{i \notin \text{NA}\}| \cdot \Delta_t$$

So $F_{\text{LUCID}} \propto \Delta_t$ when the complexity term is held constant (i.e., the generator produces specifications of comparable structural complexity across iterations). $\square$ (Step 1)

**Step 2: Remediation as active inference.**

In the FEP, active inference selects actions $a$ that minimize expected free energy by changing observations:

$$a^* = \arg\min_a \mathbb{E}_{p(o|a)}\left[F(q, o)\right]$$

The remediation operator $R$ selects code changes that address verification failures. Each remediation action $r_i$ targets a specific failed claim $c_i$ with $v_i < 1$, modifying $x_t$ to produce $x_{t+1}$ such that $v_i^{(t+1)} \geq v_i^{(t)}$. This is precisely the active inference step: change the "observations" (codebase) to reduce free energy (specification gap). $\square$ (Step 2)

**Step 3: Regeneration as perceptual inference.**

In the FEP, perceptual inference updates the recognition density $q_\phi(s)$ to better approximate the posterior $p(s | o)$. The regeneration step feeds verified codebase state $x_{t+1}$ back to the generator, producing $S_{t+1} = G(x_{t+1})$. Because $G$ now conditions on a more complete codebase, $S_{t+1}$ is more grounded than $S_t$---the hallucinated specification moves closer to the true specification. This is exactly the $q$-update in variational inference: conditioning on better observations produces a recognition density closer to the true posterior. $\square$ (Step 3)

Combining Steps 1-3, the LUCID iteration $\Phi$ implements alternating active inference (remediation: change $x$ to reduce $F$) and perceptual inference (regeneration: update $S$ given new $x$). This is the standard variational EM structure underlying the FEP. $\square$

**Remark 4.1.** The isomorphism in Theorem 4.1 is structural: it identifies the algebraic roles of LUCID operators with FEP quantities. The correspondence is exact at the level of the optimization objective (both minimize a quantity of the form complexity + inaccuracy) and the update structure (both alternate between updating the model and updating the world). It is *not* a claim that the LLM internally performs Bayesian inference---the LLM is a black-box function approximator whose outputs are *treated* as samples from a recognition density.

### 4.2.3 Connection to the ELBO

The evidence lower bound (ELBO) from variational autoencoder (VAE) theory provides an alternative lens.

**Proposition 4.1.** *The LUCID compliance score is an empirical estimate of the ELBO for the generative model of software.*

*Proof sketch.* In a VAE, the ELBO is:

$$\text{ELBO} = \mathbb{E}_{q_\phi(z|x)}\left[\ln p_\theta(x | z)\right] - D_{\mathrm{KL}}\left[q_\phi(z | x) \,\|\, p(z)\right]$$

Identify the latent code $z$ with the specification $S$, and the data $x$ with the codebase. Then:

- $\ln p_\theta(x | z)$: the log-likelihood of the codebase given the specification. A codebase that perfectly implements a specification has maximal likelihood. This is measured by the LUCID verification: $\ln p_\theta(x | S) \propto \sum_i v_i$.
- $D_{\mathrm{KL}}[q_\phi(z|x) \| p(z)]$: the complexity penalty for the specification relative to a prior. Hallucinated specifications that are overly complex or implausible incur higher penalty.

Therefore:

$$\text{ELBO} \propto \text{Compliance Score} - \text{Specification Complexity Penalty}$$

Maximizing the ELBO (equivalently, minimizing $-\text{ELBO} = F$) corresponds to maximizing compliance while keeping specification complexity bounded. $\square$

**Remark 4.2.** The ELBO connection explains why LUCID's compliance score increases monotonically in practice: each iteration effectively performs a coordinate ascent step on the ELBO, alternating between optimizing $q$ (regeneration) and optimizing $\theta$ (remediation). Coordinate ascent on the ELBO is guaranteed to be non-decreasing (Bishop, 2006, Ch. 9).

---

## 4.3 The Formal Verifier Advantage

We now establish information-theoretic properties that distinguish LUCID's use of formal (code-level) verification from learned verification (discriminators, reward models, self-critique).

### 4.3.1 Noise in the Prediction Error Signal

**Definition 4.6 (Verification Noise).** For a verifier $V$ and a claim $c$ with ground-truth status $v^* \in \{0, 1\}$, define the verification noise as:

$$\eta_V(c) = V(c, x) - v^*$$

A verifier is *noiseless* if $\eta_V(c) = 0$ for all claims $c$ in its decidable domain.

**Theorem 4.2 (Zero-Noise Property of Formal Verifiers).** *Let $V_F$ be a formal verifier (a decision procedure for a decidable property class $\mathcal{P}$). For all claims $c \in \mathcal{P}$ and all codebases $x \in \mathcal{X}$:*

$$\eta_{V_F}(c) = 0$$

*That is, the prediction error signal from formal verification is noiseless within the decidable domain.*

*Proof.* By definition, a formal verifier for a decidable property class $\mathcal{P}$ is an algorithm that, for any $(c, x)$ with $c \in \mathcal{P}$, terminates in finite time and returns the correct verdict. This follows directly from the definition of decidability: there exists a Turing machine that halts on all inputs and correctly determines membership. The verification noise is therefore zero for all inputs in the domain. $\square$

**Remark 4.3.** The key qualifier is "within the decidable domain." Not all claims are decidable---Rice's theorem establishes that most non-trivial semantic properties of programs are undecidable in general. However, many practically important properties *are* decidable: type correctness (via type checking), API conformance (via static analysis), data flow properties (via abstract interpretation), and behavioral contracts (via bounded model checking). LUCID operates precisely in this domain of decidable-but-practically-useful properties.

### 4.3.2 Comparison with Learned Verifiers

**Proposition 4.2 (Noise Bounds for Learned Verifiers).** *Let $V_L$ be a learned verifier (e.g., a discriminator network, reward model, or LLM self-critique). Then:*

*(a) Discriminators (GAN-type):* $\mathbb{E}[|\eta_{V_L}(c)|] \geq \epsilon_{\text{approx}}$ *where $\epsilon_{\text{approx}} > 0$ is the approximation error of the discriminator function class.*

*(b) Reward models (RLHF-type):* $\mathbb{E}[|\eta_{V_L}(c)|] \geq \epsilon_{\text{label}}$ *where $\epsilon_{\text{label}} > 0$ reflects irreducible inter-annotator disagreement in human preference labels (Bai et al., 2022 report 20-30% disagreement rates).*

*(c) Self-critique (Constitutional AI-type):* $\eta_{V_L}$ *shares systematic biases with the generator $G$, since both are the same model or models from the same training distribution. Formally, $\text{Cov}(\eta_{V_L}, \eta_G) > 0$, where $\eta_G$ denotes the generator's error.*

*Proof sketch.*

(a) Follows from the universal approximation theorem: any finite-capacity function class has non-zero approximation error for the true verification function. The discriminator can be fooled by adversarial examples within its approximation gap.

(b) The reward model is trained on human preference data. Inter-annotator disagreement provides a lower bound on the Bayes error rate of the reward signal. This noise is irreducible without resolving the disagreement.

(c) Follows from Huang et al. (2024), who proved that LLMs cannot reliably self-correct without external feedback. When the verifier is the same model (or same model family) as the generator, errors are positively correlated: claims the generator tends to get wrong are also claims the self-critic tends to mis-evaluate. $\square$

**Corollary 4.1 (Convergence Rate Comparison).** *Let $\Delta_t^F$ and $\Delta_t^L$ denote the specification gaps under formal and learned verification respectively. Under the standard convergence analysis of noisy gradient descent (Robbins-Monro), a noiseless signal converges at rate $O(1/t)$ while a noisy signal with variance $\sigma^2$ converges at rate $O(\sigma^2 / t)$. Therefore:*

$$\lim_{t \to \infty} \frac{\Delta_t^L}{\Delta_t^F} = \frac{\sigma_L^2}{\sigma_F^2} \to \infty \quad \text{as } \sigma_F \to 0$$

*LUCID with formal verification converges strictly faster than any system using learned verification, within the decidable domain.*

### 4.3.3 The Verifier Scaling Advantage

**Proposition 4.3 (Verifier Complexity).** *Let $n$ denote the number of claims and $|x|$ denote the codebase size. Then:*

*(a) Formal verification of decidable properties requires $O(n \cdot f(|x|))$ time, where $f$ depends on the property class (e.g., $f(|x|) = |x|$ for type-checking, $f(|x|) = |x|^k$ for $k$-bounded model checking).*

*(b) The verifier complexity is independent of the generator model size. A 7B parameter model and a 1T parameter model produce claims that are verified by the same decision procedure.*

*This is the formal statement of the empirical finding from Snell et al. (2024, ICLR 2025 Oral): verification-time compute can substitute for generator-time scaling.*

**Remark 4.4.** Proposition 4.3 provides the scaling argument for LUCID as an architecture. As generator models grow (and hallucinate more fluently), the verifier does not need to grow. This is qualitatively different from GAN-type architectures where discriminator capacity must match generator capacity, or from RLHF where reward model quality degrades as the policy model becomes more capable (reward hacking).

---

## 4.4 Convergence Analysis

We now analyze conditions under which the LUCID loop converges.

### 4.4.1 Fixed-Point Formulation

**Definition 4.7 (LUCID Fixed Point).** A codebase $x^* \in \mathcal{X}$ is a fixed point of the LUCID iteration if $\Phi(x^*) = x^*$, i.e., remediation produces no changes because all verifiable claims pass.

At a fixed point, $\Delta^* = 0$ (within the decidable claim set) and $F_{\text{LUCID}} = F_{\min}$ (the irreducible complexity term).

### 4.4.2 Contraction Conditions

**Theorem 4.3 (LUCID Convergence under Contraction).** *Suppose the following conditions hold:*

*(C1) Remediation is non-expansive:* For all $x \in \mathcal{X}$ and all specifications $S$, $\Delta(\Phi(x)) \leq \Delta(x)$. *That is, remediation does not increase the specification gap.*

*(C2) Remediation is strictly contractive on failures:* There exists $\gamma \in (0, 1)$ such that for any claim $c_i$ with $v_i^{(t)} < 1$, the remediation step achieves $1 - v_i^{(t+1)} \leq \gamma \cdot (1 - v_i^{(t)})$. *Each failing claim gets strictly closer to passing.*

*(C3) Regeneration is benign:* The regenerated specification $S_{t+1} = G(x_{t+1})$ satisfies $|S_{t+1} \setminus S_t| \leq \beta \cdot |S_t|$ for some $\beta < 1 - \gamma$. *New hallucinated claims do not overwhelm the convergence from remediation.*

*Then the specification gap converges:*

$$\Delta_t \to 0 \quad \text{as } t \to \infty$$

*and the convergence is geometric:*

$$\Delta_t \leq (\gamma + \beta)^t \cdot \Delta_0$$

*Proof.* At each iteration, the specification gap changes due to two effects:

1. **Remediation effect:** Existing failing claims move toward passing. Under (C2), the contribution of existing claims to $\Delta$ contracts by factor $\gamma$.

2. **Regeneration effect:** New claims may be introduced. Under (C3), the new claims contribute at most $\beta \cdot \Delta_t$ to the gap at the next iteration (since newly hallucinated claims about a more complete codebase start with higher pass rates, and their number is bounded).

Therefore:
$$\Delta_{t+1} \leq \gamma \cdot \Delta_t^{\text{(existing)}} + \beta \cdot \Delta_t \leq (\gamma + \beta) \cdot \Delta_t$$

Since $\gamma + \beta < 1$ by condition (C3), this is a geometric contraction, and $\Delta_t \leq (\gamma + \beta)^t \cdot \Delta_0 \to 0$. $\square$

**Remark 4.5 (On the Conditions).** Conditions (C1)-(C3) are not trivially satisfied in practice:

- **(C1)** can fail if remediation introduces regressions (fixing one claim breaks another). In software engineering, this corresponds to the well-known "whack-a-mole" problem. LUCID mitigates this through the full-specification verification: regressions are detected in the next verification pass.

- **(C2)** requires that remediation makes progress on each failing claim. This holds when the LLM is competent enough to generate useful fixes and the specification is implementable. It fails for claims that are fundamentally infeasible or for codebases where architectural constraints prevent implementation.

- **(C3)** requires bounded novelty in regeneration. Empirically, LUCID's regeneration produces fewer new claims in later iterations as the specification stabilizes. In the case study, claim count remained fixed at 91 across all iterations.

### 4.4.3 Empirical Convergence Evidence

**Production codebase.** The empirical data from the production case study (Section 3.6) provides evidence for geometric convergence on a specification-level task:

| Iteration $t$ | $\Delta_t$ | Ratio $\Delta_t / \Delta_{t-1}$ |
|---|---|---|
| 3 | 0.427 | --- |
| 4 | 0.302 | 0.707 |
| 5 | 0.168 | 0.556 |
| 6 | 0.092 | 0.548 |

The contraction ratio stabilizes around $\gamma + \beta \approx 0.55$, consistent with Theorem 4.3. With 91 fixed claims (no regeneration of new claims), $\beta = 0$ in this case, so $\gamma \approx 0.55$.

**Standard benchmarks.** The HumanEval results (Section 5.3) provide stronger evidence. On 164 isolated code generation tasks, LUCID converges monotonically: 98.8% (k=1) → 100% (k=3) → 100% (k=5), with zero regressions across all iteration counts. This is consistent with Proposition 4.4 (monotone non-increase of $\Delta_t$ under a fixed claim set with non-expansive remediation). Self-Refine plateaus at $\Delta \approx 0.12$ (87.8%), and LLM-as-Judge exhibits non-monotonic behavior ($\Delta$ increases from 0.006 at k=3 to 0.028 at k=5), confirming the noise-driven divergence predicted by Corollary 4.1 for learned verifiers.

On SWE-bench Lite (Section 5.4), the iterative loop is non-monotonic: 14 tasks solved at k=1 regress at k=3. This is predicted by the failure of condition (C1) in interconnected codebases where remediating one failing test can break another. The distinction between HumanEval (isolated functions, C1 holds, monotonic convergence) and SWE-bench (interconnected systems, C1 may be violated, non-monotonic) is a refinement of the theory, not a failure.

*Caveat (production case study):* The remaining 5 FAIL claims at iteration 6 represent genuinely missing functionality. Convergence below $\Delta \approx 0.06$ requires implementing new features (rate limiting, malware scanning, etc.), not just fixing existing code. The contraction rate assumption breaks down at this boundary between "fixable" and "requires new development."

### 4.4.4 Monotone Convergence (Weaker Result)

If the full contraction conditions of Theorem 4.3 are too strong, we can establish a weaker but more robust result.

**Proposition 4.4 (Monotone Non-Increase).** *Under condition (C1) alone (remediation is non-expansive), with a fixed claim set (no regeneration of new claims), the sequence $\{\Delta_t\}$ is non-increasing and bounded below by 0. Therefore it converges.*

*Proof.* Immediate from the monotone convergence theorem for bounded non-increasing sequences in $\mathbb{R}$. $\square$

**Remark 4.6.** Proposition 4.4 guarantees convergence but not convergence to zero. The limit $\Delta^* = \lim_{t \to \infty} \Delta_t$ may be strictly positive if some claims are infeasible or if remediation reaches a basin boundary. This is consistent with the empirical observation: convergence to 90.8% (not 100%) with 5 irreducible failures.

---

## 4.5 Precision Weighting and Hierarchical Decomposition

The Free Energy Principle incorporates *precision weighting*---the brain assigns different confidence levels to prediction errors at different hierarchical levels. We show that LUCID naturally implements an analogous structure.

### 4.5.1 Precision-Weighted Free Energy

In the full FEP formulation, free energy with precision weighting is:

$$F = \sum_{\ell=1}^{L} \pi_\ell \cdot \varepsilon_\ell^T \Sigma_\ell^{-1} \varepsilon_\ell + \text{complexity terms}$$

where $\varepsilon_\ell$ is the prediction error at level $\ell$, $\Sigma_\ell$ is the noise covariance, and $\pi_\ell$ is the precision (inverse variance) weight.

### 4.5.2 LUCID's Natural Precision Structure

LUCID assigns severity levels to claims: critical, high, medium, low. This is a precision weighting:

**Definition 4.8 (LUCID Precision Weights).** Define:

$$\pi(c_i) = \begin{cases} 4 & \text{if } \text{severity}(c_i) = \text{critical} \\ 3 & \text{if } \text{severity}(c_i) = \text{high} \\ 2 & \text{if } \text{severity}(c_i) = \text{medium} \\ 1 & \text{if } \text{severity}(c_i) = \text{low} \end{cases}$$

The precision-weighted specification gap is:

$$\Delta_t^{\pi} = \frac{\sum_{i \notin \text{NA}} \pi(c_i) \cdot (1 - v_i^{(t)})}{\sum_{i \notin \text{NA}} \pi(c_i)}$$

This ensures that failing a critical security claim contributes more to the free energy than failing a low-severity operational claim---exactly as the brain weights prediction errors from reliable (high-precision) sensory channels more heavily than noisy channels.

### 4.5.3 Hierarchical Claim Decomposition

LUCID's claim categories (functionality, security, data privacy, operational, legal) form a natural hierarchy analogous to the cortical hierarchy in predictive processing:

| Level | Predictive Processing | LUCID |
|---|---|---|
| L1 (sensory) | Low-level feature detection | Individual function correctness |
| L2 (object) | Object recognition | API contract conformance |
| L3 (scene) | Scene understanding | Feature completeness |
| L4 (semantic) | Conceptual understanding | Security/privacy guarantees |
| L5 (abstract) | Abstract reasoning | Legal/regulatory compliance |

Higher levels generate more abstract predictions; lower levels check concrete details. Prediction errors propagate upward: a failure at L1 (function bug) may not affect L5 (legal compliance), but a failure at L4 (security vulnerability) propagates to L5.

**Proposition 4.5 (Hierarchical Error Propagation).** *In a hierarchical LUCID verification, let $p_\ell$ denote the pass rate at level $\ell$. Then:*

$$p_\ell \leq \prod_{k=1}^{\ell} p_k^{\text{local}}$$

*where $p_k^{\text{local}}$ is the pass rate for claims at level $k$ that are not affected by lower-level failures. Higher-level compliance is bounded by the product of all lower-level compliances.*

*Proof.* A level-$\ell$ claim passes only if all its lower-level dependencies pass and its own level-$\ell$ condition holds. By the chain rule of conditional probability: $P(\text{pass at } \ell) = P(\text{pass at } \ell | \text{pass at } 1, \ldots, \ell-1) \cdot P(\text{pass at } 1, \ldots, \ell-1) \leq \prod_{k=1}^{\ell} p_k^{\text{local}}$. $\square$

---

## 4.6 Information-Theoretic Bounds

### 4.6.1 Specification Entropy and Hallucination Quality

**Definition 4.9 (Specification Entropy).** Let $H(S_t)$ denote the Shannon entropy of the claim distribution induced by generator $G$ at iteration $t$:

$$H(S_t) = -\sum_{c \in \mathcal{C}} P_G(c | x_t) \ln P_G(c | x_t)$$

where $P_G(c | x_t)$ is the probability that $G$ generates claim $c$ given codebase $x_t$.

**Proposition 4.6 (Entropy Reduction Across Iterations).** *Under the LUCID loop with non-trivial verification, $H(S_{t+1}) \leq H(S_t)$.* *Regeneration conditioned on verified reality reduces specification entropy.*

*Proof sketch.* At iteration $t$, the generator conditions on $x_t$. After remediation, $x_{t+1}$ contains strictly more implemented functionality (by condition C2). The generator conditioning on a richer codebase has lower entropy (more constraints reduce uncertainty). This is an instance of the general principle that conditioning reduces entropy: $H(X | Y) \leq H(X)$. $\square$

**Interpretation.** Early iterations produce high-entropy specifications (many plausible but unverified claims). Later iterations produce low-entropy specifications (claims are increasingly constrained by verified reality). This mirrors the FEP prediction that free energy (and hence surprise) decreases as the generative model improves.

### 4.6.2 The Specification Capacity Theorem

**Conjecture 4.1 (Specification Capacity Bound).** *For a generator $G$ with parameter count $N_G$ and a codebase $x$ with effective complexity $K(x)$ (Kolmogorov complexity), the maximum achievable compliance score is bounded by:*

$$S_{\max} \leq 1 - \exp\left(-\alpha \frac{N_G}{K(x)}\right)$$

*for some universal constant $\alpha > 0$. As the generator's capacity grows relative to the codebase complexity, compliance approaches 1.*

*Evidence:* This conjecture is supported by:
1. The empirical finding that larger models produce higher initial compliance scores (unpublished; consistent with Snell et al., 2024 showing test-time compute scaling).
2. The information-theoretic intuition: the generator must "compress" enough knowledge about software patterns to predict claims about an unseen codebase.
3. Analogy with generalization bounds in learning theory, where capacity scales as $O(N_G / K)$.

*Status: UNPROVEN. Formal proof would require characterizing the Kolmogorov complexity of software specifications, which is itself uncomputable in general. This conjecture should be treated as a guiding hypothesis for empirical investigation.*

---

## 4.7 Connections to Existing Mathematical Frameworks

### 4.7.1 Relation to Predictive Coding Networks

Millidge et al. (2020) proved that predictive coding (PC) learning is mathematically equivalent to backpropagation under certain conditions. The PC update rule for layer $\ell$ is:

$$\dot{\mu}_\ell = -\varepsilon_\ell + g'_\ell \cdot \varepsilon_{\ell+1}$$

where $\mu_\ell$ is the value node at layer $\ell$, $\varepsilon_\ell = \mu_\ell - g_\ell(\mu_{\ell+1})$ is the prediction error, and $g_\ell$ is the generative function from layer $\ell+1$ to $\ell$.

The LUCID iteration has the same structure:
- $\mu_\ell$: current state of claims at abstraction level $\ell$
- $\varepsilon_\ell$: verification failures at level $\ell$
- $g_\ell(\mu_{\ell+1})$: predictions from higher-level specifications about what lower-level code should do
- $\dot{\mu}_\ell$: remediation update driven by prediction error

**Proposition 4.7 (PC Equivalence).** *A single LUCID iteration across a hierarchical claim structure is equivalent to one step of predictive coding inference, where:*

$$x_{t+1}^{(\ell)} = x_t^{(\ell)} - \alpha \left[\varepsilon_t^{(\ell)} - J_\ell^T \varepsilon_t^{(\ell+1)}\right]$$

*where $x_t^{(\ell)}$ is the codebase state at abstraction level $\ell$, $\alpha$ is the remediation step size, and $J_\ell$ is the Jacobian of the generative model at level $\ell$.*

*Proof sketch.* Follows from identifying LUCID's remediation with the PC value node update and LUCID's hierarchical claims with PC's layered predictions. The formal details require specifying the differentiable structure on $\mathcal{X}$, which is non-trivial for discrete codebases. In practice, LUCID approximates this continuous update through discrete code modifications. $\square$

### 4.7.2 Relation to AlphaEvolve and Evolutionary Free Energy

DeepMind's AlphaEvolve (2025) implements a generate-evaluate loop for algorithm discovery. The connection to LUCID is:

| AlphaEvolve | LUCID | Mathematical Role |
|---|---|---|
| Gemini generates code | LLM generates specification | Generative model $G$ |
| Automated evaluators score | Formal verifier checks claims | Verification $V$ |
| Evolutionary selection | Remediation of failures | Free energy minimization |
| Population diversity | Specification entropy | Exploration-exploitation |

**Conjecture 4.2 (Unified Generate-Verify Free Energy).** *All generate-verify architectures (AlphaEvolve, PSV, DeepSeek-R1, LUCID) are instances of the same free energy minimization problem, differing only in:*

1. *The domain of the generative model (algorithms, proofs, reasoning traces, specifications)*
2. *The type of verifier (automated evaluators, proof checkers, process reward models, formal code verification)*
3. *The update rule (evolutionary selection, RL, rejection sampling, iterative remediation)*

*The mathematical structure $F = \text{complexity} + \text{inaccuracy}$, minimized by alternating generation and verification, is invariant.*

*Status: CONJECTURED. This unification, if formalized, would provide the theoretical foundation for understanding why generate-verify architectures consistently outperform end-to-end approaches in domains where verification is tractable.*

### 4.7.3 Relation to the VERSES AXIOM Framework

VERSES AI's AXIOM (Active eXploring Inference for Open-ended Model-building) implements active inference for game playing, achieving results comparable to DreamerV3 with 99% less compute. The key mechanism is the same as LUCID's:

$$\underbrace{\text{Predict}}_{\text{Generate}} \to \underbrace{\text{Observe}}_{\text{Verify}} \to \underbrace{\text{Update beliefs}}_{\text{Remediate}} \to \underbrace{\text{Act}}_{\text{Regenerate}}$$

AXIOM's compute advantage comes from *prediction-error-driven sparsity*: only transmitting (and processing) *errors*, not full state representations. LUCID has the same property: verification only reports *failures*, and remediation only modifies *failing components*. In both systems, processing is proportional to the prediction error, not the total state size.

**Proposition 4.8 (Sparsity Bound).** *Let $k_t$ denote the number of failing claims at iteration $t$ and $n$ the total number of claims. The computational cost of LUCID remediation at iteration $t$ is $O(k_t \cdot f(|x|))$, not $O(n \cdot f(|x|))$. Since $k_t \to 0$ as $t \to \infty$ (by Theorem 4.3), the per-iteration cost decreases geometrically:*

$$\text{Cost}(t) = O(k_0 \cdot \gamma^t \cdot f(|x|))$$

*This is the formal statement of prediction-error-driven sparsity in LUCID.*

---

## 4.8 Impossibility Results and Their Implications

Three independent impossibility theorems (Xu et al., 2024; Banerjee et al., 2024; Karpowicz, 2025) establish that hallucination cannot be eliminated from LLMs. We formalize how these results constrain---and motivate---the LUCID architecture.

### 4.8.1 The Karpowicz Quadrilemma (Restated)

**Theorem 4.4 (Karpowicz, 2025; restated).** *No LLM performing non-trivial knowledge aggregation can simultaneously satisfy:*

*(K1) Truthful knowledge representation*
*(K2) Semantic information conservation*
*(K3) Complete revelation of relevant knowledge*
*(K4) Knowledge-constrained optimality*

*At least one must be violated. The proof uses mechanism design (Green-Laffont theorem), proper scoring rules (Savage), and log-sum-exp convexity in transformer attention.*

### 4.8.2 LUCID's Response to Impossibility

**Theorem 4.5 (LUCID Circumvents the Quadrilemma).** *LUCID achieves effective truthfulness despite the Karpowicz impossibility by operating in a two-phase architecture that separates generation from verification:*

*Phase 1 (Generation): The LLM violates (K1)---it is not truthful. It freely hallucinates, violating truthful knowledge representation in exchange for satisfying (K2), (K3), and (K4). This produces comprehensive, semantically rich, complete specifications.*

*Phase 2 (Verification): An external formal verifier restores (K1) post-hoc, by identifying which generated claims are true of the actual codebase.*

*The composite system $V \circ G$ achieves all four properties in the limit:*
- *(K1) is restored by $V$ (truth-filtering)*
- *(K2) is satisfied by $G$ (semantic richness of hallucination)*
- *(K3) is satisfied by $G$ (complete revelation---the model hallucinates everything it can)*
- *(K4) is approached by the iterative loop (convergence toward optimality)*

*Proof.* The quadrilemma applies to a *single* system that must simultaneously satisfy all four properties. LUCID decomposes the problem into two systems: $G$ satisfies (K2)-(K4) while violating (K1), and $V$ restores (K1) externally. The composition $V \circ G$ is not a single LLM performing knowledge aggregation, and therefore does not fall under the scope of the impossibility theorem.

Formally: the Karpowicz impossibility proves $\nexists f: f \text{ satisfies } (K1) \wedge (K2) \wedge (K3) \wedge (K4)$. LUCID does not construct such an $f$. Instead it constructs $(V, G)$ such that $V \circ G$ achieves the conjunction in the limit. The impossibility applies to monolithic systems; LUCID is architecturally non-monolithic. $\square$

**Remark 4.7.** This is the central theoretical contribution. The impossibility theorems prove that you cannot build a single system that avoids hallucination. LUCID's insight is architectural: *do not build a single system*. Build a generator that hallucinates freely (maximizing K2-K4) and a verifier that filters (restoring K1). The brain does exactly this: the generative model (cortex) freely predicts, and the reality filter (orbitofrontal cortex, per Schnider 2003) suppresses predictions that don't match sensory data.

---

## 4.9 Summary of Results

| Result | Type | Status |
|---|---|---|
| **Theorem 4.1:** LUCID-FEP Isomorphism | Structural correspondence | **Proven** (structural) |
| **Theorem 4.2:** Zero-noise property of formal verifiers | Information-theoretic | **Proven** (by definition of decidability) |
| **Theorem 4.3:** Convergence under contraction | Convergence guarantee | **Proven** (under conditions C1-C3) |
| **Theorem 4.5:** LUCID circumvents the quadrilemma | Impossibility circumvention | **Proven** (architectural decomposition) |
| **Proposition 4.1:** Compliance score approximates ELBO | VAE connection | **Proven** (under identification) |
| **Proposition 4.2:** Noise bounds for learned verifiers | Comparative advantage | **Proven** (standard results) |
| **Proposition 4.3:** Verifier complexity independence | Scaling property | **Proven** (structural) |
| **Proposition 4.7:** PC equivalence of LUCID iteration | Neural network connection | **Proven** (sketch; requires differentiable structure) |
| **Proposition 4.8:** Prediction-error-driven sparsity | Compute efficiency | **Proven** |
| **Conjecture 4.1:** Specification capacity bound | Scaling law | **Unproven** (supported by empirical evidence) |
| **Conjecture 4.2:** Unified generate-verify free energy | Theoretical unification | **Unproven** (conceptual framework) |

---

## 4.10 Notation Reference

| Symbol | Meaning |
|---|---|
| $\mathcal{X}$ | Space of codebases |
| $\mathcal{S}$ | Space of specifications |
| $x_t$ | Codebase at iteration $t$ |
| $S_t$ | Specification at iteration $t$ |
| $G$ | Generator (hallucinator) |
| $V$ | Verifier |
| $R$ | Remediator |
| $\Phi$ | LUCID iteration operator: $\Phi = R \circ (V, G)$ |
| $\Delta_t$ | Specification gap at iteration $t$ |
| $F_{\text{LUCID}}$ | LUCID free energy |
| $v_i^{(t)}$ | Verification score of claim $i$ at iteration $t$ |
| $\pi(c_i)$ | Precision weight of claim $i$ |
| $\gamma$ | Contraction rate |
| $\beta$ | Regeneration novelty bound |
| $\eta_V$ | Verification noise |
| $H(S_t)$ | Specification entropy |
