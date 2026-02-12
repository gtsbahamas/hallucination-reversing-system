import type { VercelRequest, VercelResponse } from '@vercel/node';
import Anthropic from '@anthropic-ai/sdk';

const MODEL = 'claude-sonnet-4-5-20250929';

function getClient(): Anthropic {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY not configured');
  }
  return new Anthropic({ apiKey, timeout: 5 * 60 * 1000 });
}

// ── Spec Synthesizer ──────────────────────────────────────────

const SYNTHESIS_SYSTEM = `You are a formal specification synthesizer. Given a coding task and target language, generate 10-30 formal specifications the code MUST satisfy.

Each spec: { "id": "SPEC-001", "category": "correctness|security|performance|error-handling|edge-case|type-safety", "severity": "critical|high|medium|low", "description": "...", "assertion": "testable assertion", "rationale": "..." }

Cover: correctness, edge cases, error handling, security, type safety, performance.
Return ONLY a JSON array. No markdown fences.`;

// ── Constraint Engine ─────────────────────────────────────────

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

// ── Guided Generator ──────────────────────────────────────────

const VERIFICATION_SYSTEM = `You are a code reviewer verifying generated code against specifications.
Return ONLY a JSON array: [{ "specId": "SPEC-001", "status": "satisfied|partial|unsatisfied|unknown", "reasoning": "..." }]
No markdown fences.`;

// ── JSON Helpers ──────────────────────────────────────────────

function stripFences(text: string): string {
  let t = text.trim();
  if (t.startsWith('```')) { const nl = t.indexOf('\n'); if (nl !== -1) t = t.slice(nl + 1); }
  const lf = t.lastIndexOf('```'); if (lf !== -1) t = t.slice(0, lf);
  t = t.trim();
  if (!t.endsWith(']') && !t.endsWith('}')) {
    const lb = t.lastIndexOf('}');
    if (lb !== -1) t = t.slice(0, lb + 1) + ']';
  }
  return t;
}

function safeParseArray(text: string): unknown[] {
  try {
    const parsed = JSON.parse(stripFences(text));
    return Array.isArray(parsed) ? parsed : [];
  } catch { return []; }
}

// ── Main Handler ──────────────────────────────────────────────

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed. Use POST.' });
  }

  const { task, language = 'typescript' } = req.body || {};

  if (!task || typeof task !== 'string') {
    return res.status(400).json({ error: 'Missing required field: task (string)' });
  }

  // Optional auth
  const authHeader = req.headers.authorization;
  const expectedKey = process.env.LUCID_API_KEY;
  if (expectedKey && authHeader !== `Bearer ${expectedKey}`) {
    return res.status(401).json({ error: 'Invalid or missing API key' });
  }

  try {
    const client = getClient();
    const startTime = Date.now();
    let totalIn = 0, totalOut = 0;

    // ── Phase 1: Spec Synthesis ──
    const specMsg = await client.messages.create({
      model: MODEL, max_tokens: 16_000,
      system: SYNTHESIS_SYSTEM,
      messages: [{ role: 'user', content: `Language: ${language}\n\nTask:\n${task}` }],
    });
    totalIn += specMsg.usage.input_tokens;
    totalOut += specMsg.usage.output_tokens;
    const specText = specMsg.content.filter((b): b is Anthropic.TextBlock => b.type === 'text').map(b => b.text).join('');
    const specs = safeParseArray(specText) as Array<{ id: string; category: string; severity: string; description: string; assertion: string; rationale: string }>;

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

    const specList = specs.map(s => `[${s.id}] (${s.category}, ${s.severity}) ${s.description}\n  Assertion: ${s.assertion}`).join('\n\n');
    const conMsg = await client.messages.create({
      model: MODEL, max_tokens: 8_000,
      system: CONSTRAINT_SYSTEM,
      messages: [{ role: 'user', content: `Language: ${language}\nTask: ${task}\n\nSpecifications:\n${specList}` }],
    });
    totalIn += conMsg.usage.input_tokens;
    totalOut += conMsg.usage.output_tokens;
    const conText = conMsg.content.filter((b): b is Anthropic.TextBlock => b.type === 'text').map(b => b.text).join('');
    const specConstraints = (safeParseArray(conText) as Array<{ type: string; description: string; pattern?: string }>).map(c => ({ ...c, source: 'spec' }));

    const allConstraints = [...domainConstraints, ...specConstraints];
    const seen = new Set<string>();
    const constraints = allConstraints.filter(c => {
      const k = c.description.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    }).map((c, i) => ({ id: `CON-${String(i + 1).padStart(3, '0')}`, ...c }));

    // ── Phase 3: Guided Generation ──
    const specBlock = specs.map(s => `[${s.id}] (${s.severity}/${s.category}): ${s.description}\n  Assertion: ${s.assertion}`).join('\n');
    const musts = constraints.filter(c => c.type === 'must');
    const mustNots = constraints.filter(c => c.type === 'must-not');
    const prefers = constraints.filter(c => c.type === 'prefer');

    let conBlock = '';
    if (musts.length) conBlock += 'MUST DO:\n' + musts.map(c => `- ${c.id}: ${c.description}`).join('\n') + '\n\n';
    if (mustNots.length) conBlock += 'MUST NOT DO:\n' + mustNots.map(c => `- ${c.id}: ${c.description}${c.pattern ? `\n  Bad: ${c.pattern}` : ''}`).join('\n') + '\n\n';
    if (prefers.length) conBlock += 'PREFER:\n' + prefers.map(c => `- ${c.id}: ${c.description}`).join('\n') + '\n';

    const genSystem = `You are an expert programmer. Generate production-quality ${language} code.\n\nSPECIFICATIONS — Your code MUST satisfy ALL:\n${specBlock}\n\nCONSTRAINTS:\n${conBlock}\nReturn ONLY the code. No markdown fences, no explanations.`;

    const genMsg = await client.messages.create({
      model: MODEL, max_tokens: 16_000,
      system: genSystem,
      messages: [{ role: 'user', content: `Generate ${language} code for:\n\n${task}` }],
    });
    totalIn += genMsg.usage.input_tokens;
    totalOut += genMsg.usage.output_tokens;
    const code = stripFences(genMsg.content.filter((b): b is Anthropic.TextBlock => b.type === 'text').map(b => b.text).join(''));

    // ── Self-Verification ──
    const verMsg = await client.messages.create({
      model: MODEL, max_tokens: 8_000,
      system: VERIFICATION_SYSTEM,
      messages: [{ role: 'user', content: `CODE:\n${code}\n\nSPECIFICATIONS:\n${specBlock}` }],
    });
    totalIn += verMsg.usage.input_tokens;
    totalOut += verMsg.usage.output_tokens;
    const verText = verMsg.content.filter((b): b is Anthropic.TextBlock => b.type === 'text').map(b => b.text).join('');
    const verification = safeParseArray(verText) as Array<{ specId: string; status: string; reasoning: string }>;
    const satisfiedCount = verification.filter(v => v.status === 'satisfied').length;

    const durationMs = Date.now() - startTime;

    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(200).json({
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
        inputTokens: totalIn,
        outputTokens: totalOut,
        durationMs,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Internal server error';
    return res.status(500).json({ error: message });
  }
}
