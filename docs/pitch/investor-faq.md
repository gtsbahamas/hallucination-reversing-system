# LUCID: Investor FAQ

*Anticipated questions and answers for seed-stage conversations.*

---

### 1. "Why hasn't DeepMind already done this? They have AlphaProof, AlphaEvolve, and Gemini --- all the pieces."

DeepMind has the components but not the synthesis, for three reasons:

**Organizational incentives.** Google sells AI models. Admitting that hallucination is mathematically permanent --- and building an architecture that treats it as a feature --- undermines the product narrative that each new model is "more reliable." LUCID's thesis is contrarian to the business model of every large AI lab.

**Research silos.** At DeepMind, AlphaProof (formal verification), AlphaEvolve (evolutionary generation), and Gemini (language models) are separate teams with separate research agendas. The neuroscience group (including Friston collaborators) operates independently. Nobody has the mandate to unify these into a single architecture. That is exactly what LUCID does.

**The hallucination-as-feature step is career risk.** Proposing that hallucination should be *increased* and *harnessed* at a company spending billions to suppress it is a career-limiting move. This is a classic innovator's dilemma: the insight is structurally inaccessible to incumbents. Startups like VERSES ($2B), Sakana ($2.65B), and Liquid AI ($2B) exist precisely because big labs cannot take these architectural bets.

That said, DeepMind is a real competitive threat. Our strategy is to establish theoretical priority through publication and build the compliance business (EU AI Act) before any large lab recognizes the opportunity.

---

### 2. "Can one person / a small team actually build this?"

Yes, and precedent supports it:

- **Sakana AI** raised $479M at $2.65B valuation with a small team and a research paper (Darwin Godel Machine). The DGM paper preceded the product.
- **Liquid AI** raised $297M at $2B valuation with a team of 5 researchers from MIT. The liquid neural networks paper preceded the company.
- **VERSES AI** reached $2B valuation building on Karl Friston's academic work with a lean research team.

LUCID follows the same playbook: publish the theoretical framework, demonstrate a working prototype, and raise capital to scale. The prototype already exists. The DOI is published. The architecture paper is in progress. The seed round funds the team buildout --- not the initial research.

For the near-term compliance product, the engineering is tractable: LUCID wraps existing LLM APIs with a verification layer. We are not training foundation models. We are building the meta-architecture that makes any foundation model more reliable.

---

### 3. "Formal verification only works for code and math. How does this generalize?"

This is the most important technical question. Here is the honest answer:

**Today:** LUCID's formal verification works on code (type checking, test execution, static analysis) and mathematics (proof assistants like Lean 4). These are well-defined domains with decidable properties. The current product operates here.

**Near-term extension (12-18 months):** Logical consistency checking for natural language claims. If an AI system generates a document that says "revenue increased 15% to $12M" and separately states "revenue was $10M last year," formal logic can detect the inconsistency (15% of $10M is $11.5M, not $12M). This extends verification to structured business documents, regulatory filings, and technical documentation without requiring full semantic understanding.

**Medium-term extension (2-3 years):** Simulation-based verification for physical systems. If an AI generates a robot control policy, we can verify it in simulation against safety specifications. This is formal verification of behavior, not just code.

**The key insight:** We do not need to verify *everything* formally. We need to verify *enough* to be useful. In code, "enough" is type correctness and test passage. In compliance, "enough" is logical consistency and regulatory checklist satisfaction. The specification boundary expands over time, but even the current boundary covers a $20B+ market.

**What we cannot verify:** Subjective qualities like "is this essay well-written?" or "is this response empathetic?" These remain in the domain of learned reward models and human judgment. LUCID is not a universal solution. It is a formal verification layer for domains where formal specifications exist or can be constructed.

---

### 4. "How does this make money? What's the business model?"

Three revenue streams, staged by timeline:

**Stream 1: Compliance SaaS ($99-249/mo) --- Revenue starts Q3 2026**
- EU AI Act enforcement begins August 2, 2026
- Every company deploying AI in the EU needs conformity documentation
- LUCID generates formal verification audit trails automatically
- TAM: $13.4B by 2028 (46% CAGR)
- Unit economics: $99/mo Team, $249/mo Organization
- Target: 500 paying teams in Year 1 = ~$600K ARR

**Stream 2: Developer Tools ($99-249/mo) --- Revenue starts Q4 2026**
- AI code generation market is $7B+ by 2028
- 45% of AI-generated code fails security tests (vibe coding crisis)
- LUCID is the only tool that verifies what AI-built software actually does vs. claims
- Distribution: npm package, GitHub Action, CI/CD integration
- Target: 2,000 paying teams in Year 2 = ~$2.4M ARR

