# STATEMENT OF WORK

## AI Code Quality Audit

---

**SOW Reference:** [SOW-YYYY-NNN]
**Date:** [DATE]
**Version:** 1.0

---

### PARTIES

**Provider:**
Ty Wells d/b/a LUCID
Email: tyclaude@snapperland.com
Patent: U.S. Provisional Application No. 63/980,048

**Client:**
[CLIENT LEGAL NAME]
Address: [CLIENT ADDRESS]
Contact: [CLIENT CONTACT NAME], [TITLE]
Email: [CLIENT CONTACT EMAIL]

---

## 1. ENGAGEMENT OVERVIEW

LUCID will perform an AI Code Quality Audit of Client's software repositories using its patent-pending formal verification methodology. The audit will assess the quality, correctness, and security of AI-generated code within Client's codebase and deliver a written report with findings and remediation recommendations.

This engagement is governed by the Mutual Non-Disclosure Agreement executed between the Parties dated [NDA DATE] (the "NDA"), which is incorporated by reference.

---

## 2. SERVICE TIER

**Selected Tier:** [SELECT ONE]

| Tier | Scope | Duration | Price | Deliverable |
|------|-------|----------|-------|-------------|
| Spotlight | 1 repository, top findings | 1-2 weeks | $[10,000-15,000] | 10-page report + findings call |
| Standard | 3-5 repositories, full analysis | 3-4 weeks | $[25,000-50,000] | Full audit report + remediation plan |
| Enterprise | Organization-wide, compliance-focused | 6-8 weeks | $[75,000-150,000] | Full report + EU AI Act mapping + quarterly retainer |

---

## 3. SCOPE OF WORK

### 3.1 Repositories in Scope

| # | Repository | Language(s) | Approximate Size | Notes |
|---|------------|-------------|------------------|-------|
| 1 | [REPO NAME / URL] | [LANGUAGES] | [LOC or FILES] | [NOTES] |
| 2 | [REPO NAME / URL] | [LANGUAGES] | [LOC or FILES] | [NOTES] |
| 3 | [REPO NAME / URL] | [LANGUAGES] | [LOC or FILES] | [NOTES] |

### 3.2 Audit Activities

LUCID will perform the following activities:

1. **AI Code Footprint Analysis** -- Identify and quantify the proportion of code that is AI-generated or AI-modified within each repository.

2. **Formal Verification** -- Apply the LUCID verification loop to assess semantic correctness of AI-generated code. This uses deterministic formal methods, not LLM-based review.

3. **Security Assessment** -- Identify AI-introduced security vulnerabilities, mapped to CWE identifiers and OWASP Top 10 categories where applicable.

4. **Hallucination Pattern Detection** -- Identify common AI hallucination patterns including:
   - Missing implementations behind functional-looking UI
   - Incorrect logic that compiles but produces wrong behavior
   - Mock or placeholder data in production code
   - Authentication and authorization bypasses

5. **Quality Scoring** -- Assign per-module and overall quality scores on a 0-100 scale.

6. **Remediation Roadmap** -- Prioritize findings by severity (Critical, High, Medium, Low) with estimated remediation effort. *(Standard and Enterprise tiers only)*

7. **EU AI Act Gap Analysis** -- Assess compliance readiness against EU AI Act Article 50 obligations including transparency, documentation, and human oversight requirements. *(Enterprise tier only)*

### 3.3 Out of Scope

The following activities are explicitly excluded unless added by written change order:

- Manual code refactoring or bug fixing
- Penetration testing or network security assessments
- Performance testing or load testing
- Infrastructure or cloud configuration review
- Training or workshops (available as separate engagement)
- Code that is not AI-generated (unless relevant to AI-generated code context)
- Repositories not listed in Section 3.1

---

## 4. TIMELINE AND MILESTONES

| Milestone | Target Date | Description |
|-----------|-------------|-------------|
| Kickoff | [DATE] | Kickoff call, repository access granted |
| Access Confirmed | [DATE + 2 BUSINESS DAYS] | LUCID confirms repository access and scope |
| Interim Update | [DATE + MID-POINT] | Progress update call (Standard/Enterprise only) |
| Draft Report | [DATE + DRAFT] | Draft report delivered for Client review |
| Client Feedback | [DATE + FEEDBACK] | Client provides comments on draft |
| Final Report | [DATE + FINAL] | Final report delivered |
| Findings Call | [DATE + CALL] | 60-minute call to walk through findings |

