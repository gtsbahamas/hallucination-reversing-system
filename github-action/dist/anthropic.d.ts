import Anthropic from '@anthropic-ai/sdk';
import type { ForwardResponse } from './types.js';
export declare const MODEL = "claude-sonnet-4-5-20250929";
export type ActionMode = 'byok' | 'lucid-api';
/**
 * Detect which mode to use based on environment variables.
 * LUCID API key takes precedence if both are set.
 */
export declare function detectMode(): ActionMode;
/**
 * Get Anthropic SDK client for BYOK mode.
 * Throws if ANTHROPIC_API_KEY is not set.
 */
export declare function getClient(): Anthropic;
/**
 * Verify a code snippet via the LUCID API (lucid-api mode).
 * One call = one file = one quota unit.
 */
export declare function verifyViaLucidApi(code: string, language: string, context?: string): Promise<ForwardResponse>;