**Stream 3: Consulting / Enterprise ($2K-15K/engagement) --- Revenue starts Q2 2026**
- High-touch engagements for enterprises with immediate compliance deadlines
- Bridges to SaaS product adoption
- Validates product-market fit through direct customer interaction
- Target: 20 engagements in Year 1 = ~$100K

**Combined Year 2 target:** $3M+ ARR, positioning for Series A at 10-15x multiple.

---

### 5. "What's the defensibility? What stops someone from copying this?"

Five layers of defensibility:

**1. Theoretical priority.** LUCID is the first system to formally connect hallucination impossibility proofs, predictive processing neuroscience, and practical engineering into a unified framework. The DOI is published (10.5281/zenodo.18522644). The architecture paper establishes priority. In AI, theoretical priority matters --- it attracts researchers, citations, and talent.

**2. The data moat.** Every LUCID scan generates specification-gap data: what AI gets wrong, how it fails, and how failures cluster by domain, model, and task type. This data is unique (nobody else is collecting it) and compounds (each scan makes the remediation engine smarter). After 100K scans, we will have the most comprehensive dataset of AI failure modes in existence.

**3. Inverse positioning.** Copying LUCID requires admitting that hallucination is permanent and should be harnessed. For companies that sell AI models on the promise of "less hallucination," this is a messaging impossibility. They cannot say "our model still hallucinates, so here's a tool to make that productive" without undermining their core value proposition.

**4. Formal verification expertise.** The intersection of formal methods, ML, and neuroscience is a very small talent pool. Building a competing system requires hiring from all three communities. We plan to lock up key talent early.

**5. Compliance lock-in.** Once a company uses LUCID for EU AI Act compliance, switching costs are high: audit trails, verification records, and regulatory documentation are all format-specific. First-mover in compliance creates switching costs.

---

### 6. "The impossibility proofs --- are they actually rigorous? Could they be wrong?"

The proofs are peer-reviewed and published in major venues:

**Xu et al. (2024)** has accumulated 453+ citations in under two years. The proof is based on computational learning theory and shows that any computable LLM will hallucinate on some inputs from any non-trivial distribution. The result has been acknowledged by OpenAI.

**Banerjee et al. (2024)** extends this to show that the set of inputs on which an LLM hallucinates is not even identifiable --- you cannot build a detector that reliably distinguishes hallucinated from factual outputs.

**Karpowicz (2025)** provides the strongest result, proving via the Log-Sum-Exp convexity structure of softmax attention that hallucination and creativity are mathematically inseparable in transformer architectures.

**Could they be wrong?** The mathematical proofs are formally valid within their assumptions. The assumptions could be challenged:
- They assume specific definitions of hallucination
- They assume LLMs operate as statistical models over finite training distributions
- A fundamentally different architecture (non-transformer, non-statistical) might circumvent them

However, the three proofs use different proof techniques and different formalizations, and reach the same conclusion. This convergence from independent methods is strong evidence that the result is robust, not an artifact of a particular formalization.

**Our position is not contingent on the proofs being absolute.** Even if hallucination could theoretically be reduced to near-zero, the practical reality is that it has not been --- despite billions of dollars of effort. LUCID works regardless of whether hallucination elimination is theoretically impossible or merely practically impossible.

---

### 7. "What about the verifier problem? What verifies the verifier?"

This is the deepest objection, and LUCID has the cleanest answer of any system.

**The infinite regress:** If a verifier checks the generator's output, who checks the verifier? If a meta-verifier checks the verifier, who checks the meta-verifier? This regress is real and unsolvable in general.

**LUCID's solution: formal verification terminates the regress.** A formal verifier does not "judge" whether output is correct. It mechanically checks whether the output satisfies a formal specification. Type checkers, test suites, proof assistants, and static analyzers are *deterministic* --- given the same input and specification, they always produce the same result. There is no learned component that could drift, hallucinate, or be gamed.

**The remaining question:** "Who verifies the specification?" This is a genuine limitation. The specification must be written or generated correctly. LUCID's Extract stage generates specifications from AI output, introducing a potential failure mode. However:

1. Extracted specifications are *more conservative* than the original output (they capture only verifiable claims), so specification errors tend toward false negatives (missing claims) rather than false positives (incorrect claims).
2. Specifications are human-readable and auditable. An incorrect specification is visible in a way that an incorrect learned model is not.
3. Specifications accumulate and can be version-controlled, reviewed, and improved over time.

