# LUCID

**Leveraging Unverified Claims Into Deliverables**

A development methodology that treats AI hallucination as a requirements generator, not a defect.

---

## The Problem LUCID Solves

Every AI development workflow treats hallucination as the enemy. Spec-Driven Development writes precise specs to prevent it. Prompt engineering constrains it. Guardrails filter it out.

But hallucination is just the AI confidently describing something that doesn't exist yet. That's also what a product specification does.

## The Insight

When you ask an AI to write Terms of Service for an application that doesn't exist, it doesn't say "this application doesn't exist." It confabulates. It invents specific capabilities, data handling procedures, user rights, performance guarantees, and limitations — all in the authoritative, precise language that legal documents demand.

Every one of those hallucinated claims is a testable requirement.

## How LUCID Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  1. DESCRIBE     │────▶│  2. HALLUCINATE   │────▶│  3. EXTRACT     │
│  Loose idea of   │     │  AI writes ToS /  │     │  Each claim     │
│  the application │     │  usage policy as  │     │  becomes a      │
│                  │     │  if app is live    │     │  requirement    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐              │
│  5. CONVERGE     │◀────│  4. BUILD        │◀─────────────┘
│  Compare ToS     │     │  Implement until │
│  claims against  │     │  code satisfies  │
│  actual reality  │     │  the claims      │
└────────┬────────┘     └──────────────────┘
         │
         │  Gap found?
         │  ↓ YES: Loop back to step 4
         │  ↓ NO: ToS and reality match
         │
    ┌────▼────────────┐
    │  6. REGENERATE   │
    │  New ToS from    │
    │  updated state   │──── Loop back to step 3
    │  (may hallucinate│
    │  new features)   │
    └─────────────────┘
```

### The Cycle in Detail

1. **DESCRIBE** — Give the AI a loose, conversational description of what the application should do. Don't over-specify. Leave room for the AI to fill gaps.

2. **HALLUCINATE** — Ask the AI to write a Terms of Service and Usage Policy as if the application is already live in production. The AI will confabulate specific capabilities, limitations, data handling, SLAs, and edge cases it has no knowledge of. This is the point.

3. **EXTRACT** — Parse every declarative statement from the ToS into a testable requirement. "The Service processes up to 10,000 records per batch" becomes a performance requirement. "User data is encrypted at rest" becomes a security requirement.

4. **BUILD** — Implement the application to satisfy the extracted requirements. Use any development methodology for this phase (TDD, agile, etc.). The ToS is the acceptance criteria.

5. **CONVERGE** — Compare the ToS claims against the actual application. For each claim, determine: does reality match? Record gaps.

6. **REGENERATE** — Feed the updated application state back to the AI and generate a new ToS. The AI may hallucinate additional features or refine existing claims. New claims become new requirements. The loop continues.

### Exit Condition

The loop terminates when the delta between hallucinated ToS and verified reality reaches an acceptable threshold — defined by the team, not the AI.

## Why Terms of Service?

ToS is the ideal hallucination vehicle because the format naturally demands:

| ToS Section | Produces |
|-------------|----------|
| Service Description | Feature requirements |
| Acceptable Use | Input validation rules |
| Data Handling | Privacy & security requirements |
| Limitations | Performance boundaries |
| SLA / Uptime | Reliability requirements |
| Termination | Account lifecycle requirements |
| Liability | Error handling requirements |
| Modifications | Versioning requirements |

No other document format forces this level of specificity across this many dimensions simultaneously.

## Prior Art

LUCID occupies a previously empty intersection. Related but distinct concepts:

| Concept | Relationship to LUCID |
|---------|----------------------|
| **Protein Hallucination** (Baker, Nobel 2024) | Same core insight — hallucinated outputs as blueprints — applied to biology, not software |
| **Design Fiction** (Sterling, 2005) | Fictional artifacts guide real development, but fiction is human-authored, not AI-hallucinated |
| **Spec-Driven Development** (GitHub, 2025) | Spec-first, but designed to *prevent* hallucination. LUCID inverts this |
| **Readme-Driven Development** (Preston-Werner, 2010) | Write docs before code, but no AI, no hallucination, no convergence loop |

See [docs/prior-art.md](docs/prior-art.md) for detailed analysis.

## Principles

1. **Hallucination is signal, not noise.** The AI's confabulations reveal what a plausible version of the application looks like.
2. **Legal language enforces precision.** ToS can't be vague. "The Service may do things" isn't a valid legal clause. The format forces specificity.
3. **The gap is the backlog.** The difference between what the ToS claims and what the code does is your task list.
4. **Reality is the only test.** A claim is satisfied when verified against running code, not when code is written.
5. **The loop is the methodology.** LUCID isn't a one-shot generation. It's an iterative convergence between fiction and reality.

## Getting Started

See [docs/methodology.md](docs/methodology.md) for the full methodology guide.

## License

MIT
