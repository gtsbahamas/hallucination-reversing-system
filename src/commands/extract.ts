import { readdir, readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { getLucidDir, getIterationsDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { extractClaims } from '../lib/claim-extractor.js';
import type { ExtractionResult, HallucinationMeta } from '../types.js';

async function findLatestIteration(iterDir: string): Promise<number | null> {
  if (!(await exists(iterDir))) return null;
  const entries = await readdir(iterDir, { withFileTypes: true });
  const nums = entries
    .filter((e) => e.isDirectory())
    .map((e) => parseInt(e.name, 10))
    .filter((n) => !isNaN(n));
  return nums.length === 0 ? null : Math.max(...nums);
}

async function findHallucinatedDoc(
  iterPath: string,
): Promise<{ path: string; type: string } | null> {
  const entries = await readdir(iterPath);
  const doc = entries.find((e) => e.startsWith('hallucinated-') && e.endsWith('.md'));
  if (!doc) return null;
  const type = doc.replace('hallucinated-', '').replace('.md', '');
  return { path: join(iterPath, doc), type };
}

export async function extractCommand(options: {
  iteration?: string;
  source?: string;
}): Promise<void> {
  const iterDir = getIterationsDir();
  let content: string;
  let docType: string;
  let iteration: number;
  let iterPath: string;
  let claimsPath: string;

  if (options.source) {
    // Extract from a described source document
    const sourcesDir = join(getLucidDir(), 'sources');
    const sourcePath = join(sourcesDir, options.source);
    if (!(await exists(sourcePath))) {
      console.error(`  Error: Source file not found: ${sourcePath}`);
      console.error(`  Run \`lucid describe --url <url>\` first.`);
      process.exit(1);
    }

    content = await readFile(sourcePath, 'utf-8');
    docType = 'source';

    // Create a new iteration for source-based extraction
    const latest = await findLatestIteration(iterDir);
    iteration = (latest ?? 0) + 1;
    iterPath = join(iterDir, String(iteration));
    await mkdir(iterPath, { recursive: true });
    claimsPath = join(iterPath, 'claims.json');

    console.log(`\n  LUCID — Extracting claims from source (iteration ${iteration})`);
    console.log(`  Source: ${options.source}`);
    console.log(`  ─────────────────────────────────────\n`);
  } else {
    // Extract from a hallucinated document
    if (options.iteration) {
      iteration = parseInt(options.iteration, 10);
      if (isNaN(iteration)) {
        console.error(`  Error: Invalid iteration "${options.iteration}". Must be a number.`);
        process.exit(1);
      }
    } else {
      const latest = await findLatestIteration(iterDir);
      if (latest === null) {
        console.error('  Error: No iterations found. Run `lucid hallucinate` first.');
        process.exit(1);
      }
      iteration = latest;
    }

    iterPath = join(iterDir, String(iteration));
    if (!(await exists(iterPath))) {
      console.error(`  Error: Iteration ${iteration} not found at ${iterPath}`);
      process.exit(1);
    }

    claimsPath = join(iterPath, 'claims.json');
    if (await exists(claimsPath)) {
      const existing = JSON.parse(await readFile(claimsPath, 'utf-8')) as ExtractionResult;
      console.log(`\n  Warning: claims.json already exists for iteration ${iteration}`);
      console.log(`  (${existing.totalClaims} claims, ${existing.testableClaims} testable)`);
      console.log(`  Overwriting...\n`);
    }

    const doc = await findHallucinatedDoc(iterPath);
    if (!doc) {
      console.error(`  Error: No hallucinated-*.md found in iteration ${iteration}.`);
      process.exit(1);
    }

    docType = doc.type;
    content = await readFile(doc.path, 'utf-8');

    console.log(`\n  LUCID — Extracting claims (iteration ${iteration})`);
    console.log(`  Source: hallucinated-${doc.type}.md`);
    console.log(`  ─────────────────────────────────────\n`);
  }

  // Extract claims
  const startTime = Date.now();
  const { claims, inputTokens, outputTokens } = await extractClaims(
    content,
    (msg) => console.log(`  ${msg}`),
  );
  const durationMs = Date.now() - startTime;

  const testableClaims = claims.filter((c) => c.testable).length;

  // Build extraction result
  const result: ExtractionResult = {
    iteration,
    documentType: docType,
    claims,
    totalClaims: claims.length,
    testableClaims,
    extractedAt: new Date().toISOString(),
  };

  // Save claims.json
  await writeFile(claimsPath, JSON.stringify(result, null, 2) + '\n', 'utf-8');

  // Update meta.json with actual extraction count
  const metaPath = join(iterPath, 'meta.json');
  if (await exists(metaPath)) {
    const meta = JSON.parse(await readFile(metaPath, 'utf-8')) as HallucinationMeta;
    meta.estimatedClaims = claims.length;
    await writeFile(metaPath, JSON.stringify(meta, null, 2) + '\n', 'utf-8');
  }

  // Print category breakdown
  const byCategory = new Map<string, number>();
  const bySeverity = new Map<string, number>();
  for (const claim of claims) {
    byCategory.set(claim.category, (byCategory.get(claim.category) || 0) + 1);
    bySeverity.set(claim.severity, (bySeverity.get(claim.severity) || 0) + 1);
  }

  // Print summary
  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Saved: .lucid/iterations/${iteration}/claims.json`);
  console.log(`\n  Total claims:    ${claims.length}`);
  console.log(`  Testable:        ${testableClaims}`);
  console.log(`  Non-testable:    ${claims.length - testableClaims}`);

  console.log(`\n  By category:`);
  for (const [cat, count] of [...byCategory.entries()].sort((a, b) => b[1] - a[1])) {
    console.log(`    ${cat.padEnd(16)} ${count}`);
  }

  console.log(`\n  By severity:`);
  for (const [sev, count] of [...bySeverity.entries()].sort((a, b) => {
    const order = ['critical', 'high', 'medium', 'low'];
    return order.indexOf(a[0]) - order.indexOf(b[0]);
  })) {
    console.log(`    ${sev.padEnd(16)} ${count}`);
  }

  console.log(`\n  Input tokens:    ${inputTokens.toLocaleString()}`);
  console.log(`  Output tokens:   ${outputTokens.toLocaleString()}`);
  console.log(`  Duration:        ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`\n  Next: Run \`lucid verify --repo /path/to/codebase\` to verify claims.\n`);
}
