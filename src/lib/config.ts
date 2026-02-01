import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { exists } from './fs-utils.js';
import type { LucidConfig } from '../types.js';

const LUCID_DIR = '.lucid';
const CONFIG_FILE = 'config.json';
const ITERATIONS_DIR = 'iterations';

export function getLucidDir(cwd: string = process.cwd()): string {
  return join(cwd, LUCID_DIR);
}

export function getConfigPath(cwd: string = process.cwd()): string {
  return join(getLucidDir(cwd), CONFIG_FILE);
}

export function getIterationsDir(cwd: string = process.cwd()): string {
  return join(getLucidDir(cwd), ITERATIONS_DIR);
}

export async function configExists(cwd: string = process.cwd()): Promise<boolean> {
  return exists(getConfigPath(cwd));
}

export async function readConfig(cwd: string = process.cwd()): Promise<LucidConfig> {
  const path = getConfigPath(cwd);
  if (!(await exists(path))) {
    throw new Error(
      'No .lucid/config.json found. Run `lucid init` first.'
    );
  }
  const raw = await readFile(path, 'utf-8');
  return JSON.parse(raw) as LucidConfig;
}

export async function writeConfig(config: LucidConfig, cwd: string = process.cwd()): Promise<void> {
  const lucidDir = getLucidDir(cwd);
  const iterDir = getIterationsDir(cwd);

  if (!(await exists(lucidDir))) {
    await mkdir(lucidDir, { recursive: true });
  }
  if (!(await exists(iterDir))) {
    await mkdir(iterDir, { recursive: true });
  }

  await writeFile(getConfigPath(cwd), JSON.stringify(config, null, 2) + '\n', 'utf-8');
}
