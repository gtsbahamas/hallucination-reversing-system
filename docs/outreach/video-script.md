# LUCID Demo Video Script (60-90 seconds)

> **DRAFT — DO NOT PRODUCE WITHOUT HUMAN APPROVAL**
> Target: Product Hunt, landing page, social media
> Prepared: 2026-02-11

---

## Format

- Screen recording with voiceover
- No face cam needed (optional)
- Clean dark-theme editor/terminal
- Upbeat but not hype-y background music (low volume)

---

## Script

### HOOK (0-5 sec)

**[VISUAL: Split screen. Left: polished app UI with "Real-Time Analytics" dashboard showing beautiful charts. Right: the source code — a static array of hardcoded numbers.]**

**VO:** "This app says 'real-time analytics.' The data is hardcoded."

---

### THE PROBLEM (5-20 sec)

**[VISUAL: Quick montage — 3 code snippets, each showing a different broken pattern:]**
1. Admin route with no auth guard
2. `onClick={() => {}}` (button that does nothing)
3. Frontend calling `/api/analyze` — cut to backend with no matching route

**VO:** "AI coding tools generate code that compiles, looks professional, and passes every linter. But when you dig in — admin routes with no auth. Buttons wired to nothing. APIs that don't exist. We tested 4 real AI-built apps. Average health score: 40 out of 100."

---

### WHAT LUCID DOES (20-45 sec)

**[VISUAL: Terminal. Run `lucid verify ./my-app`. Output streams:]**

```
Extracting claims... 34 claims found
  - "Admin route requires authentication"
  - "User data persists to database"
  - "Analytics shows real-time data"
  ...

Verifying claims...
  [PASS] React component renders todo list
  [PASS] Delete handler removes items
  [FAIL] Admin route has no auth guard
  [FAIL] Analytics data is hardcoded static array
  [FAIL] /api/analyze endpoint does not exist

Health score: 42/100
3 critical issues found. Generating fix plans...
```

**VO:** "LUCID extracts every testable claim from your code. Then it verifies each one using adversarial AI-based verification — a second AI trained to break code, not rubber-stamp it. It finds the bugs that compilers, linters, and code review miss. Then it tells you exactly how to fix them."

---

### THE PROOF (45-65 sec)

**[VISUAL: The "killer chart" — bar chart showing HumanEval results across 4 conditions. LUCID bar reaches 100%. Animate the bars growing.]**

**VO:** "On HumanEval — 164 standard coding tasks — baseline AI gets 87%. Self-refine barely moves it. LLM-as-judge starts strong but actually *regresses* with more iterations."

**[VISUAL: Highlight the LUCID bar hitting 100%]**

**VO:** "LUCID hits 100% at three iterations. It's the only approach that gets better every time and never makes code worse."

**[VISUAL: Quick flash of SWE-bench results — "+65.5% improvement on 300 real-world bugs"]**

**VO:** "On real-world GitHub bugs: 65% improvement. Peer-reviewed. Patent pending."

---

### CTA (65-80 sec)

**[VISUAL: Terminal showing `npx lucid verify ./your-app` with the LUCID logo]**

**VO:** "Try it free. 100 verifications per month. Your AI code compiles — now prove it works."

**[VISUAL: URL appears: trylucid.dev]**

**[VISUAL: Below URL: "Full benchmark: trylucid.dev/report"]**

---

## Production Notes

- **Total runtime target:** 70-75 seconds
- **Pacing:** Fast cuts for the problem section. Slower, deliberate pacing for the verification demo.
- **The hook is everything.** If the first 5 seconds don't land, nothing else matters. The split screen of "what it claims" vs. "what the code says" is the visual that makes people stop scrolling.
- **Don't show the LUCID logo until the end.** Lead with the problem, not the brand.
- **The chart animation should feel like a mic drop.** All other bars stop short. LUCID reaches 100%.
- **Music:** Something like "Tech Corporate" from Artlist — clean, forward-moving, not dramatic. Drop it under the voiceover, bring it up slightly during transitions.
- **No text-to-speech.** Human voiceover only.

## Thumbnail Options

1. Split screen: polished UI / broken source code (same as hook visual)
2. Health score "40/100" in large red text, app screenshot in background
3. Terminal output with [FAIL] lines highlighted in red

## Where to Post

- Product Hunt listing (gallery video)
- Landing page (hero section, autoplay muted)
- Twitter/X (with captions, first 5 sec is the hook)
- LinkedIn (same as Twitter version)
- YouTube (full version with description linking to report)
