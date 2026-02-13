import type { AnthropicResponse, TextBlock } from './types.js';

export const MODEL = 'claude-sonnet-4-5-20250929';
const API_URL = 'https://api.anthropic.com/v1/messages';

export async function callAnthropic(
  system: string,
  userMessage: string,
  maxTokens: number,
): Promise<AnthropicResponse> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY not configured');
  }

  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: maxTokens,
      system,
      messages: [{ role: 'user', content: userMessage }],
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Anthropic API ${response.status}: ${body.slice(0, 300)}`);
  }

  return response.json() as Promise<AnthropicResponse>;
}

export function getText(resp: AnthropicResponse): string {
  return resp.content
    .filter((b): b is TextBlock => b.type === 'text')
    .map(b => b.text)
    .join('');
}

export function stripFences(text: string): string {
  let t = text.trim();
  if (t.startsWith('```')) {
    const nl = t.indexOf('\n');
    if (nl !== -1) t = t.slice(nl + 1);
  }
  const lf = t.lastIndexOf('```');
  if (lf !== -1) t = t.slice(0, lf);
  t = t.trim();
  if (!t.endsWith(']') && !t.endsWith('}')) {
    const lb = t.lastIndexOf('}');
    if (lb !== -1) t = t.slice(0, lb + 1) + ']';
  }
  return t;
}

export function safeParseArray(text: string): unknown[] {
  try {
    const parsed = JSON.parse(stripFences(text));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}
