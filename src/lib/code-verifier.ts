import type Anthropic from '@anthropic-ai/sdk';
import { getClient, MODEL } from './anthropic.js';
import { readFileContent } from './codebase-indexer.js';
import type { CodebaseIndex } from './codebase-indexer.js';
import type {
  Claim,
  ClaimVerification,
  Evidence,
  Verdict,
} from '../types.js';

const VALID_VERDICTS: Verdict[] = ['PASS', 'PARTIAL', 'FAIL', 'N/A'];

// Step 1: Ask Claude which files to examine for a batch of claims
const FILE_SELECTION_SYSTEM = `You are a code auditor. Given a list of claims and a codebase file tree, identify which files are most likely to contain evidence for or against each claim.

For each claim, list 1-5 file paths from the tree that should be examined.

OUTPUT FORMAT:
Return a JSON object mapping claim IDs to arrays of file paths:
{
  "CLAIM-001": ["src/lib/auth.ts", "src/middleware.ts"],
  "CLAIM-002": ["prisma/schema.prisma", "src/api/users/route.ts"]
}

Return ONLY the JSON. No markdown fences, no commentary.
Be specific — pick the most relevant files. If no files in the tree could contain evidence, use an empty array.`;

// Step 2: Ask Claude to evaluate a claim against file contents
const VERIFICATION_SYSTEM = `You are a compliance auditor verifying whether code implements what a legal document claims.

For each claim, evaluate the code evidence and assign a verdict:
- PASS: The code fully implements what the claim states
- PARTIAL: The code partially implements it (some aspects missing or incomplete)
- FAIL: The code does not implement what the claim states, or contradicts it
- N/A: The claim cannot be verified from code (e.g., business process, legal statement)

OUTPUT FORMAT:
Return a JSON array of verification results:
[
  {
    "claimId": "CLAIM-001",
    "verdict": "PASS",
    "evidence": [
      {
        "file": "src/lib/encryption.ts",
        "lineNumber": 42,
        "snippet": "const cipher = createCipheriv('aes-256-gcm', key, iv)",
        "confidence": 0.95
      }
    ],
    "reasoning": "AES-256-GCM encryption is implemented for data at rest in the encryption module."
  }
]

Rules:
- Evidence snippets should be short (1-3 lines), directly relevant
- Confidence: 0.0 to 1.0, how sure you are this evidence supports the verdict
- Reasoning: 1-2 sentences explaining why this verdict
- Be strict: if the claim says "AES-256" and code uses "AES-128", that's FAIL
- N/A is for claims that genuinely can't be verified from code

Return ONLY the JSON array. No markdown fences.`;

interface RawVerification {
  claimId?: string;
  verdict?: string;
  evidence?: Array<{
    file?: string;
    lineNumber?: number;
    snippet?: string;
    confidence?: number;
  }>;
  reasoning?: string;
}

function parseVerificationResponse(rawText: string): ClaimVerification[] {
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

  const parsed = JSON.parse(jsonText) as RawVerification[];
  if (!Array.isArray(parsed)) return [];

  return parsed
    .filter((r) => r.claimId && r.verdict)
    .map((r) => ({
      claimId: r.claimId!,
      claim: '',
      verdict: VALID_VERDICTS.includes(r.verdict as Verdict)
        ? (r.verdict as Verdict)
        : 'N/A',
      evidence: (r.evidence || [])
        .filter((e) => e.file && e.snippet)
        .map((e) => ({
          file: e.file!,
          lineNumber: e.lineNumber,
          snippet: e.snippet!,
          confidence: typeof e.confidence === 'number' ? e.confidence : 0.5,
        })),
      reasoning: r.reasoning || '',
    }));
}

function parseFileSelectionResponse(rawText: string): Record<string, string[]> {
  let jsonText = rawText.trim();

  if (jsonText.startsWith('```')) {
    const firstNewline = jsonText.indexOf('\n');
    if (firstNewline !== -1) jsonText = jsonText.slice(firstNewline + 1);
  }
  const lastFence = jsonText.lastIndexOf('```');
  if (lastFence !== -1) jsonText = jsonText.slice(0, lastFence);
  jsonText = jsonText.trim();

  // Handle truncation for objects
  if (!jsonText.endsWith('}')) {
    const lastBrace = jsonText.lastIndexOf('}');
    if (lastBrace !== -1) jsonText = jsonText.slice(0, lastBrace + 1);
  }

  return JSON.parse(jsonText) as Record<string, string[]>;
}

// Process claims in batches to manage API calls and context
const BATCH_SIZE = 15;

