import { getClient, MODEL } from './anthropic.js';
import { readFileContent } from './indexer.js';
const VALID_VERDICTS = ['PASS', 'PARTIAL', 'FAIL', 'N/A'];
const FILE_SELECTION_SYSTEM = `You are a code auditor. Given a list of claims and a codebase file tree, identify which files are most likely to contain evidence for or against each claim.

For each claim, list 1-5 file paths from the tree that should be examined.

OUTPUT FORMAT:
Return a JSON object mapping claim IDs to arrays of file paths:
{
  "CLAIM-001": ["src/lib/auth.ts", "src/middleware.ts"],
  "CLAIM-002": ["prisma/schema.prisma", "src/api/users/route.ts"]
}

Return ONLY the JSON. No markdown fences, no commentary.
Be specific -- pick the most relevant files. If no files in the tree could contain evidence, use an empty array.`;
const VERIFICATION_SYSTEM = `You are a compliance auditor verifying whether code implements what a claim states.

For each claim, evaluate the code evidence and assign a verdict:
- PASS: The code fully implements what the claim states
- PARTIAL: The code partially implements it (some aspects missing or incomplete)
- FAIL: The code does not implement what the claim states, or contradicts it
- N/A: The claim cannot be verified from code (e.g., business process, legal statement)

OUTPUT FORMAT:
Return a JSON array of verification results:
[
  {
    "claimId": "CLAIM-001",
    "verdict": "PASS",
    "evidence": [
      {
        "file": "src/lib/encryption.ts",
        "lineNumber": 42,
        "snippet": "const cipher = createCipheriv('aes-256-gcm', key, iv)",
        "confidence": 0.95
      }
    ],
    "reasoning": "AES-256-GCM encryption is implemented for data at rest."
  }
]

Rules:
- Evidence snippets should be short (1-3 lines), directly relevant
- Confidence: 0.0 to 1.0
- Reasoning: 1-2 sentences
- Be strict: if the claim says "AES-256" and code uses "AES-128", that's FAIL
- N/A is for claims that genuinely can't be verified from code

Return ONLY the JSON array. No markdown fences.`;
function parseVerificationResponse(rawText) {
    let jsonText = rawText.trim();
    if (jsonText.startsWith('```')) {
        const firstNewline = jsonText.indexOf('\n');
        if (firstNewline !== -1)
            jsonText = jsonText.slice(firstNewline + 1);
    }
    const lastFence = jsonText.lastIndexOf('```');
    if (lastFence !== -1)
        jsonText = jsonText.slice(0, lastFence);
    jsonText = jsonText.trim();
    if (!jsonText.endsWith(']')) {
        const lastBrace = jsonText.lastIndexOf('}');
        if (lastBrace !== -1)
            jsonText = jsonText.slice(0, lastBrace + 1) + ']';
    }
    const parsed = JSON.parse(jsonText);
    if (!Array.isArray(parsed))
        return [];
    return parsed
        .filter((r) => r.claimId && r.verdict)
        .map((r) => ({
        claimId: r.claimId,
        claim: '',
        verdict: VALID_VERDICTS.includes(r.verdict)
            ? r.verdict
            : 'N/A',
        evidence: (r.evidence || [])
            .filter((e) => e.file && e.snippet)
            .map((e) => ({
            file: e.file,
            lineNumber: e.lineNumber,
            snippet: e.snippet,
            confidence: typeof e.confidence === 'number' ? e.confidence : 0.5,
        })),
        reasoning: r.reasoning || '',
    }));
}
function parseFileSelectionResponse(rawText) {
    let jsonText = rawText.trim();
    if (jsonText.startsWith('```')) {
        const firstNewline = jsonText.indexOf('\n');
        if (firstNewline !== -1)
            jsonText = jsonText.slice(firstNewline + 1);
    }
    const lastFence = jsonText.lastIndexOf('```');
    if (lastFence !== -1)
        jsonText = jsonText.slice(0, lastFence);
    jsonText = jsonText.trim();
    if (!jsonText.endsWith('}')) {
        const lastBrace = jsonText.lastIndexOf('}');
        if (lastBrace !== -1)
            jsonText = jsonText.slice(0, lastBrace + 1);
    }
    return JSON.parse(jsonText);
}
const BATCH_SIZE = 15;
export async function verifyClaims(claims, index, log) {
    const client = getClient();
    const testableClaims = claims.filter((c) => c.testable);
    const verifications = [];
    let totalInputTokens = 0;
    let totalOutputTokens = 0;
    // Mark non-testable claims as N/A
    for (const claim of claims) {
        if (!claim.testable) {
            verifications.push({
                claimId: claim.id,
                claim: claim.text,
                verdict: 'N/A',
                evidence: [],
                reasoning: 'Claim is not testable against code.',
            });
        }
    }
    const treeStr = index.fileTree.slice(0, 2000).join('\n');
    for (let i = 0; i < testableClaims.length; i += BATCH_SIZE) {
        const batch = testableClaims.slice(i, i + BATCH_SIZE);
        const batchNum = Math.floor(i / BATCH_SIZE) + 1;
        const totalBatches = Math.ceil(testableClaims.length / BATCH_SIZE);
        log(`Batch ${batchNum}/${totalBatches}: selecting files for ${batch.length} claims...`);
        const claimList = batch
            .map((c) => `${c.id}: ${c.text} [${c.category}]`)
            .join('\n');
        // Step 1: File selection
        const fileSelResponse = await client.messages.create({
            model: MODEL,
            max_tokens: 4_000,
            system: FILE_SELECTION_SYSTEM,
            messages: [
                {
                    role: 'user',
                    content: `Claims to verify:\n${claimList}\n\nCodebase file tree:\n${treeStr}`,
                },
            ],
        });
        totalInputTokens += fileSelResponse.usage.input_tokens;
        totalOutputTokens += fileSelResponse.usage.output_tokens;
        const fileSelText = fileSelResponse.content
            .filter((b) => b.type === 'text')
            .map((b) => b.text)
            .join('');
        let fileSelections;
        try {
            fileSelections = parseFileSelectionResponse(fileSelText);
        }
        catch {
            fileSelections = {};
            for (const claim of batch) {
                fileSelections[claim.id] = index.keyFiles.slice(0, 5).map((f) => f.path);
            }
        }
        // Step 2: Read files
        const uniqueFiles = new Set();
        for (const files of Object.values(fileSelections)) {
            for (const f of files)
                uniqueFiles.add(f);
        }
        log(`Batch ${batchNum}/${totalBatches}: reading ${uniqueFiles.size} files...`);
        const fileContents = new Map();
        for (const filePath of uniqueFiles) {
            const content = await readFileContent(index.rootPath, filePath);
            if (content) {
                fileContents.set(filePath, content);
            }
        }
        // Step 3: Verify
        log(`Batch ${batchNum}/${totalBatches}: verifying ${batch.length} claims...`);
        let evidenceContext = '';
        for (const [path, content] of fileContents) {
            const truncated = content.length > 10_000
                ? content.slice(0, 10_000) + '\n[... truncated]'
                : content;
            evidenceContext += `\n--- FILE: ${path} ---\n${truncated}\n`;
        }
        if (evidenceContext.length > 80_000) {
            evidenceContext = evidenceContext.slice(0, 80_000) + '\n[... context truncated]';
        }
        const verifyResponse = await client.messages.create({
            model: MODEL,
            max_tokens: 8_000,
            system: VERIFICATION_SYSTEM,
            messages: [
                {
                    role: 'user',
                    content: `Claims to verify:\n${claimList}\n\nCode evidence:\n${evidenceContext}`,
                },
            ],
        });
        totalInputTokens += verifyResponse.usage.input_tokens;
        totalOutputTokens += verifyResponse.usage.output_tokens;
        const verifyText = verifyResponse.content
            .filter((b) => b.type === 'text')
            .map((b) => b.text)
            .join('');
        try {
            const batchResults = parseVerificationResponse(verifyText);
            for (const result of batchResults) {
                const claim = batch.find((c) => c.id === result.claimId);
                if (claim) {
                    result.claim = claim.text;
                    verifications.push(result);
                }
            }
            for (const claim of batch) {
                if (!batchResults.some((r) => r.claimId === claim.id)) {
                    verifications.push({
                        claimId: claim.id,
                        claim: claim.text,
                        verdict: 'N/A',
                        evidence: [],
                        reasoning: 'No verification result returned.',
                    });
                }
            }
        }
        catch {
            for (const claim of batch) {
                verifications.push({
                    claimId: claim.id,
                    claim: claim.text,
                    verdict: 'N/A',
                    evidence: [],
                    reasoning: 'Failed to parse verification response.',
                });
            }
        }
    }
    verifications.sort((a, b) => a.claimId.localeCompare(b.claimId));
    return {
        verifications,
        inputTokens: totalInputTokens,
        outputTokens: totalOutputTokens,
    };
}
//# sourceMappingURL=verifier.js.map