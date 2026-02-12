# Platform Outreach Emails — LUCID Verification API

> **ALL EMAILS ARE DRAFTS — DO NOT SEND WITHOUT HUMAN APPROVAL**
>
> These are personalized outreach templates based on benchmark data.
> Each requires review, personalization, and explicit approval before sending.
>
> **Prepared:** 2026-02-11
> **Revised:** 2026-02-11 (v3 — partnership framing, verified claims only)
> **By:** LUCID Team

---

## Benchmark Summary

| Platform | Sample | Score | Key Patterns |
|----------|--------|-------|-------------|
| Cursor | Not yet benchmarked | — | — |
| Bolt.new | 1 public repo (437 files) | 42/100 | Broken config bootstrap, IDOR, missing auth implementations |
| Lovable | 2 public repos (152 + 86 files) | 42/100 | Unprotected admin routes, missing error boundaries, iframe sandbox disabled |
| Replit | 1 public repo (275 files) | 32/100 | 9 critical bugs: fake analytics, missing API endpoints, non-functional features |

**LUCID baseline:** 100% HumanEval pass rate (k=3), +36.4% on SWE-bench vs baseline.

**Data source:** Real-world codebases from public GitHub repos, identified as platform-built via tooling fingerprints (`.bolt/`, `lovable-tagger`, `.replit`). These reflect what users ship with each platform — not necessarily the platform's raw output. Full methodology in report.

**Provenance note:** These are user-built applications, not controlled tests of each platform's generation. Some bugs may have been introduced post-generation. That's precisely the point — users need verification regardless of where bugs originate.

---

## Contact Sheet

| Platform | Name | Title | Email | Confidence |
|----------|------|-------|-------|------------|
| Cursor | Sualeh Asif | CPO / Co-founder | sualeh@cursor.so | High (100% use first@cursor.so) |
| Cursor | Aman Sanger | COO / Co-founder | aman@cursor.so | High |
| Cursor | Michael Truell | CEO | michael@cursor.so | High |
| Bolt.new | Albert Pai | CTO / Co-founder | albert@stackblitz.com | High (76% use first@stackblitz.com) |
| Bolt.new | Eric Simons | CEO | eric@stackblitz.com | High |
| Lovable | Fabian Hedin | CTO / Co-founder | fabian@lovable.dev | High (pattern from RocketReach) |
| Lovable | Anton Osika | CEO | anton@lovable.dev | High |
| Replit | Michele Catasta | President / Head of AI | michele@replit.com | High (70% use first@replit.com) |
| Replit | Amjad Masad | CEO | amjad@replit.com | High |

**Recommended primary targets** (technical leadership, not CEO):
- Cursor → Sualeh Asif (CPO) — note: former CTO Arvid Lunnemark left Oct 2025
- Bolt.new → Albert Pai (CTO)
- Lovable → Fabian Hedin (CTO)
- Replit → Michele Catasta (President/Head of AI, ex-Google Labs/Stanford)

**Email sources:** Company email patterns from RocketReach. Not confirmed deliverable — consider validation before sending.

---

## 1. Cursor

**To:** Sualeh Asif, CPO — sualeh@cursor.so
**CC (optional):** Aman Sanger, COO — aman@cursor.so
**DRAFT — REQUIRES HUMAN APPROVAL BEFORE SENDING**

**Subject line options:**
1. Helping Cursor users ship verified code — benchmark data
2. Code quality data on AI-generated code (Cursor not yet included)
3. Benchmark invitation: AI code verification study

**Body:**

Hi Sualeh,

We've been running formal verification on code that users build with AI coding platforms — testing what actually ships to production for security vulnerabilities, correctness, and production readiness.

Across platforms, we're finding a consistent pattern: AI-generated code compiles and looks right, but has structural issues that traditional tooling misses — unprotected admin routes, missing API endpoints, scaffolding that looks like features but doesn't function. Average health score across the apps we've analyzed: 39/100.

We haven't included Cursor-assisted code yet. Given your focus on professional developer workflows, we'd expect a different profile — and we'd like to find out.

