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
