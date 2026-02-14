export type ClaimCategory =
  | 'data-privacy'
  | 'security'
  | 'functionality'
  | 'operational'
  | 'legal';

export type ClaimSeverity = 'critical' | 'high' | 'medium' | 'low';

export interface Claim {
  id: string;
  section: string;
  category: ClaimCategory;
  severity: ClaimSeverity;
  text: string;
  testable: boolean;
}

export type Verdict = 'PASS' | 'PARTIAL' | 'FAIL' | 'N/A';

export interface Evidence {
  file: string;
  lineNumber?: number;
  snippet: string;
  confidence: number;
}

export interface ClaimVerification {
  claimId: string;
  claim: string;
  verdict: Verdict;
  evidence: Evidence[];
  reasoning: string;
}

export interface ActionInputs {
  workingDirectory: string;
  scanMode: 'full' | 'changed';
  failThreshold: number;
  docSource: string;
  changedFilesMode: 'full' | 'changed';
  mode: 'byok' | 'lucid-api';
}

export interface VerificationSummary {
  complianceScore: number;
  totalClaims: number;
  passCount: number;
  failCount: number;
  partialCount: number;
  naCount: number;
  criticalFails: ClaimVerification[];
  topIssues: ClaimVerification[];
  verifications: ClaimVerification[];
  claims: Claim[];
}

// ── LUCID API Response Types (mirrors api/lib/types.ts) ─────

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
