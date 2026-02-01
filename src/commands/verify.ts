import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { getIterationsDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { indexCodebase } from '../lib/codebase-indexer.js';
import { verifyClaims } from '../lib/code-verifier.js';
import type { ExtractionResult, VerificationReport, Verdict } from '../types.js';

async function findLatestIteration(iterDir: string): Promise<number | null> {
  if (!(await exists(iterDir))) return null;
  const entries = await readdir(iterDir, { withFileTypes: true });
  const nums = entries
    .filter((e) => e.isDirectory())
    .map((e) => parseInt(e.name, 10))
    .filter((n) => !isNaN(n));
  return nums.length === 0 ? null : Math.max(...nums);
}

export async function verifyCommand(options: {
  repo?: string;
  iteration?: string;
}): Promise<void> {
  const iterDir = getIterationsDir();
  const repoPath = resolve(options.repo || '.');

  // Determine iteration
  let iteration: number;
  if (options.iteration) {
    iteration = parseInt(options.iteration, 10);
    if (isNaN(iteration)) {
      console.error(`  Error: Invalid iteration "${options.iteration}".`);
      process.exit(1);
    }
  } else {
    const latest = await findLatestIteration(iterDir);
    if (latest === null) {
      console.error('  Error: No iterations found. Run `lucid extract` first.');
      process.exit(1);
    }
    iteration = latest;
  }

  const iterPath = join(iterDir, String(iteration));
  const claimsPath = join(iterPath, 'claims.json');

  if (!(await exists(claimsPath))) {
    console.error(`  Error: No claims.json found for iteration ${iteration}.`);
    console.error('  Run `lucid extract` first.');
    process.exit(1);
  }

  const extraction = JSON.parse(
    await readFile(claimsPath, 'utf-8'),
  ) as ExtractionResult;

  console.log(`\n  LUCID — Verifying claims against codebase (iteration ${iteration})`);
  console.log(`  Codebase: ${repoPath}`);
  console.log(`  Claims:   ${extraction.totalClaims} (${extraction.testableClaims} testable)`);
  console.log(`  ─────────────────────────────────────\n`);

  // Index the codebase
  console.log(`  Indexing codebase...`);
  const index = await indexCodebase(repoPath);
  console.log(`  ${index.summary.split('\n').join('\n  ')}\n`);

  // Run verification
  const startTime = Date.now();
  const { verifications, inputTokens, outputTokens } = await verifyClaims(
    extraction.claims,
    index,
    (msg) => console.log(`  ${msg}`),
  );
  const durationMs = Date.now() - startTime;

  // Count verdicts
  const verdicts = { pass: 0, partial: 0, fail: 0, na: 0 };
  for (const v of verifications) {
    const key = v.verdict.toLowerCase().replace('/', '') as keyof typeof verdicts;
    if (key in verdicts) {
      verdicts[key]++;
    }
  }

  // Build report
  const report: VerificationReport = {
    iteration,
    codebasePath: repoPath,
    verdicts,
    verifications,
    generatedAt: new Date().toISOString(),
  };

  const reportPath = join(iterPath, 'verification.json');
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n', 'utf-8');

  // Print verdict table
  const total = verifications.length;
  const passRate =
    total > 0
      ? (((verdicts.pass + verdicts.partial * 0.5) / (total - verdicts.na)) * 100).toFixed(1)
      : '0.0';

  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Saved: .lucid/iterations/${iteration}/verification.json`);

  console.log(`\n  Verdict Distribution:`);
  console.log(`    PASS       ${String(verdicts.pass).padStart(4)}  ${bar(verdicts.pass, total)}`);
  console.log(`    PARTIAL    ${String(verdicts.partial).padStart(4)}  ${bar(verdicts.partial, total)}`);
  console.log(`    FAIL       ${String(verdicts.fail).padStart(4)}  ${bar(verdicts.fail, total)}`);
  console.log(`    N/A        ${String(verdicts.na).padStart(4)}  ${bar(verdicts.na, total)}`);
  console.log(`    ─────────────────`);
  console.log(`    Total      ${String(total).padStart(4)}`);
  console.log(`\n  Compliance score: ${passRate}%`);

  // Print critical failures
  const criticalFails = verifications.filter(
    (v) =>
      v.verdict === 'FAIL' &&
      extraction.claims.find((c) => c.id === v.claimId)?.severity === 'critical',
  );

  if (criticalFails.length > 0) {
    console.log(`\n  CRITICAL FAILURES (${criticalFails.length}):`);
    for (const f of criticalFails) {
      console.log(`    ${f.claimId}: ${f.claim}`);
      console.log(`      Reason: ${f.reasoning}`);
    }
  }

  console.log(`\n  Input tokens:    ${inputTokens.toLocaleString()}`);
  console.log(`  Output tokens:   ${outputTokens.toLocaleString()}`);
  console.log(`  Duration:        ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`\n  Next: Run \`lucid report\` to generate the gap report.\n`);
}

function bar(value: number, total: number): string {
  if (total === 0) return '';
  const width = 20;
  const filled = Math.round((value / total) * width);
  return '#'.repeat(filled) + '-'.repeat(width - filled);
}
