import { getClient, MODEL } from './anthropic.js';
import type {
  CodeSpec,
  ConstraintType,
  ConstraintSource,
  GenerationConstraint,
  ConstraintSet,
  ClaimSeverity,
} from '../types.js';

// ---------------------------------------------------------------------------
// Domain patterns — embedded knowledge from LUCID benchmark findings
// ---------------------------------------------------------------------------

const DOMAIN_PATTERNS: Array<{
  triggers: string[];
  constraints: Array<{ type: ConstraintType; description: string; pattern?: string }>;
}> = [
  {
    triggers: ['sql', 'query', 'database', 'db'],
    constraints: [
      { type: 'must', description: 'Use parameterized queries, never string concatenation for SQL' },
      { type: 'must-not', description: 'Never build SQL with template literals or string concatenation', pattern: '`SELECT * FROM ${table} WHERE id = ${id}`' },
    ],
  },
  {
    triggers: ['password', 'auth', 'login', 'credentials'],
    constraints: [
      { type: 'must', description: 'Use bcrypt or argon2 for password hashing, never MD5/SHA1' },
      { type: 'must-not', description: 'Never store passwords in plaintext or use weak hashing' },
    ],
  },
  {
    triggers: ['counter', 'increment', 'shared', 'concurrent'],
    constraints: [
      { type: 'must', description: 'Use atomic operations or transactions for shared state updates' },
      { type: 'must-not', description: 'Never use read-then-write pattern for counters without locking', pattern: 'const count = await getCount(); await setCount(count + 1);' },
    ],
  },
  {
    triggers: ['api', 'fetch', 'request', 'http'],
    constraints: [
      { type: 'must', description: 'Handle HTTP errors explicitly (check response.ok or status code)' },
      { type: 'must-not', description: 'Never ignore HTTP error responses or assume success' },
      { type: 'prefer', description: 'Include timeout configuration for HTTP requests' },
    ],
  },
  {
    triggers: ['array', 'list', 'collection', 'filter', 'map', 'reduce'],
    constraints: [
      { type: 'must', description: 'Handle empty array/collection edge case' },
      { type: 'prefer', description: 'Use Set for O(1) lookups instead of nested array iterations' },
    ],
  },
  {
    triggers: ['parse', 'json', 'input', 'user input', 'form'],
    constraints: [
      { type: 'must', description: 'Validate and sanitize all external input before processing' },
      { type: 'must', description: 'Wrap JSON.parse in try-catch' },
    ],
  },
  {
    triggers: ['file', 'path', 'directory', 'fs'],
    constraints: [
      { type: 'must', description: 'Check file/directory existence before operations' },
      { type: 'must', description: 'Handle file operation errors (ENOENT, EACCES, etc.)' },
    ],
  },
  {
    triggers: ['regex', 'pattern', 'match'],
    constraints: [
      { type: 'must-not', description: 'Never use regex with /g flag in repeated calls without resetting lastIndex (JavaScript)' },
    ],
  },
  {
    triggers: ['float', 'decimal', 'money', 'price', 'calculation'],
    constraints: [
      { type: 'must-not', description: 'Never compare floating point numbers with strict equality', pattern: 'if (a === 0.3)' },
      { type: 'prefer', description: 'Use epsilon comparison for floating point: Math.abs(a - b) < Number.EPSILON' },
    ],
  },
  {
    triggers: ['sort', 'order', 'rank', 'compare'],
    constraints: [
      { type: 'must', description: 'Provide an explicit comparator for numeric sorts (JavaScript default sort is lexicographic)', pattern: 'array.sort()' },
      { type: 'must', description: 'Ensure sort comparator is consistent (if a < b then b > a)' },
    ],
  },
  {
    triggers: ['async', 'await', 'promise', 'callback'],
    constraints: [
      { type: 'must', description: 'Handle promise rejections with try-catch or .catch()' },
      { type: 'must-not', description: 'Never fire-and-forget promises without error handling' },
      { type: 'prefer', description: 'Use Promise.allSettled instead of Promise.all when partial failures are acceptable' },
    ],
  },
  {
    triggers: ['cache', 'memo', 'memoize', 'store'],
    constraints: [
      { type: 'must', description: 'Include cache invalidation or TTL mechanism' },
      { type: 'must-not', description: 'Never allow unbounded cache growth without eviction policy' },
    ],
  },
  {
    triggers: ['recursive', 'recursion', 'tree', 'graph', 'traverse'],
    constraints: [
      { type: 'must', description: 'Include a base case that terminates recursion' },
      { type: 'prefer', description: 'Guard against circular references in graph/tree traversal' },
      { type: 'prefer', description: 'Consider stack depth limits for deep recursion; use iteration if depth is unbounded' },
    ],
  },
  {
    triggers: ['string', 'text', 'substring', 'split', 'join'],
    constraints: [
      { type: 'must', description: 'Handle empty string edge case' },
      { type: 'prefer', description: 'Consider Unicode/multi-byte characters when indexing strings' },
    ],
  },
  {
    triggers: ['date', 'time', 'timestamp', 'schedule', 'cron'],
    constraints: [
      { type: 'must', description: 'Handle timezone conversions explicitly, do not assume UTC' },
      { type: 'must-not', description: 'Never construct dates from string concatenation without validation' },
    ],
  },
  {
    triggers: ['divide', 'division', 'ratio', 'percentage', 'average'],
    constraints: [
      { type: 'must', description: 'Check for division by zero before dividing' },
    ],
  },
  {
    triggers: ['env', 'environment', 'config', 'secret', 'token'],
    constraints: [
      { type: 'must', description: 'Validate that required environment variables are set before using them' },
      { type: 'must-not', description: 'Never log or expose secrets/tokens in error messages or console output' },
    ],
  },
  {
    triggers: ['stream', 'pipe', 'buffer', 'socket', 'websocket'],
    constraints: [
      { type: 'must', description: 'Handle stream error events to prevent unhandled exceptions' },
      { type: 'must', description: 'Clean up resources (close streams/sockets) in error and completion paths' },
    ],
  },
];

