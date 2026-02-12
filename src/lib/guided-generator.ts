import { getClient, MODEL } from './anthropic.js';
import type {
  CodeSpec,
  GenerationConstraint,
  GeneratedCode,
  SelfVerificationResult,
  SelfVerificationStatus,
} from '../types.js';
import type Anthropic from '@anthropic-ai/sdk';

const MAX_TOKENS = 16_000;

function buildGenerationSystemPrompt(
  language: string,
  specs: CodeSpec[],
  constraints: GenerationConstraint[],
): string {
  const specLines = specs.map((s) => {
    return `[${s.id}] (${s.severity}/${s.category}): ${s.description}\n  Assertion: ${s.assertion}`;
  });

  const musts = constraints.filter((c) => c.type === 'must');
  const mustNots = constraints.filter((c) => c.type === 'must-not');
  const prefers = constraints.filter((c) => c.type === 'prefer');

  let constraintBlock = '';

  if (musts.length > 0) {
    constraintBlock += 'MUST DO:\n';
    constraintBlock += musts
      .map((c) => `- ${c.id}: ${c.description}${c.pattern ? `\n  Example: ${c.pattern}` : ''}`)
      .join('\n');
    constraintBlock += '\n\n';
  }

  if (mustNots.length > 0) {
    constraintBlock += 'MUST NOT DO:\n';
    constraintBlock += mustNots
      .map((c) => `- ${c.id}: ${c.description}${c.pattern ? `\n  Bad example: ${c.pattern}` : ''}`)
      .join('\n');
    constraintBlock += '\n\n';
  }

  if (prefers.length > 0) {
    constraintBlock += 'PREFER:\n';
    constraintBlock += prefers
      .map((c) => `- ${c.id}: ${c.description}${c.pattern ? `\n  Example: ${c.pattern}` : ''}`)
      .join('\n');
    constraintBlock += '\n';
  }

  return `You are an expert programmer. Generate production-quality ${language} code.

SPECIFICATIONS — Your code MUST satisfy ALL of these:
${specLines.join('\n')}

CONSTRAINTS:
${constraintBlock}
OUTPUT RULES:
- Return ONLY the code
- No markdown code fences
- No explanations before or after the code
- Include all necessary imports
- Include type annotations
- The code should be complete and runnable`;
}

const VERIFICATION_SYSTEM_PROMPT = `You are a code reviewer verifying generated code against specifications. For each specification, determine whether the code satisfies it.

OUTPUT FORMAT:
Return ONLY a JSON array. No markdown fences, no commentary. Each element:
{
  "specId": "SPEC-001",
  "status": "satisfied" | "partial" | "unsatisfied" | "unknown",
  "reasoning": "Brief explanation of why the code does or does not satisfy this spec"
}

STATUS MEANINGS:
- satisfied: The code clearly and correctly implements this specification
- partial: The code addresses this specification but incompletely or with caveats
- unsatisfied: The code does not implement this specification or violates it
- unknown: Cannot determine from static analysis alone (e.g., runtime/performance specs)`;

function stripCodeFences(text: string): string {
  let result = text.trim();

  // Remove opening code fence (```language or just ```)
  if (result.startsWith('```')) {
    const firstNewline = result.indexOf('\n');
    if (firstNewline !== -1) {
      result = result.slice(firstNewline + 1);
    }
  }

  // Remove closing code fence
  const lastFence = result.lastIndexOf('```');
  if (lastFence !== -1) {
    result = result.slice(0, lastFence);
  }

  return result.trim();
}

const VALID_STATUSES: SelfVerificationStatus[] = [
  'satisfied', 'partial', 'unsatisfied', 'unknown',
];

interface RawVerification {
  specId?: string;
  status?: string;
  reasoning?: string;
}

