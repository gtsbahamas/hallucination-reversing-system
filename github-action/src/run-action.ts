#!/usr/bin/env node

import { resolve } from 'node:path';
import { readFile, writeFile } from 'node:fs/promises';
import { appendFileSync } from 'node:fs';
import { indexCodebase } from './indexer.js';
import { extractClaimsFromCodebase, extractClaimsFromDocument } from './extractor.js';
import { verifyClaims } from './verifier.js';
import { buildPrComment } from './comment-builder.js';
import type { ActionInputs, Claim, VerificationSummary } from './types.js';

function parseArgs(): ActionInputs {
  const args = process.argv.slice(2);
  const map = new Map<string, string>();

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--') && i + 1 < args.length) {
      map.set(args[i].slice(2), args[i + 1]);
      i++;
    }
  }

  return {
    workingDirectory: map.get('working-directory') || '.',
    scanMode: (map.get('scan-mode') || 'changed') as 'full' | 'changed',
    failThreshold: parseFloat(map.get('fail-threshold') || '0'),
    docSource: map.get('doc-source') || '',
    changedFilesMode: (map.get('changed-files-mode') || 'full') as 'full' | 'changed',
  };
}

function setOutput(name: string, value: string): void {
  const outputFile = process.env.GITHUB_OUTPUT;
  if (outputFile) {
    appendFileSync(outputFile, `${name}=${value}\n`);
  }
  // Also log for local testing
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

async function main(): Promise<void> {
  const inputs = parseArgs();
  const workDir = resolve(inputs.workingDirectory);

  log('Starting LUCID verification');
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

  // Step 3: Verify claims against codebase
  log('Verifying claims against codebase...');
  const { verifications, inputTokens: verifyTokensIn, outputTokens: verifyTokensOut } =
    await verifyClaims(claims, index, log);

  // Step 4: Compute results
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

  // Top issues: all FAILs sorted by severity, then PARTIALs
  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  const topIssues = verifications
    .filter((v) => v.verdict === 'FAIL' || v.verdict === 'PARTIAL')
    .sort((a, b) => {
      // FAILs first
      if (a.verdict !== b.verdict) return a.verdict === 'FAIL' ? -1 : 1;
      // Then by severity
      const aClaim = claimMap.get(a.claimId);
      const bClaim = claimMap.get(b.claimId);
      const aSev = severityOrder[aClaim?.severity || 'medium'] ?? 2;
      const bSev = severityOrder[bClaim?.severity || 'medium'] ?? 2;
      return aSev - bSev;
    });

  const summary: VerificationSummary = {
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

  // Step 5: Set outputs
  setOutput('compliance-score', complianceScore.toFixed(1));
  setOutput('total-claims', String(total));
  setOutput('pass-count', String(verdicts.pass));
  setOutput('fail-count', String(verdicts.fail));
  setOutput('partial-count', String(verdicts.partial));

  // Step 6: Build and save PR comment
  const comment = buildPrComment(summary);
  await writeFile('/tmp/lucid-pr-comment.md', comment, 'utf-8');
  log(`PR comment saved to /tmp/lucid-pr-comment.md`);

  // Step 7: Print summary
  const totalTokensIn = extractTokensIn + verifyTokensIn;
  const totalTokensOut = extractTokensOut + verifyTokensOut;

  log('');
  log('=== LUCID Verification Complete ===');
  log(`Compliance score: ${complianceScore.toFixed(1)}%`);
  log(`Claims: ${total} total, ${verdicts.pass} pass, ${verdicts.partial} partial, ${verdicts.fail} fail, ${verdicts.na} n/a`);
  if (criticalFails.length > 0) {
    log(`CRITICAL FAILURES: ${criticalFails.length}`);
    for (const f of criticalFails) {
      log(`  ${f.claimId}: ${f.claim}`);
    }
  }
  log(`API usage: ${totalTokensIn.toLocaleString()} input + ${totalTokensOut.toLocaleString()} output tokens`);
  log('===================================');

  // Step 8: Save report artifact
  const reportPath = '/tmp/lucid-report.json';
  await writeFile(reportPath, JSON.stringify({
    complianceScore,
    verdicts,
    verifications,
    claims,
    tokensUsed: { input: totalTokensIn, output: totalTokensOut },
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
