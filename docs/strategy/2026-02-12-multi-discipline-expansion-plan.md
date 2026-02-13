# LUCID Multi-Discipline Expansion Plan

*Created: 2026-02-12*
*Author: Ty Wells*
*Status: DRAFT — requires validation*
*Patent: App #63/980,048 (provisional, filed 2026-02-11)*

---

## Executive Summary

LUCID's core innovation is not "code verification." It is a **domain-agnostic orchestration loop** that wraps any verification oracle:

```
Generator → Claim Extractor → [Domain Verifier] → Remediator → Loop
```

The strategic insight: **don't build domain verifiers — integrate existing ones.** Every discipline already has underused formal verification tools. They're underused because they require manual specification of *what to verify*. LUCID automates that step (claim extraction) and the fix step (remediation). The verifier itself is pluggable.

This means expanding to new disciplines is an **integration problem, not a research problem.** Each new domain requires:
1. An adapter to an existing verification tool (~2-4 weeks engineering)
2. Domain-specific claim extraction prompts (~1 week prompt engineering)
3. A beachhead customer willing to pilot (~1-3 months sales)

The plan below sequences 7 disciplines by revenue timing, capital efficiency, and strategic value.

---

## Part 1: Platform Architecture Evolution

### Current State (February 2026)

The LUCID API has:
- Forward pipeline (extract claims → verify → remediate)
- Reverse pipeline (synthesize specs → generate → verify)
- Hardcoded `DOMAIN_PATTERNS` for code (SQL injection, auth, async patterns)
- Python test executor as the verification oracle
- Supabase for API keys, usage tracking, tier management
- Vercel deployment with 300s timeout, 1GB memory

**Problem:** The verifier is tightly coupled to Python code execution. To support new disciplines, the verifier must become a pluggable interface.

### Target State (Month 6)

```
┌─────────────────────────────────────────────────┐
│                  LUCID Runtime                   │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Claim    │  │ Verifier │  │ Remediator   │  │
│  │ Extractor │→ │ Router   │→ │              │  │
│  └──────────┘  └────┬─────┘  └──────────────┘  │
│                     │                            │
└─────────────────────┼────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
   ┌────────────┐ ┌────────┐ ┌────────┐
   │ Code       │ │ Smart  │ │ IaC    │
   │ Executor   │ │Contract│ │ Policy │
   │ (Python,   │ │(Certora│ │ (OPA/  │
   │  Jest,etc) │ │Slither)│ │ Rego)  │
   └────────────┘ └────────┘ └────────┘
```

### Architecture Changes Required

**1. Verifier Plugin Interface** (~2 weeks)

```typescript
interface DomainVerifier {
  domain: string;
  // Extract testable claims from generated output
  extractClaims(output: string, context: DomainContext): Promise<Claim[]>;
  // Verify each claim against ground truth
  verify(claim: Claim): Promise<VerificationResult>;
  // Generate remediation guidance for failed claims
  remediate(failures: VerificationResult[]): Promise<RemediationPlan>;
}
```

**2. Domain Registry** (~1 week)

```sql
CREATE TABLE domains (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  verifier_type TEXT NOT NULL,  -- 'python_exec' | 'certora' | 'opa' | 'lean4' | 'rule_engine'
  claim_extraction_prompt TEXT, -- Domain-specific prompt template
  config JSONB,                 -- Verifier-specific configuration
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE domain_patterns (
  id SERIAL PRIMARY KEY,
  domain_id TEXT REFERENCES domains(id),
  trigger_keywords TEXT[],
  constraints JSONB,
  severity TEXT CHECK (severity IN ('critical', 'high', 'medium', 'low'))
);
```

**3. Verifier Adapters** (~2-4 weeks each, per domain)

Each adapter translates LUCID claims into domain-specific verification calls:

| Domain | Adapter | External Tool | Integration Method |
|--------|---------|---------------|-------------------|
| Code (Python) | `PythonExecVerifier` | subprocess | Already built |
| Code (JS/TS) | `NodeExecVerifier` | subprocess | Jest/Vitest runner |
| Smart Contracts | `CertoraVerifier` | Certora CLI / API | certora-cli subprocess |
| Smart Contracts | `SlitherVerifier` | Slither | slither CLI |
| IaC | `OPAVerifier` | OPA/Rego | opa eval CLI |
| IaC | `TerraformVerifier` | terraform validate | terraform CLI |
| Math Proofs | `Lean4Verifier` | Lean 4 | lean CLI |
| Legal | `ClauseVerifier` | Rule engine | Internal rule DB |
| Compliance | `RegulationVerifier` | Checklist engine | Internal rule DB |

**4. API Endpoint Generalization** (~1 week)

```
POST /v1/verify
{
  "domain": "solidity",        // Routes to CertoraVerifier
  "input": "contract code...",
  "context": { ... },
  "max_iterations": 3
}
```

**Total platform refactor: ~6-8 weeks of engineering.**

