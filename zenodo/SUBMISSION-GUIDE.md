# Zenodo Publication — Submission Guide

## Goal: Obtain a DOI for the LUCID paper

## Steps

### 1. Create Zenodo Account
- Go to https://zenodo.org
- Sign in with GitHub (recommended) or create account
- Sign in at https://zenodo.org/login

### 2. Create New Upload
- Click "New Upload" (top right)
- Upload: `arxiv-submission/main.pdf`
- Rename the file to: `lucid-leveraging-unverified-claims-into-deliverables.pdf`

### 3. Fill Metadata

**Upload type:** Publication → Preprint

**Title:**
LUCID: Leveraging Unverified Claims Into Deliverables — A Neuroscience-Grounded Framework for Exploiting Large Language Model Hallucination as a Software Specification Engine

**Authors:**
- Wells, Ty | Independent Researcher | (add ORCID if you have one)

**Description (paste this):**
Large language model (LLM) hallucination is universally treated as a defect to be minimized. We argue this framing is backwards. Hallucination — the confident generation of plausible but unverified claims — is computationally identical to the brain's pattern completion mechanism that underlies both perception and imagination. We present LUCID (Leveraging Unverified Claims Into Deliverables), a development methodology that deliberately invokes LLM hallucination, extracts the resulting claims as testable requirements, verifies them against a real codebase, and iteratively converges hallucinated fiction toward verified reality. By prompting an LLM to author Terms of Service for an application that does not yet exist, we exploit the model's confabulatory tendency to produce comprehensive, precise, multi-dimensional specifications — covering functionality, security, data privacy, performance, and legal compliance — in seconds. We provide theoretical grounding through three convergent lines of evidence: (1) the mathematical equivalence between transformer attention and hippocampal pattern completion, (2) the predictive processing framework from cognitive neuroscience, and (3) the REBUS model of psychedelic hallucination. We demonstrate the framework on a real-world application, achieving convergence from 57.3% to 90.8% compliance across six iterations. We position LUCID as the software engineering analogue of protein hallucination (Baker Lab, Nobel Prize 2024), where neural network "dreams" serve as blueprints validated against physical reality.

**Publication date:** 2026-02-07

**Keywords:**
- LLM hallucination
- confabulation
- predictive processing
- specification generation
- requirements engineering
- iterative convergence
- neuroscience
- software engineering
- AI safety
- large language models

**License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

**Access right:** Open Access

**Language:** English

**Version:** 1.0

**Related identifiers:**
- https://github.com/gtsbahamas/hallucination-reversing-system (relationship: isSupplementedBy)

**Notes:**
Preprint. 12 pages, 5 tables, 35 references. Open-source CLI implementation available at GitHub repository.

### 4. Publish
- Review all metadata
- Click "Publish"
- **WARNING: Publishing is permanent. You cannot delete the record.**
- DOI will be active immediately

### 5. Record the DOI
After publishing, copy the DOI (format: 10.5281/zenodo.XXXXXXX) and update:
- `.claude/production-plan.md` (mark task 1.1 complete, record DOI)
- `arxiv-submission/main.tex` (add DOI to paper)
- `docs/paper.md` (add DOI reference)
- Any blog posts or social media

## Optional: API Submission

If you prefer to use the REST API:

### Get API Token
1. Go to https://zenodo.org/account/settings/applications/
2. Create a new personal access token with scope: deposit:write
3. Save the token securely

### API Commands (replace YOUR_TOKEN)

```bash
# Step 1: Create empty deposit
curl -X POST 'https://zenodo.org/api/deposit/depositions' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{}'

# Note the "id" and "links.bucket" from response

# Step 2: Upload PDF
curl -X PUT 'https://zenodo.org/api/files/BUCKET_ID/lucid-leveraging-unverified-claims-into-deliverables.pdf' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @arxiv-submission/main.pdf

# Step 3: Add metadata (see zenodo-metadata.json)
curl -X PUT 'https://zenodo.org/api/deposit/depositions/DEPOSITION_ID' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d @zenodo/zenodo-metadata.json

# Step 4: Publish
curl -X POST 'https://zenodo.org/api/deposit/depositions/DEPOSITION_ID/actions/publish' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

## Tip: Use Sandbox First
Test at https://sandbox.zenodo.org before publishing for real.
Create a separate token at the sandbox site.
