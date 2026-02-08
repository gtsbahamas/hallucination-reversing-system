# I Built a Tool That Treats AI Hallucination as a Feature -- Here's Why It Works

Everyone working with LLMs has the same goal: make them stop making stuff up.

RAG. Chain-of-thought. Guardrails. Constitutional AI. Fine-tuning on curated datasets. Billions of dollars in research, all aimed at one objective: suppress hallucination.

I went the other direction. I built a tool that deliberately triggers hallucination, harvests the output, and uses it to generate comprehensive software specifications. It works disturbingly well. And the neuroscience explains why.

## The trick that started it

Ask an LLM to write a Terms of Service for an application that doesn't exist.

Don't tell it the app doesn't exist. Just say: "Write a Terms of Service and Acceptable Use Policy for [app description], as if it's live in production with paying customers. Write as the company's legal team."

The model doesn't blink. It confabulates. It invents specific capabilities, data handling procedures, user rights, performance guarantees, rate limits, encryption standards, data retention policies, SLA commitments, and account lifecycle rules -- all in the precise, declarative language that legal documents demand.

Here's the thing: legal language can't be vague. "The Service may do things" is not a valid legal clause. So the format forces the model to hallucinate *precisely*. You get 400-600 lines of dense, specific, testable claims about an application that does not yet exist.

Every one of those claims is a requirement.

## Why this isn't as crazy as it sounds

Two independent formal proofs published in 2024 (Xu et al. and Banerjee et al.) established that hallucination is mathematically inevitable in LLMs. Not "hard to fix." Inevitable. Any model that generalizes beyond its training data will sometimes generate outputs inconsistent with ground truth. Banerjee reached the same conclusion through Godel's Incompleteness Theorem.

If hallucination can't be eliminated, maybe we should stop trying to eliminate it and start figuring out how to use it.

This isn't a new idea. It's exactly what David Baker's lab did with proteins.

## The protein hallucination parallel

In 2021, Baker's lab at the University of Washington published a paper in Nature describing how they used a neural network called trRosetta to "hallucinate" novel protein structures. They started with random amino acid sequences, ran them through the network's gradient-based optimization, and generated structures that don't exist in nature -- proteins the network "dreamed up."

Then they synthesized them in bacteria. The hallucinated structures matched predictions closely. The proteins were real and functional.

This methodology -- neural network dreams as engineering blueprints -- produced roughly 100 patents, spawned 20+ biotech companies, and won the 2024 Nobel Prize in Chemistry.

LUCID applies the same principle to software. The LLM dreams up a specification. Verification against the real codebase filters fantasy from reality. Iteration converges the dream toward something you can ship.

## "We're all hallucinating all the time"

That's Anil Seth, professor of cognitive and computational neuroscience at Sussex. His point, grounded in the predictive processing framework (Friston, Clark, Hohwy), is that perception itself is a controlled hallucination. Your brain doesn't passively receive reality. It generates top-down predictions about what it expects to perceive and only propagates the *error signal* -- the surprise, the part it got wrong.

When those predictions are well-constrained by sensory data, you call it perception. When they're unconstrained, you call it hallucination. Same machinery, different amount of constraint.

Ramsauer et al. (2020) proved that transformer self-attention is mathematically equivalent to the update rule of Hopfield networks -- associative memory systems that retrieve stored patterns from partial cues. This is pattern completion: the same computation the hippocampus performs when reconstructing a memory from a fragment. Some of what it reconstructs is accurate. Some is gap-filling confabulation.

When an LLM generates a Terms of Service for a nonexistent app, it's pattern-completing from partial cues (your prompt) against representations (training data from millions of real ToS documents, codebases, and documentation). The output isn't random. It's informed extrapolation -- what a plausible application in this domain *tends* to look like, based on the statistical regularities the model has encoded.

That's useful. Extremely useful. If you verify it.

## The tool: LUCID

LUCID stands for Leveraging Unverified Claims Into Deliverables. It's a CLI built in TypeScript that implements a six-phase loop:

**Describe** -- Give it a loose description of your app. Don't over-specify. The gaps are where the model does its best work.

**Hallucinate** -- The model writes a ToS as if the app is live. This produces 80-150 extractable claims.

**Extract** -- Each declarative statement becomes a structured claim with an ID, category (security, functionality, data-privacy, operational, legal), severity level, and testability flag.