Our verification system (LUCID) uses formal methods, not LLM-based review. On HumanEval it achieves 100% correctness at k=3 iterations, compared to 87% for self-refine approaches. Peer-reviewed methodology: DOI 10.5281/zenodo.18522644.

**Would you be open to a collaborative benchmark?** We'd run Cursor-assisted code through our verification pipeline and share the full results with your team before any publication. If Cursor users ship cleaner code (which we'd expect), that's a powerful differentiator for you.

Published benchmark report: https://trylucid.dev/report
API documentation: https://trylucid.dev/docs
Research paper: https://doi.org/10.5281/zenodo.18522644

Best,
Ty Wells

**Personalization notes for sender:**
- Sualeh Asif is CPO, Aman Sanger is COO — both co-founders from MIT
- Former CTO Arvid Lunnemark left Oct 2025 to start Integrous Research (safety lab)
- Anysphere valued at ~$29.3B (Jan 2026) — they're the market leader
- Cursor is developer-facing (not no-code), so framing around "professional workflows" resonates
- Reference any recent Cursor blog posts about code quality or AI accuracy
- Check if Cursor has published their own benchmarks — acknowledge them

---

## 2. Bolt.new (StackBlitz)

**To:** Albert Pai, CTO — albert@stackblitz.com
**CC (optional):** Eric Simons, CEO — eric@stackblitz.com
**DRAFT — REQUIRES HUMAN APPROVAL BEFORE SENDING**

**Subject line options:**
1. What Bolt.new users are shipping to production — verification data
2. Helping Bolt.new users catch structural bugs before deploy
3. Free verification pipeline for Bolt.new users — research findings

**Body:**

Hi Albert,

We've been running formal verification on code that users build with AI coding platforms — not to grade the platforms, but to understand what's actually shipping to production.

We analyzed a healthcare scheduling app built with Bolt.new (identified by `.bolt/` directory, 437 source files, public GitHub repo). It scored 42/100 on our production-readiness analysis. The bugs we found aren't about code style — they're structural issues that compilers and linters can't catch:

1. **Broken config bootstrap** — `ensureRuntimeSupabaseConfig` is never called before the React app renders, so all Supabase API calls fail with undefined URL/keys. The app is non-functional out of the box.
2. **IDOR vulnerability** — any therapist can view any other therapist's data by navigating to `/therapists/:therapistId`. RoleGuard checks the role but never verifies ownership. In healthcare, that's a HIPAA risk.
3. **Auto-scheduler crashes on edge case** — if any client lacks an active program, the entire scheduling operation throws instead of skipping gracefully.
4. **Auth components referenced but missing** — `RoleGuard` and `PrivateRoute` are used throughout routing but their implementations aren't in the codebase.

To be clear: we can't know which of these bugs came from Bolt.new's generation vs. user modifications afterward. That's actually the point — **users need a verification layer regardless of where bugs originate**, and that layer doesn't exist in most workflows today.

On the positive side: the app had solid query configuration, accessibility testing, and good UX patterns. The gap is between "code that looks right" and "code that works right" — and that's exactly what formal verification closes.

