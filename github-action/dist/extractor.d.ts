import type { Claim } from './types.js';
export declare function extractClaimsFromCodebase(fileTree: string[], keyFileSummary: string, log: (msg: string) => void): Promise<{
    claims: Claim[];
    inputTokens: number;
    outputTokens: number;
}>;
export declare function extractClaimsFromDocument(documentContent: string, log: (msg: string) => void): Promise<{
    claims: Claim[];
    inputTokens: number;
    outputTokens: number;
}>;
