#!/usr/bin/env node

import { resolve, extname } from 'node:path';
import { readFile, writeFile } from 'node:fs/promises';
import { appendFileSync } from 'node:fs';
import { indexCodebase, readFileContent } from './indexer.js';
import { extractClaimsFromCodebase, extractClaimsFromDocument } from './extractor.js';
import { verifyClaims } from './verifier.js';
import { buildPrComment } from './comment-builder.js';
import { detectMode, verifyViaLucidApi } from './anthropic.js';
import type { ActionInputs, Claim, ClaimVerification, VerificationSummary, ForwardResponse } from './types.js';
import type { CodebaseIndex } from './indexer.js';

// ── Language detection ───────────────────────────────────────

const EXT_TO_LANGUAGE: Record<string, string> = {
  '.ts': 'typescript', '.tsx': 'typescript', '.js': 'javascript', '.jsx': 'javascript',
  '.py': 'python', '.rb': 'ruby', '.go': 'go', '.rs': 'rust', '.java': 'java',
  '.cs': 'csharp', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
  '.scala': 'scala', '.vue': 'vue', '.svelte': 'svelte',
  '.sql': 'sql', '.graphql': 'graphql', '.gql': 'graphql', '.prisma': 'prisma',
};

function detectLanguage(filePath: string): string {
  return EXT_TO_LANGUAGE[extname(filePath)] || 'text';
}

// ── Category mapping (API → Action) ─────────────────────────

const API_CATEGORY_MAP: Record<string, Claim['category']> = {
  'correctness': 'functionality',
  'security': 'security',
  'performance': 'operational',
  'error-handling': 'functionality',
  'edge-case': 'functionality',
  'type-safety': 'functionality',
};

// ── CLI argument parsing ─────────────────────────────────────

function parseArgs(): ActionInputs {
  const args = process.argv.slice(2);
  const map = new Map<string, string>();

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--') && i + 1 < args.length) {
      map.set(args[i].slice(2), args[i + 1]);
      i++;
    }
  }

  const mode = detectMode();

  return {
    workingDirectory: map.get('working-directory') || '.',
    scanMode: (map.get('scan-mode') || 'changed') as 'full' | 'changed',
    failThreshold: parseFloat(map.get('fail-threshold') || '0'),
    docSource: map.get('doc-source') || '',
    changedFilesMode: (map.get('changed-files-mode') || 'full') as 'full' | 'changed',
    mode,
  };
}

function setOutput(name: string, value: string): void {
  const outputFile = process.env.GITHUB_OUTPUT;
  if (outputFile) {
    appendFileSync(outputFile, `${name}=${value}\n`);
  }
  console.log(`::set-output name=${name}::${value}`);
}

function log(msg: string): void {
  console.log(`[LUCID] ${msg}`);
}

async function loadChangedFiles(): Promise<string[] | undefined> {
  try {
    const content = await readFile('/tmp/lucid-changed-files.txt', 'utf-8');
    const files = content.trim().split('\n').filter(Boolean);
    return files.length > 0 ? files : undefined;
  } catch {
    return undefined;
  }
}

