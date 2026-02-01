import type Anthropic from '@anthropic-ai/sdk';
import { getClient, MODEL } from './anthropic.js';
import { readFileContent } from './codebase-indexer.js';
import type { CodebaseIndex } from './codebase-indexer.js';
import type {
  Claim,
  ClaimVerification,
  RemediationAction,
  RemediationTask,
  ClaimSeverity,
  ClaimCategory,
} from '../types.js';

const VALID_ACTIONS: RemediationAction[] = ['add', 'modify', 'remove', 'configure'];
const VALID_EFFORTS = ['trivial', 'small', 'medium', 'large'] as const;

const REMEDIATION_SYSTEM = `You are a senior software engineer generating code-level fix tasks for a codebase that does not fully implement its specification.

For each failed or partially-implemented claim, produce a remediation task with:
- claimId: the original claim ID
- title: one-line fix description (imperative, e.g. "Add AES-256 encryption for data at rest")
- description: detailed guidance (2-4 sentences)
- action: one of "add" (new code/file), "modify" (change existing), "remove" (delete dead/wrong code), "configure" (env/config change)
- targetFiles: array of file paths to change or create
- estimatedEffort: "trivial" (< 10 lines), "small" (10-50 lines), "medium" (50-200 lines), "large" (> 200 lines)
- codeGuidance: specific code-level instructions (mention functions, modules, patterns to use)

OUTPUT FORMAT:
Return a JSON array of task objects:
[
  {
    "claimId": "CLAIM-001",
    "title": "Add rate limiting middleware",
    "description": "The API lacks rate limiting. Add express-rate-limit middleware to all public endpoints.",
    "action": "add",
    "targetFiles": ["src/middleware/rate-limit.ts", "src/app.ts"],
    "estimatedEffort": "small",
    "codeGuidance": "Create rate-limit.ts exporting a configurable middleware using express-rate-limit. Apply it in app.ts before route handlers. Use 100 req/15min for authenticated, 20 req/15min for unauthenticated."
  }
]

Rules:
- Be specific about files, functions, and patterns
- targetFiles should reference actual files from the codebase when modifying, or proposed new paths when adding
- codeGuidance should be actionable enough for a developer to implement without guessing
- For PARTIAL verdicts, focus on what's missing rather than what exists
- For FAIL verdicts, provide the full implementation approach

Return ONLY the JSON array. No markdown fences, no commentary.`;

interface RawTask {
  claimId?: string;
  title?: string;
  description?: string;
  action?: string;
  targetFiles?: string[];
  estimatedEffort?: string;
  codeGuidance?: string;
}

function parseRemediationResponse(rawText: string): RawTask[] {
  let jsonText = rawText.trim();

  // Remove code fences
  if (jsonText.startsWith('```')) {
    const firstNewline = jsonText.indexOf('\n');
    if (firstNewline !== -1) {
      jsonText = jsonText.slice(firstNewline + 1);
    }
  }
  const lastFence = jsonText.lastIndexOf('```');
  if (lastFence !== -1) {
    jsonText = jsonText.slice(0, lastFence);
  }
  jsonText = jsonText.trim();

  // Handle truncation
  if (!jsonText.endsWith(']')) {
    const lastBrace = jsonText.lastIndexOf('}');
    if (lastBrace !== -1) {
      jsonText = jsonText.slice(0, lastBrace + 1) + ']';
    }
  }

  const parsed = JSON.parse(jsonText) as RawTask[];
  if (!Array.isArray(parsed)) return [];
  return parsed;
}

const BATCH_SIZE = 15;

