import { getClient, MODEL } from './anthropic.js';
const EXTRACTION_SYSTEM = `You are a compliance auditor. Given a codebase summary, generate testable claims about what the code should do.

Focus on:
- Security claims (auth, encryption, input validation, CSRF, XSS protection)
- Data privacy claims (data handling, storage, retention, user consent)
- Functionality claims (core features, error handling, edge cases)
- Operational claims (logging, monitoring, rate limiting, backups)

For each claim, provide:
- id: Sequential ID like CLAIM-001
- section: Category grouping
- category: one of data-privacy, security, functionality, operational, legal
- severity: critical, high, medium, or low
- text: The specific testable claim
- testable: true if verifiable from code, false otherwise

OUTPUT FORMAT:
Return a JSON array of claims. No markdown fences, no commentary.
Generate 15-30 claims, prioritizing critical and high severity items.`;
const DESCRIBE_EXTRACTION_SYSTEM = `You are a compliance auditor. Given a legal document (Terms of Service, Privacy Policy, or API docs), extract every testable claim.

A "claim" is any statement that implies the code MUST do something specific. Examples:
- "We encrypt all data at rest" → testable: check for encryption
- "Users can delete their accounts" → testable: check for delete endpoint
- "We never share data with third parties" → not testable from code alone

For each claim, provide:
- id: Sequential ID like CLAIM-001
- section: The document section it came from
- category: one of data-privacy, security, functionality, operational, legal
- severity: critical, high, medium, or low
- text: The exact claim or a clear paraphrase
- testable: true if verifiable from code

OUTPUT FORMAT:
Return a JSON array of claims. No markdown fences, no commentary.`;
function parseClaimsResponse(rawText) {
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
    // Handle truncation
    if (!jsonText.endsWith(']')) {
        const lastBrace = jsonText.lastIndexOf('}');
        if (lastBrace !== -1)
            jsonText = jsonText.slice(0, lastBrace + 1) + ']';
    }
    const parsed = JSON.parse(jsonText);
    if (!Array.isArray(parsed))
        return [];
    const validCategories = new Set(['data-privacy', 'security', 'functionality', 'operational', 'legal']);
    const validSeverities = new Set(['critical', 'high', 'medium', 'low']);
    return parsed
        .filter((c) => c.id && c.text)
        .map((c) => ({
        id: c.id,
        section: c.section || 'General',
        category: validCategories.has(c.category || '') ? c.category : 'functionality',
        severity: validSeverities.has(c.severity || '') ? c.severity : 'medium',
        text: c.text,
        testable: c.testable !== false,
    }));
}
export async function extractClaimsFromCodebase(fileTree, keyFileSummary, log) {
    const client = getClient();
    log('Generating claims from codebase analysis...');
    const treeStr = fileTree.slice(0, 1500).join('\n');
    const response = await client.messages.create({
        model: MODEL,
        max_tokens: 8_000,
        system: EXTRACTION_SYSTEM,
        messages: [
            {
                role: 'user',
                content: `Analyze this codebase and generate testable compliance claims.\n\nFile tree:\n${treeStr}\n\nKey files:\n${keyFileSummary}`,
            },
        ],
    });
    const text = response.content
        .filter((b) => b.type === 'text')
        .map((b) => b.text)
        .join('');
    const claims = parseClaimsResponse(text);
    log(`Extracted ${claims.length} claims`);
    return {
        claims,
        inputTokens: response.usage.input_tokens,
        outputTokens: response.usage.output_tokens,
    };
}
export async function extractClaimsFromDocument(documentContent, log) {
    const client = getClient();
    log('Extracting claims from document...');
    const truncated = documentContent.length > 50_000
        ? documentContent.slice(0, 50_000) + '\n[... truncated]'
        : documentContent;
    const response = await client.messages.create({
        model: MODEL,
        max_tokens: 8_000,
        system: DESCRIBE_EXTRACTION_SYSTEM,
        messages: [
            {
                role: 'user',
                content: `Extract all testable claims from this document:\n\n${truncated}`,
            },
        ],
    });
    const text = response.content
        .filter((b) => b.type === 'text')
        .map((b) => b.text)
        .join('');
    const claims = parseClaimsResponse(text);
    log(`Extracted ${claims.length} claims`);
    return {
        claims,
        inputTokens: response.usage.input_tokens,
        outputTokens: response.usage.output_tokens,
    };
}
//# sourceMappingURL=extractor.js.map