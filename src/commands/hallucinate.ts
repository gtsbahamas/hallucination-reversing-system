import { readdir, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { readConfig, getIterationsDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';
import { streamHallucination } from '../lib/anthropic.js';
import type { HallucinationType, HallucinationMeta } from '../types.js';

const VALID_TYPES: HallucinationType[] = ['tos', 'api-docs', 'user-manual'];

function countSections(content: string): number {
  // Count markdown headings (## or ###) as sections
  const headings = content.match(/^#{1,3}\s+.+$/gm);
  return headings?.length ?? 0;
}

function estimateClaims(content: string): number {
  // Heuristic: count sentences with specific numbers, named technologies,
  // or declarative statements about capabilities
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

async function getNextIteration(iterDir: string): Promise<number> {
  if (!(await exists(iterDir))) {
    return 1;
  }
  const entries = await readdir(iterDir, { withFileTypes: true });
  const nums = entries
    .filter(e => e.isDirectory())
    .map(e => parseInt(e.name, 10))
    .filter(n => !isNaN(n));

  return nums.length === 0 ? 1 : Math.max(...nums) + 1;
}

export async function hallucinateCommand(options: { type?: string }): Promise<void> {
  const type = (options.type ?? 'tos') as HallucinationType;
  if (!VALID_TYPES.includes(type)) {
    console.error(`  Error: Invalid type "${type}". Must be one of: ${VALID_TYPES.join(', ')}`);
    process.exit(1);
  }

  let config;
  try {
    config = await readConfig();
  } catch (err) {
    console.error(`  Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }

  const iterDir = getIterationsDir();
  const iteration = await getNextIteration(iterDir);

  console.log(`\n  LUCID — Hallucinating ${type} (iteration ${iteration})`);
  console.log(`  Project: ${config.projectName}`);
  console.log(`  ─────────────────────────────────────\n`);

  let result;
  const startTime = Date.now();
  try {
    result = await streamHallucination(config, type);
  } catch (err) {
    console.error(`\n  Error: ${err instanceof Error ? err.message : err}`);
    process.exit(1);
  }
  const durationMs = Date.now() - startTime;

  // Create iteration directory only after successful generation
  const iterPath = join(iterDir, String(iteration));
  await mkdir(iterPath, { recursive: true });

  // Save hallucinated document
  const docPath = join(iterPath, `hallucinated-${type}.md`);
  await writeFile(docPath, result.content, 'utf-8');

  // Compute stats
  const sectionCount = countSections(result.content);
  const estimatedClaims = estimateClaims(result.content);

  // Save metadata
  const meta: HallucinationMeta = {
    type,
    iteration,
    model: 'claude-sonnet-4-5-20250929',
    inputTokens: result.inputTokens,
    outputTokens: result.outputTokens,
    sectionCount,
    estimatedClaims,
    generatedAt: new Date().toISOString(),
    durationMs,
  };

  const metaPath = join(iterPath, 'meta.json');
  await writeFile(metaPath, JSON.stringify(meta, null, 2) + '\n', 'utf-8');

  // Print summary
  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Saved: .lucid/iterations/${iteration}/hallucinated-${type}.md`);
  console.log(`  Meta:  .lucid/iterations/${iteration}/meta.json`);
  console.log(`\n  Sections:         ${sectionCount}`);
  console.log(`  Estimated claims: ${estimatedClaims}`);
  console.log(`  Input tokens:     ${result.inputTokens.toLocaleString()}`);
  console.log(`  Output tokens:    ${result.outputTokens.toLocaleString()}`);
  console.log(`  Duration:         ${(durationMs / 1000).toFixed(1)}s\n`);
}
