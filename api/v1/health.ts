import type { VercelRequest, VercelResponse } from '@vercel/node';
import { withCors } from '../lib/middleware.js';

async function handler(req: VercelRequest, res: VercelResponse) {
  res.status(200).json({
    status: 'ok',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
}

export default withCors(handler);
