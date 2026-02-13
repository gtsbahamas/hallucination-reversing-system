import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

let redis: Redis | null = null;

function getRedis(): Redis {
  if (redis) return redis;

  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;

  if (!url || !token) {
    throw new Error('UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must be set');
  }

  redis = new Redis({ url, token });
  return redis;
}

const limiters = new Map<number, Ratelimit>();

export function getRateLimiter(requestsPerMinute: number): Ratelimit {
  const existing = limiters.get(requestsPerMinute);
  if (existing) return existing;

  const limiter = new Ratelimit({
    redis: getRedis(),
    limiter: Ratelimit.slidingWindow(requestsPerMinute, '1 m'),
    prefix: `lucid:ratelimit:${requestsPerMinute}`,
  });

  limiters.set(requestsPerMinute, limiter);
  return limiter;
}
