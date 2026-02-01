import { readdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { readConfig, getIterationsDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { indexCodebase } from '../lib/codebase-indexer.js';
import { generateRemediationTasks } from '../lib/remediator.js';
import { generateRemediationReport } from '../lib/remediation-generator.js';
import type {
  ExtractionResult,
  VerificationReport,
  RemediationPlan,
} from '../types.js';

async function findLatestIteration(iterDir: string): Promise<number | null> {
  if (!(await exists(iterDir))) return null;
  const entries = await readdir(iterDir, { withFileTypes: true });
  const nums = entries
    .filter((e) => e.isDirectory())
    .map((e) => parseInt(e.name, 10))
    .filter((n) => !isNaN(n));
  return nums.length === 0 ? null : Math.max(...nums);
}

export async function remediateCommand(options: {
  iteration?: string;
  repo?: string;
  threshold?: string;
}): Promise<void> {
  const iterDir = getIterationsDir();
  const repoPath = resolve(options.repo || '.');
  const threshold = parseFloat(options.threshold || '95');

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
      console.error('  Error: No iterations found. Run the full pipeline first:');
      console.error('    lucid hallucinate → lucid extract → lucid verify');
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

  // Read inputs
  const extraction = JSON.parse(await readFile(claimsPath, 'utf-8')) as ExtractionResult;
  const verification = JSON.parse(await readFile(verificationPath, 'utf-8')) as VerificationReport;

  // Compute current score
  const { verdicts, verifications } = verification;
  const total = verifications.length;
  const assessed = total - verdicts.na;
  const currentScore =
    assessed > 0
      ? ((verdicts.pass + verdicts.partial * 0.5) / assessed) * 100
      : 0;

  // Check convergence
  if (currentScore >= threshold) {
    console.log(`\n  LUCID — Remediation (iteration ${iteration})`);
    console.log(`  ─────────────────────────────────────`);
    console.log(`\n  CONVERGED: Compliance score ${currentScore.toFixed(1)}% >= ${threshold}% threshold.`);
    console.log(`  No remediation tasks needed.\n`);
    return;
  }

  // Read config for project name
  let projectName: string | undefined;
  try {
    const config = await readConfig();
    projectName = config.projectName;
  } catch {
    // Config is optional for display purposes
  }

  console.log(`\n  LUCID — Generating remediation tasks (iteration ${iteration})`);
  console.log(`  Codebase:   ${repoPath}`);
  console.log(`  Score:      ${currentScore.toFixed(1)}% (target: ${threshold}%)`);
  console.log(`  Gap:        ${(threshold - currentScore).toFixed(1)} points`);
  console.log(`  ─────────────────────────────────────\n`);

  // Filter verifications
  const failVerifications = verifications.filter((v) => v.verdict === 'FAIL');
  const partialVerifications = verifications.filter((v) => v.verdict === 'PARTIAL');

  console.log(`  Claims to remediate: ${failVerifications.length} FAIL, ${partialVerifications.length} PARTIAL\n`);

  // Index codebase
  console.log(`  Indexing codebase...`);
  const index = await indexCodebase(repoPath);
  console.log(`  ${index.summary.split('\n').join('\n  ')}\n`);

  // Generate remediation tasks
  const startTime = Date.now();
  const { tasks, inputTokens, outputTokens } = await generateRemediationTasks(
    failVerifications,
    partialVerifications,
    extraction.claims,
    index,
    (msg) => console.log(`  ${msg}`),
  );
  const durationMs = Date.now() - startTime;

  // Build plan
  const tasksBySeverity = { critical: 0, high: 0, medium: 0, low: 0 };
  for (const t of tasks) {
    tasksBySeverity[t.severity]++;
  }

  const plan: RemediationPlan = {
    iteration,
    codebasePath: repoPath,
    currentScore,
    targetScore: threshold,
    totalTasks: tasks.length,
    tasksByVerdict: {
      fail: tasks.filter((t) => t.verdict === 'FAIL').length,
      partial: tasks.filter((t) => t.verdict === 'PARTIAL').length,
    },
    tasksBySeverity,
    tasks,
    generatedAt: new Date().toISOString(),
    inputTokens,
    outputTokens,
    durationMs,
  };

  // Write outputs
  const jsonPath = join(iterPath, 'remediation.json');
  const mdPath = join(iterPath, 'remediation.md');

  await writeFile(jsonPath, JSON.stringify(plan, null, 2) + '\n', 'utf-8');

  const report = generateRemediationReport(plan, projectName);
  await writeFile(mdPath, report, 'utf-8');

  // Print summary
  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Saved: .lucid/iterations/${iteration}/remediation.json`);
  console.log(`  Saved: .lucid/iterations/${iteration}/remediation.md`);

  console.log(`\n  Remediation Tasks: ${tasks.length}`);
  console.log(`    FAIL tasks:     ${plan.tasksByVerdict.fail}`);
  console.log(`    PARTIAL tasks:  ${plan.tasksByVerdict.partial}`);
  console.log(`\n  By severity:`);
  if (tasksBySeverity.critical > 0) console.log(`    Critical:  ${tasksBySeverity.critical}`);
  if (tasksBySeverity.high > 0) console.log(`    High:      ${tasksBySeverity.high}`);
  if (tasksBySeverity.medium > 0) console.log(`    Medium:    ${tasksBySeverity.medium}`);
  if (tasksBySeverity.low > 0) console.log(`    Low:       ${tasksBySeverity.low}`);

  // Show top priority tasks
  const topTasks = tasks.slice(0, 3);
  if (topTasks.length > 0) {
    console.log(`\n  Top priority tasks:`);
    for (const t of topTasks) {
      console.log(`    ${t.id} [${t.severity}] ${t.title}`);
      console.log(`      → ${t.targetFiles.join(', ')}`);
    }
  }

  console.log(`\n  Input tokens:    ${inputTokens.toLocaleString()}`);
  console.log(`  Output tokens:   ${outputTokens.toLocaleString()}`);
  console.log(`  Duration:        ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`\n  Fix the tasks above, then re-verify: \`lucid verify → lucid report\`\n`);
}
