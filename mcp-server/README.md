# LUCID MCP Server

AI code verification for Claude Code, Cursor, and Windsurf.

LUCID catches hallucinations, bugs, and security issues in AI-generated code — before they ship. It extracts implicit claims from code, verifies each one against the implementation, and reports exactly what would have gone to production without verification.

## Quick Start

### 1. Get a free API key

Sign up at [trylucid.dev](https://trylucid.dev) and generate a key from your dashboard.

### 2. Add to your editor

**Claude Code** (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "lucid": {
      "command": "npx",
      "args": ["-y", "lucid-mcp"],
      "env": {
        "LUCID_API_KEY": "lk_live_your_key_here"
      }
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "lucid": {
      "command": "npx",
      "args": ["-y", "lucid-mcp"],
      "env": {
        "LUCID_API_KEY": "lk_live_your_key_here"
      }
    }
  }
}
```

**Windsurf** (`~/.windsurf/mcp.json`):

```json
{
  "mcpServers": {
    "lucid": {
      "command": "npx",
      "args": ["-y", "lucid-mcp"],
      "env": {
        "LUCID_API_KEY": "lk_live_your_key_here"
      }
    }
  }
}
```

### 3. Use it

Ask your AI assistant to verify code:

- "Verify this file with LUCID"
- "Check my code for hallucinations"
- "Generate a verified function that parses CSV files"

## Tools

| Tool | Description |
|------|-------------|
| `lucid_verify` | Verify a code string for hallucinations, bugs, and security issues |
| `lucid_verify_file` | Verify a file by path (auto-detects language from extension) |
| `lucid_generate` | Generate verified code from a task description |
| `lucid_health` | Check API status and validate your API key |

### lucid_verify

Extracts claims from your code, verifies each one, and reports what it caught.

**Parameters:**
- `code` (required) — The code to verify
- `language` (optional) — Programming language (auto-detected if omitted)
- `context` (optional) — What the code should do

### lucid_verify_file

Reads a file from disk and verifies it. Supports TypeScript, JavaScript, Python, Go, Rust, Java, and more.

**Parameters:**
- `path` (required) — Absolute path to the file
- `context` (optional) — What the code should do

### lucid_generate

Generates code with built-in verification. Synthesizes a spec, applies domain constraints, generates code, then verifies it — so you get code that's been checked before you see it.

**Parameters:**
- `task` (required) — What the code should do
- `language` (optional) — Target language

### lucid_health

Quick check that the API is up and your key is valid. No parameters.

## What LUCID catches

- Correctness bugs (logic errors, off-by-one, wrong return values)
- Security issues (injection, auth bypass, data exposure)
- Performance problems (N+1 queries, memory leaks, blocking calls)
- Missing error handling (uncaught exceptions, silent failures)
- Edge cases (null inputs, empty arrays, concurrent access)
- Type safety issues (implicit any, unsafe casts, missing checks)

## Pricing

- **Free:** 100 verifications/month
- **Pro/Team:** Coming soon — [join the waitlist](https://trylucid.dev/dashboard/settings)

## Links

- [trylucid.dev](https://trylucid.dev) — Dashboard, API keys, usage
- [GitHub](https://github.com/gtsbahamas/hallucination-reversing-system) — Source code
- [Benchmark Report](https://trylucid.dev/report) — 100% HumanEval pass@5, +65.5% SWE-bench

## License

MIT
