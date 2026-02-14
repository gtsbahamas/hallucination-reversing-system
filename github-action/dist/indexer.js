import { readdir, readFile, stat } from 'node:fs/promises';
import { join, relative, extname } from 'node:path';
const IGNORE_DIRS = new Set([
    'node_modules', '.git', '.next', '.vercel', '.lucid', 'dist', 'build',
    'out', '.cache', 'coverage', '__pycache__', '.venv', 'venv',
    '.turbo', '.nuxt', '.svelte-kit', 'vendor',
]);
const CODE_EXTENSIONS = new Set([
    '.ts', '.tsx', '.js', '.jsx', '.py', '.rb', '.go', '.rs', '.java',
    '.cs', '.php', '.swift', '.kt', '.scala', '.vue', '.svelte',
    '.sql', '.graphql', '.gql', '.prisma',
]);
async function walkDir(dir, root, files, maxFiles) {
    if (files.length >= maxFiles)
        return;
    let entries;
    try {
        entries = await readdir(dir, { withFileTypes: true });
    }
    catch {
        return;
    }
    for (const entry of entries) {
        if (files.length >= maxFiles)
            return;
        if (entry.isDirectory()) {
            if (IGNORE_DIRS.has(entry.name) || entry.name.startsWith('.'))
                continue;
            await walkDir(join(dir, entry.name), root, files, maxFiles);
        }
        else {
            const relPath = relative(root, join(dir, entry.name));
            files.push(relPath);
        }
    }
}
export async function indexCodebase(rootPath, changedFiles, maxFiles = 3000) {
    const info = await stat(rootPath);
    if (!info.isDirectory()) {
        throw new Error(`Path is not a directory: ${rootPath}`);
    }
    const files = [];
    await walkDir(rootPath, rootPath, files, maxFiles);
    const codeFiles = files.filter((f) => CODE_EXTENSIONS.has(extname(f)));
    // If we have changed files, prioritize those in key files
    const keyFiles = [];
    if (changedFiles && changedFiles.length > 0) {
        for (const f of changedFiles) {
            if (CODE_EXTENSIONS.has(extname(f))) {
                keyFiles.push({ path: f, reason: 'changed in PR' });
            }
        }
    }
    // Also add config/schema/API/auth files
    for (const file of files) {
        const basename = file.split('/').pop() || '';
        if (/auth|login|session|middleware/i.test(file) && CODE_EXTENSIONS.has(extname(file))) {
            keyFiles.push({ path: file, reason: 'authentication' });
        }
        else if (file.includes('/api/') && CODE_EXTENSIONS.has(extname(file))) {
            keyFiles.push({ path: file, reason: 'API route' });
        }
        else if (basename === 'package.json' || basename.includes('config')) {
            keyFiles.push({ path: file, reason: 'configuration' });
        }
    }
    const summary = [
        `Total files: ${files.length} (${codeFiles.length} code files)`,
        `Key files: ${keyFiles.length}`,
        changedFiles ? `Changed files: ${changedFiles.length}` : '',
    ].filter(Boolean).join('\n');
    return {
        rootPath,
        totalFiles: files.length,
        fileTree: files,
        keyFiles,
        summary,
    };
}
export async function readFileContent(rootPath, relativePath) {
    const fullPath = join(rootPath, relativePath);
    try {
        const content = await readFile(fullPath, 'utf-8');
        if (content.length > 30_000) {
            return content.slice(0, 30_000) + '\n\n[... truncated at 30K chars]';
        }
        return content;
    }
    catch {
        return null;
    }
}
//# sourceMappingURL=indexer.js.map