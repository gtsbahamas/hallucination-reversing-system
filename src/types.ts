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

// --- Remediation types ---

export type RemediationAction = 'add' | 'modify' | 'remove' | 'configure';

export interface RemediationTask {
  id: string;
  claimId: string;
  verdict: 'FAIL' | 'PARTIAL';
  severity: ClaimSeverity;
  category: ClaimCategory;
  title: string;
  description: string;
  action: RemediationAction;
  targetFiles: string[];
  estimatedEffort: 'trivial' | 'small' | 'medium' | 'large';
  codeGuidance: string;
}

export interface RemediationPlan {
  iteration: number;
  codebasePath: string;
  currentScore: number;
  targetScore: number;
  totalTasks: number;
  tasksByVerdict: { fail: number; partial: number };
  tasksBySeverity: { critical: number; high: number; medium: number; low: number };
  tasks: RemediationTask[];
  generatedAt: string;
  inputTokens: number;
  outputTokens: number;
  durationMs: number;
}

// ============================================================
// Reverse LUCID types — generation-time hallucination prevention
// ============================================================

export type SpecCategory =
  | 'correctness'
  | 'security'
  | 'performance'
  | 'error-handling'
  | 'edge-case'
  | 'type-safety';

/** A formal specification that generated code must satisfy */
export interface CodeSpec {
  id: string;
  category: SpecCategory;
  severity: ClaimSeverity;
  description: string;
  assertion: string;
  rationale: string;
}

export interface SpecSynthesisResult {
  task: string;
  language: string;
  specs: CodeSpec[];
  totalSpecs: number;
  synthesizedAt: string;
  inputTokens: number;
  outputTokens: number;
}

export type ConstraintType = 'must' | 'must-not' | 'prefer';
export type ConstraintSource = 'benchmark' | 'spec' | 'domain';

/** A constraint that guides code generation */
export interface GenerationConstraint {
  id: string;
  type: ConstraintType;
  description: string;
  pattern?: string;
  source: ConstraintSource;
}

export interface ConstraintSet {
  task: string;
  constraints: GenerationConstraint[];
  totalConstraints: number;
  generatedAt: string;
  inputTokens: number;
  outputTokens: number;
}

export type SelfVerificationStatus = 'satisfied' | 'partial' | 'unsatisfied' | 'unknown';

export interface SelfVerificationResult {
  specId: string;
  status: SelfVerificationStatus;
  reasoning: string;
}

/** The output of guided generation */
export interface GeneratedCode {
  task: string;
  code: string;
  language: string;
  specs: CodeSpec[];
  constraints: GenerationConstraint[];
  selfVerification: SelfVerificationResult[];
  satisfiedCount: number;
  totalSpecs: number;
  generatedAt: string;
  inputTokens: number;
  outputTokens: number;
}

/** Full reverse pipeline result */
export interface ReverseLucidResult {
  task: string;
  language: string;
  specSynthesis: SpecSynthesisResult;
  constraintSet: ConstraintSet;
  generatedCode: GeneratedCode;
  totalInputTokens: number;
  totalOutputTokens: number;
  totalDurationMs: number;
}
