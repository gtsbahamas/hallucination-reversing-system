import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  res.setHeader('Access-Control-Allow-Origin', '*');

  const apiKey = process.env.ANTHROPIC_API_KEY;
  const keyInfo = apiKey
    ? `set (${apiKey.length} chars, starts: ${apiKey.slice(0, 8)}...)`
    : 'NOT SET';

  // Test raw fetch to Anthropic API
  let fetchResult: string;
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey || '',
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-5-20250929',
        max_tokens: 16,
        messages: [{ role: 'user', content: 'Say "ok"' }],
      }),
    });
    const body = await response.text();
    fetchResult = `${response.status} ${response.statusText}: ${body.slice(0, 200)}`;
  } catch (e) {
    fetchResult = `FETCH ERROR: ${e instanceof Error ? `${e.name}: ${e.message}` : String(e)}`;
  }

  return res.status(200).json({
    status: 'ok',
    env: {
      ANTHROPIC_API_KEY: keyInfo,
      NODE_ENV: process.env.NODE_ENV,
      VERCEL_REGION: process.env.VERCEL_REGION,
    },
    fetchTest: fetchResult,
    timestamp: new Date().toISOString(),
  });
}