**Build** -- Implement code. Use whatever methodology you want. The extracted claims are your acceptance criteria.

**Converge** -- Verify every claim against the actual codebase. Each gets a verdict: PASS, PARTIAL, FAIL, or N/A.

**Regenerate** -- Feed verified reality back to the model. It writes an updated ToS that retains what's real, revises what's partial, and hallucinates new capabilities grounded in what actually exists now.

Then loop.

### Using it

```bash
# Install
git clone https://github.com/gtsbahamas/hallucination-reversing-system
cd hallucination-reversing-system
npm install && npm run build

# Initialize in your project
lucid init

# Generate hallucinated Terms of Service
lucid hallucinate

# Extract testable claims
lucid extract

# Verify claims against your codebase
lucid verify

# See what's real and what's not
lucid report

# Generate fix tasks for gaps
lucid remediate

# Feed reality back, get updated spec
lucid regenerate
```

Each iteration's artifacts go into `.lucid/iterations/{N}/`, so you have a full audit trail of how the specification evolved.

## The convergence data

I ran LUCID against a production Next.js application -- roughly 30,000 lines of TypeScript across 200+ files. Career platform with AI coaching, financial planning, goal tracking, document management.

| Iteration | Compliance Score | PASS | PARTIAL | FAIL |
|-----------|-----------------|------|---------|------|
| 3         | 57.3%           | 38   | 15      | 32   |
| 4         | 69.8%           | 47   | 18      | 20   |
| 5         | 83.2%           | 61   | 15      | 9    |
| 6         | 90.8%           | 68   | 12      | 5    |

57.3% to 90.8% across six iterations. Total API cost: approximately $17.

The five remaining failures at iteration 6 were all legitimate gaps: no weekly job data refresh, no subscription downgrade retention logic, no malware scanning on file uploads, no server-side rate limiting, and wrong account lockout parameters. Every one of them is a real thing the app should have. The hallucinated spec correctly identified requirements that a human product manager might have missed entirely.

The gap between hallucination and reality *is* the backlog. And it's a surprisingly good one.

## The lucid dreaming connection

The name isn't just a backronym. Lucid dreaming is when you become aware you're dreaming without waking up. You gain metacognitive control -- you can steer the dream, reality-test within it, harvest creative content -- while staying in the generative state.

That's exactly what LUCID does with LLM hallucination. It doesn't try to wake the model up. It doesn't try to suppress the dream. It gains awareness (the Extract phase turns claims into *hypotheses* rather than facts), reality-tests (verification against the codebase), and steers (regeneration constrains future hallucinations with verified reality).

The neuroscience research on lucid dreaming (Baird et al., 2019; Filevich et al., 2015) shows that the key event is reactivation of the dorsolateral prefrontal cortex -- the seat of executive function and reality monitoring. In ordinary dreaming, it's suppressed. In lucid dreaming, it comes back online.

LLMs are pure dreaming. They have no prefrontal cortex, no reality monitor, no executive function. LUCID provides one externally. The convergence loop *is* the deliberate, checking function that the model lacks.

## The deeper point

LUCID isn't a hallucination reduction technique. It's a specification extraction technique that uses hallucination as its input signal.

No human requirements-gathering process produces 91 testable claims spanning functionality, security, data privacy, performance, operations, and legal compliance in 30 seconds. The hallucination does. The convergence loop then refines this raw material into something you can actually build against.

As models get better, the initial hallucination quality improves. If the first pass starts at 80% compliance instead of 35%, you converge faster. At the limit -- good enough model, fast enough verification -- this approaches single-iteration specification generation. The verification step never goes away, because that's what makes the output trustworthy. But the loop compresses.

The formal impossibility results tell us hallucination isn't going away. The Nobel Prize in protein design tells us hallucination-as-blueprint works across domains. The neuroscience tells us that the generative process underlying hallucination and perception is the same -- the only difference is how much reality constrains it.

LUCID adds the constraint.

---

The code is on GitHub: [github.com/gtsbahamas/hallucination-reversing-system](https://github.com/gtsbahamas/hallucination-reversing-system)

A full academic paper covering the theoretical foundations, neuroscience grounding, and empirical results is available: [DOI: 10.5281/zenodo.18522644](https://doi.org/10.5281/zenodo.18522644).

If you have a codebase and an Anthropic API key, you can run it right now. I'd be curious what compliance score your app gets on the first pass -- it tells you more about your codebase than you might expect.