async function fetchDocument(url: string): Promise<string> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch document: ${response.status} ${response.statusText}`);
  }
  return response.text();
}

// ── LUCID API Mode ───────────────────────────────────────────

/**
 * Convert a ForwardResponse from the LUCID API into Action-compatible
 * claims and verifications, scoped to a specific file.
 */
function mapForwardResponse(
  resp: ForwardResponse,
  filePath: string,
  claimOffset: number,
): { claims: Claim[]; verifications: ClaimVerification[] } {
  const claims: Claim[] = resp.claims.items.map((fc, i) => ({
    id: `CLAIM-${String(claimOffset + i + 1).padStart(3, '0')}`,
    section: filePath,
    category: API_CATEGORY_MAP[fc.category] || 'functionality',
    severity: fc.severity,
    text: fc.description,
    testable: fc.testable,
  }));

  // Build a map from original API claim IDs to our new IDs
  const idMap = new Map<string, string>();
  resp.claims.items.forEach((fc, i) => {
    idMap.set(fc.id, claims[i].id);
  });

  const verifications: ClaimVerification[] = resp.verification.items.map((fv) => {
    const newId = idMap.get(fv.claimId) || fv.claimId;
    const claim = claims.find((c) => c.id === newId);
    return {
      claimId: newId,
      claim: claim?.text || '',
      verdict: fv.verdict,
      evidence: fv.evidence
        ? [{ file: filePath, snippet: fv.evidence, confidence: 0.8 }]
        : [],
      reasoning: fv.reasoning,
    };
  });

  // Any claims not in verification items get N/A
  for (const claim of claims) {
    if (!verifications.some((v) => v.claimId === claim.id)) {
      verifications.push({
        claimId: claim.id,
        claim: claim.text,
        verdict: 'N/A',
        evidence: [],
        reasoning: 'No verification result returned from API.',
      });
    }
  }

  return { claims, verifications };
}

async function runLucidApiMode(
  inputs: ActionInputs,
  index: CodebaseIndex,
  changedFiles: string[] | undefined,
): Promise<{
  summary: VerificationSummary;
  tokensIn: number;
  tokensOut: number;
}> {
  // Determine which files to verify
  const filesToVerify = changedFiles || index.keyFiles.map((f) => f.path);

  if (filesToVerify.length === 0) {
    log('No files to verify.');
    return {
      summary: {
        complianceScore: 100,
        totalClaims: 0,
        passCount: 0,
        failCount: 0,
        partialCount: 0,
        naCount: 0,
        criticalFails: [],
        topIssues: [],
        verifications: [],
        claims: [],
      },
      tokensIn: 0,
      tokensOut: 0,
    };
  }

  log(`Verifying ${filesToVerify.length} file(s) via LUCID API...`);

  const allClaims: Claim[] = [];
  const allVerifications: ClaimVerification[] = [];
  let totalTokensIn = 0;
  let totalTokensOut = 0;

  for (let i = 0; i < filesToVerify.length; i++) {
    const filePath = filesToVerify[i];
    const content = await readFileContent(index.rootPath, filePath);

    if (!content) {
      log(`  [${i + 1}/${filesToVerify.length}] ${filePath} — skipped (unreadable)`);
      continue;
    }

    const language = detectLanguage(filePath);
    log(`  [${i + 1}/${filesToVerify.length}] ${filePath} (${language})...`);

    try {
      const resp = await verifyViaLucidApi(content, language);
      const { claims, verifications } = mapForwardResponse(resp, filePath, allClaims.length);

      allClaims.push(...claims);
      allVerifications.push(...verifications);
      totalTokensIn += resp.usage.input_tokens;
      totalTokensOut += resp.usage.output_tokens;

      log(`    → ${resp.verification.passed} pass, ${resp.verification.failed} fail, ${resp.verification.partial} partial`);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      log(`    → ERROR: ${message}`);

      // If quota exceeded, stop early
      if (message.includes('quota exceeded')) {
        log('Stopping: LUCID API quota exceeded.');
        break;
      }
    }
  }

  // Compute summary
  return {
    summary: computeSummary(allClaims, allVerifications),
    tokensIn: totalTokensIn,
    tokensOut: totalTokensOut,
  };
}

// ── Shared summary computation ───────────────────────────────

function computeSummary(
  claims: Claim[],
  verifications: ClaimVerification[],
): VerificationSummary {
  const verdicts = { pass: 0, partial: 0, fail: 0, na: 0 };
  for (const v of verifications) {
    const key = v.verdict.toLowerCase().replace('/', '') as keyof typeof verdicts;
    if (key in verdicts) verdicts[key]++;
  }

  const total = verifications.length;
  const assessed = total - verdicts.na;
  const complianceScore = assessed > 0
    ? ((verdicts.pass + verdicts.partial * 0.5) / assessed) * 100
    : 100;

  const claimMap = new Map(claims.map((c) => [c.id, c]));

  const criticalFails = verifications.filter((v) => {
    if (v.verdict !== 'FAIL') return false;
    const claim = claimMap.get(v.claimId);
    return claim?.severity === 'critical';
  });

  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  const topIssues = verifications
    .filter((v) => v.verdict === 'FAIL' || v.verdict === 'PARTIAL')
    .sort((a, b) => {
      if (a.verdict !== b.verdict) return a.verdict === 'FAIL' ? -1 : 1;
      const aClaim = claimMap.get(a.claimId);
      const bClaim = claimMap.get(b.claimId);
      const aSev = severityOrder[aClaim?.severity || 'medium'] ?? 2;
      const bSev = severityOrder[bClaim?.severity || 'medium'] ?? 2;
      return aSev - bSev;
    });

  return {
    complianceScore,
    totalClaims: total,
    passCount: verdicts.pass,
    failCount: verdicts.fail,
    partialCount: verdicts.partial,
    naCount: verdicts.na,
    criticalFails,
    topIssues,
    verifications,
    claims,
  };
}

// ── BYOK Mode (existing flow) ────────────────────────────────

async function runByokMode(
  inputs: ActionInputs,
  index: CodebaseIndex,
): Promise<{
  summary: VerificationSummary;
  tokensIn: number;
  tokensOut: number;
}> {
  // Step 2: Extract claims
  let claims: Claim[];
  let extractTokensIn = 0;
  let extractTokensOut = 0;

  if (inputs.docSource) {
    log(`Fetching document from: ${inputs.docSource}`);
    const docContent = await fetchDocument(inputs.docSource);
    const result = await extractClaimsFromDocument(docContent, log);
    claims = result.claims;
    extractTokensIn = result.inputTokens;
    extractTokensOut = result.outputTokens;
  } else {
    const keyFileSummary = index.keyFiles
      .map((f) => `${f.path} (${f.reason})`)
      .join('\n');
    const result = await extractClaimsFromCodebase(index.fileTree, keyFileSummary, log);
    claims = result.claims;
    extractTokensIn = result.inputTokens;
    extractTokensOut = result.outputTokens;
  }

  if (claims.length === 0) {
    return {
      summary: {
        complianceScore: 100,
        totalClaims: 0,
        passCount: 0,
        failCount: 0,
        partialCount: 0,
        naCount: 0,
        criticalFails: [],
        topIssues: [],
        verifications: [],
        claims: [],
      },
      tokensIn: extractTokensIn,
      tokensOut: extractTokensOut,
    };
  }

  // Step 3: Verify claims against codebase
  log('Verifying claims against codebase...');
  const { verifications, inputTokens: verifyTokensIn, outputTokens: verifyTokensOut } =
    await verifyClaims(claims, index, log);

  return {
    summary: computeSummary(claims, verifications),
    tokensIn: extractTokensIn + verifyTokensIn,
    tokensOut: extractTokensOut + verifyTokensOut,
  };
}

// ── Main ─────────────────────────────────────────────────────

async function main(): Promise<void> {
  const inputs = parseArgs();
  const workDir = resolve(inputs.workingDirectory);

  log('Starting LUCID verification');
  log(`Mode: ${inputs.mode === 'lucid-api' ? 'LUCID API' : 'BYOK (Anthropic)'}`);
  log(`Working directory: ${workDir}`);
  log(`Scan mode: ${inputs.scanMode}`);
  log(`Fail threshold: ${inputs.failThreshold}%`);

  // Step 1: Index the codebase
  log('Indexing codebase...');
  const changedFiles = inputs.changedFilesMode === 'changed'
    ? await loadChangedFiles()
    : undefined;

  if (changedFiles) {
    log(`Analyzing ${changedFiles.length} changed files`);
  }

  const index = await indexCodebase(workDir, changedFiles);
  log(index.summary);

  // Step 2-4: Run verification (mode-specific)
  let result: { summary: VerificationSummary; tokensIn: number; tokensOut: number };

  if (inputs.mode === 'lucid-api') {
    result = await runLucidApiMode(inputs, index, changedFiles);
  } else {
    result = await runByokMode(inputs, index);
  }

  const { summary, tokensIn, tokensOut } = result;

  // Handle empty results
  if (summary.totalClaims === 0) {
    log('No claims extracted. Nothing to verify.');
    setOutput('compliance-score', '100');
    setOutput('total-claims', '0');
    setOutput('pass-count', '0');
    setOutput('fail-count', '0');
    setOutput('partial-count', '0');

    const comment = [
      '## LUCID Verification Report',
      '',
      'No testable claims were extracted from this codebase. This may indicate:',
      '- The codebase is too small to analyze',
      '- No security, privacy, or compliance-relevant patterns were detected',
      '',
      '---',
      '*Powered by [LUCID](https://trylucid.dev) — AI code verification that catches what tests miss*',
    ].join('\n');
    await writeFile('/tmp/lucid-pr-comment.md', comment, 'utf-8');
    return;
  }

  // Step 5: Set outputs
  setOutput('compliance-score', summary.complianceScore.toFixed(1));
  setOutput('total-claims', String(summary.totalClaims));
  setOutput('pass-count', String(summary.passCount));
  setOutput('fail-count', String(summary.failCount));
  setOutput('partial-count', String(summary.partialCount));

  // Step 6: Build and save PR comment
  const comment = buildPrComment(summary);
  await writeFile('/tmp/lucid-pr-comment.md', comment, 'utf-8');
  log(`PR comment saved to /tmp/lucid-pr-comment.md`);

  // Step 7: Print summary
  log('');
  log('=== LUCID Verification Complete ===');
  log(`Mode: ${inputs.mode === 'lucid-api' ? 'LUCID API' : 'BYOK'}`);
  log(`Compliance score: ${summary.complianceScore.toFixed(1)}%`);
  log(`Claims: ${summary.totalClaims} total, ${summary.passCount} pass, ${summary.partialCount} partial, ${summary.failCount} fail, ${summary.naCount} n/a`);
  if (summary.criticalFails.length > 0) {
    log(`CRITICAL FAILURES: ${summary.criticalFails.length}`);
    for (const f of summary.criticalFails) {
      log(`  ${f.claimId}: ${f.claim}`);
    }
  }
  log(`API usage: ${tokensIn.toLocaleString()} input + ${tokensOut.toLocaleString()} output tokens`);
  log('===================================');

  // Step 8: Save report artifact
  const reportPath = '/tmp/lucid-report.json';
  await writeFile(reportPath, JSON.stringify({
    mode: inputs.mode,
    complianceScore: summary.complianceScore,
    verdicts: {
      pass: summary.passCount,
      partial: summary.partialCount,
      fail: summary.failCount,
      na: summary.naCount,
    },
    verifications: summary.verifications,
    claims: summary.claims,
    tokensUsed: { input: tokensIn, output: tokensOut },
    generatedAt: new Date().toISOString(),
  }, null, 2), 'utf-8');
  setOutput('report-path', reportPath);
}

main().catch((err) => {
  console.error(`[LUCID] Fatal error: ${err instanceof Error ? err.message : String(err)}`);
  if (err instanceof Error && err.stack) {
    console.error(err.stack);
  }
  process.exit(1);
});
