import type { CodebaseIndex } from './indexer.js';
import type { Claim, ClaimVerification } from './types.js';
export declare function verifyClaims(claims: Claim[], index: CodebaseIndex, log: (msg: string) => void): Promise<{
    verifications: ClaimVerification[];
    inputTokens: number;
    outputTokens: number;
}>;
