import Anthropic from '@anthropic-ai/sdk';
export const MODEL = 'claude-sonnet-4-5-20250929';
let clientInstance = null;
/**
 * Detect which mode to use based on environment variables.
 * LUCID API key takes precedence if both are set.
 */
export function detectMode() {
    const lucidKey = process.env.LUCID_API_KEY;
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    if (lucidKey)
        return 'lucid-api';
    if (anthropicKey)
        return 'byok';
    throw new Error('No API key found. Set either LUCID_API_KEY (recommended) or ANTHROPIC_API_KEY.\n' +
        '  - LUCID API key: Get one free at https://trylucid.dev\n' +
        '  - Anthropic API key: https://console.anthropic.com');
}
/**
 * Get Anthropic SDK client for BYOK mode.
 * Throws if ANTHROPIC_API_KEY is not set.
 */
export function getClient() {
    if (clientInstance)
        return clientInstance;
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
        throw new Error('ANTHROPIC_API_KEY is not set. Pass it via the anthropic-api-key input.');
    }
    clientInstance = new Anthropic({ apiKey, timeout: 10 * 60 * 1000 });
    return clientInstance;
}
const LUCID_API_BASE = 'https://api.trylucid.dev';
/**
 * Verify a code snippet via the LUCID API (lucid-api mode).
 * One call = one file = one quota unit.
 */
export async function verifyViaLucidApi(code, language, context) {
    const apiKey = process.env.LUCID_API_KEY;
    if (!apiKey) {
        throw new Error('LUCID_API_KEY is not set. Pass it via the lucid-api-key input.');
    }
    const body = { code, language };
    if (context)
        body.context = context;
    const response = await fetch(`${LUCID_API_BASE}/api/v1/forward`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        const errorBody = await response.text();
        let message = `LUCID API error (${response.status})`;
        try {
            const parsed = JSON.parse(errorBody);
            if (parsed.error?.message)
                message = parsed.error.message;
            if (parsed.error?.code === 'quota_exceeded') {
                message = 'LUCID API quota exceeded. Upgrade at https://trylucid.dev or switch to BYOK mode with your own Anthropic key.';
            }
            if (parsed.error?.code === 'unauthorized') {
                message = 'Invalid LUCID API key. Get a key at https://trylucid.dev';
            }
        }
        catch {
            // use default message
        }
        throw new Error(message);
    }
    return response.json();
}
//# sourceMappingURL=anthropic.js.map