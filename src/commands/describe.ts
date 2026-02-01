import { writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { getLucidDir } from '../lib/config.js';
import { exists } from '../lib/fs-utils.js';

function getSourcesDir(cwd: string = process.cwd()): string {
  return join(getLucidDir(cwd), 'sources');
}

async function fetchPage(url: string): Promise<string> {
  const response = await fetch(url, {
    headers: {
      'User-Agent':
        'Mozilla/5.0 (compatible; LUCID-Auditor/1.0; +https://franklabs.io/lucid)',
      Accept: 'text/html,application/xhtml+xml,text/plain',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const contentType = response.headers.get('content-type') || '';
  const text = await response.text();

  // If it's HTML, strip tags to get meaningful text
  if (contentType.includes('html')) {
    return stripHtml(text);
  }

  return text;
}

function stripHtml(html: string): string {
  // Remove script, style, nav, footer, header elements entirely
  let text = html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<nav[\s\S]*?<\/nav>/gi, '')
    .replace(/<footer[\s\S]*?<\/footer>/gi, '');

  // Convert common block elements to newlines
  text = text
    .replace(/<\/?(h[1-6]|p|div|section|article|li|tr|br|hr)[^>]*>/gi, '\n')
    .replace(/<\/?(ul|ol|table|thead|tbody)[^>]*>/gi, '\n');

  // Remove all remaining tags
  text = text.replace(/<[^>]+>/g, '');

  // Decode common HTML entities
  text = text
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/&#x27;/g, "'")
    .replace(/&#x2F;/g, '/')
    .replace(/&mdash;/g, '—')
    .replace(/&ndash;/g, '–')
    .replace(/&hellip;/g, '...')
    .replace(/&#\d+;/g, '');

  // Clean up whitespace
  text = text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .join('\n');

  return text;
}

function slugifyUrl(url: string): string {
  try {
    const parsed = new URL(url);
    return (parsed.hostname + parsed.pathname)
      .replace(/[^a-z0-9]+/gi, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 80);
  } catch {
    return url.replace(/[^a-z0-9]+/gi, '-').slice(0, 80);
  }
}

export async function describeCommand(options: {
  url?: string[];
}): Promise<void> {
  const urls = options.url;
  if (!urls || urls.length === 0) {
    console.error('  Error: At least one --url is required.');
    console.error('  Usage: lucid describe --url https://example.com/tos');
    process.exit(1);
  }

  const sourcesDir = getSourcesDir();
  if (!(await exists(sourcesDir))) {
    await mkdir(sourcesDir, { recursive: true });
  }

  console.log(`\n  LUCID — Fetching source documents`);
  console.log(`  ─────────────────────────────────────\n`);

  const saved: string[] = [];

  for (const url of urls) {
    console.log(`  Fetching: ${url}`);
    try {
      const content = await fetchPage(url);
      const slug = slugifyUrl(url);
      const filename = `${slug}.txt`;
      const filepath = join(sourcesDir, filename);

      // Prepend source URL as metadata
      const withMeta = `# Source: ${url}\n# Fetched: ${new Date().toISOString()}\n\n${content}`;
      await writeFile(filepath, withMeta, 'utf-8');

      const lineCount = content.split('\n').length;
      console.log(`  Saved: .lucid/sources/${filename} (${lineCount} lines)`);
      saved.push(filename);
    } catch (err) {
      console.error(
        `  Error fetching ${url}: ${err instanceof Error ? err.message : err}`,
      );
    }
  }

  if (saved.length === 0) {
    console.error('\n  No documents fetched successfully.');
    process.exit(1);
  }

  console.log(`\n  ─────────────────────────────────────`);
  console.log(`  Fetched ${saved.length} document(s) to .lucid/sources/`);
  console.log(`\n  Next: Run \`lucid extract --source <filename>\` to extract claims.`);
  console.log(`  Or: Run \`lucid hallucinate\` to generate a hallucinated spec instead.\n`);
}
