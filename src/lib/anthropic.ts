import Anthropic from '@anthropic-ai/sdk';
import type { HallucinationType } from '../types.js';
import type { LucidConfig } from '../types.js';
import { getSystemPrompt, getUserPrompt } from './system-prompts.js';

export const MODEL = 'claude-sonnet-4-5-20250929';
const MAX_TOKENS = 12_000;

export function getClient(): Anthropic {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      'ANTHROPIC_API_KEY environment variable is not set.\n' +
      'Export it before running: export ANTHROPIC_API_KEY=sk-ant-...'
    );
  }
  return new Anthropic({ apiKey });
}

export interface StreamResult {
  content: string;
  inputTokens: number;
  outputTokens: number;
}

export async function streamHallucination(
  config: LucidConfig,
  type: HallucinationType,
): Promise<StreamResult> {
  const client = getClient();

  const systemPrompt = getSystemPrompt(type, config);
  const userPrompt = getUserPrompt(type, config);

  let content = '';
  let inputTokens = 0;
  let outputTokens = 0;

  const stream = client.messages.stream({
    model: MODEL,
    max_tokens: MAX_TOKENS,
    system: systemPrompt,
    messages: [{ role: 'user', content: userPrompt }],
  });

  stream.on('text', (text) => {
    process.stdout.write(text);
    content += text;
  });

  const finalMessage = await stream.finalMessage();
  inputTokens = finalMessage.usage.input_tokens;
  outputTokens = finalMessage.usage.output_tokens;

  // Newline after streamed content
  console.log();

  return { content, inputTokens, outputTokens };
}