// ---------------------------------------------------------------------------
// LLM-based constraint derivation from specs
// ---------------------------------------------------------------------------

const CONSTRAINT_SYSTEM_PROMPT = `You are a constraint generator for code generation. Given a set of formal specifications that code must satisfy, produce generation constraints that PREVENT common failures.

CONSTRAINT RULES:

1. For each specification, produce 1-2 constraints that guide the code generator:
   - correctness spec → "must" constraint with specific implementation guidance
   - security spec → "must-not" constraint with anti-pattern example
   - edge-case spec → "must" constraint for boundary handling
   - error-handling spec → "must" constraint for explicit error paths
   - type-safety spec → "must-not" constraint against unsafe coercions
   - performance spec → "prefer" constraint with recommended approach

2. Each constraint must have:
   - type: "must" | "must-not" | "prefer"
   - description: Clear guidance for the code generator (1-2 sentences)
   - pattern: (optional) A short code snippet showing the anti-pattern (for must-not) or expected pattern (for must)

3. Be SPECIFIC and ACTIONABLE:
   - GOOD: "Must handle the case where input array is empty by returning an empty array"
   - GOOD: "Must-not use indexOf for existence checks on large arrays; use Set or Map"
   - BAD: "Must be correct" (too vague)
   - BAD: "Must handle errors" (not actionable)

4. Do NOT duplicate: If two specs would produce the same constraint, only include it once.

OUTPUT FORMAT:
Return ONLY a JSON array of constraint objects. No markdown fences, no commentary.
[
  {
    "type": "must",
    "description": "...",
    "pattern": "..."
  }
]`;

interface RawConstraint {
  type?: string;
  description?: string;
  pattern?: string;
}

const VALID_TYPES: ConstraintType[] = ['must', 'must-not', 'prefer'];

function validateConstraint(raw: RawConstraint): Omit<GenerationConstraint, 'id' | 'source'> | null {
  if (!raw.description || typeof raw.description !== 'string') return null;

  const type = VALID_TYPES.includes(raw.type as ConstraintType)
    ? (raw.type as ConstraintType)
    : 'must';

  return {
    type,
    description: raw.description.trim(),
    pattern: typeof raw.pattern === 'string' ? raw.pattern.trim() : undefined,
  };
}

// ---------------------------------------------------------------------------
// Domain pattern matching
// ---------------------------------------------------------------------------

function matchDomainPatterns(task: string): Array<Omit<GenerationConstraint, 'id'>> {
  const taskLower = task.toLowerCase();
  const matched: Array<Omit<GenerationConstraint, 'id'>> = [];
  const seen = new Set<string>();

  for (const pattern of DOMAIN_PATTERNS) {
    const triggered = pattern.triggers.some((t) => taskLower.includes(t));
    if (!triggered) continue;

    for (const c of pattern.constraints) {
      // Deduplicate by description
      if (seen.has(c.description)) continue;
      seen.add(c.description);

      matched.push({
        type: c.type,
        description: c.description,
        pattern: c.pattern,
        source: 'domain' as ConstraintSource,
      });
    }
  }

  return matched;
}

