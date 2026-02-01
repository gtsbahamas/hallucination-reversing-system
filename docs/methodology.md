# LUCID Methodology Guide

**Leveraging Unverified Claims Into Deliverables**

---

## Overview

LUCID is a development methodology where AI hallucination drives requirements generation. Instead of fighting the AI's tendency to confabulate, LUCID exploits it — using hallucinated Terms of Service documents as the specification source for iterative application development.

---

## Phase 1: Seed

### Input
A loose, conversational description of the application. Deliberately incomplete. The gaps are where hallucination does its work.

### What to provide
- What problem the application solves
- Who uses it
- General domain (e.g., "a scheduling tool for freelancers")

### What NOT to provide
- Detailed feature lists
- Technical architecture
- Performance requirements
- Data handling specifics

The less you specify, the more the AI fills in. The AI's gap-filling is the raw material.

### Example Seed

> "An application that helps small restaurant owners manage their daily operations — orders, inventory, staff scheduling. Nothing fancy, just something that works."

---

## Phase 2: Hallucinate

### The Prompt

Ask the AI to write a Terms of Service and Acceptable Use Policy as if the application is live in production with paying customers. The AI should write as the company's legal team, not as a developer.

### Key instruction
The AI must NOT be told "make up features" or "be creative." It should believe (or act as if) the application exists. The hallucination must be organic — the AI filling gaps with plausible confabulations, not deliberately inventing.

### What the AI produces
A formal legal document containing specific, declarative claims about:
- What the Service does (features)
- What the Service does not do (limitations)
- How user data is handled (privacy/security)
- What users can and cannot do (validation rules)
- Service availability and performance (SLAs)
- Account lifecycle (creation, suspension, termination)
- Liability and disclaimers (error handling)
- Modification and versioning policies

### Why ToS specifically
1. **Legal documents cannot be vague.** "The Service may process data" is not a valid legal clause. The format demands "The Service processes up to X records of type Y within Z timeframe."
2. **ToS covers the full surface area.** Features, security, performance, data handling, edge cases, user rights — all in one document.
3. **The authoritative tone prevents hedging.** The AI won't say "the Service might support..." It will say "the Service supports..." Every statement is a commitment.

---

## Phase 3: Extract

### Parse claims into requirements

Read every declarative statement in the hallucinated ToS. Each one maps to a requirement category:

| ToS Statement | Requirement Type | Example |
|---------------|-----------------|---------|
| "The Service allows users to..." | Functional requirement | User can create, read, update, delete orders |
| "Data is encrypted using..." | Security requirement | AES-256 encryption at rest |
| "The Service supports up to..." | Performance requirement | 10,000 concurrent users |
| "Users may not..." | Input validation rule | No file uploads exceeding 50MB |
| "The Service maintains 99.9%..." | Reliability requirement | 99.9% uptime SLA |
| "Upon account termination..." | Lifecycle requirement | Data retained for 30 days post-deletion |
| "The Service is not liable for..." | Error handling requirement | Graceful degradation on third-party API failure |

### Output
A structured requirements document derived entirely from the hallucinated ToS. Each requirement traces back to a specific ToS clause.

---

## Phase 4: Build

### Implementation

Build the application to satisfy the extracted requirements. LUCID does not prescribe an implementation methodology — use TDD, agile, waterfall, or any approach. The ToS-derived requirements are the acceptance criteria.

### Tooling recommendation
An autonomous build loop (like Ralph) works well here:
1. Generate a PRD from the extracted requirements
2. Feed the PRD to an autonomous coding agent
3. Agent builds iteratively until requirements pass validation
4. Each requirement maps to a verifiable test

### What "satisfies" means
A requirement is satisfied when there is **verified evidence** that the running application does what the ToS claims. Not when code exists — when behavior is proven.

---

## Phase 5: Converge

### Gap analysis

Compare every ToS claim against verified application behavior:

| ToS Claim | Code Exists | Behavior Verified | Gap |
|-----------|------------|-------------------|-----|
| "Processes 10K records/batch" | Yes | Tested at 10K: passes | None |
| "Encrypted at rest with AES-256" | Yes | Verified encryption method | None |
| "Real-time notifications" | No | — | Feature missing |
| "99.9% uptime" | Partial | No monitoring in place | Monitoring needed |

### Gap categories
- **Missing feature** — ToS claims it, code doesn't have it
- **Partial implementation** — Code exists but doesn't fully satisfy the claim
- **Unverified** — Code exists but behavior hasn't been proven
- **Exceeds claim** — Code does more than the ToS claims (update ToS to match)

### Output
A gap report that becomes the next iteration's task list.

---

## Phase 6: Regenerate

### Feed back and re-hallucinate

Provide the AI with:
1. The current application state (what it actually does now)
2. The original ToS
3. The gap report

Ask the AI to write an updated Terms of Service for the application as it exists now — plus whatever new capabilities the AI hallucinates.

### What happens
- Previously hallucinated features that are now real will appear accurately in the new ToS
- The AI will hallucinate NEW features based on the evolved application
- Some original hallucinations may be dropped (the AI recognizes they don't fit)
- The new ToS becomes the next iteration's specification

### The convergence effect
With each iteration:
- The ratio of accurate-to-hallucinated claims increases
- New hallucinations become more contextually appropriate (built on real foundation)
- The application grows in directions the AI deems plausible for the domain
- The gap between ToS and reality shrinks

---

## Exit Condition

LUCID terminates when the team decides the delta between ToS claims and verified reality is acceptable. This is a human judgment call, not an automated threshold.

Possible exit criteria:
- All ToS claims verified against running code
- Remaining gaps are intentionally deferred (v2 features)
- New hallucinations in regenerated ToS are marginal (diminishing novelty)

---

## When to Use LUCID

| Scenario | LUCID fit |
|----------|-----------|
| Greenfield application, vague requirements | Strong fit |
| Exploring what an application "should" be | Strong fit |
| Solo developer or small team needing a comprehensive spec fast | Strong fit |
| Regulated industry needing ToS anyway | Strong fit — you get a real ToS as a byproduct |
| Well-defined requirements already exist | Weak fit — use SDD instead |
| Incremental feature addition to existing app | Weak fit — scope is too narrow |
| Performance optimization or refactoring | Not applicable |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| AI hallucinates impossible requirements | Gap analysis catches infeasible claims; team can reject |
| ToS becomes too ambitious | Scope each iteration; don't build everything in one pass |
| Hallucination quality degrades | Use strong models; provide clear application context |
| Legal team takes hallucinated ToS literally | Label all LUCID-generated ToS as drafts until verified |
| Convergence stalls | Set iteration limits; accept "good enough" |