**Total Duration:** [1-2 / 3-4 / 6-8] weeks from kickoff date.

---

## 5. DELIVERABLES

| # | Deliverable | Format | Tier |
|---|-------------|--------|------|
| 1 | AI Code Quality Audit Report | PDF | All |
| 2 | Executive Summary (1 page) | PDF | All |
| 3 | Findings Call (60 minutes) | Video call | All |
| 4 | Prioritized Remediation Roadmap | PDF | Standard, Enterprise |
| 5 | Risk Heatmap (repos x severity) | PDF | Standard, Enterprise |
| 6 | EU AI Act Compliance Gap Analysis | PDF | Enterprise |
| 7 | Quarterly Review (first quarter) | Video call + PDF | Enterprise |

---

## 6. PRICING AND PAYMENT

### 6.1 Fees

| Item | Amount |
|------|--------|
| Audit Fee ([TIER] Tier) | $[AMOUNT] USD |
| **Total** | **$[AMOUNT] USD** |

### 6.2 Payment Schedule

| Payment | Amount | Due |
|---------|--------|-----|
| Deposit (50%) | $[AMOUNT / 2] USD | Upon execution of this SOW |
| Final Payment (50%) | $[AMOUNT / 2] USD | Upon delivery of Final Report |

### 6.3 Payment Terms

- Invoices are due within fifteen (15) calendar days of issuance.
- Payments shall be made by wire transfer or ACH to the account specified on the invoice.
- Late payments accrue interest at 1.5% per month or the maximum rate permitted by law, whichever is less.
- If Client disputes an invoice in good faith, Client shall pay the undisputed portion and notify Provider in writing within ten (10) days of invoice date.

---

## 7. CLIENT RESPONSIBILITIES

Client shall provide the following to enable LUCID to perform the audit:

1. **Repository Access** -- Read-only access to all in-scope repositories within two (2) business days of SOW execution. Access may be granted via GitHub, GitLab, Bitbucket, or secure file transfer.

2. **Point of Contact** -- A designated technical contact available to answer questions about the codebase, architecture, and AI tool usage within one (1) business day.

3. **AI Tool Information** -- Documentation of which AI coding tools are in use (e.g., GitHub Copilot, Cursor, ChatGPT), team adoption level, and any internal policies governing AI code.

4. **NDA Execution** -- Execution of the Mutual Non-Disclosure Agreement prior to or concurrent with this SOW.

5. **Feedback Window** -- Review of the draft report and provision of feedback within five (5) business days of receipt.

Delays caused by Client's failure to meet these responsibilities may extend the timeline without penalty to LUCID.

---

## 8. ASSUMPTIONS

1. All repositories in scope are accessible via standard Git tooling.
2. Codebase languages are among those supported by LUCID's verification methodology (most mainstream languages are supported; exotic or proprietary languages may require a scope adjustment).
3. Client will not materially alter the in-scope codebase during the audit period in ways that invalidate findings.
4. The audit assesses the codebase as of the date access is granted. Subsequent changes are not covered unless a retainer engagement is in place.
5. Findings are based on LUCID's patent-pending methodology and represent LUCID's professional assessment; they are not legal advice.

---

## 9. INTELLECTUAL PROPERTY

### 9.1 Client IP

Client retains all ownership rights in its source code, documentation, and proprietary information. Nothing in this SOW grants LUCID any ownership interest in Client's intellectual property.

### 9.2 LUCID IP

LUCID retains all ownership rights in its verification methodology, tools, processes, and any general knowledge or techniques developed or refined during this engagement. The LUCID formal verification methodology is protected by U.S. Provisional Patent Application No. 63/980,048.

### 9.3 Deliverable Ownership

Upon receipt of full payment, Client shall own the audit report and all deliverables produced specifically for Client under this SOW. LUCID retains the right to use anonymized and aggregated data from this engagement for research, benchmarking, and marketing purposes, provided that no Client-identifiable information is disclosed without written consent.