// ---------------------------------------------------------------------------
// JSON parsing helpers (same pattern as claim-extractor / spec-synthesizer)
// ---------------------------------------------------------------------------

function stripCodeFences(text: string): string {
  let jsonText = text.trim();

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

  return jsonText.trim();
}

function repairTruncatedArray(jsonText: string, onProgress?: (msg: string) => void): string {
  if (jsonText.endsWith(']')) return jsonText;

  const lastCloseBrace = jsonText.lastIndexOf('}');
  if (lastCloseBrace !== -1) {
    onProgress?.('Note: Response was truncated. Recovered partial constraints.');
    return jsonText.slice(0, lastCloseBrace + 1) + '\n]';
  }
  return jsonText;
}

// ---------------------------------------------------------------------------
// Spec-derived constraints via LLM
// ---------------------------------------------------------------------------

async function deriveSpecConstraints(
  specs: CodeSpec[],
  task: string,
  language: string,
  onProgress?: (msg: string) => void,
): Promise<{ constraints: Array<Omit<GenerationConstraint, 'id'>>; inputTokens: number; outputTokens: number }> {
  if (specs.length === 0) {
    return { constraints: [], inputTokens: 0, outputTokens: 0 };
  }

  const client = getClient();

  onProgress?.('Deriving spec constraints via Claude (streaming)...');

  const specsText = specs
    .map((s) => `[${s.id}] (${s.category}, ${s.severity}) ${s.description}\n  Assertion: ${s.assertion}`)
    .join('\n\n');

  const stream = client.messages.stream({
    model: MODEL,
    max_tokens: 8_000,
    system: CONSTRAINT_SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Generate constraints for the following coding task and specifications.\n\nLanguage: ${language}\nTask: ${task}\n\nSpecifications:\n${specsText}`,
      },
    ],
  });

  let rawText = '';
  stream.on('text', (text) => {
    rawText += text;
  });

  const finalMessage = await stream.finalMessage();

  onProgress?.('Parsing constraint results...');

  let jsonText = stripCodeFences(rawText);
  jsonText = repairTruncatedArray(jsonText, onProgress);

  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    throw new Error(
      `Failed to parse Claude's constraint response as JSON.\n` +
      `First 200 chars: ${jsonText.slice(0, 200)}`,
    );
  }

  if (!Array.isArray(parsed)) {
    throw new Error('Expected a JSON array of constraints from Claude.');
  }

  const constraints: Array<Omit<GenerationConstraint, 'id'>> = [];
  for (const raw of parsed) {
    const validated = validateConstraint(raw as RawConstraint);
    if (validated) {
      constraints.push({
        ...validated,
        source: 'spec' as ConstraintSource,
      });
    }
  }

  return {
    constraints,
    inputTokens: finalMessage.usage.input_tokens,
    outputTokens: finalMessage.usage.output_tokens,
  };
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export async function generateConstraints(
  task: string,
  language: string,
  specs: CodeSpec[],
  onProgress?: (msg: string) => void,
): Promise<ConstraintSet> {
  // 1. Match domain patterns
  onProgress?.('Matching domain patterns...');
  const domainConstraints = matchDomainPatterns(task);
  onProgress?.(`Matched ${domainConstraints.length} domain constraint(s).`);

  // 2. Derive spec constraints via LLM
  const { constraints: specConstraints, inputTokens, outputTokens } =
    await deriveSpecConstraints(specs, task, language, onProgress);
  onProgress?.(`Derived ${specConstraints.length} spec constraint(s).`);

  // 3. Merge and deduplicate (domain first, then spec-derived)
  const allConstraints = [...domainConstraints, ...specConstraints];
  const seen = new Set<string>();
  const deduped: Array<Omit<GenerationConstraint, 'id'>> = [];

  for (const c of allConstraints) {
    const key = c.description.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(c);
  }

  // 4. Number all constraints CON-001, CON-002, etc.
  const numbered: GenerationConstraint[] = deduped.map((c, i) => ({
    id: `CON-${String(i + 1).padStart(3, '0')}`,
    type: c.type,
    description: c.description,
    pattern: c.pattern,
    source: c.source!,
  }));

  onProgress?.(`Total: ${numbered.length} constraint(s) after deduplication.`);

  return {
    task,
    constraints: numbered,
    totalConstraints: numbered.length,
    generatedAt: new Date().toISOString(),
    inputTokens,
    outputTokens,
  };
}
