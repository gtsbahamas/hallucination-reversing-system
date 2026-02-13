import type { VercelRequest, VercelResponse } from '@vercel/node';
import { getSupabase } from './supabase.js';
import { getRateLimiter } from './rate-limiter.js';
import type { UsageEntry } from './usage-tracker.js';
import { ApiError, sendError, sendInternalError } from './errors.js';
import type { RequestContext, ApiKeyRecord, TierConfig } from './types.js';

function generateRequestId(): string {
  return `req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

async function hashKey(key: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(key);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export type AuthenticatedHandler = (
  req: VercelRequest,
  res: VercelResponse,
  ctx: RequestContext,
) => Promise<void>;

function setCorsHeaders(res: VercelResponse): void {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

/**
 * Wraps a handler with auth, rate limiting, and usage tracking.
 * Extracts Bearer token, looks up API key, checks rate limit, runs handler, logs usage.
 */
export function withAuth(handler: AuthenticatedHandler) {
  return async (req: VercelRequest, res: VercelResponse): Promise<void> => {
    const requestId = generateRequestId();

    // CORS preflight
    setCorsHeaders(res);
    if (req.method === 'OPTIONS') {
      res.status(200).end();
      return;
    }

    const startTime = Date.now();
    let statusCode = 200;
    let errorCode: string | undefined;

    try {
      // 1. Extract Bearer token
      const authHeader = req.headers.authorization;
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        throw new ApiError('unauthorized', 'Missing or invalid Authorization header. Use: Bearer lk_live_...');
      }
      const token = authHeader.slice(7);

      if (!token.startsWith('lk_live_') && !token.startsWith('lk_test_')) {
        throw new ApiError('unauthorized', 'Invalid API key format. Keys start with lk_live_ or lk_test_');
      }

      // 2. Hash and lookup
      const keyHash = await hashKey(token);
      const db = getSupabase();

      const { data: keyRow, error: keyError } = await db
        .from('api_keys')
        .select('*, tier:tiers(*)')
        .eq('key_hash', keyHash)
        .eq('is_active', true)
        .single();

      if (keyError || !keyRow) {
        throw new ApiError('unauthorized', 'Invalid or inactive API key');
      }

      const apiKey = keyRow as ApiKeyRecord & { tier: TierConfig };
      const tier = apiKey.tier;

      if (!tier) {
        throw new ApiError('internal_error', 'API key has no associated tier');
      }

      // 3. Rate limit check (Upstash sliding window)
      const limiter = getRateLimiter(tier.requests_per_minute);
      const { success: rateLimitOk, reset } = await limiter.limit(apiKey.id);

      if (!rateLimitOk) {
        res.setHeader('Retry-After', Math.ceil((reset - Date.now()) / 1000).toString());
        throw new ApiError('rate_limited', `Rate limit exceeded. ${tier.requests_per_minute} requests/minute for ${tier.name} tier.`);
      }

      // 4. Monthly quota check (for limited tiers)
      const endpoint = req.url?.replace('/api/v1/', '') || 'unknown';
      const isForward = endpoint.startsWith('forward');
      const monthlyLimit = isForward ? tier.forward_monthly_limit : tier.reverse_monthly_limit;

      if (monthlyLimit !== null) {
        const now = new Date();
        const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();

        const { count } = await db
          .from('usage_logs')
          .select('*', { count: 'exact', head: true })
          .eq('api_key_id', apiKey.id)
          .eq('endpoint', endpoint)
          .gte('created_at', monthStart);

        if (count !== null && count >= monthlyLimit) {
          throw new ApiError('quota_exceeded', `Monthly quota exceeded. ${monthlyLimit} ${endpoint} requests/month for ${tier.name} tier. Upgrade at https://trylucid.dev/pricing`);
        }
      }

      // 5. Update last_used_at (awaited to ensure completion before function terminates)
      await db.from('api_keys')
        .update({ last_used_at: new Date().toISOString() })
        .eq('id', apiKey.id);

      // 6. Build context and run handler
      const ctx: RequestContext = { apiKey, tier, requestId };
      await handler(req, res, ctx);

    } catch (err) {
      if (err instanceof ApiError) {
        statusCode = err.statusCode;
        errorCode = err.code;
        sendError(res, err, requestId);
      } else {
        statusCode = 500;
        errorCode = 'internal_error';
        sendInternalError(res, err, requestId);
      }
    }

    // Usage tracking is handled inside each endpoint handler (with correct token counts)
  };
}

/**
 * Simple wrapper for unauthenticated endpoints (health check).
 * Just handles CORS and error catching.
 */
export function withCors(handler: (req: VercelRequest, res: VercelResponse) => Promise<void>) {
  return async (req: VercelRequest, res: VercelResponse): Promise<void> => {
    setCorsHeaders(res);
    if (req.method === 'OPTIONS') {
      res.status(200).end();
      return;
    }
    try {
      await handler(req, res);
    } catch (err) {
      const requestId = generateRequestId();
      sendInternalError(res, err, requestId);
    }
  };
}