---

## 10. RESPONSIBLE DISCLOSURE

### 10.1 Critical Vulnerabilities

If during the audit LUCID discovers a vulnerability of Critical severity (defined as: actively exploitable, could result in data breach, or could cause significant business disruption), LUCID will:

1. Notify Client's designated contact within twenty-four (24) hours of confirmed discovery.
2. Provide a preliminary written description of the vulnerability and recommended immediate mitigation.
3. Not disclose the vulnerability to any third party.

### 10.2 Non-Disclosure of Findings

All audit findings are confidential and subject to the NDA. LUCID will not disclose specific findings, vulnerabilities, or quality scores attributable to Client without prior written consent. LUCID may reference the engagement in general terms (e.g., "audited a fintech company's AI-generated code") for marketing purposes unless Client objects in writing.

---

## 11. LIABILITY LIMITATIONS

### 11.1 Limitation of Liability

LUCID's total aggregate liability arising out of or related to this SOW shall not exceed the total fees paid by Client under this SOW. In no event shall either party be liable for indirect, incidental, special, consequential, or punitive damages, including lost profits, lost data, or business interruption, regardless of the theory of liability.

### 11.2 No Guarantee

The audit provides LUCID's professional assessment based on its methodology and the information available at the time of the audit. LUCID does not guarantee that all defects, vulnerabilities, or issues in the codebase will be identified. The audit is not a certification and should not be represented as such.

### 11.3 Sole Remedy

Client's sole remedy for any claim arising under this SOW is limited to the fees paid. Client acknowledges that LUCID's methodology identifies issues in AI-generated code with high accuracy, but no verification methodology is infallible.

---

## 12. CHANGE ORDERS

Changes to scope, timeline, or fees require a written change order signed by both parties. Change order requests may be initiated by either party. LUCID will provide a cost and timeline estimate for any proposed scope changes within three (3) business days of the request.

If the audit reveals that the actual scope materially exceeds the assumptions in Section 8 (e.g., significantly larger codebase, additional languages not originally identified), LUCID will notify Client and the parties will negotiate a change order in good faith before proceeding with the additional work.

---

## 13. TERM AND TERMINATION

### 13.1 Term

This SOW is effective upon execution by both parties and continues until all deliverables have been provided and all payments have been made, unless terminated earlier.

### 13.2 Termination for Convenience

Either party may terminate this SOW with fifteen (15) days' written notice. Upon termination:
- Client shall pay for all work completed through the termination date.
- LUCID shall deliver any completed or in-progress deliverables.
- The deposit is non-refundable after the kickoff milestone.

### 13.3 Termination for Cause

Either party may terminate immediately upon written notice if the other party materially breaches this SOW and fails to cure the breach within ten (10) business days of receiving written notice of the breach.

---

## 14. GENERAL TERMS

### 14.1 Governing Law

This SOW shall be governed by the laws of [STATE / JURISDICTION], without regard to conflict of laws principles.

### 14.2 Dispute Resolution

Any disputes arising under this SOW shall first be addressed through good-faith negotiation. If unresolved within thirty (30) days, disputes shall be resolved by binding arbitration under the rules of the American Arbitration Association, conducted in [CITY, STATE].

### 14.3 Independent Contractor

LUCID is an independent contractor. Nothing in this SOW creates an employment, partnership, joint venture, or agency relationship between the parties.

### 14.4 Entire Agreement

This SOW, together with the NDA referenced in Section 1, constitutes the entire agreement between the parties regarding the subject matter hereof and supersedes all prior negotiations, representations, and agreements.

### 14.5 Amendments

This SOW may only be amended by a written instrument signed by both parties.

### 14.6 Counterparts

This SOW may be executed in counterparts, including electronic signatures, each of which shall constitute an original.

---

## SIGNATURES

**PROVIDER: Ty Wells d/b/a LUCID**

Signature: ________________________________
Name: Ty Wells
Title: Principal
Date: ________________________________

**CLIENT: [CLIENT LEGAL NAME]**

Signature: ________________________________
Name: [CLIENT SIGNER NAME]
Title: [CLIENT SIGNER TITLE]
Date: ________________________________