export async function generateRemediationTasks(
  failedVerifications: ClaimVerification[],
  partialVerifications: ClaimVerification[],
  claims: Claim[],
  index: CodebaseIndex,
  onProgress?: (msg: string) => void,
): Promise<{ tasks: RemediationTask[]; inputTokens: number; outputTokens: number }> {
  const client = getClient();
  const claimMap = new Map(claims.map((c) => [c.id, c]));
  const tasks: RemediationTask[] = [];
  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let taskCounter = 0;

  const treeStr = index.fileTree.slice(0, 2000).join('\n');

  // Process FAIL claims first, then PARTIAL
  const groups: Array<{ label: string; verifications: ClaimVerification[]; emphasis: string }> = [
    {
      label: 'FAIL',
      verifications: failedVerifications,
      emphasis: 'These claims are NOT implemented. Provide full implementation guidance.',
    },
    {
      label: 'PARTIAL',
      verifications: partialVerifications,
      emphasis: 'These claims are PARTIALLY implemented. Focus on what is MISSING, not what exists.',
    },
  ];

  for (const group of groups) {
    if (group.verifications.length === 0) continue;

    for (let i = 0; i < group.verifications.length; i += BATCH_SIZE) {
      const batch = group.verifications.slice(i, i + BATCH_SIZE);
      const batchNum = Math.floor(i / BATCH_SIZE) + 1;
      const totalBatches = Math.ceil(group.verifications.length / BATCH_SIZE);

      onProgress?.(
        `${group.label} batch ${batchNum}/${totalBatches}: reading evidence files for ${batch.length} claims...`,
      );

      // Collect all evidence files from this batch
      const uniqueFiles = new Set<string>();
      for (const v of batch) {
        for (const e of v.evidence) {
          uniqueFiles.add(e.file);
        }
      }

      // Read file contents
      const fileContents = new Map<string, string>();
      for (const filePath of uniqueFiles) {
        const content = await readFileContent(index.rootPath, filePath);
        if (content) {
          fileContents.set(filePath, content);
        }
      }

      // Build context
      let evidenceContext = '';
      for (const [path, content] of fileContents) {
        const truncated =
          content.length > 10_000
            ? content.slice(0, 10_000) + '\n[... truncated]'
            : content;
        evidenceContext += `\n--- FILE: ${path} ---\n${truncated}\n`;
      }

      if (evidenceContext.length > 100_000) {
        evidenceContext = evidenceContext.slice(0, 100_000) + '\n[... context truncated]';
      }

      // Build claim+verification list
      const claimList = batch
        .map((v) => {
          const claim = claimMap.get(v.claimId);
          return [
            `${v.claimId} [${claim?.severity || 'medium'}, ${claim?.category || 'functionality'}]:`,
            `  Claim: ${v.claim}`,
            `  Verdict: ${v.verdict}`,
            `  Reasoning: ${v.reasoning}`,
          ].join('\n');
        })
        .join('\n\n');

      onProgress?.(
        `${group.label} batch ${batchNum}/${totalBatches}: generating remediation tasks...`,
      );

      const response = await client.messages.create({
        model: MODEL,
        max_tokens: 8_000,
        system: REMEDIATION_SYSTEM,
        messages: [
          {
            role: 'user',
            content: [
              group.emphasis,
              '',
              'Claims requiring remediation:',
              claimList,
              '',
              'Codebase file tree:',
              treeStr,
              '',
              'Relevant source files:',
              evidenceContext,
            ].join('\n'),
          },
        ],
      });

      totalInputTokens += response.usage.input_tokens;
      totalOutputTokens += response.usage.output_tokens;

      const responseText = response.content
        .filter((b): b is Anthropic.TextBlock => b.type === 'text')
        .map((b) => b.text)
        .join('');

      try {
        const rawTasks = parseRemediationResponse(responseText);

        for (const raw of rawTasks) {
          if (!raw.claimId || !raw.title) continue;

          const claim = claimMap.get(raw.claimId);
          const verification = batch.find((v) => v.claimId === raw.claimId);
          if (!verification) continue;

          taskCounter++;
          const id = `REM-${String(taskCounter).padStart(3, '0')}`;

          tasks.push({
            id,
            claimId: raw.claimId,
            verdict: verification.verdict as 'FAIL' | 'PARTIAL',
            severity: (claim?.severity || 'medium') as ClaimSeverity,
            category: (claim?.category || 'functionality') as ClaimCategory,
            title: raw.title,
            description: raw.description || '',
            action: VALID_ACTIONS.includes(raw.action as RemediationAction)
              ? (raw.action as RemediationAction)
              : 'modify',
            targetFiles: Array.isArray(raw.targetFiles) ? raw.targetFiles : [],
            estimatedEffort: VALID_EFFORTS.includes(raw.estimatedEffort as typeof VALID_EFFORTS[number])
              ? (raw.estimatedEffort as RemediationTask['estimatedEffort'])
              : 'medium',
            codeGuidance: raw.codeGuidance || '',
          });
        }
      } catch {
        onProgress?.(`Warning: Failed to parse remediation response for ${group.label} batch ${batchNum}`);
      }
    }
  }

  // Sort: critical first, then high, medium, low
  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  tasks.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  // Re-number after sorting
  for (let i = 0; i < tasks.length; i++) {
    tasks[i].id = `REM-${String(i + 1).padStart(3, '0')}`;
  }

  return {
    tasks,
    inputTokens: totalInputTokens,
    outputTokens: totalOutputTokens,
  };
}
