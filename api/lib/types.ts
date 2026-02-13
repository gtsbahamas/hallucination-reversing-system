// ── Tier Configuration ───────────────────────────────────────

export interface TierConfig {
  id: string;
  name: string;
  forward_monthly_limit: number | null;  // null = unlimited
  reverse_monthly_limit: number | null;
  requests_per_minute: number;
  forward_price_cents: number;
  reverse_price_cents: number;
}

// ── API Key ──────────────────────────────────────────────────

export interface ApiKeyRecord {
  id: string;
  key_hash: string;
  key_prefix: string;
  name: string;
  tier_id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  tier?: TierConfig;
}

// ── Request Context (attached by middleware) ──────────────────

export interface RequestContext {
  apiKey: ApiKeyRecord;
  tier: TierConfig;
  requestId: string;
}

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

// ── Usage ────────────────────────────────────────────────────

export interface UsageResponse {
  request_id: string;
  period: string;
  forward: { count: number; limit: number | null };
  reverse: { count: number; limit: number | null };
  total_input_tokens: number;
  total_output_tokens: number;
}

// ── Keys ─────────────────────────────────────────────────────

export interface CreateKeyRequest {
  email: string;
  name: string;
  tier?: string;
}

export interface CreateKeyResponse {
  request_id: string;
  key: string;         // Only returned once at creation
  key_prefix: string;
  name: string;
  tier: string;
  email: string;
  created_at: string;
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

// ── Anthropic ────────────────────────────────────────────────

export interface TextBlock {
  type: 'text';
  text: string;
}

export interface AnthropicResponse {
  content: Array<TextBlock | { type: string }>;
  usage: { input_tokens: number; output_tokens: number };
}
