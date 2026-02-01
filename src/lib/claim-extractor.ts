import type Anthropic from '@anthropic-ai/sdk';
import { getClient, MODEL } from './anthropic.js';
import type { Claim, ClaimCategory, ClaimSeverity } from '../types.js';

const EXTRACTION_SYSTEM_PROMPT = `You are a legal and technical claim extractor. Your job is to read a document (Terms of Service, Privacy Policy, API documentation, or user manual) and extract every declarative promise, commitment, or factual claim the document makes.

EXTRACTION RULES:

1. A "claim" is any statement that asserts something IS true, WILL happen, or IS provided.
   - GOOD claim: "User data is encrypted at rest using AES-256"
   - GOOD claim: "The API rate limit is 1,000 requests per minute"
   - NOT a claim: "Users should review these terms periodically" (advice, not a promise)

2. Split compound claims into individual claims.
   - "Data is encrypted at rest and in transit" → TWO claims: encryption at rest, encryption in transit

3. Mark each claim as testable or non-testable:
   - Testable: Can be verified by examining code, config, infrastructure, or behavior
   - Non-testable: Legal boilerplate, jurisdictional claims, subjective statements

4. Assign a category:
   - data-privacy: Data collection, storage, sharing, retention, deletion, consent
   - security: Encryption, authentication, access control, vulnerability management
   - functionality: Features, capabilities, performance, limits, SLAs
   - operational: Support, availability, maintenance, backup, disaster recovery
   - legal: Liability, indemnification, dispute resolution, IP, terms changes

5. Assign severity based on impact if the claim is false:
   - critical: Data breach, security failure, regulatory violation, data loss
   - high: Feature completely missing, SLA violation, payment issues
   - medium: Feature partially working, minor data handling issue
   - low: Documentation inaccuracy, cosmetic, non-functional

6. Include the section heading where the claim appears.

OUTPUT FORMAT:
Return a JSON array of claims. Each claim object:
{
  "id": "CLAIM-001",
  "section": "Section heading where claim appears",
  "category": "data-privacy|security|functionality|operational|legal",
  "severity": "critical|high|medium|low",
  "text": "The exact claim, rephrased as a testable assertion if needed",
  "testable": true|false
}

Number claims sequentially: CLAIM-001, CLAIM-002, etc.
Return ONLY the JSON array. No markdown fences, no commentary.`;

interface RawClaim {
  id?: string;
  section?: string;
  category?: string;
  severity?: string;
  text?: string;
  testable?: boolean;
}

const VALID_CATEGORIES: ClaimCategory[] = [
  'data-privacy', 'security', 'functionality', 'operational', 'legal',
];

const VALID_SEVERITIES: ClaimSeverity[] = [
  'critical', 'high', 'medium', 'low',
];

function validateClaim(raw: RawClaim, index: number): Claim | null {
  if (!raw.text || typeof raw.text !== 'string') return null;

  const category = VALID_CATEGORIES.includes(raw.category as ClaimCategory)
    ? (raw.category as ClaimCategory)
    : 'functionality';

  const severity = VALID_SEVERITIES.includes(raw.severity as ClaimSeverity)
    ? (raw.severity as ClaimSeverity)
    : 'medium';

  return {
    id: raw.id || `CLAIM-${String(index + 1).padStart(3, '0')}`,
    section: raw.section || 'Unknown',
    category,
    severity,
    text: raw.text.trim(),
    testable: typeof raw.testable === 'boolean' ? raw.testable : true,
  };
}

export async function extractClaims(
  document: string,
  onProgress?: (msg: string) => void,
): Promise<{ claims: Claim[]; inputTokens: number; outputTokens: number }> {
  const client = getClient();

  onProgress?.('Sending document to Claude for claim extraction...');

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 32_000,
    system: EXTRACTION_SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Extract all claims from this document:\n\n${document}`,
      },
    ],
  });

  const rawText = response.content
    .filter((block): block is Anthropic.TextBlock => block.type === 'text')
    .map((block) => block.text)
    .join('');

  onProgress?.('Parsing extraction results...');

  // Strip markdown code fences if present, then find the JSON array
  let jsonText = rawText.trim();

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

  jsonText = jsonText.trim();

  // If response was truncated (no closing ]), try to repair by closing the array
  if (!jsonText.endsWith(']')) {
    // Find the last complete object (ends with })
    const lastCloseBrace = jsonText.lastIndexOf('}');
    if (lastCloseBrace !== -1) {
      jsonText = jsonText.slice(0, lastCloseBrace + 1) + '\n]';
      onProgress?.('Note: Response was truncated. Recovered partial claims.');
    }
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(jsonText);
  } catch {
    throw new Error(
      `Failed to parse Claude's response as JSON.\n` +
      `First 200 chars: ${jsonText.slice(0, 200)}`,
    );
  }

  if (!Array.isArray(parsed)) {
    throw new Error('Expected a JSON array of claims from Claude.');
  }

  const claims: Claim[] = [];
  for (let i = 0; i < parsed.length; i++) {
    const validated = validateClaim(parsed[i] as RawClaim, i);
    if (validated) {
      claims.push(validated);
    }
  }

  return {
    claims,
    inputTokens: response.usage.input_tokens,
    outputTokens: response.usage.output_tokens,
  };
}

