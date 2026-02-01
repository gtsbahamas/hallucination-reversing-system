import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { getIterationsDir, readConfig } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { generateGapReport } from '../lib/report-generator.js';
import type { ExtractionResult, VerificationReport } from '../types.js';

async function findLatestIteration(iterDir: string): Promise<number | null> {
  if (!(await exists(iterDir))) return null;
  const entries = await readdir(iterDir, { withFileTypes: true });
  const nums = entries
    .filter((e) => e.isDirectory())
    .map((e) => parseInt(e.name, 10))
    .filter((n) => !isNaN(n));
  return nums.length === 0 ? null : Math.max(...nums);
}

export async function reportCommand(options: {
  iteration?: string;
}): Promise<void> {
  const iterDir = getIterationsDir();

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
      console.error('  Error: No iterations found.');
      process.exit(1);
    }
    iteration = latest;
  }

  const iterPath = join(iterDir, String(iteration));
  const claimsPath = join(iterPath, 'claims.json');
  const verificationPath = join(iterPath, 'verification.json');

  if (!(await exists(claimsPath))) {
    console.error(`  Error: No claims.json found for iteration ${iteration}.`);
    console.error('  Run `lucid extract` first.');
    process.exit(1);
  }

  if (!(await exists(verificationPath))) {
    console.error(`  Error: No verification.json found for iteration ${iteration}.`);
    console.error('  Run `lucid verify` first.');
    process.exit(1);
  }

  const extraction = JSON.parse(
    await readFile(claimsPath, 'utf-8'),
  ) as ExtractionResult;

  const verification = JSON.parse(
    await readFile(verificationPath, 'utf-8'),
  ) as VerificationReport;

  // Try to get project name from config
  let projectName: string | undefined;
  try {
    const config = await readConfig();
    projectName = config.projectName;
  } catch {
    // Config not required for report
  }

  console.log(`\n  LUCID — Generating gap report (iteration ${iteration})`);
  console.log(`  ─────────────────────────────────────\n`);

  const report = generateGapReport({
    extraction,
    verification,
    projectName,
  });

  const reportPath = join(iterPath, 'gap-report.md');
  await writeFile(reportPath, report, 'utf-8');

  const { verdicts } = verification;
  const total = verification.verifications.length;
  const assessed = total - verdicts.na;
  const score =
    assessed > 0
      ? ((verdicts.pass + verdicts.partial * 0.5) / assessed) * 100
      : 0;

  console.log(`  Saved: .lucid/iterations/${iteration}/gap-report.md`);
  console.log(`\n  Report Summary:`);
  console.log(`    Total claims:     ${total}`);
  console.log(`    PASS:             ${verdicts.pass}`);
  console.log(`    PARTIAL:          ${verdicts.partial}`);
  console.log(`    FAIL:             ${verdicts.fail}`);
  console.log(`    N/A:              ${verdicts.na}`);
  console.log(`    Compliance score: ${score.toFixed(1)}%`);
  console.log(`\n  The gap report is ready for delivery.\n`);
}