Our system (LUCID) achieves 100% HumanEval pass rate (k=3) and +36.4% on SWE-bench. US patent pending (App #63/980,048). It can run as a post-generation verification step — catching these issues before users deploy.

**Would you be interested in a collaborative benchmark?** We'd generate fresh apps on Bolt.new, run them through our pipeline, and share full results with your team. If you're already working on code quality internally, we'd love to compare approaches.

Full report: https://trylucid.dev/report
API docs: https://trylucid.dev/docs
Research: https://doi.org/10.5281/zenodo.18522644

Best,
Ty Wells

**Personalization notes for sender:**
- Albert Pai is CTO and co-founder of StackBlitz (since 2017)
- Eric Simons is CEO — CC him if you want founder-level visibility
- Reference StackBlitz's WebContainer technology and developer trust positioning
- Bolt.new grew from near-death to ~$40M ARR in 5 months
- "We can't know which bugs came from generation vs. user" preempts their main objection
- The collaborative benchmark offer lets them control the narrative — they'll want to show good results
- Healthcare/HIPAA angle is compelling because it shows real-world consequences for their users

---

## 3. Lovable

**To:** Fabian Hedin, CTO — fabian@lovable.dev
**CC (optional):** Anton Osika, CEO — anton@lovable.dev
**DRAFT — REQUIRES HUMAN APPROVAL BEFORE SENDING**

**Subject line options:**
1. What Lovable users are shipping — formal verification findings
2. Code quality as a differentiator — verification data from Lovable-built apps
3. Helping Lovable users ship production-ready code

**Body:**

Hi Fabian,

Congratulations on the recent raise. As you scale, code quality becomes a differentiator — and we have data that might be useful.

We've been running formal verification on code that users build with AI coding platforms, analyzing real-world apps from public GitHub repos. We looked at two Lovable-built codebases (identified by `lovable-tagger` in package.json) — a brand monitoring SaaS (152 files) and an AI agent interface (86 files). Both scored 42/100 on production readiness.

The patterns we found across both apps:

From the brand monitoring app:
1. **Admin routes with no auth guards** — all `/admin/*` routes (users, monitoring, configuration, tools) are defined with zero authentication. Any user can navigate directly to admin panels.
2. **Supabase client config unverifiable** — imported from `@/integrations/supabase/client` but implementation not in the codebase. If RLS is misconfigured or a service key is used client-side, all data is exposed.
3. **Critical missing implementations** — `AppErrorBoundary` and `createApiUrl()` are imported throughout the app but never defined. If either is absent, the app white-screens on errors or all admin API calls silently fail.

From the AI agent interface:
4. **iframe sandbox disabled** — allows arbitrary script execution in embedded content.
5. **Path traversal protection is client-side only** — bypassable via direct API calls.

We can't attribute these bugs specifically to Lovable's generation vs. user edits — and that's actually the insight. **Your users need a verification step between "it builds" and "it's production-ready,"** and that step doesn't exist today. Whoever provides it first wins the quality reputation.

Across all platforms we've tested, Lovable-built apps are tied for the highest score (42/100 vs. 32/100 for Replit-built). You're already ahead — formal verification could widen that gap.

LUCID achieves 100% HumanEval correctness (k=3), +36.4% on SWE-bench. US patent pending (App #63/980,048). It can integrate as a post-generation verification layer.

**Would you be interested in a collaborative benchmark?** We'd generate fresh apps on Lovable, run them through our pipeline, and share results with your team first. If quality is a competitive advantage for you, this is the data to prove it.

Report: https://trylucid.dev/report
API: https://trylucid.dev/docs
Research: https://doi.org/10.5281/zenodo.18522644

Best,
Ty Wells

**Personalization notes for sender:**
- Fabian Hedin is CTO and co-founder (Stockholm-based, ex-SpaceX engineers collab, built Stephen Hawking's communication interface)
- Anton Osika is CEO (ex-CTO of Depict.ai, ex-Sana Labs)
- Lovable raised $200M Series A at $1.8B valuation (led by Accel) — NOT $7M anymore
- Hit $100M ARR in under a year — one of fastest-growing startups in history
- Won "AI Swede" award with Fabian — they're proud of the Swedish angle
- "Tied for highest score" positions them as winning — they want to maintain that
- "Whoever provides it first wins" creates urgency without attacking their product
- Admin route finding is the strongest hook — it's unambiguous and serious

---

## 4. Replit

**To:** Michele Catasta, President / Head of AI — michele@replit.com
**CC (optional):** Amjad Masad, CEO — amjad@replit.com
**DRAFT — REQUIRES HUMAN APPROVAL BEFORE SENDING**

**Subject line options:**
1. The verification gap in deploy-from-IDE workflows — research data
2. What Replit users are shipping to production — formal verification findings
3. Formal verification for the Agent era — collaborative research proposal

**Body:**

Hi Michele,

Replit Agent changes the deployment model — users generate and deploy from the same environment, often without a separate code review step. That makes the gap between "it builds" and "it works" a more urgent problem than it is in traditional workflows.

We've been running formal verification on code that users build with AI coding platforms. A Replit-built computer vision app (275 files, identified by `.replit` config, public GitHub repo) scored 32/100 on production readiness — with 9 critical bugs. The patterns are worth examining:

**Non-existent backends:**
- Scene analysis calls `/ai/analyze-scene` and translation calls `/ai/translate` — neither endpoint exists. Both features silently fall back to mock data, so the app *appears* to work while core functionality is fake.

**Scaffolding that looks like features:**
- Analytics dashboard renders professional charts labeled "Real-time insights" — backed entirely by hardcoded static arrays. The `useEffect` just calls `setLoading(false)`. No API calls, no real data.
- 5 of 6 accessibility features trigger "coming soon" alerts. Voice, camera, and file input buttons have no `onPress` handlers — they're purely decorative UI.

**Data that never persists:**
- User profile stored in `useState` with hardcoded defaults (`name: 'John Doe'`). Settings changes update local state only — lost on every restart.

**And the README claims "Platform Status: FULLY OPERATIONAL."**

We can't know which of these issues came from Agent's generation vs. user modifications — that's inherent to analyzing shipped code. But the pattern itself is the finding: **AI-generated code that compiles and looks polished can have fundamentally broken functionality that no linter, type checker, or visual review will catch.**

This is what we call the verification gap, and it matters most in deploy-from-IDE workflows where there's no separate review step. Formal verification closes it.

Our system (LUCID) achieves 100% HumanEval (k=3) and +36.4% on SWE-bench using formal methods, not LLM-based review. US patent pending (App #63/980,048).

**Would you be interested in a collaborative study?** Given your academic background, I think there's a research angle here — the verification gap in AI-assisted development is an open problem. We'd generate fresh apps with Replit Agent, run formal verification, and share results with your team. If you're already working on output quality internally, we'd welcome comparing approaches.

Report: https://trylucid.dev/report
API: https://trylucid.dev/docs
Research: https://doi.org/10.5281/zenodo.18522644

Best,
Ty Wells

**Personalization notes for sender:**
- Michele Catasta is President & Head of AI — ex-Google Labs (Head of Applied Research), ex-Google X, Stanford PhD + AI instructor
- He wrote the Replit AI Manifesto — reference it to show you've done your homework
- Amjad Masad is CEO — valued at $3B (Jan 2026), YC alum
- "Collaborative study" framing appeals to Michele's academic instincts
- "Deploy-from-IDE" is Replit's differentiator — frame verification as essential to that model, not a criticism of it
- The "README says FULLY OPERATIONAL" detail demonstrates the problem viscerally
- Don't compare scores to other platforms in this email — 32 is the lowest and comparing would feel like ranking
- Replit has strong community — co-publishing could be mutually beneficial

---

## Follow-up Sequence (All Platforms)

If no response after 5 business days:

**Subject:** Re: [original subject] — happy to share raw data

**Body (template):**

Hi [First Name],

Quick follow-up on the verification data I shared. Happy to send the raw results for your team to review independently — full claim-by-claim analysis with code references.

We're also building platform integrations — an API that can run post-generation to catch structural issues before users deploy. Early docs at https://trylucid.dev/docs.

No pressure — just wanted to make sure the data reached the right person.

Best,
Ty Wells

---

## Sending Checklist

Before sending any email:

- [ ] Human has reviewed and approved the specific email
- [ ] Recipient name and email confirmed (verify emails are deliverable)
- [ ] Recent company news referenced where applicable
- [ ] Tone reviewed — partnership pitch, not adversarial audit
- [ ] All links verified as live (trylucid.dev/report, /docs, DOI)
- [ ] No LUCID implementation details or trade secrets included
- [ ] Subject line selected (pick one of three options)
- [ ] Provenance framing checked — says "users built with" not "platform produced"
- [ ] Sending from ty@trylucid.dev (not personal email)