The verifier regress is solved for the verification step. The specification generation step is where human oversight and iterative improvement apply. This is a dramatically better position than any system where the verifier itself is a black-box neural network.

---

### 8. "How is this different from Tessl? They raised $125M for spec-driven development."

Tessl and LUCID are philosophically *inverse* --- and that distinction matters:

**Tessl's approach (top-down):** Start with formal specifications written by humans. Generate code that satisfies those specifications. The specification is the *input*; the code is the *output*.

**LUCID's approach (bottom-up):** Let AI generate code freely (hallucinate). Extract implicit specifications from the generated code. Verify the code against those specifications. Use the gap to improve. The hallucination is the *input*; the specification is the *output*.

**Why LUCID's direction is more powerful:**

1. **Specification generation is the bottleneck.** Writing formal specs is hard, expensive, and requires specialized expertise. LUCID generates specs automatically from AI output. Tessl requires humans to write them upfront.

2. **Tessl assumes the spec is correct.** If the human-written spec has a bug, Tessl generates buggy code that satisfies a buggy spec. LUCID's iterative loop catches specification errors because the generate-verify cycle exposes inconsistencies.

3. **Tessl fights hallucination; LUCID harnesses it.** Tessl constrains generation to satisfy specs. LUCID lets generation run free and uses verification to select the best outputs. The unconstrained approach explores a larger solution space, which is why AlphaEvolve (unconstrained generation + verification) outperforms constrained synthesis.

4. **Market position.** Tessl's $750M valuation validates the market for AI verification tools. LUCID occupies the complementary position: bottom-up specification generation rather than top-down specification enforcement.

---

### 9. "What if a big lab just adds a verification layer to their models?"

This is likely to happen, and it *validates* LUCID rather than threatening it:

**Scenario 1: They add verification as a feature.** This proves the market exists and the approach works. LUCID's advantage is being model-agnostic --- it works with *any* generator. A lab-specific verification layer only works with that lab's models.

**Scenario 2: They adopt the full LUCID framework.** This requires admitting hallucination is permanent and productive. The messaging cost is enormous for companies selling "safer, less hallucinatory" models. It is the equivalent of a tobacco company launching an anti-smoking campaign.

**Scenario 3: They acquire LUCID.** This is a positive outcome for investors. Architecture companies with theoretical priority command premium acquisition multiples (Google acquired DeepMind for $500M when it had zero revenue; the theoretical priority in reinforcement learning was the asset).

**Our strategy:** Establish theoretical priority through publication, build the data moat through usage, and create switching costs through compliance integration. By the time a big lab recognizes the opportunity, LUCID should have the published framework, the proprietary data, and the compliance customer base.

---

### 10. "What's the technical risk? What could go wrong?"

We assess five principal risks:

**Risk 1: Formal verification does not generalize beyond code/math.**
*Likelihood: Medium. Impact: Limits TAM but does not kill the business.*
Mitigation: The code + compliance market alone is $20B+. If LUCID never extends beyond code, it is still a large business. Generalization to new domains is upside, not the base case.

**Risk 2: Generate-verify loops are too slow for real-time applications.**
*Likelihood: Low-Medium. Impact: Limits use cases.*
Mitigation: Most LUCID use cases (code review, compliance auditing, specification generation) are not real-time. For CI/CD integration, median 2-3 iteration convergence is acceptable. Inference-time scaling research is actively reducing this.

**Risk 3: A big lab unifies the components first.**
*Likelihood: Medium. Impact: High if pre-publication, low if post-publication.*
Mitigation: Publication establishes theoretical priority. The DOI is already registered. The architecture paper will be submitted to a top-tier venue. In AI, publishing first matters enormously for talent attraction and credibility.

**Risk 4: The specification-generation step introduces errors that compound.**
*Likelihood: Low-Medium. Impact: Medium.*
Mitigation: Specifications are human-readable and auditable. The iterative loop catches specification errors over multiple cycles. Empirically, specification quality improves with iterations (convergence at 90.8%).

**Risk 5: Market timing --- EU AI Act enforcement is delayed or weakened.**
*Likelihood: Low (legislation is passed; enforcement date is set). Impact: Delays near-term revenue.*
Mitigation: Compliance is one of three revenue streams. Developer tools and consulting operate independently of regulatory timelines.

---

### 11. "Why should we believe a solo founder can compete with billion-dollar labs?"

Because this is not a compute competition. It is a *framing* competition.

