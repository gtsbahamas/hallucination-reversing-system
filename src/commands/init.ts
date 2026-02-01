import { configExists, writeConfig } from '../lib/config.js';
import { prompt, confirm, closePrompts } from '../lib/prompts.js';
import type { LucidConfig } from '../types.js';

export async function initCommand(): Promise<void> {
  console.log('\n  LUCID — Project Initialization\n');

  if (await configExists()) {
    const overwrite = await confirm('  .lucid/config.json already exists. Overwrite?');
    if (!overwrite) {
      console.log('  Aborted.');
      return;
    }
  }

  const projectName = await prompt('  Project name');
  if (!projectName) {
    console.error('  Error: Project name is required.');
    process.exit(1);
  }

  const description = await prompt('  Description (what does it do?)');
  if (!description) {
    console.error('  Error: Description is required.');
    process.exit(1);
  }

  const techStack = await prompt('  Tech stack', 'TypeScript, Node.js');
  const targetAudience = await prompt('  Target audience', 'developers');

  closePrompts();

  const config: LucidConfig = {
    projectName,
    description,
    techStack,
    targetAudience,
    createdAt: new Date().toISOString(),
  };

  await writeConfig(config);

  console.log('\n  Created:');
  console.log('    .lucid/config.json');
  console.log('    .lucid/iterations/');
  console.log('\n  Tip: Add .lucid/ to your .gitignore');
  console.log(`\n  Next: Run \`lucid hallucinate\` to generate your first hallucinated spec.\n`);
}
