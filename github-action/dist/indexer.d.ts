export interface CodebaseIndex {
    rootPath: string;
    totalFiles: number;
    fileTree: string[];
    keyFiles: {
        path: string;
        reason: string;
    }[];
    summary: string;
}
export declare function indexCodebase(rootPath: string, changedFiles?: string[], maxFiles?: number): Promise<CodebaseIndex>;
export declare function readFileContent(rootPath: string, relativePath: string): Promise<string | null>;
