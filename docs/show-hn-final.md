# Show HN Final Submission

**Title:** Show HN: LUCID – Catch hallucinations in AI-generated code before they ship

**URL:** https://github.com/gtsbahamas/hallucination-reversing-system

---

## Submission Body

Hi HN, I'm Ty. I built LUCID because I kept shipping bugs that my AI coding assistant hallucinated into existence.

Three independent papers have proven that LLM hallucination is mathematically inevitable (Xu et al. 2024, Banerjee et al. 2024, Karpowicz 2025). You can't train it away. You can't prompt it away. So I built a verification layer instead.

**How it works:** LUCID extracts implicit claims from AI-generated code (e.g., "this function handles null input," "this query is injection-safe," "this handles concurrent access"), then uses a second, adversarial AI pass to verify each claim against the actual implementation. You get a report showing exactly what would have shipped to production without verification.

**"But can't the verifier hallucinate too?"** Yes — and that's the right question. The benchmarks below were validated by running real test suites, not by trusting LUCID's judgment. The value is that structured claim extraction + adversarial verification catches bugs that a single generation pass misses. The architecture also supports swapping LLM verification for formal methods (SMT solvers, property-based testing) per claim type as those integrations mature.

**Benchmarks:**

- HumanEval: 86.6% baseline → 100% pass@5 with LUCID (164/164 problems)
- SWE-bench: 18.3% baseline → 30.3% with LUCID (+65.5%)
- Both benchmarks were validated by running actual test suites, not by LLM judgment
- LLM-as-judge actually performs worse at higher k values — it hallucinates false positives

**Three ways to use it:**

1. **MCP Server** (Claude Code, Cursor, Windsurf) — one config line, verification as a native tool:
   ```json
   { "mcpServers": { "lucid": { "command": "npx", "args": ["-y", "lucid-mcp"], "env": { "LUCID_API_KEY": "your_key" } } } }
   ```

2. **GitHub Action** — automated verification on every PR with inline comments

3. **CLI** — `npx lucid verify --repo /path/to/code`

Free tier: 100 verifications/month. Get a key at https://trylucid.dev

The neuroscience angle: LUCID is based on predictive processing (Friston, Seth). Hallucination and perception are the same generative process under different constraint levels. LUCID deliberately operates unconstrained during generation, then progressively constrains through verification — just as the brain does. The name comes from lucid dreaming: maintaining metacognitive awareness while remaining inside the generative process.

Curious what HN thinks about the approach. The conventional wisdom is to suppress hallucination. We think that's fighting thermodynamics. And yes, we know the verifier is also an LLM — the roadmap includes plugging in real formal methods for specific claim types. The structured claim extraction is the foundation that makes that possible.

Code: https://github.com/gtsbahamas/hallucination-reversing-system
Paper: https://doi.org/10.5281/zenodo.18522644
Dashboard: https://trylucid.dev

---

## Submission Checklist

### Timing
- [ ] **Best days:** Tuesday-Thursday
- [ ] **Best time:** 7-9am Pacific (10am-12pm Eastern)
- [ ] **Avoid:** Friday afternoons, weekends, major holidays
- [ ] **Check:** Not during major tech news events (Apple events, OpenAI launches)

### Pre-Submission
- [ ] Test all links (GitHub, Zenodo, trylucid.dev)
- [ ] Verify free tier signup works
- [ ] Ensure README has clear quick-start
- [ ] Check that trylucid.dev loads in <2s
- [ ] Have responses ready for common questions (see below)

### During Submission
- [ ] Submit between 7-9am PT
- [ ] Monitor first 30 minutes closely
- [ ] Respond to ALL comments within first hour
- [ ] Keep responses technical, humble, curious
- [ ] Don't argue, acknowledge limitations
- [ ] Link to paper/benchmarks when appropriate

### Response Strategy
- **Tone:** Curious, technical, humble
- **Length:** Match the question (short Q = short A)
- **Links:** Always provide evidence for claims
- **Acknowledge:** "That's a great point" before addressing
- **No marketing:** Focus on technical merit, not sales

