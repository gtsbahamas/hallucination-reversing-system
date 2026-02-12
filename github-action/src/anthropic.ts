import Anthropic from '@anthropic-ai/sdk';

export const MODEL = 'claude-sonnet-4-5-20250929';

let clientInstance: Anthropic | null = null;

export function getClient(): Anthropic {
  if (clientInstance) return clientInstance;

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      'ANTHROPIC_API_KEY is not set. Pass it via the anthropic-api-key input.'
    );
  }
  clientInstance = new Anthropic({ apiKey, timeout: 10 * 60 * 1000 });
  return clientInstance;
}
