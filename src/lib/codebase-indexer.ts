import { readdir, readFile, stat } from 'node:fs/promises';
import { join, relative, extname } from 'node:path';
import { exists } from './fs-utils.js';

export interface CodebaseIndex {
  rootPath: string;
  totalFiles: number;
  fileTree: string[];
  frameworks: string[];
  keyFiles: KeyFile[];
  summary: string;
}

interface KeyFile {
  path: string;
  reason: string;
}

const IGNORE_DIRS = new Set([
  'node_modules', '.git', '.next', '.vercel', '.lucid', 'dist', 'build',
  'out', '.cache', 'coverage', '__pycache__', '.venv', 'venv',
  '.turbo', '.nuxt', '.svelte-kit', 'vendor',
]);

const CODE_EXTENSIONS = new Set([
  '.ts', '.tsx', '.js', '.jsx', '.py', '.rb', '.go', '.rs', '.java',
  '.cs', '.php', '.swift', '.kt', '.scala', '.vue', '.svelte',
  '.sql', '.graphql', '.gql', '.prisma',
]);

const CONFIG_FILES = new Set([
  'package.json', 'tsconfig.json', 'next.config.js', 'next.config.ts',
  'next.config.mjs', 'vite.config.ts', 'vite.config.js',
  'nuxt.config.ts', 'svelte.config.js',
  'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
  '.env.example', '.env.local.example',
  'prisma/schema.prisma', 'drizzle.config.ts',
  'supabase/config.toml',
  'vercel.json', 'fly.toml', 'railway.toml',
  'wrangler.toml', 'Procfile',
]);

const SCHEMA_PATTERNS = [
  'schema.prisma', 'schema.sql', 'schema.graphql',
  'drizzle', 'migrations',
];

async function walkDir(
  dir: string,
  root: string,
  files: string[],
  maxFiles: number,
): Promise<void> {
  if (files.length >= maxFiles) return;

  let entries;
  try {
    entries = await readdir(dir, { withFileTypes: true });
  } catch {
    return;
  }

  for (const entry of entries) {
    if (files.length >= maxFiles) return;

    if (entry.isDirectory()) {
      if (IGNORE_DIRS.has(entry.name) || entry.name.startsWith('.')) continue;
      await walkDir(join(dir, entry.name), root, files, maxFiles);
    } else {
      const relPath = relative(root, join(dir, entry.name));
      files.push(relPath);
    }
  }
}

function detectFrameworks(files: string[]): string[] {
  const frameworks: string[] = [];
  const fileSet = new Set(files);

  if (fileSet.has('package.json')) frameworks.push('Node.js');
  if (files.some((f) => f.includes('next.config'))) frameworks.push('Next.js');
  if (files.some((f) => f.includes('nuxt.config'))) frameworks.push('Nuxt');
  if (files.some((f) => f.includes('svelte.config'))) frameworks.push('SvelteKit');
  if (files.some((f) => f.includes('vite.config'))) frameworks.push('Vite');
  if (fileSet.has('requirements.txt') || fileSet.has('pyproject.toml')) frameworks.push('Python');
  if (fileSet.has('Gemfile')) frameworks.push('Ruby');
  if (fileSet.has('go.mod')) frameworks.push('Go');
  if (fileSet.has('Cargo.toml')) frameworks.push('Rust');
  if (files.some((f) => f.includes('prisma/schema.prisma'))) frameworks.push('Prisma');
  if (files.some((f) => f.includes('supabase/'))) frameworks.push('Supabase');
  if (fileSet.has('Dockerfile')) frameworks.push('Docker');
  if (fileSet.has('vercel.json') || files.some((f) => f.includes('.vercel'))) frameworks.push('Vercel');

  return frameworks;
}

function identifyKeyFiles(files: string[]): KeyFile[] {
  const keyFiles: KeyFile[] = [];

  for (const file of files) {
    const basename = file.split('/').pop() || '';

    if (CONFIG_FILES.has(basename)) {
      keyFiles.push({ path: file, reason: 'configuration' });
      continue;
    }

    if (SCHEMA_PATTERNS.some((p) => file.includes(p))) {
      keyFiles.push({ path: file, reason: 'schema/database' });
      continue;
    }

    // API routes
    if (file.includes('/api/') && CODE_EXTENSIONS.has(extname(file))) {
      keyFiles.push({ path: file, reason: 'API route' });
      continue;
    }

    // Auth-related files
    if (
      /auth|login|session|middleware/i.test(file) &&
      CODE_EXTENSIONS.has(extname(file))
    ) {
      keyFiles.push({ path: file, reason: 'authentication' });
      continue;
    }

    // Config/env handling
    if (/config|env|secret/i.test(basename) && CODE_EXTENSIONS.has(extname(file))) {
      keyFiles.push({ path: file, reason: 'configuration' });
    }
  }

  return keyFiles;
}

export async function indexCodebase(
  rootPath: string,
  maxFiles = 5000,
): Promise<CodebaseIndex> {
  if (!(await exists(rootPath))) {
    throw new Error(`Codebase path does not exist: ${rootPath}`);
  }

  const fileInfo = await stat(rootPath);
  if (!fileInfo.isDirectory()) {
    throw new Error(`Path is not a directory: ${rootPath}`);
  }

  const files: string[] = [];
  await walkDir(rootPath, rootPath, files, maxFiles);

  const codeFiles = files.filter((f) => CODE_EXTENSIONS.has(extname(f)));
  const frameworks = detectFrameworks(files);
  const keyFiles = identifyKeyFiles(files);

  const summary = [
    `Codebase at: ${rootPath}`,
    `Total files: ${files.length} (${codeFiles.length} code files)`,
    `Frameworks: ${frameworks.join(', ') || 'unknown'}`,
    `Key files: ${keyFiles.length}`,
  ].join('\n');

  return {
    rootPath,
    totalFiles: files.length,
    fileTree: files,
    frameworks,
    keyFiles,
    summary,
  };
}

export async function readFileContent(
  rootPath: string,
  relativePath: string,
): Promise<string | null> {
  const fullPath = join(rootPath, relativePath);
  try {
    const content = await readFile(fullPath, 'utf-8');
    // Truncate very large files
    if (content.length > 50_000) {
      return content.slice(0, 50_000) + '\n\n[... truncated at 50K chars]';
    }
    return content;
  } catch {
    return null;
  }
}