---

## Part 2: Discipline Expansion Sequence

### Sequencing Criteria

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Revenue speed | 30% | Need cash flow to fund expansion |
| Technical proximity | 25% | How much new engineering per domain |
| Market timing | 20% | Deadlines, trends, urgency |
| Strategic value | 15% | IP, moat, defensibility |
| Capital required | 10% | Lower is better for bootstrapping |

### Expansion Order

| Phase | Discipline | Timeline | Revenue Target | Why This Order |
|-------|-----------|----------|----------------|----------------|
| 0 | Software (code) | NOW | $150K-$370K Y1 | Already proven, generating revenue |
| 1 | Smart Contracts | Month 2-4 | $100K-$300K Y1 | 1-4 week sales cycle, $50K-$150K per audit, same skills |
| 2 | IaC / Cloud Security | Month 4-6 | $200K-$500K Y1 | Adjacent to software, OPA exists, CSPM is $5B market |
| 3 | EU AI Act Compliance | Month 3-6 | $100K-$400K Y1 | August 2026 deadline creates urgency |
| 4 | Legal / Contract Analysis | Month 6-9 | Partnership revenue | $10.8B market by 2030, 28% CAGR |
| 5 | Hardware (EDA) | Month 9-12 | Partnership / licensing | $19B market, 60-70% of cost is verification |
| 6 | Math / Formal Proofs | Month 6-12 | Academic + licensing | Axiom raised $64M, strategic IP |
| 7 | Medical / Clinical | Year 2+ | TBD | FDA pathway required, 9-18 month sales cycle |

---

## Phase 0: Software (Current — Months 1-3)

**Status:** Operational. API deployed, benchmarks published, patent filed.

**Verifier:** Python test executor (built), expanding to JS/TS.

**Revenue model:** Enterprise consulting ($10K-$150K per engagement) + API usage.

**Immediate actions (already in strategy doc):**
1. Publish benchmark report
2. Close first Spotlight audit ($10K-$15K)
3. Platform outreach (Cursor, Bolt, Lovable, Replit)
4. GitHub Action MVP

**This phase funds everything else.** Target: $50K revenue by month 3.

---

## Phase 1: Smart Contracts (Months 2-4)

### Why First

- **Shortest sales cycle in tech** — DeFi teams need audits before mainnet launch (1-4 weeks)
- **Highest willingness to pay** — $50K-$150K per audit is standard
- **Verification tools already exist** — Certora, Slither, Echidna, Mythril
- **Same engineering skillset** — Solidity is code, claim extraction is similar
- **Market growing 22.8% CAGR** — $890M → $6.1B by 2033
- **Certora secured $196.5B TVL** — proves formal verification demand exists

### What LUCID Adds That Doesn't Exist

Current smart contract audits are either:
- **Manual** (Trail of Bits, OpenZeppelin): Expensive ($50K-$150K), 4-8 weeks, doesn't scale
- **Automated but shallow** (Slither, Mythril): Fast, catches known patterns, misses semantic bugs
- **Formal but manual spec** (Certora): Powerful but requires writing formal specifications by hand

**LUCID fills the gap:** Automatically extract claims from Solidity → generate formal specs → run through Certora/Slither → remediate → iterate. No manual spec writing needed.

### Verifier Build

**Adapter: `SolidityVerifier`** (~3 weeks)

```
Solidity code
  → Claim Extractor (LLM): "This function transfers tokens" → Claim: "transfer reduces sender balance by amount"
  → Slither (static): Known vulnerability patterns (reentrancy, overflow, etc.)
  → Certora (formal): Custom-generated invariants from claims
  → Remediation: Fix identified issues, re-verify
```

**Integration steps:**
1. Install Certora CLI + Slither as dependencies
2. Build claim-to-invariant translator (LLM prompt)
3. Build Solidity compilation wrapper (solc)
4. Build results parser (Certora JSON output → LUCID claims format)
5. Test on known vulnerable contracts (Damn Vulnerable DeFi)

### Go-to-Market

**Beachhead customer profile:**
- DeFi protocol 2-8 weeks from mainnet launch
- TVL target $10M-$100M
- Can't afford $150K Trail of Bits audit
- Wants formal verification but can't write Certora specs

**Pricing:**
| Tier | Price | What They Get |
|------|-------|---------------|
| Pre-launch scan | $15K-$25K | Single contract, automated LUCID + manual review |
| Full audit | $40K-$80K | Full protocol, LUCID + Certora formal verification |
| Continuous monitoring | $5K-$10K/mo | Ongoing verification on every commit |

**Undercuts** Trail of Bits/OpenZeppelin by 40-60% while adding formal verification they don't offer.

**GTM channels:**
- Crypto Twitter / CT (direct outreach to protocol teams)
- DeFi Discord communities (Aave, Compound, Uniswap governance forums)
- ETHGlobal hackathon sponsorship ($2K-$5K, high-intent audience)
- Publish "We verified [known vulnerable contract] and found X" case study
- Partner with one mid-tier audit firm to offer LUCID as an add-on

