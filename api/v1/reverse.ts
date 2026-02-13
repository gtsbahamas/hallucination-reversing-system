import type { VercelRequest, VercelResponse } from '@vercel/node';
import { callAnthropic, getText, safeParseArray, stripFences } from '../lib/anthropic.js';
import { withAuth } from '../lib/middleware.js';
import { ApiError } from '../lib/errors.js';
import { trackUsage } from '../lib/usage-tracker.js';
import type {
  ReverseSpec,
  ReverseConstraint,
  ReverseVerificationItem,
  ReverseResponse,
} from '../lib/types.js';

// ── Phase 1: Spec Synthesizer ────────────────────────────────────

const SYNTHESIS_SYSTEM = `You are a formal specification synthesizer. Given a coding task and target language, generate 10-30 formal specifications the code MUST satisfy.

Each spec: { "id": "SPEC-001", "category": "correctness|security|performance|error-handling|edge-case|type-safety", "severity": "critical|high|medium|low", "description": "...", "assertion": "testable assertion", "rationale": "..." }

Cover: correctness, edge cases, error handling, security, type safety, performance.
Return ONLY a JSON array. No markdown fences.`;

// ── Phase 2: Constraint Engine ───────────────────────────────────

interface DomainPattern {
  triggers: string[];
  constraints: Array<{ type: string; description: string; pattern?: string }>;
}

const DOMAIN_PATTERNS: DomainPattern[] = [
  { triggers: ['sql', 'query', 'database', 'db'], constraints: [
    { type: 'must', description: 'Use parameterized queries, never string concatenation for SQL' },
    { type: 'must-not', description: 'Never build SQL with template literals or string concatenation' },
  ]},
  { triggers: ['password', 'auth', 'login'], constraints: [
    { type: 'must', description: 'Use bcrypt or argon2 for password hashing' },
    { type: 'must-not', description: 'Never store passwords in plaintext or use weak hashing' },
  ]},
  { triggers: ['counter', 'increment', 'concurrent'], constraints: [
    { type: 'must', description: 'Use atomic operations for shared state updates' },
    { type: 'must-not', description: 'Never use read-then-write without locking' },
  ]},
  { triggers: ['api', 'fetch', 'request', 'http'], constraints: [
    { type: 'must', description: 'Handle HTTP errors explicitly' },
    { type: 'prefer', description: 'Include timeout for HTTP requests' },
  ]},
  { triggers: ['array', 'list', 'collection'], constraints: [
    { type: 'must', description: 'Handle empty array/collection edge case' },
  ]},
  { triggers: ['parse', 'json', 'input'], constraints: [
    { type: 'must', description: 'Validate external input before processing' },
    { type: 'must', description: 'Wrap JSON.parse in try-catch' },
  ]},
  { triggers: ['file', 'path', 'fs'], constraints: [
    { type: 'must', description: 'Handle file operation errors' },
  ]},
  { triggers: ['float', 'decimal', 'money'], constraints: [
    { type: 'must-not', description: 'Never compare floats with strict equality' },
  ]},
  { triggers: ['async', 'await', 'promise'], constraints: [
    { type: 'must', description: 'Handle promise rejections' },
  ]},
];

const CONSTRAINT_SYSTEM = `You are a constraint generator. Given specs, produce constraints that PREVENT common failures.
Each: { "type": "must|must-not|prefer", "description": "...", "pattern": "optional code example" }
Return ONLY a JSON array. No markdown fences.`;

// ── Phase 3: Guided Generation ───────────────────────────────────
// (System prompt is built dynamically from specs and constraints)

// ── Phase 4: Self-Verification ───────────────────────────────────

const VERIFICATION_SYSTEM = `You are a code reviewer verifying generated code against specifications.
Return ONLY a JSON array: [{ "specId": "SPEC-001", "status": "satisfied|partial|unsatisfied|unknown", "reasoning": "..." }]
No markdown fences.`;

// ── Handler ──────────────────────────────────────────────────────

