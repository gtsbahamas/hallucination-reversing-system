import { readdir, readFile, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { readConfig, getIterationsDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { streamRegeneration } from '../lib/anthropic.js';
import type { RegenerationContext } from '../lib/system-prompts.js';
import type {
  HallucinationType,
  HallucinationMeta,
  ExtractionResult,
  VerificationReport,
} from '../types.js';

const VALID_TYPES: HallucinationType[] = ['tos', 'api-docs', 'user-manual'];

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
): Promise<{ path: string; type: HallucinationType } | null> {
  const entries = await readdir(iterPath);
  const doc = entries.find((e) => e.startsWith('hallucinated-') && e.endsWith('.md'));
  if (!doc) return null;
  const type = doc.replace('hallucinated-', '').replace('.md', '') as HallucinationType;
  if (!VALID_TYPES.includes(type)) return null;
  return { path: join(iterPath, doc), type };
}

function countSections(content: string): number {
  const headings = content.match(/^#{1,3}\s+.+$/gm);
  return headings?.length ?? 0;
}

function estimateClaims(content: string): number {
  const sentences = content.split(/[.!]\s+/);
  let claims = 0;
  for (const sentence of sentences) {
    const hasNumber = /\d+/.test(sentence);
    const hasDeclarative = /\b(is|are|will|provides?|supports?|includes?|requires?|limits?|allows?|ensures?|stores?|encrypts?|processes?|retains?)\b/i.test(sentence);
    const hasSpecific = /\b(GB|MB|TB|ms|seconds?|minutes?|hours?|days?|%|per|AES|SHA|RSA|SSL|TLS|HTTPS|OAuth|JWT|REST|GraphQL)\b/i.test(sentence);

    if (hasNumber || (hasDeclarative && hasSpecific)) {
      claims++;
    }
  }
  return claims;
}

export async function regenerateCommand(options: {
  iteration?: string;
}): Promise<void> {
  const iterDir = getIterationsDir();

  // Determine source iteration
  let sourceIteration: number;
  if (options.iteration) {
    sourceIteration = parseInt(options.iteration, 10);
    if (isNaN(sourceIteration)) {
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
    sourceIteration = latest;
  }

  const sourcePath = join(iterDir, String(sourceIteration));

  // Verify all required files exist
  const claimsPath = join(sourcePath, 'claims.json');
  const verificationPath = join(sourcePath, 'verification.json');

  if (!(await exists(claimsPath))) {
    console.error(`  Error: No claims.json found for iteration ${sourceIteration}.`);
    console.error('  Run `lucid extract` first.');
    process.exit(1);
  }

  if (!(await exists(verificationPath))) {
    console.error(`  Error: No verification.json found for iteration ${sourceIteration}.`);
    console.error('  Run `lucid verify` first.');
    process.exit(1);
  }

  const doc = await findHallucinatedDoc(sourcePath);
  if (!doc) {
    console.error(`  Error: No hallucinated-*.md found in iteration ${sourceIteration}.`);
    process.exit(1);
  }

  // Read all inputs
  let config;
  try {
    config = await readConfig();
  } catch (err) {
    console.error(`  Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }

  const priorDocument = await readFile(doc.path, 'utf-8');
  const extraction = JSON.parse(await readFile(claimsPath, 'utf-8')) as ExtractionResult;
  const verification = JSON.parse(await readFile(verificationPath, 'utf-8')) as VerificationReport;

  const { verdicts } = verification;
  const total = verification.verifications.length;
  const assessed = total - verdicts.na;
  const score = assessed > 0
    ? ((verdicts.pass + verdicts.partial * 0.5) / assessed) * 100
    : 0;

  const nextIteration = sourceIteration + 1;

  console.log(`\n  LUCID — Regenerating ${doc.type} (iteration ${sourceIteration} → ${nextIteration})`);
  console.log(`  Project: ${config.projectName}`);
  console.log(`  Prior compliance: ${score.toFixed(1)}% (${verdicts.pass} pass, ${verdicts.partial} partial, ${verdicts.fail} fail)`);
  console.log(`  ─────────────────────────────────────\n`);

  const ctx: RegenerationContext = {
    config,
    type: doc.type,
    priorDocument,
    extraction,
    verification,
  };

  let result;
  const startTime = Date.now();
  try {
    result = await streamRegeneration(ctx);
  } catch (err) {
    console.error(`\n  Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }
  const durationMs = Date.now() - startTime;

  // Create next iteration directory
  const nextPath = join(iterDir, String(nextIteration));
  await mkdir(nextPath, { recursive: true });

  // Save regenerated document
  const docPath = join(nextPath, `hallucinated-${doc.type}.md`);
  await writeFile(docPath, result.content, 'utf-8');

  // Compute stats
  const sectionCount = countSections(result.content);
  const estimatedClaimCount = estimateClaims(result.content);

  // Save metadata
  const meta: HallucinationMeta = {
    type: doc.type,
    iteration: nextIteration,
    model: 'claude-sonnet-4-5-20250929',
    inputTokens: result.inputTokens,
    outputTokens: result.outputTokens,
    sectionCount,
    estimatedClaims: estimatedClaimCount,
    generatedAt: new Date().toISOString(),
    durationMs,
  };

  const metaPath = join(nextPath, 'meta.json');
  await writeFile(metaPath, JSON.stringify(meta, null, 2) + '\n', 'utf-8');

  // Print summary
  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Saved: .lucid/iterations/${nextIteration}/hallucinated-${doc.type}.md`);
  console.log(`  Meta:  .lucid/iterations/${nextIteration}/meta.json`);
  console.log(`\n  Sections:         ${sectionCount}`);
  console.log(`  Estimated claims: ${estimatedClaimCount}`);
  console.log(`  Input tokens:     ${result.inputTokens.toLocaleString()}`);
  console.log(`  Output tokens:    ${result.outputTokens.toLocaleString()}`);
  console.log(`  Duration:         ${(durationMs / 1000).toFixed(1)}s`);
  console.log(`\n  The convergence loop continues.`);
  console.log(`  Next: Run \`lucid extract -i ${nextIteration}\` → \`lucid verify\` → \`lucid report\`\n`);
}
