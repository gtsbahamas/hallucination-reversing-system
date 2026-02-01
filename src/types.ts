export interface LucidConfig {
  projectName: string;
  description: string;
  techStack: string;
  targetAudience: string;
  createdAt: string;
}

export type HallucinationType = 'tos' | 'api-docs' | 'user-manual';

export interface HallucinationMeta {
  type: HallucinationType;
  iteration: number;
  model: string;
  inputTokens: number;
  outputTokens: number;
  sectionCount: number;
  estimatedClaims: number;
  generatedAt: string;
  durationMs: number;
}

// --- Claim extraction types ---

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

export interface ExtractionResult {
  iteration: number;
  documentType: string;
  claims: Claim[];
  totalClaims: number;
  testableClaims: number;
  extractedAt: string;
}

// --- Verification types ---

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

export interface VerificationReport {
  iteration: number;
  codebasePath: string;
  verdicts: { pass: number; partial: number; fail: number; na: number };
  verifications: ClaimVerification[];
  generatedAt: string;
}