---

## Pre-Written Responses to Common Questions

### "Can't the verifier hallucinate too?"

Yes — this is the core tension in the design. Here's how we handle it:

1. **Different failure modes:** The generator optimizes for coherence. The verifier optimizes for finding contradictions. These are orthogonal objectives, so they tend to fail differently.

2. **Empirical validation:** We validated the benchmarks by running real test suites (HumanEval's assert statements, SWE-bench's actual tests), not by trusting LUCID's judgment. The 100% pass@5 on HumanEval means the code actually passed the tests, not that LUCID said it would.

3. **Roadmap:** The architecture is designed to swap LLM verification for formal methods per claim type. For "this SQL query has no injection vulnerabilities," we can route to a SQL parser. For "this function terminates," we can route to a termination checker. The value of the current implementation is proving that structured claim extraction works — the verifier is the part we plan to replace.

The real question is: does adversarial LLM verification catch more bugs than single-pass generation? The benchmarks say yes. Is it perfect? No. But it's measurably better.

---

### "What's the false positive rate?"

We report two types of false positives:

**1. Verification false positives** (claims LUCID flags as bugs that aren't):
- On HumanEval: We don't measure this directly, but the 100% pass@5 suggests it's not rejecting correct code in the top 5 candidates.
- On SWE-bench: We didn't measure this separately — we only counted whether the final patch passed the actual tests.

**2. Generation false positives** (code that looks right but fails tests):
- Baseline k=1: 13.4% on HumanEval (142/164 pass)
- LUCID k=1: 1.2% on HumanEval (162/164 pass)

The second metric is more meaningful for practical use: "How often does the first solution actually work?" LUCID's rate is 10x better.

We should add explicit false positive tracking in the next version of the benchmark. Thanks for the question — it's a real gap in the current data.

---

### "How is this different from static analysis?"

Static analysis checks code against syntactic or type rules. LUCID checks code against *semantic claims* about what the code is supposed to do.

**Static analyzer:** "This variable might be undefined"
**LUCID:** "The docstring says this handles null input, but the implementation doesn't check for null"

**Static analyzer:** "This function could throw"
**LUCID:** "The code claims this is idempotent, but it increments a counter on every call"

**Static analyzer:** "Type error"
**LUCID:** "The function signature says it returns sorted output, but the implementation doesn't sort"

Static analysis is grammar. LUCID is interpretation. They're complementary — you should use both.

---

### "What does it cost?"

**Free tier:** 100 verifications/month

**Paid tiers:**
- Individual: $29/month (1,000 verifications)
- Team: $99/month (10,000 verifications)
- Enterprise: Custom pricing

**Per-call cost (if you BYOK with Anthropic API):**
- ~$0.05-0.10 per file verification (depends on file size)
- HumanEval benchmark cost: ~$220 for 820 verifications (164 problems × 5 attempts)
- SWE-bench cost: ~$246 for 300 tasks

The GitHub Action has a built-in triage layer (Haiku filter) that only runs full verification on files flagged as high-risk, which cuts costs by ~80% in typical PR workflows.

---

### "Why not just write better tests?"

You should! LUCID doesn't replace tests. But:

**1. Tests are written by the same person/AI that wrote the code** — they share blind spots. LUCID uses an adversarial second pass to find bugs the first pass missed.

**2. Tests are expensive to write** — especially for LLM-generated code, where the human doesn't deeply understand the implementation. LUCID generates verification claims automatically from the code itself.

**3. Tests don't catch semantic bugs** — a function can pass all its tests and still violate its documented behavior. LUCID extracts claims from comments, docstrings, and type signatures, then verifies the implementation matches.

**4. The SWE-bench results prove this empirically** — these are real-world bugs from open-source projects that *already had tests*. The tests didn't catch the bugs. LUCID's verification did.

Think of LUCID as "test-driven development where the tests write themselves from the spec."

---

### "What about the neuroscience framing? Isn't that just marketing?"

Fair question. The neuroscience framing does two things:

**1. Explains why hallucination is inevitable** — Predictive processing theory (Karl Friston, Anil Seth) says perception is controlled hallucination. The brain generates predictions, then constrains them with sensory input. LLMs are generative models without the constraint step. Hallucination isn't a bug, it's the architecture.

**2. Justifies the two-pass design** — Instead of trying to suppress generation (which breaks creativity), LUCID lets the generator run unconstrained, then adds the constraint pass separately. This mirrors how the brain works: generate freely, then verify.

Is it necessary? No. The benchmarks stand on their own. But it's a useful mental model for why verification should be a separate pass, not baked into generation.

The name "LUCID" comes from lucid dreaming: maintaining metacognitive awareness (verification) while remaining inside the generative process. It's a mnemonic, not a scientific claim.

If the framing feels like marketing, ignore it. The technical result is: adversarial verification catches more bugs than single-pass generation.

---

## Follow-Up Resources

If specific questions come up that need deep dives, link to:

- **Full benchmark results:** https://trylucid.dev/report
- **Paper (formal proofs):** https://doi.org/10.5281/zenodo.18522644
- **GitHub (implementation):** https://github.com/gtsbahamas/hallucination-reversing-system
- **HumanEval raw data:** `results/humaneval-final/` in repo
- **SWE-bench raw data:** `results/swebench-v2/` in repo

---

## Engagement Strategy

**First 30 minutes:**
- Respond to every comment
- Acknowledge critiques before defending
- Provide evidence (links) for claims
- Ask clarifying questions

**First 2 hours:**
- Prioritize technical questions over praise
- Admit gaps in data (e.g., false positive tracking)
- Offer to run follow-up experiments if suggested

**After initial wave:**
- Continue monitoring for 24 hours
- Respond to substantive critiques
- Update README/docs based on feedback
- Note feature requests for roadmap

**If negative:**
- Don't argue with "this won't work" comments
- Focus on "here's what we measured" responses
- Acknowledge limitations honestly
- Link to benchmarks for verification

**If positive:**
- Thank people for trying it
- Ask what use case they're testing
- Solicit feedback on pain points
- Note feature requests

---

## Post-Submission Tasks

Within 24 hours:
- [ ] Update README based on top questions
- [ ] Add FAQ section if common patterns emerge
- [ ] Fix any bugs reported in comments
- [ ] Update roadmap based on feature requests

Within 1 week:
- [ ] Write blog post summarizing feedback
- [ ] Address top 3 limitations mentioned
- [ ] Add metrics for gaps identified (e.g., false positive rate)
- [ ] Submit to relevant subreddits if HN goes well

---

## Success Metrics

- **Comments:** >50 substantive comments
- **Stars:** >100 GitHub stars in 24h
- **Signups:** >50 trylucid.dev signups
- **Coverage:** Picked up by AI/dev newsletters
- **Quality:** At least 3 technical critiques that improve the project

---

## Failure Recovery

If submission doesn't gain traction (< 10 upvotes in first hour):

- **Don't resubmit immediately** (wait 1 week minimum)
- **Revise title** — make it more specific or remove jargon
- **Shorten body** — HN favors concise posts
- **Lead with benchmarks** — move numbers higher
- **Remove neuroscience framing** — if it's distracting

If submission gets negative feedback:

- **Don't defend** — acknowledge and ask clarifying questions
- **Extract signal** — what technical critiques are valid?
- **Update docs** — fix gaps before next attempt
- **Consider pivot** — if core premise is rejected, reassess

---

## Final Checklist Before Hitting Submit

- [ ] Title is <80 characters
- [ ] URL is live and loads fast
- [ ] All links work
- [ ] Benchmarks are clearly stated
- [ ] Free tier is available
- [ ] GitHub README is polished
- [ ] Responses to top 6 questions are ready
- [ ] Monitoring notifications are on
- [ ] Coffee is ready (you'll be responding for hours)

Good luck.