**Revenue target:** 3-5 audits in first 6 months = $100K-$300K.

### Risks

| Risk | Mitigation |
|------|-----------|
| Certora CLI licensing costs | Start with Slither (free), add Certora for premium tier |
| Solidity claim extraction accuracy | Train on known-vulnerable contracts (DeFi exploits DB) |
| Reputation risk if we miss a bug | Never claim "audited" — claim "LUCID-verified" (complementary to manual audit) |
| Short window before mainnet | Offer 48-hour express scan for $8K (automated only) |

---

## Phase 2: Infrastructure as Code / Cloud Security (Months 4-6)

### Why Second

- **Same customer as Phase 0** — VP Engineering who buys code audits also owns IaC
- **OPA/Rego is a mature verifier** — CNCF Graduated, deterministic policy evaluation
- **Cross-sell from existing relationships** — "We audited your code, now let's audit your infra"
- **CSPM market is $5.25B** — and growing 15% CAGR
- **Gomboc AI raised $13M** for deterministic IaC remediation — validates the approach

### What LUCID Adds

Current IaC security is:
- **Static scanners** (Checkov, tfsec): Pattern matching, high false positive rate
- **Policy engines** (OPA, Sentinel): Powerful but require writing policies manually
- **CSPM platforms** (Wiz, Prisma Cloud): Monitor running infra, don't verify IaC pre-deploy

**LUCID fills the gap:** Extract claims from Terraform/CloudFormation → generate OPA policies automatically → evaluate → remediate → iterate. Shift-left CSPM.

### Verifier Build

**Adapter: `IaCVerifier`** (~2 weeks — OPA has excellent CLI)

```
Terraform code
  → Claim Extractor: "S3 bucket has encryption enabled" → Policy: package s3; deny { not input.resource.aws_s3_bucket.*.server_side_encryption_configuration }
  → terraform validate: Syntax check
  → OPA eval: Policy evaluation against plan JSON
  → CIS/SOC2 benchmark rules: Compliance mapping
  → Remediation: Fix violations, re-verify
```

**Integration steps:**
1. Generate `terraform plan -out=plan.json` from HCL
2. Build claim-to-Rego translator (LLM prompt + template library)
3. Bundle CIS AWS Foundations Benchmark as baseline policies
4. Parse OPA evaluation results into LUCID claims format
5. Test on intentionally misconfigured Terraform (CloudGoat)

### Go-to-Market

**Cross-sell motion:** Every Phase 0 consulting customer gets an IaC scan as an add-on.

**Pricing:**
| Tier | Price | What They Get |
|------|-------|---------------|
| IaC scan add-on | $5K-$10K | Scan Terraform/CloudFormation alongside code audit |
| Standalone IaC audit | $15K-$30K | Full infrastructure review + compliance mapping |
| CI/CD integration | $3K-$8K/mo | OPA policy enforcement on every `terraform plan` |

**GTM channels:**
- Cross-sell to Phase 0 customers (warmest leads)
- HashiConf / KubeCon conference presence
- "How many of your Terraform configs would pass CIS benchmarks?" — free scan as lead gen
- Partner with cloud consulting firms (Contino, Cloudreach, etc.)

**Revenue target:** 5-10 add-ons + 2-3 standalone = $100K-$250K in months 4-9.

---

## Phase 3: EU AI Act Compliance (Months 3-6)

### Why This Timing

**August 2, 2026 — Annex III high-risk AI system requirements take effect.** This is 6 months away. Companies are scrambling.

- **Fines:** EUR 35M or 7% global annual turnover (whichever is higher)
- **Who's affected:** Every company deploying AI in EU for employment, credit, education, law enforcement, biometrics, critical infrastructure
- **Market size:** AI governance software is $340M → $1.21B by 2030
- **No clear market leader yet** — this is greenfield
- **LUCID's benchmark data IS compliance evidence** — we already prove AI code quality

### What LUCID Adds

The EU AI Act requires (Article 9-15 for high-risk systems):
- Risk management system (Art. 9)
- Data governance (Art. 10)
- Technical documentation (Art. 11)
- Record-keeping (Art. 12)
- Transparency (Art. 13)
- Human oversight (Art. 14)
- Accuracy, robustness, cybersecurity (Art. 15)

**LUCID directly addresses Article 15** — accuracy and robustness of AI systems. Our verification loop IS the quality management system the regulation requires. The audit trail IS the technical documentation.

### Verifier Build

**Adapter: `ComplianceVerifier`** (~3 weeks)

```
AI system description + code
  → Claim Extractor: "System performs [risk category] function" → Claims about compliance requirements
  → Article Checker: Map claims against EU AI Act articles
  → Evidence Validator: Check if documentation/tests exist for each requirement
  → Gap Analysis: Identify missing compliance elements
  → Remediation: Generate compliance documentation, recommend tests
```

