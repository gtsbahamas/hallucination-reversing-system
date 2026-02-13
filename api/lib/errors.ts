import type { VercelResponse } from '@vercel/node';
import type { ErrorCode, ErrorResponse } from './types.js';

const STATUS_MAP: Record<ErrorCode, number> = {
  bad_request: 400,
  unauthorized: 401,
  forbidden: 403,
  not_found: 404,
  method_not_allowed: 405,
  rate_limited: 429,
  quota_exceeded: 429,
  internal_error: 500,
  upstream_error: 502,
};

export class ApiError extends Error {
  constructor(
    public readonly code: ErrorCode,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get statusCode(): number {
    return STATUS_MAP[this.code];
  }

  toResponse(requestId: string): ErrorResponse {
    return {
      error: { code: this.code, message: this.message },
      request_id: requestId,
    };
  }
}

export function sendError(res: VercelResponse, error: ApiError, requestId: string): void {
  res.status(error.statusCode).json(error.toResponse(requestId));
}

export function sendInternalError(res: VercelResponse, err: unknown, requestId: string): void {
  const message = err instanceof Error ? err.message : 'Internal server error';
  console.error(`[${requestId}] Internal error:`, message);
  const apiError = new ApiError('internal_error', message);
  sendError(res, apiError, requestId);
}
