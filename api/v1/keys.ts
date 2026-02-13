import type { VercelRequest, VercelResponse } from '@vercel/node';
import { withCors } from '../lib/middleware.js';
import { getSupabase } from '../lib/supabase.js';
import { ApiError, sendError, sendInternalError } from '../lib/errors.js';
import type { CreateKeyRequest, CreateKeyResponse, TierConfig } from '../lib/types.js';

function generateRequestId(): string {
  return `req_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

async function generateApiKey(): Promise<string> {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
  return `lk_live_${hex}`;
}

async function sha256(input: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

async function handler(req: VercelRequest, res: VercelResponse) {
  const requestId = generateRequestId();

  try {
    // POST only
    if (req.method !== 'POST') {
      throw new ApiError('method_not_allowed', 'Use POST to create an API key');
    }

    const body = req.body as CreateKeyRequest | undefined;

    if (!body || !body.email || !body.name) {
      throw new ApiError('bad_request', 'email and name are required');
    }

    const { email, name, tier: tierName = 'free' } = body;

    // Validate email format
    if (!isValidEmail(email)) {
      throw new ApiError('bad_request', 'Invalid email format');
    }

    // Validate name length
    if (name.length < 1 || name.length > 100) {
      throw new ApiError('bad_request', 'name must be between 1 and 100 characters');
    }

    // Non-free tiers require admin auth (not implemented for MVP)
    if (tierName !== 'free') {
      throw new ApiError('forbidden', 'Only free tier keys can be created via self-service. Contact sales@trylucid.dev for paid tiers.');
    }

    const db = getSupabase();

    // Look up the tier
    const { data: tier, error: tierError } = await db
      .from('tiers')
      .select('*')
      .eq('name', tierName)
      .single();

    if (tierError || !tier) {
      throw new ApiError('bad_request', `Unknown tier: ${tierName}`);
    }

    const tierConfig = tier as TierConfig;

    // Generate API key and hash
    const apiKey = await generateApiKey();
    const keyHash = await sha256(apiKey);
    const keyPrefix = apiKey.slice(0, 12); // "lk_live_XXXX"

    // Insert into api_keys
    const { data: inserted, error: insertError } = await db
      .from('api_keys')
      .insert({
        key_hash: keyHash,
        key_prefix: keyPrefix,
        name,
        tier_id: tierConfig.id,
        email,
        is_active: true,
      })
      .select('created_at')
      .single();

    if (insertError) {
      console.error(`[${requestId}] Failed to insert API key:`, insertError.message);
      throw new ApiError('internal_error', 'Failed to create API key');
    }

    const response: CreateKeyResponse = {
      request_id: requestId,
      key: apiKey,
      key_prefix: keyPrefix,
      name,
      tier: tierConfig.name,
      email,
      created_at: inserted.created_at,
    };

    res.status(201).json(response);
  } catch (err) {
    if (err instanceof ApiError) {
      sendError(res, err, requestId);
    } else {
      sendInternalError(res, err, requestId);
    }
  }
}

export default withCors(handler);