export async function verifyClaims(
  claims: Claim[],
  index: CodebaseIndex,
  onProgress?: (msg: string) => void,
): Promise<{
  verifications: ClaimVerification[];
  inputTokens: number;
  outputTokens: number;
}> {
  const client = getClient();
  const testableClaims = claims.filter((c) => c.testable);
  const verifications: ClaimVerification[] = [];
  let totalInputTokens = 0;
  let totalOutputTokens = 0;

  // Mark non-testable claims as N/A immediately
  for (const claim of claims) {
    if (!claim.testable) {
      verifications.push({
        claimId: claim.id,
        claim: claim.text,
        verdict: 'N/A',
        evidence: [],
        reasoning: 'Claim is not testable against code.',
      });
    }
  }

  // Build file tree string (truncated to avoid hitting context limits)
  const treeStr = index.fileTree.slice(0, 2000).join('\n');

  // Process testable claims in batches
  for (let i = 0; i < testableClaims.length; i += BATCH_SIZE) {
    const batch = testableClaims.slice(i, i + BATCH_SIZE);
    const batchNum = Math.floor(i / BATCH_SIZE) + 1;
    const totalBatches = Math.ceil(testableClaims.length / BATCH_SIZE);

    onProgress?.(
      `Batch ${batchNum}/${totalBatches}: selecting files for ${batch.length} claims...`,
    );

    // Step 1: Ask which files to examine
    const claimList = batch
      .map((c) => `${c.id}: ${c.text} [${c.category}]`)
      .join('\n');

    const fileSelResponse = await client.messages.create({
      model: MODEL,
      max_tokens: 4_000,
      system: FILE_SELECTION_SYSTEM,
      messages: [
        {
          role: 'user',
          content: `Claims to verify:\n${claimList}\n\nCodebase file tree:\n${treeStr}`,
        },
      ],
    });

    totalInputTokens += fileSelResponse.usage.input_tokens;
    totalOutputTokens += fileSelResponse.usage.output_tokens;

    const fileSelText = fileSelResponse.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map((b) => b.text)
      .join('');

    let fileSelections: Record<string, string[]>;
    try {
      fileSelections = parseFileSelectionResponse(fileSelText);
    } catch {
      // If parsing fails, use key files as fallback
      fileSelections = {};
      for (const claim of batch) {
        fileSelections[claim.id] = index.keyFiles.slice(0, 5).map((f) => f.path);
      }
    }

    // Step 2: Read all unique files needed for this batch
    const uniqueFiles = new Set<string>();
    for (const files of Object.values(fileSelections)) {
      for (const f of files) uniqueFiles.add(f);
    }

    onProgress?.(
      `Batch ${batchNum}/${totalBatches}: reading ${uniqueFiles.size} files...`,
    );

    const fileContents = new Map<string, string>();
    for (const filePath of uniqueFiles) {
      const content = await readFileContent(index.rootPath, filePath);
      if (content) {
        fileContents.set(filePath, content);
      }
    }

    // Step 3: Verify claims against file contents
    onProgress?.(
      `Batch ${batchNum}/${totalBatches}: verifying ${batch.length} claims...`,
    );

    // Build context with file contents for this batch
    let evidenceContext = '';
    for (const [path, content] of fileContents) {
      // Limit each file to keep total context manageable
      const truncated =
        content.length > 10_000
          ? content.slice(0, 10_000) + '\n[... truncated]'
          : content;
      evidenceContext += `\n--- FILE: ${path} ---\n${truncated}\n`;
    }

    // If total context is too large, truncate
    if (evidenceContext.length > 100_000) {
      evidenceContext = evidenceContext.slice(0, 100_000) + '\n[... context truncated]';
    }

    const verifyResponse = await client.messages.create({
      model: MODEL,
      max_tokens: 8_000,
      system: VERIFICATION_SYSTEM,
      messages: [
        {
          role: 'user',
          content: `Claims to verify:\n${claimList}\n\nCode evidence:\n${evidenceContext}`,
        },
      ],
    });

    totalInputTokens += verifyResponse.usage.input_tokens;
    totalOutputTokens += verifyResponse.usage.output_tokens;

    const verifyText = verifyResponse.content
      .filter((b): b is Anthropic.TextBlock => b.type === 'text')
      .map((b) => b.text)
      .join('');

    try {
      const batchResults = parseVerificationResponse(verifyText);
      // Attach claim text
      for (const result of batchResults) {
        const claim = batch.find((c) => c.id === result.claimId);
        if (claim) {
          result.claim = claim.text;
          verifications.push(result);
        }
      }

      // Any claims not covered in response get N/A
      for (const claim of batch) {
        if (!batchResults.some((r) => r.claimId === claim.id)) {
          verifications.push({
            claimId: claim.id,
            claim: claim.text,
            verdict: 'N/A',
            evidence: [],
            reasoning: 'No verification result returned.',
          });
        }
      }
    } catch {
      // If verification parsing fails, mark batch as N/A
      for (const claim of batch) {
        verifications.push({
          claimId: claim.id,
          claim: claim.text,
          verdict: 'N/A',
          evidence: [],
          reasoning: 'Failed to parse verification response.',
        });
      }
    }
  }

  // Sort by claim ID
  verifications.sort((a, b) => a.claimId.localeCompare(b.claimId));

  return {
    verifications,
    inputTokens: totalInputTokens,
    outputTokens: totalOutputTokens,
  };
}
