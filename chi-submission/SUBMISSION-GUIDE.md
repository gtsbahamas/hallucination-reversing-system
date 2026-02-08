# CHI 2026 Tools for Thought Workshop — Submission Guide

## Deadline: February 12, 2026 (Anywhere on Earth)

## Submission URL
https://forms.fillout.com/t/u5Dx2rkszPus

## Three Required Components

### 1. Workshop Paper (4 pages, excluding references)
- **File:** `main.tex` (compile to PDF)
- **Format:** 2-column ACM format (`acmart` document class, `sigconf`)
- **Status:** DRAFT COMPLETE — needs compilation and review

### 2. Mini Poster (Miro Board)
- Go to the workshop website for the Miro template: https://ai-tools-for-thought.github.io/workshop/
- Fill out the template with LUCID's key points
- Export as PDF
- Submit both the Miro sharing URL and the PDF export
- **Status:** NOT YET CREATED — requires Miro account

### 3. Personal Statement (max 150 words per attending author)
- **File:** `personal-statement.md`
- **Status:** COMPLETE (131 words)

## Compilation Instructions

```bash
cd chi-submission
# Option 1: Standard LaTeX
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# Option 2: If acmart.cls is not installed
# Download from: https://www.acm.org/publications/proceedings-template
# Place acmart.cls in this directory, then run the above commands

# Option 3: Overleaf
# Upload main.tex and references.bib to a new Overleaf project
# Select "ACM Conference Proceedings" template
```

## Key Dates
- **Submission deadline:** Feb 12, 2026 (AoE)
- **Acceptance notification:** Feb 25, 2026
- **Camera-ready:** Mar 26, 2026
- **Workshop:** During CHI 2026, Apr 13-17, Barcelona

## Contact
chi.tft.workshop@gmail.com
