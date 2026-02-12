#!/usr/bin/env node

import { Command } from 'commander';
import { initCommand } from './commands/init.js';
import { hallucinateCommand } from './commands/hallucinate.js';
import { extractCommand } from './commands/extract.js';
import { describeCommand } from './commands/describe.js';
import { verifyCommand } from './commands/verify.js';
import { reportCommand } from './commands/report.js';
import { regenerateCommand } from './commands/regenerate.js';
import { remediateCommand } from './commands/remediate.js';
import { reverseCommand } from './commands/reverse.js';

const program = new Command();

program
  .name('lucid')
  .description('LUCID — Leveraging Unverified Claims Into Deliverables')
  .version('0.1.0');

program
  .command('init')
  .description('Initialize a LUCID project in the current directory')
  .action(initCommand);

program
  .command('hallucinate')
  .description('Generate a hallucinated spec from your project config')
  .option('-t, --type <type>', 'Document type: tos, api-docs, user-manual', 'tos')
  .action(hallucinateCommand);

program
  .command('describe')
  .description('Fetch an existing ToS or Privacy Policy from a URL')
  .option('-u, --url <url...>', 'URL(s) to fetch')
  .action(describeCommand);

program
  .command('extract')
  .description('Extract testable claims from a hallucinated or described document')
  .option('-i, --iteration <number>', 'Iteration number (defaults to latest)')
  .option('-s, --source <filename>', 'Source file from .lucid/sources/ instead of iteration')
  .action(extractCommand);

program
  .command('verify')
  .description('Verify extracted claims against a codebase')
  .option('-r, --repo <path>', 'Path to the codebase to verify against', '.')
  .option('-i, --iteration <number>', 'Iteration number (defaults to latest)')
  .action(verifyCommand);

program
  .command('report')
  .description('Generate a gap report from verification results')
  .option('-i, --iteration <number>', 'Iteration number (defaults to latest)')
  .action(reportCommand);

program
  .command('regenerate')
  .description('Regenerate a hallucinated spec from prior verification results (Phase 6)')
  .option('-i, --iteration <number>', 'Source iteration to regenerate from (defaults to latest)')
  .action(regenerateCommand);

program
  .command('remediate')
  .description('Generate code-level fix tasks from verification results (converge code toward spec)')
  .option('-i, --iteration <number>', 'Iteration number (defaults to latest)')
  .option('-r, --repo <path>', 'Path to the codebase to remediate', '.')
  .option('-t, --threshold <number>', 'Compliance threshold (default: 95)', '95')
  .action(remediateCommand);

program
  .command('reverse')
  .description('Reverse LUCID — generate code with hallucination prevention')
  .option('-t, --task <task>', 'Coding task description')
  .option('-f, --task-file <path>', 'Read task from file')
  .option('-l, --lang <language>', 'Target language', 'typescript')
  .option('-o, --output <path>', 'Output file path')
  .option('-v, --verbose', 'Show detailed progress')
  .action(reverseCommand);

program.parse();
