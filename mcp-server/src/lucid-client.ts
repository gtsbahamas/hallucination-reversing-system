import type { ForwardRequest, ForwardResponse, ReverseRequest, ReverseResponse } from './types.js';

const LUCID_API_BASE = 'https://api.trylucid.dev';
const REQUEST_TIMEOUT_MS = 60_000; // 60 seconds

export class LucidClient {
  private apiKey: string;

  constructor(apiKey: string) {
    if (!apiKey.trim()) {
      throw new Error('API key cannot be empty');
    }
    this.apiKey = apiKey;
  }

  async forward(request: ForwardRequest): Promise<ForwardResponse> {
    return this.post<ForwardResponse>('/api/v1/forward', request);
  }

  async reverse(request: ReverseRequest): Promise<ReverseResponse> {
    return this.post<ReverseResponse>('/api/v1/reverse', request);
  }

  async health(): Promise<{ status: string; version?: string }> {
    const response = await fetch(`${LUCID_API_BASE}/api/v1/health`, {
      headers: { 'Authorization': `Bearer ${this.apiKey}` },
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    const data: unknown = await response.json();
    if (!data || typeof data !== 'object') {
      throw new Error('Health check returned invalid response');
    }
    const result = data as Record<string, unknown>;
    return {
      status: typeof result.status === 'string' ? result.status : 'unknown',
      version: typeof result.version === 'string' ? result.version : undefined,
    };
  }

  private async post<T>(path: string, body: object): Promise<T> {
    const response = await fetch(`${LUCID_API_BASE}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      let message = `LUCID API error (${response.status})`;
      try {
        const parsed = JSON.parse(errorBody);
        if (parsed.error?.message) message = parsed.error.message;
        if (parsed.error?.code === 'quota_exceeded') {
          message = 'Monthly quota exceeded. Upgrade at https://trylucid.dev/dashboard/settings';
        }
        if (parsed.error?.code === 'unauthorized') {
          message = 'Invalid API key. Get one at https://trylucid.dev/dashboard/keys';
        }
        if (parsed.error?.code === 'rate_limited') {
          message = 'Rate limited. Please wait a moment and try again.';
        }
      } catch {
        // use default message
      }
      throw new Error(message);
    }

    const data: unknown = await response.json();
    if (!data || typeof data !== 'object') {
      throw new Error('API returned invalid response');
    }
    return data as T;
  }
}
