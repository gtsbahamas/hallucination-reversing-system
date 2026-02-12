import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname } from 'node:path';
import { synthesizeSpecs } from '../lib/spec-synthesizer.js';
import { generateConstraints } from '../lib/constraint-engine.js';
import { generateWithConstraints } from '../lib/guided-generator.js';
import type { ReverseLucidResult } from '../types.js';

interface ReverseOptions {
  task?: string;
  taskFile?: string;
  lang: string;
  output?: string;
  verbose?: boolean;
}

export async function reverseCommand(options: ReverseOptions): Promise<void> {
  const startTime = Date.now();

  // Resolve task description
  let task: string;
  if (options.task) {
    task = options.task;
  } else if (options.taskFile) {
    try {
      task = (await readFile(options.taskFile, 'utf-8')).trim();
    } catch {
      console.error(`Error: Cannot read task file: ${options.taskFile}`);
      process.exit(1);
    }
  } else {
    console.error('Error: Provide --task or --task-file');
    process.exit(1);
  }

  if (!task) {
    console.error('Error: Task description is empty');
    process.exit(1);
  }

  const language = options.lang;
  const verbose = options.verbose ?? false;

  const progress = (msg: string) => {
    if (verbose) {
      console.error(`  ${msg}`);
    }
  };

  // ── Phase 1: Spec Synthesis ──────────────────────────────
  console.error('\n┌─ REVERSE LUCID ─────────────────────────────────┐');
  console.error(`│ Task: ${task.slice(0, 45)}${task.length > 45 ? '...' : ''}`);
  console.error(`│ Language: ${language}`);
  console.error('└─────────────────────────────────────────────────┘\n');

  console.error('▸ Phase 1/3: Synthesizing specifications...');
  const specResult = await synthesizeSpecs(task, language, progress);
  console.error(`  ✓ ${specResult.totalSpecs} specs generated`);

  if (verbose) {
    for (const spec of specResult.specs) {
      console.error(`    [${spec.id}] (${spec.severity}/${spec.category}) ${spec.description}`);
    }
  }

  // ── Phase 2: Constraint Generation ───────────────────────
  console.error('\n▸ Phase 2/3: Generating constraints...');
  const constraintResult = await generateConstraints(task, language, specResult.specs, progress);
  console.error(`  ✓ ${constraintResult.totalConstraints} constraints generated`);

  if (verbose) {
    const musts = constraintResult.constraints.filter(c => c.type === 'must');
    const mustNots = constraintResult.constraints.filter(c => c.type === 'must-not');
    const prefers = constraintResult.constraints.filter(c => c.type === 'prefer');
    console.error(`    MUST: ${musts.length} | MUST-NOT: ${mustNots.length} | PREFER: ${prefers.length}`);
  }

  // ── Phase 3: Guided Generation ───────────────────────────
  console.error('\n▸ Phase 3/3: Generating code with constraints...');
  const codeResult = await generateWithConstraints(
    task, language, specResult.specs, constraintResult.constraints, progress,
  );

  const satisfiedPct = codeResult.totalSpecs > 0
    ? ((codeResult.satisfiedCount / codeResult.totalSpecs) * 100).toFixed(1)
    : '0.0';

  console.error(`  ✓ Code generated — ${codeResult.satisfiedCount}/${codeResult.totalSpecs} specs satisfied (${satisfiedPct}%)`);

  if (verbose) {
    for (const sv of codeResult.selfVerification) {
      const icon = sv.status === 'satisfied' ? '✓'
        : sv.status === 'partial' ? '◐'
        : sv.status === 'unsatisfied' ? '✗'
        : '?';
      console.error(`    ${icon} ${sv.specId}: ${sv.reasoning.slice(0, 80)}`);
    }
  }

  // ── Output ───────────────────────────────────────────────
  const totalDurationMs = Date.now() - startTime;
  const totalInputTokens = specResult.inputTokens + constraintResult.inputTokens + codeResult.inputTokens;
  const totalOutputTokens = specResult.outputTokens + constraintResult.outputTokens + codeResult.outputTokens;

  if (options.output) {
    // Ensure output directory exists
    await mkdir(dirname(options.output), { recursive: true });
    await writeFile(options.output, codeResult.code, 'utf-8');
    console.error(`\n✓ Code written to: ${options.output}`);
  } else {
    // Write code to stdout
    process.stdout.write(codeResult.code);
  }

  // ── Summary ──────────────────────────────────────────────
  console.error('\n┌─ SUMMARY ───────────────────────────────────────┐');
  console.error(`│ Specs:       ${specResult.totalSpecs} synthesized`);
  console.error(`│ Constraints: ${constraintResult.totalConstraints} generated`);
  console.error(`│ Satisfied:   ${codeResult.satisfiedCount}/${codeResult.totalSpecs} (${satisfiedPct}%)`);
  console.error(`│ Tokens:      ${totalInputTokens.toLocaleString()} in / ${totalOutputTokens.toLocaleString()} out`);
  console.error(`│ Duration:    ${(totalDurationMs / 1000).toFixed(1)}s`);
  console.error('└─────────────────────────────────────────────────┘');

  // ── Write full result as JSON sidecar ────────────────────
  if (options.output) {
    const result: ReverseLucidResult = {
      task,
      language,
      specSynthesis: specResult,
      constraintSet: constraintResult,
      generatedCode: codeResult,
      totalInputTokens,
      totalOutputTokens,
      totalDurationMs,
    };

    const sidecarPath = options.output.replace(/\.[^.]+$/, '.reverse-lucid.json');
    await writeFile(sidecarPath, JSON.stringify(result, null, 2), 'utf-8');
    console.error(`✓ Full result written to: ${sidecarPath}`);
  }
}
