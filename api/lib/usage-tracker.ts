import { getSupabase } from './supabase.js';

export interface UsageEntry {
  api_key_id: string;
  endpoint: string;
  status_code: number;
  input_tokens: number;
  output_tokens: number;
  duration_ms: number;
  pipeline_calls: number;
  request_id: string;
  error_code?: string;
}

/** Awaitable usage log insert. Must be awaited before sending response (Vercel kills function after res.end). */
export async function trackUsage(entry: UsageEntry): Promise<void> {
  try {
    const db = getSupabase();
    const { error } = await db.from('usage_logs').insert(entry);
    if (error) {
      console.error(`[usage-tracker] Failed to log usage for ${entry.request_id}:`, error.message);
    }
  } catch (err) {
    console.error(`[usage-tracker] Exception for ${entry.request_id}:`, err);
  }
}