function validateVerification(raw: RawVerification, specs: CodeSpec[]): SelfVerificationResult | null {
  if (!raw.specId || typeof raw.specId !== 'string') return null;
  if (!raw.reasoning || typeof raw.reasoning !== 'string') return null;

  // Verify the specId references a real spec
  const matchesSpec = specs.some((s) => s.id === raw.specId);
  if (!matchesSpec) return null;

  const status = VALID_STATUSES.includes(raw.status as SelfVerificationStatus)
    ? (raw.status as SelfVerificationStatus)
    : 'unknown';

  return {
    specId: raw.specId,
    status,
    reasoning: raw.reasoning.trim(),
  };
}

function parseVerificationJson(rawText: string, specs: CodeSpec[], onProgress?: (msg: string) => void): SelfVerificationResult[] {
  let jsonText = stripCodeFences(rawText);

  // If response was truncated (no closing ]), try to repair
  if (!jsonText.endsWith(']')) {
    const lastCloseBrace = jsonText.lastIndexOf('}');
    if (lastCloseBrace !== -1) {
      jsonText = jsonText.slice(0, lastCloseBrace + 1) + '\n]';
      onProgress?.('Note: Verification response was truncated. Recovered partial results.');
    }
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    onProgress?.('Warning: Failed to parse self-verification JSON. Returning empty results.');
    return [];
  }

  if (!Array.isArray(parsed)) {
    onProgress?.('Warning: Self-verification response was not an array. Returning empty results.');
    return [];
  }

  const results: SelfVerificationResult[] = [];
  for (const item of parsed) {
    const validated = validateVerification(item as RawVerification, specs);
    if (validated) {
      results.push(validated);
    }
  }

  return results;
}

export async function generateWithConstraints(
  task: string,
  language: string,
  specs: CodeSpec[],
  constraints: GenerationConstraint[],
  onProgress?: (msg: string) => void,
): Promise<GeneratedCode> {
  const client = getClient();

  let totalInputTokens = 0;
  let totalOutputTokens = 0;

  // ── Step 1: Guided code generation (streaming) ──

  onProgress?.('Generating code with spec-aware constraints (streaming)...');

  const systemPrompt = buildGenerationSystemPrompt(language, specs, constraints);

  const stream = client.messages.stream({
    model: MODEL,
    max_tokens: MAX_TOKENS,
    system: systemPrompt,
    messages: [
      {
        role: 'user',
        content: `Generate ${language} code for the following task:\n\n${task}`,
      },
    ],
  });

  let rawCode = '';
  stream.on('text', (text) => {
    rawCode += text;
  });

  const genMessage = await stream.finalMessage();
  totalInputTokens += genMessage.usage.input_tokens;
  totalOutputTokens += genMessage.usage.output_tokens;

  const code = stripCodeFences(rawCode);

  onProgress?.(`Code generated (${totalOutputTokens} tokens). Running self-verification...`);

  // ── Step 2: Self-verification (non-streaming) ──

  const specList = specs
    .map((s) => `[${s.id}] (${s.severity}/${s.category}): ${s.description}\n  Assertion: ${s.assertion}`)
    .join('\n');

  const verifyResponse = await client.messages.create({
    model: MODEL,
    max_tokens: 8_000,
    system: VERIFICATION_SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Verify the following code against the specifications below.\n\nCODE:\n${code}\n\nSPECIFICATIONS:\n${specList}`,
      },
    ],
  });

  totalInputTokens += verifyResponse.usage.input_tokens;
  totalOutputTokens += verifyResponse.usage.output_tokens;

  const verifyText = verifyResponse.content
    .filter((block): block is Anthropic.TextBlock => block.type === 'text')
    .map((block) => block.text)
    .join('');

  const selfVerification = parseVerificationJson(verifyText, specs, onProgress);
  const satisfiedCount = selfVerification.filter((v) => v.status === 'satisfied').length;

  onProgress?.(
    `Self-verification complete: ${satisfiedCount}/${specs.length} specs satisfied.`,
  );

  return {
    task,
    code,
    language,
    specs,
    constraints,
    selfVerification,
    satisfiedCount,
    totalSpecs: specs.length,
    generatedAt: new Date().toISOString(),
    inputTokens: totalInputTokens,
    outputTokens: totalOutputTokens,
  };
}
