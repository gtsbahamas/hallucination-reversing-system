# Free Verification Audit — Template Post

> **DRAFT — DO NOT POST WITHOUT HUMAN APPROVAL**
> Adapt tone for the specific community. This is the base template.
> Prepared: 2026-02-11

---

## Short Version (for comments, replies, Twitter/X)

I'll verify your AI-built app for free. Send me a GitHub link and I'll run formal verification on it — you get a report showing which features actually work vs. which are scaffolding. Takes ~5 min. DM me or submit at https://trylucid.dev

---

## Full Version (for standalone posts)

### Title: Send me your AI-built app. I'll tell you what's actually broken.

I built a formal verification system for AI-generated code. It doesn't lint your code or check types — it checks whether your features actually *work*.

Does your auth actually block unauthorized users? Does your data persist, or is it local state that dies on refresh? Is your analytics dashboard showing real data, or hardcoded arrays?

I've been running it on public repos and finding an average health score of **40/100** across AI-built apps, with **21 critical bugs** in 4 codebases. The most common patterns:

- **API endpoints the frontend calls that don't exist** (the app shows "loading" forever or falls back to mock data)
- **Auth guards that are imported but never wired up** (any user can hit admin routes)
- **"Real-time" dashboards backed by static constants** (the charts look great, the data is fake)
- **Features that work in demo but not in production** (state management that doesn't persist)

### What you get

A verification report covering:

1. **Every testable claim** extracted from your codebase (e.g., "admin route requires authentication," "user data persists to database")
2. **Pass/fail status** for each claim with code references
3. **Fix plans** for every failure — specific files, functions, and changes needed
4. **Health score** (0-100) based on the ratio of verified vs. failing claims

### How to submit

1. **Public repo:** Drop a GitHub link in the comments or DM me
2. **Private repo:** Email the link to ty@trylucid.dev (I won't share your code)
3. **Specific concern:** Tell me what feature you're worried about and I'll focus there

### Turnaround

- Simple apps (< 50 files): same day
- Medium apps (50-200 files): 1-2 days
- Large apps (200+ files): 2-3 days

### What's in it for me

Honest answer: data. Every codebase I verify makes LUCID better. I'm building verification infrastructure for AI coding platforms and I need volume to prove the patterns hold across different tools, languages, and complexity levels. You get free bug-finding. I get validation data.

### Fine print

- Your code stays private. Results are shared only with you.
- I won't publish findings from your specific codebase without your permission.
- If I find security vulnerabilities, I'll flag them immediately and disclose responsibly.
- This is the actual tool, not a consultant reading your code. You get the same pipeline that achieved 100% on HumanEval and +65.5% on SWE-bench.

Full benchmark report: https://trylucid.dev/report
Research paper: https://doi.org/10.5281/zenodo.18522644
GitHub: https://github.com/gtsbahamas/hallucination-reversing-system

---

## Community-Specific Adaptations

### For dev-focused communities (HN, Reddit r/programming, Dev.to)

Lead with the technical findings. Mention the benchmark numbers. Offer the audit as "if you're curious how your code scores."

### For builder communities (Indie Hackers, Bolt/Lovable/Replit Discords)

Lead with the problem ("have you ever shipped something that looked done but wasn't?"). Frame the audit as helping them ship with confidence.

### For AI/ML communities (Reddit r/MachineLearning, AI Discord servers)

Lead with the research angle. Mention the LLM-judge regression finding (99.4% to 97.2% at k=5). Frame it as a systems result, not a product pitch.

### For security communities (Reddit r/netsec, security Discords)

Lead with the security findings (IDOR in healthcare app, unprotected admin routes, disabled iframe sandbox). Frame the audit as a security assessment.