This is primarily a **rule-based verifier** (regulatory requirements are enumerated in the Act) with LLM-assisted evidence evaluation.

**Integration steps:**
1. Encode EU AI Act requirements as structured rules (Articles 9-15, ~200 specific requirements)
2. Build risk classification engine (is this system high-risk per Annex III?)
3. Build evidence mapper (link code artifacts to compliance requirements)
4. Generate compliance report template (aligned with harmonized standards)
5. Test on our own LUCID system (eat our own dogfood — we're an AI system too)

### Go-to-Market

**This is a land-grab.** First mover with a credible compliance tool wins.

**Positioning:** "LUCID Compliance — Automated EU AI Act Readiness Assessment"

**Pricing:**
| Tier | Price | What They Get |
|------|-------|---------------|
| Readiness assessment | $15K-$25K | Gap analysis + remediation roadmap |
| Full compliance package | $50K-$100K | Assessment + documentation generation + evidence trails |
| Ongoing compliance | $5K-$15K/mo | Continuous monitoring + quarterly reports |

**Undercuts Big 4** (who charge $75K-$250K) while providing more technical depth.

**GTM channels:**
- EU-focused tech conferences (Web Summit, Slush, VivaTech, Station F Demo Days)
- LinkedIn thought leadership ("Your AI coding tool generates code that doesn't comply with Article 15")
- Partner with EU law firms specializing in tech regulation
- Webinar: "EU AI Act for Engineering Leaders — What You Actually Need to Do"
- Cold outreach to VP Engineering at EU-operating companies (Spotify, Klarna, N26, Adyen, etc.)

**Revenue target:** 3-5 assessments by August 2026 deadline = $100K-$300K. Post-deadline: ongoing compliance monitoring revenue.

### Strategic Value

Even if initial revenue is modest, **being known as "the EU AI Act compliance tool" creates enormous strategic leverage.** When the regulation enforces, every company needs a solution. Being first with benchmark data + patent = defensible position.

---

## Phase 4: Legal / Contract Analysis (Months 6-9)

### Why This Phase

- **Fastest growing market** — 28.3% CAGR, $3.1B → $10.8B by 2030
- **Verification maps naturally** — contracts have required clauses, consistency rules, regulatory cross-references
- **LLM hallucination in legal is dangerous** — Harvey AI ($100M+ raised) generates plausible but wrong legal analysis
- **Revenue per customer is high** — AmLaw 100 firms spend $500K-$2M/year on legal tech

### What LUCID Adds

Legal AI tools today generate documents but **don't formally verify them**. A contract generated by Harvey could:
- Miss a required clause for the jurisdiction
- Include conflicting terms in different sections
- Use non-standard language that voids enforceability
- Misapply regulatory requirements

**LUCID verifies legal output** against:
- Clause completeness checklists (jurisdiction-specific)
- Internal consistency (no conflicting terms)
- Regulatory requirement cross-references
- Template compliance (firm-specific standards)

### Verifier Build

**Adapter: `LegalVerifier`** (~4 weeks)

```
Contract draft
  → Claim Extractor: "Section 3.2 contains indemnification clause" → Claims about clause presence, consistency, compliance
  → Clause Checker: Required clauses present per jurisdiction/contract type?
  → Consistency Checker: No conflicting terms across sections?
  → Regulatory Cross-Ref: Meets applicable regulatory requirements?
  → Remediation: Flag missing/conflicting clauses with specific fixes
```

**Key difference:** The verifier here is a **rule engine** (clause databases, consistency rules) rather than an external tool. This means building the rule database is the main work.

**Partnership approach:** Partner with a legal data provider (Thomson Reuters, LexisNexis) or a legal AI company (Harvey, Casetext) to provide the clause databases. LUCID provides the verification loop, they provide the domain knowledge.

### Go-to-Market

**Partner-led, not direct sales.** Legal has a 6-12 month enterprise sales cycle and requires domain credibility we don't yet have.

**Partnership targets:**
1. **Harvey AI** — They generate legal documents. We verify them. Complementary.
2. **Ironclad** — Contract lifecycle management. LUCID as a verification layer.
3. **Thomson Reuters** — CoCounsel needs verification. We provide the loop.

**Value proposition to partners:** "Your AI generates contracts. Ours verifies them. Together, you can guarantee accuracy that neither can alone."

**Revenue model:** White-label licensing to legal tech platforms ($100K-$500K/year per partner) or revenue share on verification API calls.

**Revenue target:** 1-2 partnerships = $100K-$300K/year in licensing by month 12.

---

## Phase 5: Hardware / EDA (Months 9-12)

### Why This Phase

- **Largest single TAM** — EDA is $19B, verification is 60-70% of chip design cost
- **Highest cost of failure** — a single respin at 3nm costs $50M+
- **Ricursive raised $335M at $4B** — proves AI + formal verification in hardware is investable
- **Verification tools exist** — Synopsys JasperGold, Cadence JasperGold, Siemens Questa
- **Massive enterprise budgets** — $500K-$10M/year for EDA tools

### Why Not Earlier

- **18-month sales cycle** — need to start conversations now for revenue in 12-18 months
- **Requires partnership** — can't compete with Synopsys/Cadence alone
- **Domain expertise gap** — RTL design is specialized, need hiring or partnership

### What LUCID Adds

Current hardware verification:
- **Simulation** (90% of verification): Slow, can't cover full state space
- **Formal verification** (10%): Powerful but requires manual property writing (the bottleneck)
- **AI-assisted design** (emerging): Ricursive, but focused on generation not verification

**LUCID's value:** Automatically extract properties from RTL → generate SystemVerilog Assertions (SVA) → run through formal tools → remediate → iterate. **Automate the property writing bottleneck.**

### Verifier Build

**Adapter: `HDLVerifier`** (~6-8 weeks — most complex adapter)

```
Verilog/SystemVerilog code
  → Claim Extractor: "This FSM has 4 states" → Claims about state transitions, timing, protocols
  → SVA Generator: Convert claims to SystemVerilog Assertions
  → Formal Tool (JasperGold/Questa): Model checking against assertions
  → Simulation: Testbench generation and execution
  → Remediation: Fix RTL based on counterexamples
```

### Go-to-Market

**Partnership-first.** The EDA market is an oligopoly (Synopsys 31%, Cadence 30%, Siemens 13%). You don't sell against them — you sell WITH them.

**Partnership targets:**
1. **Siemens EDA (Questa)** — Third place, most motivated to differentiate. Their Questa Formal tool + LUCID auto-property generation = competitive advantage vs Synopsys/Cadence.
2. **Smaller EDA players** (Aldec, Metrics) — More willing to integrate novel tech.
3. **RISC-V ecosystem** — Open hardware movement needs verification tooling, less vendor lock-in.

**Revenue model:** OEM licensing ($500K-$2M/year per EDA partner) or per-seat licensing through partner channel.

**Start now (month 1):** Begin relationship-building conversations with Siemens EDA, attend DVCon (Design and Verification Conference), write white paper on "Automated Property Generation for Formal Verification."

**Revenue target:** LOI by month 12, first licensing revenue month 18-24.

---

## Phase 6: Mathematical Proofs (Months 6-12)

### Why This Phase

- **Axiom raised $64M at ~$300M** for AI math proofs — validates the category
- **Lean 4 is the target** — DeepSeek-Prover, LeanDojo, and others all target Lean
- **Verification is trivial** — Lean's type checker IS the oracle. Perfect convergence guarantee.
- **Strategic IP value** — proving mathematical theorems with LUCID strengthens the patent
- **Academic credibility** — publications in ICML/NeurIPS/ICLR carry enormous weight

### What LUCID Adds

Current AI theorem proving:
- **Neural provers** (DeepSeek-Prover, AlphaProof): Generate proof attempts, check with Lean
- **But no systematic loop:** They generate-and-check, not generate-verify-remediate-iterate

**LUCID adds the remediation step.** When Lean rejects a proof step, LUCID's remediator extracts the specific error, generates a targeted fix, and retries. This is the iterative refinement that current provers lack.

### Verifier Build

**Adapter: `Lean4Verifier`** (~3 weeks — Lean has excellent CLI)

```
Math statement
  → Claim Extractor: Decompose into lemmas
  → Lean 4 Compiler: Type-check each proof step
  → Error Parser: Extract specific failure from Lean error messages
  → Remediator: Generate alternative proof tactics based on error
  → Iterate until all steps type-check
```

### Go-to-Market

**Academic-first, commercial-second.**

**Academic track:**
- Publish "LUCID-Prove: Iterative Formal Verification for Neural Theorem Proving" at ICML 2027
- Benchmark on MiniF2F dataset (standard benchmark)
- Collaborate with Lean Mathlib community
- Target: 1-2 publications, conference talks

**Commercial track:**
- **Quantitative finance** — Axiom's first customers are quant funds verifying trading strategies
- **Chip design** — formal properties for hardware (bridges to Phase 5)
- **Aerospace/defense** — DO-178C requires formal methods for safety-critical software

**Revenue model:** Research grants initially (NSF SBIR Phase I = $305K), licensing to Axiom-like companies later.

**Revenue target:** NSF SBIR submission by month 6. If awarded: $305K non-dilutive funding.

---

## Phase 7: Medical / Clinical Decision Support (Year 2+)

### Why Last

- **9-18 month sales cycle** — healthcare procurement is the slowest
- **FDA regulatory pathway** — SaMD may require 510(k) or De Novo clearance
- **Domain expertise required** — need clinical advisors, not just engineers
- **Highest risk** — errors in clinical decisions = patient harm = liability

### Why Do It At All

- **$3.34B market by 2033** at 7.4% CAGR
- **FDA is becoming MORE permissive** (Jan 2026 revised CDS guidance)
- **Drug interaction databases ARE formal verifiers** — DrugBank, Micromedex are ground truth
- **The need is enormous** — 44,000-98,000 preventable deaths/year from medical errors (IOM)
- **If LUCID can verify clinical recommendations, that's a $B+ opportunity**

### What LUCID Adds

Clinical AI tools today:
- Generate differential diagnoses (hallucination rate unknown)
- Recommend treatments (no formal verification against guidelines)
- Calculate dosages (potential for catastrophic errors)

**LUCID verifies clinical AI output against:**
- Drug interaction databases (DrugBank — 14,000+ drug entries)
- Clinical practice guidelines (UpToDate, Cochrane)
- Dosage calculators (pharmacokinetic models)
- Contraindication databases

### Verifier Build

**Adapter: `ClinicalVerifier`** (~8 weeks + regulatory compliance)

```
Clinical recommendation
  → Claim Extractor: "Recommend Drug X at dose Y for condition Z"
  → Drug Interaction Check: DrugBank API → any interactions with current medications?
  → Dosage Validator: Is dose within therapeutic range for patient parameters?
  → Guideline Compliance: Does recommendation align with current clinical guidelines?
  → Contraindication Check: Any contraindications given patient history?
  → Remediation: Flag issues with specific alternative recommendations
```

### Go-to-Market

**Partnership required.** We cannot sell directly to hospitals without clinical credibility.

**Partnership targets:**
1. **Wolters Kluwer (UpToDate)** — They launched UpToDate Expert AI (Oct 2025). LUCID as verification layer.
2. **Epic/Oracle Health** — EHR platforms with embedded CDS. LUCID as a safety layer.
3. **Microsoft (Dragon Copilot)** — GA for nurses (Jan 2026). Needs verification.

**Revenue model:** OEM licensing to health IT platforms. Per-verification pricing to clinical AI companies.

**Regulatory path:** Start with CDS that is NOT a medical device (per Jan 2026 FDA guidance). Focus on decision SUPPORT, not decision MAKING. The clinician reviews the recommendation independently.

**Timeline:**
- Month 12: Begin clinical advisory board recruitment (2-3 physicians)
- Month 15: Build clinical verifier prototype
- Month 18: Partner conversations with health IT platforms
- Month 24: First pilot deployment
- Month 30: Revenue

---

## Part 3: Financial Model

### Year 1 Revenue Projection (Conservative)

| Phase | Discipline | Q1 | Q2 | Q3 | Q4 | Total |
|-------|-----------|-----|-----|-----|-----|-------|
| 0 | Software | $25K | $75K | $100K | $120K | $320K |
| 1 | Smart Contracts | — | $30K | $80K | $100K | $210K |
| 2 | IaC / Cloud | — | — | $40K | $80K | $120K |
| 3 | EU AI Act | — | $15K | $50K | $100K | $165K |
| 4 | Legal | — | — | — | $25K | $25K |
| — | Training Signal | — | — | $50K | $50K | $100K |
| | **Total** | **$25K** | **$120K** | **$320K** | **$475K** | **$940K** |

### Year 1 Cost Structure

| Item | Monthly | Annual |
|------|---------|--------|
| Claude API (generation + verification) | $2K-$5K | $24K-$60K |
| Vercel Pro | $20 | $240 |
| Supabase Pro | $25 | $300 |
| Upstash Redis | $10 | $120 |
| Certora CLI license | TBD | $5K-$20K |
| Sales (LinkedIn Navigator) | $100 | $1.2K |
| Conferences (2-3) | — | $10K |
| Legal (non-provisional patent) | — | $5K-$15K |
| Contractor (month 6+) | $5K-$10K | $30K-$60K |
| **Total** | | **$76K-$167K** |

### Margin

**Year 1 gross margin: 82-92%** (consulting is high-margin, API costs are low).

### Break-Even

At $76K minimum annual cost: **break-even at month 2-3** (first Spotlight audit covers 2+ months of costs).

---

## Part 4: Platform Build Sequence

### Engineering Roadmap

| Month | Platform Work | Domain Adapters | Hours/Week |
|-------|-------------|-----------------|------------|
| 1 | Publish benchmark report, GitHub Action MVP | — | 20 |
| 2 | Verifier plugin interface + domain registry | Solidity adapter (start) | 30 |
| 3 | API generalization (/v1/verify with domain routing) | Solidity adapter (ship) | 30 |
| 4 | CI/CD integration framework | OPA/Terraform adapter (start) | 25 |
| 5 | Compliance rule engine | OPA adapter (ship), EU AI Act rules (start) | 30 |
| 6 | SaaS dashboard MVP | EU AI Act rules (ship), Lean4 adapter (start) | 35 |
| 7-8 | Dashboard + billing | Lean4 adapter (ship), Legal rule engine (start) | 30 |
| 9-10 | Multi-tenant, team features | Legal rules (ship), HDL adapter (start) | 30 |
| 11-12 | Domain pack marketplace | HDL adapter (ship) | 25 |

### Hiring Trigger

**Hire first contractor when monthly revenue exceeds $30K consistently (likely month 4-5).**

Role: Senior engineer, part-time (20 hrs/week), focused on adapter development while Ty handles sales + core platform.

**Hire second person when monthly revenue exceeds $60K (likely month 7-8).**

Role: Domain specialist (smart contracts OR compliance), part-time, focused on customer delivery.

---

## Part 5: Partnership Strategy

### Tier 1: Integration Partners (Months 2-6)

These are tools LUCID wraps as verifiers. The partnership is technical (API integration).

| Partner | What They Provide | What LUCID Provides | Deal Structure |
|---------|------------------|--------------------|----|
| Certora | Formal verification engine for Solidity | Automated spec generation + loop | Revenue share on joint customers |
| OPA/Styra | Policy engine for IaC | Automated policy generation + loop | Integration partnership (OPA is OSS) |
| Lean 4 / Mathlib | Proof checker | Automated proof generation + loop | Open source collaboration |

### Tier 2: Channel Partners (Months 4-9)

These are companies that sell LUCID to their customers. The partnership is commercial.

| Partner | Their Customer Base | LUCID's Role | Deal Structure |
|---------|-------------------|-------------|----------------|
| Cloud consulting firms | Enterprise DevOps teams | IaC verification add-on | 20-30% referral fee |
| Smart contract audit firms | DeFi protocols | Formal verification layer | White-label or co-branded |
| EU law firms (tech practice) | EU-operating companies | AI Act compliance tool | Referral agreement |
| EDA companies (Siemens) | Semiconductor companies | Property generation plugin | OEM licensing |

### Tier 3: Strategic Partners (Months 9-18)

These are large companies where LUCID becomes a core capability.

| Partner | Strategic Value | LUCID's Role | Deal Structure |
|---------|---------------|-------------|----------------|
| GitHub / Microsoft | Distribution to 150M developers | Code verification in Actions/Copilot | Acquisition or deep integration |
| Anthropic / OpenAI | Model improvement via RLVF signal | Training data factory | Data licensing ($M/year) |
| Synopsys / Cadence | EDA market access | Verification automation | OEM licensing or acquisition |

---

## Part 6: Risk Matrix

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Competitors copy the loop architecture | High | Medium | Patent filed. First-mover advantage in benchmarks. Multi-domain moat. |
| Domain adapters harder than expected | Medium | Medium | Start with simplest (Solidity, OPA). Each adapter validates the pattern. |
| Smart contract market downturn | Medium | Low | Diversified across 7 disciplines. Software is stable. |
| EU AI Act enforcement delayed | Low | Medium | Compliance need exists regardless. Companies prepare anyway. |
| Can't hire domain experts affordably | Medium | High | Partnership model reduces need for in-house expertise. |
| Certora/OPA change licensing | Low | Medium | Build alternative adapters. Core loop is tool-agnostic. |
| Major LLM provider builds similar loop | High | High | Training signal business is defensible (RLVF data is our moat). |
| Solo founder burnout | High | Critical | Hire at $30K/mo revenue. Automate what's automatable. Prioritize ruthlessly. |

---

## Part 7: Decision Gates

### Gate 1: Month 3 — "Is software consulting working?"

| Metric | Go | No-Go |
|--------|-----|-------|
| Revenue | >$30K cumulative | <$15K cumulative |
| Pipeline | >$100K in qualified leads | <$50K pipeline |
| Benchmark report published | Yes | No |

**If Go:** Proceed to Phase 1 (Smart Contracts)
**If No-Go:** Double down on software, delay expansion

### Gate 2: Month 5 — "Does the plugin architecture work?"

| Metric | Go | No-Go |
|--------|-----|-------|
| Solidity adapter functional | Yes, tested on 20+ contracts | Adapter incomplete |
| First smart contract customer | Closed or in pipeline | No interest |
| OPA adapter started | In development | Not started |

**If Go:** Proceed to Phase 2 (IaC) and Phase 3 (EU AI Act) in parallel
**If No-Go:** Simplify plugin architecture, focus on one domain

### Gate 3: Month 8 — "Should we raise funding?"

| Metric | Raise | Bootstrap |
|--------|-------|-----------|
| Monthly revenue | >$50K and growing | >$40K and stable |
| Domains active | 3+ | 2 |
| Partnership LOIs | 2+ signed | 1 or fewer |
| Training signal interest | LOI from frontier lab | None |

**If Raise:** Seed round ($2-5M) to accelerate hiring + domain expansion
**If Bootstrap:** Continue profitable growth, consider NSF SBIR

### Gate 4: Month 12 — "What's the company?"

| Signal | Path A: Verification Platform | Path B: Training Signal Factory | Path C: Acquisition Target |
|--------|------------------------------|--------------------------------|---------------------------|
| Revenue mix | 70%+ from verification API | 50%+ from training data sales | Inbound interest from strategic |
| Customer type | Many small-medium | Few large (frontier labs) | 1-2 acquirers circling |
| Moat | Multi-domain verifier network | Proprietary preference data | Patent + team + benchmarks |
| Valuation basis | ARR multiple (10-20x) | Data asset value | Strategic premium |

---

## Part 8: Immediate Next Actions (This Week)

| # | Action | Owner | Deadline | Dependency |
|---|--------|-------|----------|-----------|
| 1 | Publish benchmark report | Ty | Feb 14 | None |
| 2 | Begin Verifier Plugin Interface design | Ty | Feb 19 | None |
| 3 | Research Certora CLI licensing / API access | Ty | Feb 16 | None |
| 4 | Identify 10 DeFi protocols 4-8 weeks from launch | Ty | Feb 19 | None |
| 5 | Write "LUCID for Smart Contracts" one-pager | Ty | Feb 21 | #3 |
| 6 | Draft EU AI Act compliance mapping (Art. 9-15) | Ty | Feb 23 | None |
| 7 | Reach out to 3 EU-based tech companies re: compliance | Ty | Feb 28 | #6 |
| 8 | Submit NSF SBIR Phase I LOI | Ty | Mar 1 | None |
| 9 | Begin Solidity adapter development | Ty | Mar 1 | #2 |
| 10 | Attend/submit to ETHDenver or ETHGlobal hackathon | Ty | Next event | #5 |

---

## Appendix A: Verifier Availability by Discipline

| Discipline | Verifier Tool | License | Integration Effort | Verification Strength |
|-----------|--------------|---------|-------------------|----------------------|
| Python code | subprocess (test exec) | Free | Built | Deterministic |
| JS/TS code | Jest/Vitest | Free | 1 week | Deterministic |
| Solidity | Slither | Free (OSS) | 2 weeks | Static (medium) |
| Solidity | Certora | Commercial | 3 weeks | Formal (strong) |
| Terraform | terraform validate | Free | 1 week | Syntax only |
| Terraform/K8s | OPA/Rego | Free (OSS) | 2 weeks | Policy (strong) |
| Math proofs | Lean 4 | Free (OSS) | 3 weeks | Formal (absolute) |
| Hardware (RTL) | Questa Formal | Commercial ($$$) | 6-8 weeks | Formal (strong) |
| Legal contracts | Custom rule engine | Build | 4 weeks | Rule-based (medium) |
| Clinical | DrugBank API | Commercial | 4 weeks | Database (strong) |
| EU AI Act | Custom checklist | Build | 3 weeks | Rule-based (medium) |

## Appendix B: Competitor Funding Context

| Company | Raised | Valuation | Focus | LUCID's Relationship |
|---------|--------|-----------|-------|---------------------|
| Ricursive Intelligence | $335M | $4B | AI chip design | Potential partner (LUCID loop + their generation) |
| Axiom Math | $64M | ~$300M | AI math proofs | Direct competitor in math domain |
| Certora | $43.2M | Undisclosed | Smart contract formal verification | Integration partner (LUCID wraps Certora) |
| Gomboc AI | $13M | Undisclosed | Deterministic IaC remediation | Competitor in IaC domain |
| VERSES AI | CAD$14M+ | Public | Active inference + formal methods | Philosophical ally, potential partner |
| Qodo | $40M | Undisclosed | AI code quality | Competitor in software (uses LLM judge, no formal verification) |
| Patronus AI | $40M | Undisclosed | AI evaluation/testing | Competitor (evaluation, not formal verification) |

**Key insight:** LUCID's competitors in each domain are well-funded but use different approaches (LLM judges, heuristics, static analysis). None use the iterative formal verification loop. The patent protects this approach.

## Appendix C: The Training Signal Flywheel

This revenue stream is independent of any single discipline and scales across all of them:

```
Phase 0: Software verification → preference pairs (pass/fail on code)
Phase 1: Smart contract verification → preference pairs (secure/vulnerable)
Phase 2: IaC verification → preference pairs (compliant/non-compliant)
Phase 3: Compliance verification → preference pairs (meets regulation/doesn't)
...
Each domain adds more training signal. More signal = more valuable dataset.
```

**Buyer:** Frontier labs (Anthropic, OpenAI, Mistral, Cohere)
**Product:** Verified preference pairs for DPO/RLHF training
**Cost to produce:** ~$0.25 per pair (LLM generation + verification)
**Value to buyer:** Replaces human labelers at $50-$100 per pair (200-400x cheaper)
**Pricing:** $5-$50 per pair depending on domain and quality tier

At scale (100K pairs/month across domains): $500K-$5M/month revenue.

**This is the endgame.** Verification across all disciplines generates the most valuable AI training data in the world — domain-specific, formally verified preference signals that no human labeling operation can match in accuracy or cost.
