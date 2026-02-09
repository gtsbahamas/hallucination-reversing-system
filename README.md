<div align="center">

# LUCID

### Leveraging Unverified Claims Into Deliverables

**A development methodology that treats AI hallucination as a requirements generator, not a defect.**

*What if hallucination isn't a bug to suppress, but a specification engine to harness?*

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/gtsbahamas/hallucination-reversing-system?style=social)](https://github.com/gtsbahamas/hallucination-reversing-system/stargazers)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Paper](https://img.shields.io/badge/Paper-PDF-red?logo=arxiv)](arxiv-submission/main.pdf)
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18522644-blue)](https://doi.org/10.5281/zenodo.18522644)

[Website](https://gtsbahamas.github.io/hallucination-reversing-system/) | [Paper](docs/paper.md) | [Methodology Guide](docs/methodology.md) | [Prior Art](docs/prior-art.md) | [CLI Reference](#cli-reference)

</div>

---

## The Problem

Every AI development workflow treats hallucination as the enemy. Spec-Driven Development writes precise specs to prevent it. Prompt engineering constrains it. Guardrails filter it out.

But three independent formal proofs have established that **hallucination cannot be eliminated** from LLMs:

- **Xu et al. (2024)** -- learning theory proof that LLMs must hallucinate as general problem solvers
- **Banerjee et al. (2024)** -- Godel's Incompleteness Theorem applied to LLM architecture
- **Karpowicz (2025)** -- impossibility theorem via mechanism design and transformer analysis

If hallucination is mathematically inevitable, suppressing it is fighting thermodynamics. **LUCID harnesses it instead.**

## The Insight

When you ask an AI to write Terms of Service for an application that doesn't exist, it doesn't say "this application doesn't exist." It **confabulates**. It invents specific capabilities, data handling procedures, user rights, performance guarantees, and limitations -- all in the authoritative, precise language that legal documents demand.

Every one of those hallucinated claims is a **testable requirement**.

A single hallucinated ToS produces 80--150 testable claims spanning functionality, security, data privacy, performance, operations, and legal compliance. No human requirements-gathering process generates this breadth in 30 seconds.

---

## How LUCID Works

LUCID is a six-phase iterative cycle that converges hallucinated fiction toward verified reality:

```
                        THE LUCID CYCLE
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   ┌───────────┐    ┌──────────────┐    ┌──────────┐  │
    │   │ 1. DESCRIBE│───>│2. HALLUCINATE│───>│3. EXTRACT│  │
    │   │            │    │              │    │          │  │
    │   │ Loose idea │    │ AI writes    │    │ Each     │  │
    │   │ of the app │    │ ToS as if    │    │ claim =  │  │
    │   │            │    │ app is live  │    │ testable │  │
    │   └───────────┘    └──────────────┘    │ req      │  │
    │                                        └────┬─────┘  │
    │                                             │        │
    │   ┌────────────┐    ┌─────────────┐         │        │
    │   │5. CONVERGE │<───│  4. BUILD   │<────────┘        │
    │   │            │    │             │                   │
    │   │ Verify ToS │    │ Implement   │                   │
    │   │ vs reality │    │ until code  │                   │
    │   │            │    │ satisfies   │                   │
    │   └─────┬──────┘    └─────────────┘                   │
    │         │                                            │
    │    Gap found?                                        │
    │    YES ──> Fix ──> Re-verify                         │
    │    NO  ──> Continue                                  │
    │         │                                            │
    │   ┌─────v────────┐                                   │
    │   │6. REGENERATE │   Feed verified reality back.     │
    │   │              │   AI writes updated ToS.          │
    │   │ New ToS from │   New hallucinations = new reqs.  │
    │   │ updated state│────────────────────────────────────┘
    │   └──────────────┘   Loop to step 3
    │
    └── EXIT: Delta between ToS and reality is acceptable
```

### Phase Details

| Phase | What Happens | Output |
|-------|-------------|--------|
| **1. Describe** | Give the AI a loose, intentionally incomplete description. The gaps are where hallucination does its best work. | Seed description |
| **2. Hallucinate** | AI writes Terms of Service as if the app is live in production with paying customers. Legal language forces precision -- no hedging allowed. | 400--600 lines of dense legal text |
| **3. Extract** | Parse every declarative statement into a structured, testable claim with category, severity, and traceability back to the ToS clause. | 80--150 categorized claims |
| **4. Build** | Implement the application using any methodology (TDD, agile, etc.). The ToS-derived claims are the acceptance criteria. | Working code |
| **5. Converge** | Verify every claim against the actual codebase. Assign verdicts: PASS, PARTIAL, FAIL, or N/A. Generate a gap report. | Compliance score + gap report |
| **6. Regenerate** | Feed verified reality back to the AI. It writes an updated ToS -- keeping what's real, revising what's partial, and hallucinating new features. | Next iteration's specification |

### Convergence

With each iteration:
- The ratio of accurate-to-hallucinated claims increases
- New hallucinations become more contextually grounded
- The gap between spec and reality shrinks
- The application grows in directions the AI deems plausible for the domain

**Exit condition:** The team decides the delta is acceptable. This is a human judgment call, not an automated threshold.

---

## Empirical Results

LUCID was applied to a production Next.js application (~30,000 lines of TypeScript, 200+ files):

| Iteration | Compliance | PASS | PARTIAL | FAIL | N/A |
|-----------|-----------|------|---------|------|-----|
| 1 | ~35% (est.) | -- | -- | -- | -- |
| 3 | 57.3% | 38 | 15 | 32 | 6 |
| 4 | 69.8% | 47 | 18 | 20 | 6 |
| 5 | 83.2% | 61 | 15 | 9 | 6 |
| **6** | **90.8%** | **68** | **12** | **5** | **6** |

```
Compliance Over Iterations:

100% ┤
 90% ┤                                          ●  90.8%
 80% ┤                              ●  83.2%
 70% ┤                  ●  69.8%
 60% ┤      ●  57.3%
 50% ┤
 40% ┤
 35% ┤  ●  ~35%
     └──┬──────┬──────┬──────┬──────┬──────┬──
        1      2      3      4      5      6
                    Iteration
```

**Total cost for 6 iterations: ~$17 in API tokens.**

The 5 remaining FAIL claims after convergence were all **genuine missing functionality** -- not false positives. The hallucinated ToS correctly identified requirements a production app should have.

---

## Why Terms of Service?

ToS is the ideal hallucination vehicle because the document format forces specificity across every dimension of a software product simultaneously:

| ToS Section | Produces | Example Claim |
|-------------|----------|---------------|
| Service Description | Feature requirements | "The Service allows batch processing of up to 10,000 records" |
| Acceptable Use | Input validation rules | "Users may not upload files exceeding 50MB" |
| Data Handling | Privacy & security requirements | "User data is encrypted at rest using AES-256" |
| Limitations | Performance boundaries | "The Service supports up to 10,000 concurrent users" |
| SLA / Uptime | Reliability requirements | "The Service maintains 99.9% uptime" |
| Termination | Account lifecycle requirements | "Data is retained for 30 days post-deletion" |
| Liability | Error handling requirements | "Graceful degradation on third-party API failure" |
| Modifications | Versioning requirements | "Users are notified 30 days before changes" |

Legal language cannot be vague. *"The Service may do things"* is not a valid legal clause. The format forces the AI to hallucinate **precisely**.

---

## Quick Start

### Prerequisites

- Node.js 20+
- An [Anthropic API key](https://console.anthropic.com/) (Claude)

### Installation

```bash
# Clone the repository
git clone https://github.com/gtsbahamas/hallucination-reversing-system.git
cd hallucination-reversing-system

# Install dependencies
npm install

# Build the CLI
npm run build

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run Your First LUCID Cycle

```bash
# 1. Initialize a LUCID project
npx lucid init

# 2. Generate a hallucinated Terms of Service
npx lucid hallucinate

# 3. Extract testable claims from the hallucination
npx lucid extract

# 4. Verify claims against your codebase
npx lucid verify --repo /path/to/your/project

# 5. Generate a gap report
npx lucid report

# 6. Generate remediation tasks for gaps
npx lucid remediate --repo /path/to/your/project

# 7. After fixing gaps, regenerate for the next iteration
npx lucid regenerate
```

Each iteration stores artifacts in `.lucid/iterations/{N}/`, maintaining a complete audit trail.

---

## CLI Reference

| Command | Phase | Description |
|---------|-------|-------------|
| `lucid init` | Setup | Initialize project configuration (name, description, tech stack, audience) |
| `lucid hallucinate` | Phase 2 | Generate a hallucinated ToS/API docs/user manual from project config |
| `lucid describe` | Alt. input | Fetch an existing ToS from a URL (verify an existing product) |
| `lucid extract` | Phase 3 | Extract testable claims from a hallucinated or fetched document |
| `lucid verify` | Phase 5 | Verify extracted claims against a codebase |
| `lucid report` | Analysis | Generate a gap report from verification results |
| `lucid remediate` | Convergence | Generate code-level fix tasks from gaps |
| `lucid regenerate` | Phase 6 | Feed verified reality back, regenerate spec for next iteration |

### Options

```bash
lucid hallucinate --type tos|api-docs|user-manual   # Document type (default: tos)
lucid extract --iteration 3                          # Specify iteration (default: latest)
lucid extract --source my-tos.md                     # Extract from a file in .lucid/sources/
lucid verify --repo /path/to/code --iteration 3      # Verify specific iteration
lucid remediate --threshold 95                       # Set compliance target (default: 95%)
lucid regenerate --iteration 3                       # Regenerate from specific iteration
```

---

## Scoring Methodology

LUCID assigns four verdicts to each claim:

| Verdict | Meaning | Score Weight |
|---------|---------|-------------|
| **PASS** | Code fully implements the claim | 1.0 |
| **PARTIAL** | Code partially implements (some aspects missing) | 0.5 |
| **FAIL** | Code does not implement or contradicts the claim | 0.0 |
| **N/A** | Cannot be verified from code (e.g., legal-only claims) | Excluded |

**Compliance score:**

```
Score = (PASS + 0.5 * PARTIAL) / (Total - N/A) * 100
```

Claims are categorized by type and severity:

| Category | Examples |
|----------|---------|
| `functionality` | Features, user workflows, UI components |
| `security` | Encryption, auth, access control |
| `data-privacy` | Data handling, retention, deletion |
| `operational` | Performance, uptime, monitoring |
| `legal` | Terms, disclaimers, compliance |

| Severity | Meaning |
|----------|---------|
| `critical` | Security breach or data loss if false |
| `high` | Core functionality broken if false |
| `medium` | Important but not showstopping |
| `low` | Nice-to-have or cosmetic |

---

## The Neuroscience Behind LUCID

LUCID is not an arbitrary methodology. It is grounded in three convergent lines of evidence from cognitive neuroscience:

### 1. Transformers = Hippocampal Pattern Completion

Ramsauer et al. (2020) proved that transformer self-attention is **mathematically equivalent** to the update rule of Hopfield networks -- the same associative memory computation performed by the hippocampal CA3 network. When an LLM generates text about a nonexistent app, it performs pattern completion from partial cues, filling gaps with plausible details. This is identical to how human memory reconstructs events -- some accurate, some confabulated.

### 2. Perception as Controlled Hallucination

The predictive processing framework (Friston, Clark, Seth) holds that the brain is a prediction machine. As Anil Seth states: *"We're all hallucinating all the time; when we agree about our hallucinations, we call it reality."* Hallucination and perception are the same generative process under different constraint levels. LUCID deliberately operates unconstrained during the Hallucinate phase, then progressively introduces constraint through Converge and Regenerate.

### 3. The REBUS Model (Relaxed Beliefs Under Psychedelics)

Carhart-Harris and Friston (2019) showed that psychedelics relax the brain's top-down constraints, enabling novel associations that rigid priors normally suppress. This maps directly to LLM temperature: higher temperature = more novel (and hallucination-prone) outputs. LUCID exploits this by generating freely at "high temperature," then constraining iteratively -- just as the brain reintegrates psychedelic insights under normal conditions.

### The Naming

LUCID is not just an acronym. It embodies **lucid dreaming** -- the state where a dreamer becomes metacognitively aware they are dreaming while remaining in the dream. A lucid dreamer does not fight the dream. They participate with awareness, harvesting creative content while maintaining the ability to distinguish generated from real. LUCID does exactly this to AI hallucination.

---

## How LUCID Differs From Traditional Approaches

| Approach | Hallucination Stance | Spec Source | Convergence Loop | Verification |
|----------|---------------------|-------------|------------------|-------------|
| **Spec-Driven Development** (GitHub, 2025) | Prevents | Human-written | No | Spec compliance |
| **Readme-Driven Development** (Preston-Werner, 2010) | N/A | Human-written | No | Manual |
| **Design Fiction** (Sterling, 2005) | Intentional (human) | Human fiction | Loose | Informal |
| **Vibe Coding** (Karpathy, 2025) | Tolerates | Human prompt | No | Ad hoc |
| **Protein Hallucination** (Baker, Nobel 2024) | Exploits | Neural network | Validate-only | Lab synthesis |
| **LUCID** | **Exploits** | **AI-hallucinated ToS** | **Yes** | **Codebase verification** |

LUCID is the only methodology that combines AI-generated specification, deliberate hallucination exploitation, and iterative convergence verification against a real codebase.

The closest analogue is David Baker's protein hallucination -- where neural network "dreams" serve as blueprints for novel biological structures. That insight earned the **2024 Nobel Prize in Chemistry**. LUCID applies the identical principle to software engineering.

---

## Real-World Application

LUCID was developed and dogfooded on production applications built by [FrankLabs](https://franklabs.io), including an event photography platform and an AI agent platform. The gap analysis from a real LUCID iteration looks like this:

```
Iteration 1: CrowdPics TV (112 claims extracted)
┌──────────────────────────────────┐
│  REAL          36  (32%)  ████   │
│  PARTIAL       13  (12%)  ██     │
│  HALLUCINATED  63  (56%)  ██████ │
└──────────────────────────────────┘

Each HALLUCINATED claim is a missing feature.
Each PARTIAL claim is incomplete work.
The gap IS the backlog.
```

After iterative remediation and regeneration, compliance converges toward 90%+. The remaining gaps are genuine missing functionality that serves as a prioritized development roadmap.

---

## Project Structure

```
hallucination-reversing-system/
├── src/                        # CLI source (TypeScript)
│   ├── cli.ts                  # Entry point (Commander.js)
│   ├── commands/               # One file per CLI command
│   │   ├── init.ts             # Project initialization
│   │   ├── hallucinate.ts      # ToS generation
│   │   ├── describe.ts         # Fetch existing ToS from URL
│   │   ├── extract.ts          # Claim extraction
│   │   ├── verify.ts           # Codebase verification
│   │   ├── report.ts           # Gap report generation
│   │   ├── remediate.ts        # Fix task generation
│   │   └── regenerate.ts       # Iterative regeneration
│   ├── lib/                    # Core modules
│   │   ├── anthropic.ts        # Claude SDK wrapper
│   │   ├── claim-extractor.ts  # Claim parsing logic
│   │   ├── code-verifier.ts    # Codebase verification engine
│   │   ├── codebase-indexer.ts # File tree indexing
│   │   ├── config.ts           # Project configuration
│   │   ├── prompts.ts          # LLM prompt templates
│   │   └── ...
│   └── types.ts                # Type definitions
├── docs/                       # Documentation
│   ├── paper.md                # Full research paper
│   ├── methodology.md          # Methodology guide
│   └── prior-art.md            # Prior art analysis
├── applications/               # Real-world LUCID applications
├── arxiv-submission/           # Academic paper (LaTeX + PDF)
├── chi-submission/             # CHI 2026 workshop submission
├── index.html                  # Landing page (GitHub Pages)
└── .lucid/                     # LUCID's own self-audit
    └── iterations/
        └── self-audit/         # LUCID audited against itself
```

---

## Publications

| Venue | Status | Link |
|-------|--------|------|
| **Zenodo** (peer-reviewed DOI) | Published | [10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644) |
| **arXiv** | Submitted | [arxiv-submission/main.pdf](arxiv-submission/main.pdf) |
| **CHI 2026 Workshop** | In progress | [chi-submission/](chi-submission/) |

---

## Token Economics

Running a full LUCID iteration is inexpensive:

| Phase | Input Tokens | Output Tokens | Cost (approx.) |
|-------|-------------|---------------|----------------|
| Hallucinate | ~2K | ~12K | $0.15 |
| Extract | ~15K | ~8K | $0.25 |
| Verify | ~80K | ~20K | $1.50 |
| Remediate | ~30K | ~15K | $0.60 |
| Regenerate | ~20K | ~12K | $0.40 |
| **Full iteration** | | | **~$2.90** |

A complete 6-iteration cycle that achieves 90%+ compliance costs approximately **$17 in API tokens** -- producing a verified specification with 91 claims, a gap report, and a prioritized remediation plan.

---

## Principles

1. **Hallucination is signal, not noise.** The AI's confabulations reveal what a plausible version of the application looks like.
2. **Legal language enforces precision.** ToS cannot be vague. The format forces the AI to hallucinate precisely.
3. **The gap is the backlog.** The difference between what the ToS claims and what the code does is your task list.
4. **Reality is the only test.** A claim is satisfied when verified against running code, not when code is written.
5. **The loop is the methodology.** LUCID is not one-shot generation. It is iterative convergence between fiction and reality.
6. **Verification requires external ground truth.** LLMs cannot self-correct without external feedback (Huang et al., ICLR 2024). The codebase is the ground truth.

---

## Contributing

Contributions are welcome. Areas where help is particularly valuable:

- **Multi-document hallucination** -- Extending beyond ToS to API docs, user manuals, privacy policies, and compliance certifications simultaneously
- **Formal verification integration** -- Replacing LLM-based verification with property-based testing, model checking, or static analysis for specific claim categories
- **CI/CD integration** -- Running LUCID in continuous integration pipelines for specification-drift detection
- **Language support** -- The CLI currently targets TypeScript/JavaScript codebases; other languages need codebase indexing adapters
- **Benchmarking** -- Comparing initial hallucination quality across different LLMs (Claude, GPT-4, Gemini, Llama)

### Development

```bash
git clone https://github.com/gtsbahamas/hallucination-reversing-system.git
cd hallucination-reversing-system
npm install
npm run dev    # Watch mode (TypeScript compilation)
npm run build  # Production build
```

---

## FAQ

**Q: Isn't this just "make stuff up and hope for the best"?**

No. The hallucination is the *input*, not the output. LUCID verifies every claim against the actual codebase. Unverified claims are surfaced as gaps. Nothing ships without evidence. The methodology is closer to the scientific method: hypothesize (hallucinate), test (verify), refine (regenerate).

**Q: Why not just write requirements manually?**

You can. But no human writes 91 testable requirements spanning functionality, security, data privacy, performance, operations, and legal compliance in 30 seconds. LUCID generates comprehensive first-draft specifications at machine speed, then converges them toward reality through verification.

**Q: Does this actually work in production?**

Yes. LUCID was developed while building production applications. The empirical results (57% to 91% compliance over 6 iterations) come from a real codebase with 30,000+ lines of TypeScript. The remaining gaps were genuine missing functionality, not false positives.

**Q: How is this different from vibe coding?**

Vibe coding tolerates hallucination in the *code*. LUCID exploits hallucination in the *specification* and then demands rigorous verification of the code against that specification. The verification loop is the critical difference -- vibe coding has no convergence mechanism.

**Q: What models does LUCID support?**

The CLI currently uses Anthropic's Claude via the official SDK. The architecture is model-agnostic -- any LLM capable of generating structured legal text and performing code analysis can be substituted.

---

## Citation

```bibtex
@article{wells2026lucid,
  title={LUCID: Leveraging Unverified Claims Into Deliverables},
  author={Wells, Ty},
  year={2026},
  doi={10.5281/zenodo.18522644},
  url={https://github.com/gtsbahamas/hallucination-reversing-system}
}
```

---

## License

[MIT](LICENSE) -- Use it, fork it, build on it.

---

<div align="center">

*"Normal specification is hallucination constrained by reality. LUCID is the first development methodology that uses this principle: generate freely, then constrain iteratively, just as the brain does."*

**Built by [FrankLabs](https://franklabs.io)**

</div>
