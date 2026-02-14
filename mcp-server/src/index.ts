#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { readFile, stat } from 'node:fs/promises';
import { extname, resolve } from 'node:path';
import { LucidClient } from './lucid-client.js';
import { formatForwardResult, formatReverseResult } from './formatters.js';

// ── Language detection ───────────────────────────────────────

const EXT_TO_LANGUAGE: Record<string, string> = {
  '.ts': 'typescript', '.tsx': 'typescript', '.js': 'javascript', '.jsx': 'javascript',
  '.py': 'python', '.rb': 'ruby', '.go': 'go', '.rs': 'rust', '.java': 'java',
  '.cs': 'csharp', '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
  '.scala': 'scala', '.vue': 'vue', '.svelte': 'svelte',
  '.sql': 'sql', '.graphql': 'graphql', '.gql': 'graphql', '.prisma': 'prisma',
};

const ALLOWED_EXTENSIONS = new Set(Object.keys(EXT_TO_LANGUAGE));

function detectLanguage(filePath: string): string | undefined {
  return EXT_TO_LANGUAGE[extname(filePath)];
}

// ── File size limits ─────────────────────────────────────────

const WARN_SIZE = 100 * 1024;  // 100KB
const MAX_SIZE = 500 * 1024;   // 500KB

// ── Server setup ─────────────────────────────────────────────

const apiKey = process.env.LUCID_API_KEY;
if (!apiKey) {
  console.error('LUCID_API_KEY environment variable is required.');
  console.error('Get a free API key at https://trylucid.dev');
  process.exit(1);
}

const client = new LucidClient(apiKey);

const server = new McpServer({
  name: 'lucid-mcp',
  version: '0.1.1',
});

// ── Tool: lucid_verify ───────────────────────────────────────

server.tool(
  'lucid_verify',
  'Verify code for hallucinations, bugs, and security issues. Extracts implicit claims from the code, verifies each one, and reports what would have shipped to production without verification.',
  {
    code: z.string().max(MAX_SIZE).describe('The code to verify'),
    language: z.string().optional().describe('Programming language (auto-detected if omitted)'),
    context: z.string().optional().describe('Additional context about what the code should do'),
  },
  async ({ code, language, context }) => {
    try {
      const resp = await client.forward({ code, language, context });
      const formatted = formatForwardResult(resp);
      return { content: [{ type: 'text' as const, text: formatted }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: 'text' as const, text: `Verification failed: ${message}` }], isError: true };
    }
  },
);

// ── Tool: lucid_verify_file ──────────────────────────────────

server.tool(
  'lucid_verify_file',
  'Verify a file for hallucinations by reading it from disk. Auto-detects language from file extension. Use this to verify code you just wrote.',
  {
    path: z.string().describe('Absolute path to the file to verify'),
    context: z.string().optional().describe('Additional context about what the code should do'),
  },
  async ({ path, context }) => {
    try {
      const resolved = resolve(path);
      const ext = extname(resolved);

      // Path traversal protection: only allow known code file extensions
      if (!ALLOWED_EXTENSIONS.has(ext)) {
        return {
          content: [{ type: 'text' as const, text: `File type '${ext}' is not a supported code file. Supported: ${[...ALLOWED_EXTENSIONS].join(', ')}` }],
          isError: true,
        };
      }

      // Check file size before reading into memory
      const fileStat = await stat(resolved);
      if (fileStat.size > MAX_SIZE) {
        return {
          content: [{ type: 'text' as const, text: `File too large (${(fileStat.size / 1024).toFixed(0)}KB). Maximum is ${MAX_SIZE / 1024}KB.` }],
          isError: true,
        };
      }

      let warning = '';
      if (fileStat.size > WARN_SIZE) {
        warning = `Note: Large file (${(fileStat.size / 1024).toFixed(0)}KB). Verification may take longer.\n\n`;
      }

      const content = await readFile(resolved, 'utf-8');
      const language = detectLanguage(resolved);
      const resp = await client.forward({ code: content, language, context });
      const formatted = formatForwardResult(resp);
      return { content: [{ type: 'text' as const, text: warning + formatted }] };
    } catch (err) {
      if (err instanceof Error && 'code' in err && (err as NodeJS.ErrnoException).code === 'ENOENT') {
        return { content: [{ type: 'text' as const, text: `File not found: ${path}` }], isError: true };
      }
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: 'text' as const, text: `Verification failed: ${message}` }], isError: true };
    }
  },
);

// ── Tool: lucid_generate ─────────────────────────────────────

server.tool(
  'lucid_generate',
  'Generate verified code from a task description. Synthesizes a spec, applies domain constraints, generates code, and self-verifies — producing code that has been checked before you see it.',
  {
    task: z.string().describe('Description of what the code should do'),
    language: z.string().optional().describe('Target programming language'),
  },
  async ({ task, language }) => {
    try {
      const resp = await client.reverse({ task, language });
      const formatted = formatReverseResult(resp);
      return { content: [{ type: 'text' as const, text: formatted }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: 'text' as const, text: `Generation failed: ${message}` }], isError: true };
    }
  },
);

// ── Tool: lucid_health ───────────────────────────────────────

server.tool(
  'lucid_health',
  'Check LUCID API status and verify your API key is working.',
  {},
  async () => {
    try {
      const result = await client.health();
      return {
        content: [{
          type: 'text' as const,
          text: `LUCID API is ${result.status}. Your API key is valid.${result.version ? ` Version: ${result.version}` : ''}`,
        }],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: 'text' as const, text: `LUCID API health check failed: ${message}` }], isError: true };
    }
  },
);

// ── Start ────────────────────────────────────────────────────

async function main(): Promise<void> {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('LUCID MCP server started');

  const shutdown = async () => {
    console.error('LUCID MCP server shutting down');
    await server.close();
    process.exit(0);
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

main().catch((err) => {
  const message = err instanceof Error ? err.message : 'Unknown error';
  console.error('Fatal error:', message);
  process.exit(1);
});