async function handler(req: VercelRequest, res: VercelResponse, ctx: import('../lib/types.js').RequestContext) {
  if (req.method !== 'POST') {
    throw new ApiError('method_not_allowed', 'Method not allowed. Use POST.');
  }

  const { task, language = 'typescript' } = req.body || {};

  if (!task || typeof task !== 'string') {
    throw new ApiError('bad_request', 'Missing required field: task (string)');
  }

  const startTime = Date.now();
  let totalIn = 0;
  let totalOut = 0;
  let pipelineCalls = 0;

  console.log(`[reverse] Starting: task="${task.slice(0, 50)}" lang=${language}`);

  // ── Phase 1: Spec Synthesis ──

  const specResp = await callAnthropic(
    SYNTHESIS_SYSTEM,
    `Language: ${language}\n\nTask:\n${task}`,
    16_000,
  );
  totalIn += specResp.usage.input_tokens;
  totalOut += specResp.usage.output_tokens;
  pipelineCalls++;

  const specs = safeParseArray(getText(specResp)) as ReverseSpec[];
  console.log(`[reverse] Phase 1 done: ${specs.length} specs`);

  // ── Phase 2: Constraints ──

  const taskLower = task.toLowerCase();
  const domainConstraints: Array<{ type: string; description: string; pattern?: string; source: string }> = [];
  for (const p of DOMAIN_PATTERNS) {
    if (p.triggers.some(t => taskLower.includes(t))) {
      for (const c of p.constraints) {
        domainConstraints.push({ ...c, source: 'domain' });
      }
    }
  }

  const specList = specs.map(s =>
    `[${s.id}] (${s.category}, ${s.severity}) ${s.description}\n  Assertion: ${s.assertion}`
  ).join('\n\n');

  const conResp = await callAnthropic(
    CONSTRAINT_SYSTEM,
    `Language: ${language}\nTask: ${task}\n\nSpecifications:\n${specList}`,
    8_000,
  );
  totalIn += conResp.usage.input_tokens;
  totalOut += conResp.usage.output_tokens;
  pipelineCalls++;

  const specConstraints = (safeParseArray(getText(conResp)) as Array<{
    type: string; description: string; pattern?: string;
  }>).map(c => ({ ...c, source: 'spec' }));

  const allConstraints = [...domainConstraints, ...specConstraints];
  const seen = new Set<string>();
  const constraints: ReverseConstraint[] = allConstraints.filter(c => {
    const k = c.description.toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  }).map((c, i) => ({
    id: `CON-${String(i + 1).padStart(3, '0')}`,
    type: c.type as 'must' | 'must-not' | 'prefer',
    description: c.description,
    pattern: c.pattern,
    source: c.source,
  }));

  console.log(`[reverse] Phase 2 done: ${constraints.length} constraints`);

  // ── Phase 3: Guided Generation ──

  const specBlock = specs.map(s =>
    `[${s.id}] (${s.severity}/${s.category}): ${s.description}\n  Assertion: ${s.assertion}`
  ).join('\n');

  const musts = constraints.filter(c => c.type === 'must');
  const mustNots = constraints.filter(c => c.type === 'must-not');
  const prefers = constraints.filter(c => c.type === 'prefer');

  let conBlock = '';
  if (musts.length) conBlock += 'MUST DO:\n' + musts.map(c => `- ${c.id}: ${c.description}`).join('\n') + '\n\n';
  if (mustNots.length) conBlock += 'MUST NOT DO:\n' + mustNots.map(c => `- ${c.id}: ${c.description}${c.pattern ? `\n  Bad: ${c.pattern}` : ''}`).join('\n') + '\n\n';
  if (prefers.length) conBlock += 'PREFER:\n' + prefers.map(c => `- ${c.id}: ${c.description}`).join('\n') + '\n';

  const genSystem = `You are an expert programmer. Generate production-quality ${language} code.\n\nSPECIFICATIONS — Your code MUST satisfy ALL:\n${specBlock}\n\nCONSTRAINTS:\n${conBlock}\nReturn ONLY the code. No markdown fences, no explanations.`;

  const genResp = await callAnthropic(
    genSystem,
    `Generate ${language} code for:\n\n${task}`,
    16_000,
  );
  totalIn += genResp.usage.input_tokens;
  totalOut += genResp.usage.output_tokens;
  pipelineCalls++;

  const code = stripFences(getText(genResp));
  console.log(`[reverse] Phase 3 done: ${code.length} chars of code`);

  // ── Phase 4: Self-Verification ──

  const verResp = await callAnthropic(
    VERIFICATION_SYSTEM,
    `CODE:\n${code}\n\nSPECIFICATIONS:\n${specBlock}`,
    8_000,
  );
  totalIn += verResp.usage.input_tokens;
  totalOut += verResp.usage.output_tokens;
  pipelineCalls++;

  const verification = safeParseArray(getText(verResp)) as ReverseVerificationItem[];
  const satisfiedCount = verification.filter(v => v.status === 'satisfied').length;

  const durationMs = Date.now() - startTime;

  console.log(`[reverse] Done: ${satisfiedCount}/${specs.length} specs satisfied in ${durationMs}ms`);

  // ── Track usage ──

  await trackUsage({
    api_key_id: ctx.apiKey.id,
    endpoint: 'reverse',
    status_code: 200,
    input_tokens: totalIn,
    output_tokens: totalOut,
    duration_ms: durationMs,
    pipeline_calls: pipelineCalls,
    request_id: ctx.requestId,
  });

  const response: ReverseResponse = {
    request_id: ctx.requestId,
    task,
    language,
    code,
    specs: { count: specs.length, items: specs },
    constraints: { count: constraints.length, items: constraints },
    verification: {
      satisfied: satisfiedCount,
      total: specs.length,
      percentage: specs.length > 0 ? +((satisfiedCount / specs.length) * 100).toFixed(1) : 0,
      items: verification,
    },
    usage: {
      input_tokens: totalIn,
      output_tokens: totalOut,
      duration_ms: durationMs,
      pipeline_calls: pipelineCalls,
    },
  };

  res.status(200).json(response);
}

export default withAuth(handler);
