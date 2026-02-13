import type { VercelRequest, VercelResponse } from '@vercel/node';
import { callAnthropic, getText, safeParseArray, stripFences } from '../lib/anthropic.js';
import { withAuth } from '../lib/middleware.js';
import { ApiError } from '../lib/errors.js';
import { trackUsage } from '../lib/usage-tracker.js';
import type {
  ForwardClaim,
  ForwardVerification,
  ForwardRemediation,
  ForwardResponse,
} from '../lib/types.js';

// ── Phase 1: Claim Extraction ────────────────────────────────────

const EXTRACTION_SYSTEM = `You are a code quality auditor. Given source code, extract every testable claim the code makes about its behavior.

A "claim" is any implicit or explicit assertion about what the code does:
- Function signatures claim they accept certain inputs and return certain outputs
- Error handling claims it handles specific failure modes
- Security-sensitive code claims it prevents attacks
- Edge case handling claims it handles boundary conditions
- Type annotations claim data conforms to a shape
- Performance-sensitive code claims acceptable resource usage

For each claim:
{ "id": "CLAIM-001", "category": "correctness|security|performance|error-handling|edge-case|type-safety", "severity": "critical|high|medium|low", "description": "human-readable description of the claim", "assertion": "precise testable assertion", "testable": true }

Be thorough. A typical function has 3-8 claims. Cover:
- Return value correctness for all input classes
- Error/exception handling completeness
- Boundary/edge case coverage
- Security properties (injection, auth, data leaks)
- Type safety and null handling
- Concurrency safety if applicable

Return ONLY a JSON array. No markdown fences.`;

// ── Phase 2: Claim Verification ──────────────────────────────────

const VERIFICATION_SYSTEM = `You are a formal verification engine. Given source code and a list of claims about that code, verify each claim against the actual implementation.

For each claim, determine:
- PASS: The code fully satisfies the claim with evidence
- PARTIAL: The code partially satisfies the claim but has gaps
- FAIL: The code does NOT satisfy the claim
- N/A: The claim is not applicable to this code

Provide specific evidence: quote code lines, identify missing checks, point to logic gaps.

Return ONLY a JSON array:
[{ "claimId": "CLAIM-001", "verdict": "PASS|PARTIAL|FAIL|N/A", "reasoning": "detailed explanation with code evidence", "evidence": "quoted code or identified gap" }]
No markdown fences.`;

// ── Phase 3: Remediation ─────────────────────────────────────────

const REMEDIATION_SYSTEM = `You are a code remediation engine. Given source code, claims, and verification results showing FAIL or PARTIAL verdicts, generate specific remediation tasks.

For each failed or partial claim, produce a fix task:
{ "claimId": "CLAIM-001", "title": "short fix title", "description": "what needs to change and why", "action": "add|modify|remove", "severity": "critical|high|medium|low", "codeGuidance": "specific code changes needed — reference function names or line patterns in the provided code" }

Focus on actionable, specific guidance. Reference the actual code structure.

Return ONLY a JSON array. No markdown fences.`;

// ── Handler ──────────────────────────────────────────────────────

async function handler(req: VercelRequest, res: VercelResponse, ctx: import('../lib/types.js').RequestContext) {
  if (req.method !== 'POST') {
    throw new ApiError('method_not_allowed', 'Method not allowed. Use POST.');
  }

  const { code, language = 'typescript', context } = req.body || {};

  if (!code || typeof code !== 'string') {
    throw new ApiError('bad_request', 'Missing required field: code (string)');
  }

  const startTime = Date.now();
  let totalIn = 0;
  let totalOut = 0;
  let pipelineCalls = 0;

  console.log(`[forward] Starting: code=${code.length} chars, lang=${language}`);

  // ── Phase 1: Extract Claims ──

  const contextBlock = context ? `\n\nAdditional context:\n${context}` : '';
  const extractResp = await callAnthropic(
    EXTRACTION_SYSTEM,
    `Language: ${language}\n\nCode:\n${code}${contextBlock}`,
    16_000,
  );
  totalIn += extractResp.usage.input_tokens;
  totalOut += extractResp.usage.output_tokens;
  pipelineCalls++;

  const claims = safeParseArray(getText(extractResp)) as ForwardClaim[];
  console.log(`[forward] Phase 1 done: ${claims.length} claims extracted`);

  // ── Phase 2: Verify Claims ──

  const claimList = claims.map(c =>
    `[${c.id}] (${c.category}, ${c.severity}) ${c.description}\n  Assertion: ${c.assertion}`
  ).join('\n\n');

  const verifyResp = await callAnthropic(
    VERIFICATION_SYSTEM,
    `Language: ${language}\n\nCode:\n${code}\n\nClaims to verify:\n${claimList}`,
    16_000,
  );
  totalIn += verifyResp.usage.input_tokens;
  totalOut += verifyResp.usage.output_tokens;
  pipelineCalls++;

  const verifications = safeParseArray(getText(verifyResp)) as ForwardVerification[];
  const passed = verifications.filter(v => v.verdict === 'PASS').length;
  const failed = verifications.filter(v => v.verdict === 'FAIL').length;
  const partial = verifications.filter(v => v.verdict === 'PARTIAL').length;

  console.log(`[forward] Phase 2 done: ${passed} pass, ${failed} fail, ${partial} partial`);

  // ── Phase 3: Remediate ──

  const failedOrPartial = verifications.filter(v => v.verdict === 'FAIL' || v.verdict === 'PARTIAL');
  let remediations: ForwardRemediation[] = [];

  if (failedOrPartial.length > 0) {
    const failedClaimDetails = failedOrPartial.map(v => {
      const claim = claims.find(c => c.id === v.claimId);
      return `[${v.claimId}] verdict=${v.verdict}\n  Claim: ${claim?.description ?? 'unknown'}\n  Reasoning: ${v.reasoning}`;
    }).join('\n\n');

    const remResp = await callAnthropic(
      REMEDIATION_SYSTEM,
      `Language: ${language}\n\nCode:\n${code}\n\nFailed/Partial claims:\n${failedClaimDetails}`,
      8_000,
    );
    totalIn += remResp.usage.input_tokens;
    totalOut += remResp.usage.output_tokens;
    pipelineCalls++;

    remediations = safeParseArray(getText(remResp)) as ForwardRemediation[];
    console.log(`[forward] Phase 3 done: ${remediations.length} remediation tasks`);
  } else {
    console.log(`[forward] Phase 3 skipped: no failures to remediate`);
  }

  const durationMs = Date.now() - startTime;

  // ── Track usage ──

  await trackUsage({
    api_key_id: ctx.apiKey.id,
    endpoint: 'forward',
    status_code: 200,
    input_tokens: totalIn,
    output_tokens: totalOut,
    duration_ms: durationMs,
    pipeline_calls: pipelineCalls,
    request_id: ctx.requestId,
  });

  console.log(`[forward] Complete: ${claims.length} claims, ${passed}/${verifications.length} passed in ${durationMs}ms`);

  const response: ForwardResponse = {
    request_id: ctx.requestId,
    code,
    language,
    claims: { count: claims.length, items: claims },
    verification: {
      passed,
      failed,
      partial,
      total: verifications.length,
      items: verifications,
    },
    remediation: { count: remediations.length, items: remediations },
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
