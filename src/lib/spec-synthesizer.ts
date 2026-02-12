import { getClient, MODEL } from './anthropic.js';
import type { CodeSpec, SpecSynthesisResult, SpecCategory, ClaimSeverity } from '../types.js';

const SYNTHESIS_SYSTEM_PROMPT = `You are a formal specification synthesizer. Given a coding task description and target programming language, you generate a comprehensive set of formal specifications that any correct implementation MUST satisfy.

SYNTHESIS RULES:

1. Generate 10-30 specifications covering ALL of these categories:
   - correctness: Happy-path behavior, expected outputs for standard inputs
   - edge-case: Boundary values, empty inputs, maximum values, off-by-one scenarios
   - error-handling: Invalid inputs, missing data, exception behavior
   - security: Injection, overflow, unauthorized access, input sanitization
   - type-safety: Type constraints, null/undefined handling, coercion traps
   - performance: Time/space complexity, resource limits, scaling behavior

2. Each specification must have:
   - id: Sequential "SPEC-001", "SPEC-002", etc.
   - category: One of correctness, edge-case, error-handling, security, type-safety, performance
   - severity: How bad is it if the code violates this spec?
     - critical: Would be a bug causing incorrect results or crashes
     - high: Significant quality issue, data loss, or security flaw
     - medium: Best practice violation, poor robustness
     - low: Nice-to-have, minor optimization
   - description: Clear statement of what the code must do or guarantee
   - assertion: A specific, testable assertion (pseudocode or natural language test case) that can be verified programmatically against the generated code
   - rationale: Why this specification matters

3. Assertions must be SPECIFIC and TESTABLE:
   - GOOD: "sorted([3,1,2]) returns [1,2,3]"
   - GOOD: "rateLimiter(100, '1m').check('user1') returns { allowed: true, remaining: 99 }"
   - GOOD: "Passing null as input throws TypeError with message containing 'expected string'"
   - BAD: "Function works correctly" (too vague)
   - BAD: "Handles errors" (not testable)

4. Prioritize CRITICAL specs first, then HIGH, then MEDIUM, then LOW.

5. Think adversarially: What inputs would break a naive implementation? What edge cases do developers commonly miss?

OUTPUT FORMAT:
Return ONLY a JSON array of specification objects. No markdown fences, no commentary.`;

interface RawSpec {
  id?: string;
  category?: string;
  severity?: string;
  description?: string;
  assertion?: string;
  rationale?: string;
}

const VALID_CATEGORIES: SpecCategory[] = [
  'correctness', 'security', 'performance', 'error-handling', 'edge-case', 'type-safety',
];

const VALID_SEVERITIES: ClaimSeverity[] = [
  'critical', 'high', 'medium', 'low',
];

function validateSpec(raw: RawSpec, index: number): CodeSpec | null {
  if (!raw.description || typeof raw.description !== 'string') return null;
  if (!raw.assertion || typeof raw.assertion !== 'string') return null;

  const category = VALID_CATEGORIES.includes(raw.category as SpecCategory)
    ? (raw.category as SpecCategory)
    : 'correctness';

  const severity = VALID_SEVERITIES.includes(raw.severity as ClaimSeverity)
    ? (raw.severity as ClaimSeverity)
    : 'medium';

  return {
    id: raw.id || `SPEC-${String(index + 1).padStart(3, '0')}`,
    category,
    severity,
    description: raw.description.trim(),
    assertion: raw.assertion.trim(),
    rationale: typeof raw.rationale === 'string' ? raw.rationale.trim() : 'No rationale provided',
  };
}

export async function synthesizeSpecs(
  task: string,
  language: string,
  onProgress?: (msg: string) => void,
): Promise<SpecSynthesisResult> {
  const client = getClient();

  onProgress?.('Sending task to Claude for spec synthesis (streaming)...');

  const stream = client.messages.stream({
    model: MODEL,
    max_tokens: 16_000,
    system: SYNTHESIS_SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Generate formal specifications for the following coding task.\n\nLanguage: ${language}\n\nTask:\n${task}`,
      },
    ],
  });

  let rawText = '';
  stream.on('text', (text) => {
    rawText += text;
  });

  const finalMessage = await stream.finalMessage();

  onProgress?.('Parsing synthesis results...');

  // Strip markdown code fences if present
  let jsonText = rawText.trim();

  // Remove opening code fence
  if (jsonText.startsWith('```')) {
    const firstNewline = jsonText.indexOf('\n');
    if (firstNewline !== -1) {
      jsonText = jsonText.slice(firstNewline + 1);
    }
  }

  // Remove closing code fence
  const lastFence = jsonText.lastIndexOf('```');
  if (lastFence !== -1) {
    jsonText = jsonText.slice(0, lastFence);
  }

  jsonText = jsonText.trim();

  // If response was truncated (no closing ]), try to repair by closing the array
  if (!jsonText.endsWith(']')) {
    const lastCloseBrace = jsonText.lastIndexOf('}');
    if (lastCloseBrace !== -1) {
      jsonText = jsonText.slice(0, lastCloseBrace + 1) + '\n]';
      onProgress?.('Note: Response was truncated. Recovered partial specs.');
    }
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    throw new Error(
      `Failed to parse Claude's spec synthesis response as JSON.\n` +
      `First 200 chars: ${jsonText.slice(0, 200)}`,
    );
  }

  if (!Array.isArray(parsed)) {
    throw new Error('Expected a JSON array of specs from Claude.');
  }

  const specs: CodeSpec[] = [];
  for (let i = 0; i < parsed.length; i++) {
    const validated = validateSpec(parsed[i] as RawSpec, i);
    if (validated) {
      specs.push(validated);
    }
  }

  return {
    task,
    language,
    specs,
    totalSpecs: specs.length,
    synthesizedAt: new Date().toISOString(),
    inputTokens: finalMessage.usage.input_tokens,
    outputTokens: finalMessage.usage.output_tokens,
  };
}
