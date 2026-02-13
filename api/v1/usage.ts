import type { VercelRequest, VercelResponse } from '@vercel/node';
import { withAuth, type AuthenticatedHandler } from '../lib/middleware.js';
import { getSupabase } from '../lib/supabase.js';
import { ApiError, sendError, sendInternalError } from '../lib/errors.js';
import type { UsageResponse, RequestContext } from '../lib/types.js';

const handler: AuthenticatedHandler = async (
  req: VercelRequest,
  res: VercelResponse,
  ctx: RequestContext,
) => {
  // GET only
  if (req.method !== 'GET') {
    throw new ApiError('method_not_allowed', 'Use GET to retrieve usage stats');
  }

  const db = getSupabase();

  // Current month boundaries
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
  const period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;

  // Fetch all usage logs for this key this month
  const { data: logs, error: logsError } = await db
    .from('usage_logs')
    .select('endpoint, input_tokens, output_tokens')
    .eq('api_key_id', ctx.apiKey.id)
    .gte('created_at', monthStart);

  if (logsError) {
    console.error(`[${ctx.requestId}] Failed to query usage:`, logsError.message);
    throw new ApiError('internal_error', 'Failed to retrieve usage data');
  }

  // Aggregate in JS (low volume for MVP)
  let forwardCount = 0;
  let reverseCount = 0;
  let totalInputTokens = 0;
  let totalOutputTokens = 0;

  for (const log of logs ?? []) {
    if (log.endpoint === 'forward') {
      forwardCount++;
    } else if (log.endpoint === 'reverse') {
      reverseCount++;
    }
    totalInputTokens += log.input_tokens ?? 0;
    totalOutputTokens += log.output_tokens ?? 0;
  }

  const response: UsageResponse = {
    request_id: ctx.requestId,
    period,
    forward: {
      count: forwardCount,
      limit: ctx.tier.forward_monthly_limit,
    },
    reverse: {
      count: reverseCount,
      limit: ctx.tier.reverse_monthly_limit,
    },
    total_input_tokens: totalInputTokens,
    total_output_tokens: totalOutputTokens,
  };

  res.status(200).json(response);
};

export default withAuth(handler);
