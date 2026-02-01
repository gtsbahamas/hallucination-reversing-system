import { createInterface, type Interface } from 'node:readline/promises';
import { stdin, stdout } from 'node:process';

let rl: Interface | null = null;
let pipeLines: string[] | null = null;
let pipeLinesLoaded = false;

async function loadPipeLines(): Promise<void> {
  if (pipeLinesLoaded) return;
  pipeLinesLoaded = true;

  if (stdin.isTTY) return;

  // Read all lines from piped stdin upfront
  const chunks: Buffer[] = [];
  for await (const chunk of stdin) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const text = Buffer.concat(chunks).toString('utf-8');
  pipeLines = text.split('\n');
}

function getInterface(): Interface {
  if (!rl) {
    rl = createInterface({ input: stdin, output: stdout });
    rl.on('close', () => { rl = null; });
  }
  return rl;
}

export function closePrompts(): void {
  if (rl) {
    rl.close();
    rl = null;
  }
}

export async function prompt(question: string, defaultValue?: string): Promise<string> {
  const suffix = defaultValue ? ` (${defaultValue})` : '';
  const display = `${question}${suffix}: `;

  await loadPipeLines();

  if (pipeLines !== null) {
    const line = pipeLines.shift() ?? '';
    stdout.write(display + line + '\n');
    return line.trim() || defaultValue || '';
  }

  const iface = getInterface();
  const answer = await iface.question(display);
  return answer.trim() || defaultValue || '';
}

export async function confirm(question: string): Promise<boolean> {
  const answer = await prompt(`${question} [y/N]`);
  return answer.toLowerCase() === 'y';
}