The billion-dollar labs have more compute, more data, and more engineers than LUCID ever will. They also have a massive blind spot: they are organizationally committed to hallucination suppression. They cannot pivot to "hallucination is a feature" without undermining their product narrative, confusing their customers, and reversing years of safety messaging.

**LUCID competes on insight, not infrastructure.** The value is in the theoretical framework (free energy minimization explains why generate-verify works), the architectural design (formal verification as the verifier, not learned models), and the positioning (hallucination-as-feature).

**Historical precedent:**
- Attention is All You Need (2017) was written by 8 people at Google Brain. It created the transformer architecture that powers every major AI system. The insight was worth more than any amount of compute.
- VERSES AI ($2B valuation) is built on Karl Friston's academic papers. The theoretical framework IS the product.
- Sakana AI ($2.65B valuation) was founded by two researchers with a paper about evolutionary self-improvement.

In AI architecture, the team that articulates the right framework first wins disproportionately. LUCID's bet is that "hallucination as computational primitive" is the right framework.

---

### 12. "What does the team look like at scale?"

**Immediate hires (seed round, 5-7 people):**

| Role | Why | Profile |
|------|-----|---------|
| Formal Methods Lead | Scale the verification engine | PhD in PL/FM, industry experience with proof assistants or static analysis |
| ML Engineer (2) | Generator optimization, benchmark infrastructure | Strong engineering, experience with LLM inference and evaluation |
| Neuroscience Advisor | Validate and extend the predictive processing mapping | Active researcher in computational neuroscience, ideally connected to Friston/Seth community |
| Product Engineer | Build the compliance and developer tools products | Full-stack, experience with developer tools or compliance software |
| Go-to-Market Lead | Enterprise sales for EU AI Act compliance | B2B SaaS sales experience, ideally in compliance/governance tooling |

**Key advisor targets:**
- Karl Friston (UCL/VERSES) --- theoretical advisor
- Beren Millidge --- predictive coding scaling advisor
- Someone from the Lean 4 / formal verification community

**Series A team expansion (12-18 people):** Additional ML engineers, formal methods researchers, sales, and customer success for enterprise compliance contracts.

---

### 13. "What are the unit economics?"

**SaaS (Team plan, $99/mo):**
- COGS: ~$15/mo (LLM API calls per scan, compute for verification)
- Gross margin: ~85%
- CAC target: $500 (developer tool marketing, content, conference presence)
- LTV (24-month avg): $2,376
- LTV:CAC ratio: 4.75x

**SaaS (Organization plan, $249/mo):**
- COGS: ~$40/mo (higher scan volume)
- Gross margin: ~84%
- CAC target: $1,500 (enterprise marketing, sales-assisted)
- LTV (24-month avg): $5,976
- LTV:CAC ratio: 3.98x

**Consulting ($2K-15K/engagement):**
- COGS: Founder time (pre-team), then engineer time at ~$200/hr loaded
- Gross margin: ~70%
- No CAC (inbound from content + compliance urgency)

**Blended target at $3M ARR:** 75% gross margin, LTV:CAC > 4x.

*Note: LLM API costs are falling rapidly (60%+ YoY declines). COGS will decrease over time while pricing holds.*

---

### 14. "What's your ask, and what do investors get?"

**Ask:** $5-8M seed round.

**Terms:** Standard seed-stage preferred equity. Target 15-20% dilution.

**What investors get:**
1. Ownership in the company that formalized "hallucination as computational primitive" --- a paradigm shift with a published, citable, DOI-backed theoretical framework.
2. Near-term revenue catalyst (EU AI Act, August 2026) that de-risks the timeline to Series A.
3. Optionality across three outcomes:
   - **Base case:** $10-50M ARR compliance/dev tools company (3-5x at Series A)
   - **Growth case:** Architecture platform adopted broadly ($100M+ ARR, 10x+ at Series A)
   - **Moonshot case:** LUCID-as-architecture becomes the next paradigm (VERSES/Sakana-class $1B+ outcome)
4. A contrarian bet that is *structurally inaccessible* to incumbents due to their commitment to hallucination suppression.

**Use of funds:** 50% team, 30% product, 15% research, 5% operations.

**18-month milestones:**
- Enterprise compliance product live (Q2 2026)
- Architecture paper published in top venue (Q3 2026)
- $1M ARR from compliance + dev tools (Q4 2026)
- Scaling experiments demonstrating verification-loop superiority (Q1 2027)
- Series A at $30-50M valuation (Q2 2027)
