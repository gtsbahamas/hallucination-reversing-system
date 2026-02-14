// ── Forward Pipeline ─────────────────────────────────────────

export interface ForwardRequest {
  code: string;
  language?: string;
  context?: string;
}

export interface ForwardClaim {
  id: string;
  category: 'correctness' | 'security' | 'performance' | 'error-handling' | 'edge-case' | 'type-safety';
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  assertion: string;
  testable: boolean;
}

export interface ForwardVerification {
  claimId: string;
  verdict: 'PASS' | 'PARTIAL' | 'FAIL' | 'N/A';
  reasoning: string;
  evidence?: string;
}

export interface ForwardRemediation {
  claimId: string;
  title: string;
  description: string;
  action: 'add' | 'modify' | 'remove';
  severity: string;
  codeGuidance: string;
}

export interface ForwardResponse {
  request_id: string;
  code: string;
  language: string;
  claims: { count: number; items: ForwardClaim[] };
  verification: {
    passed: number;
    failed: number;
    partial: number;
    total: number;
    items: ForwardVerification[];
  };
  remediation: { count: number; items: ForwardRemediation[] };
  usage: {
    input_tokens: number;
    output_tokens: number;
    duration_ms: number;
    pipeline_calls: number;
  };
}

// ── Reverse Pipeline ─────────────────────────────────────────

export interface ReverseRequest {
  task: string;
  language?: string;
}

export interface ReverseSpec {
  id: string;
  category: string;
  severity: string;
  description: string;
  assertion: string;
  rationale: string;
}

export interface ReverseConstraint {
  id: string;
  type: 'must' | 'must-not' | 'prefer';
  description: string;
  pattern?: string;
  source: string;
}

export interface ReverseVerificationItem {
  specId: string;
  status: 'satisfied' | 'partial' | 'unsatisfied' | 'unknown';
  reasoning: string;
}

export interface ReverseResponse {
  request_id: string;
  task: string;
  language: string;
  code: string;
  specs: { count: number; items: ReverseSpec[] };
  constraints: { count: number; items: ReverseConstraint[] };
  verification: {
    satisfied: number;
    total: number;
    percentage: number;
    items: ReverseVerificationItem[];
  };
  usage: {
    input_tokens: number;
    output_tokens: number;
    duration_ms: number;
    pipeline_calls: number;
  };
}

// ── Error ────────────────────────────────────────────────────

export type ErrorCode =
  | 'bad_request'
  | 'unauthorized'
  | 'forbidden'
  | 'not_found'
  | 'method_not_allowed'
  | 'rate_limited'
  | 'quota_exceeded'
  | 'internal_error'
  | 'upstream_error';

export interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
  };
  request_id: string;
}
