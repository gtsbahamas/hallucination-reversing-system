import type { ForwardResponse, ReverseResponse } from './types.js';

// ── Forward (Verify) Formatter ──────────────────────────────

export function formatForwardResult(resp: ForwardResponse): string {
  const { verification, claims, remediation } = resp;
  const lines: string[] = [];

  const verificationItems = verification?.items ?? [];
  const claimItems = claims?.items ?? [];
  const remediationItems = remediation?.items ?? [];

  const claimMap = new Map(claimItems.map((c) => [c.id, c]));

  // Derive counts from actual items to avoid divergence
  const failures = verificationItems.filter((v) => v.verdict === 'FAIL');
  const partials = verificationItems.filter((v) => v.verdict === 'PARTIAL');
  const passing = verificationItems.filter((v) => v.verdict === 'PASS');
  const notApplicable = verificationItems.filter((v) => v.verdict === 'N/A');
  const issueCount = failures.length + partials.length;

  // Hero line — the social proof framing
  if (issueCount === 0) {
    lines.push(`## LUCID verified your code — no issues found`);
    lines.push('');
    lines.push(`All ${passing.length} claims passed verification.`);
  } else {
    lines.push(`## LUCID caught ${issueCount} issue${issueCount === 1 ? '' : 's'} in your code`);
    lines.push('');
    lines.push(`Without verification, ${issueCount === 1 ? 'this issue' : 'these issues'} would have shipped to production.`);
  }
  lines.push('');

  // Summary bar
  lines.push('| Passed | Failed | Partial | Total |');
  lines.push('|--------|--------|---------|-------|');
  lines.push(`| ${passing.length} | ${failures.length} | ${partials.length} | ${verificationItems.length} |`);
  lines.push('');

  // Failed claims — the "what would have shipped" section
  if (failures.length > 0) {
    lines.push('### Issues caught');
    lines.push('');
    for (const v of failures) {
      const claim = claimMap.get(v.claimId);
      const sev = claim ? `[${claim.severity.toUpperCase()}]` : '';
      const cat = claim ? `(${claim.category})` : '';
      lines.push(`- **${sev}** ${claim?.description || v.claimId} ${cat}`);
      lines.push(`  ${v.reasoning}`);
      if (v.evidence) {
        lines.push(`  Evidence: ${v.evidence}`);
      }
      lines.push('');
    }
  }

  // Partial claims
  if (partials.length > 0) {
    lines.push('### Partial issues');
    lines.push('');
    for (const v of partials) {
      const claim = claimMap.get(v.claimId);
      const sev = claim ? `[${claim.severity.toUpperCase()}]` : '';
      lines.push(`- **${sev}** ${claim?.description || v.claimId}`);
      lines.push(`  ${v.reasoning}`);
      lines.push('');
    }
  }

  // Remediation — how to fix
  if (remediationItems.length > 0) {
    lines.push('### How to fix');
    lines.push('');
    for (const r of remediationItems) {
      lines.push(`**[${r.severity.toUpperCase()}] ${r.title}** (${r.action})`);
      lines.push(`${r.description}`);
      if (r.codeGuidance) {
        lines.push('');
        lines.push('```');
        lines.push(r.codeGuidance);
        lines.push('```');
      }
      lines.push('');
    }
  }

  // Passing claims — collapsed
  if (passing.length > 0) {
    lines.push(`### Verified (${passing.length} passed)`);
    lines.push('');
    for (const v of passing) {
      const claim = claimMap.get(v.claimId);
      lines.push(`- ${claim?.description || v.claimId}`);
    }
    lines.push('');
  }

  // N/A claims — not silently dropped
  if (notApplicable.length > 0) {
    lines.push(`### Not applicable (${notApplicable.length})`);
    lines.push('');
    for (const v of notApplicable) {
      const claim = claimMap.get(v.claimId);
      lines.push(`- ${claim?.description || v.claimId}: ${v.reasoning}`);
    }
    lines.push('');
  }

  // Footer
  lines.push('---');
  lines.push(`*${verificationItems.length} claims extracted and verified by [LUCID](https://trylucid.dev)*`);

  return lines.join('\n');
}

// ── Reverse (Generate) Formatter ────────────────────────────

export function formatReverseResult(resp: ReverseResponse): string {
  const { verification, specs, constraints } = resp;
  const lines: string[] = [];

  const verificationItems = verification?.items ?? [];
  const specItems = specs?.items ?? [];
  const constraintItems = constraints?.items ?? [];

  // Hero line
  lines.push(`## LUCID generated verified ${resp.language} code`);
  lines.push('');
  lines.push(`${verification.satisfied}/${verification.total} specs satisfied (${verification.percentage.toFixed(0)}%)`);
  lines.push('');

  // The code
  lines.push('```' + resp.language);
  lines.push(resp.code);
  lines.push('```');
  lines.push('');

  // Verification results
  const unsatisfied = verificationItems.filter((v) => v.status === 'unsatisfied');
  const partial = verificationItems.filter((v) => v.status === 'partial');

  if (unsatisfied.length > 0 || partial.length > 0) {
    lines.push('### Verification gaps');
    lines.push('');
    for (const v of [...unsatisfied, ...partial]) {
      const spec = specItems.find((s) => s.id === v.specId);
      lines.push(`- **[${v.status.toUpperCase()}]** ${spec?.description || v.specId}`);
      lines.push(`  ${v.reasoning}`);
      lines.push('');
    }
  }

  // Constraints applied
  if (constraintItems.length > 0) {
    lines.push('### Constraints applied');
    lines.push('');
    for (const c of constraintItems) {
      const marker = c.type === 'must' ? 'MUST' : c.type === 'must-not' ? 'MUST NOT' : 'PREFER';
      lines.push(`- **[${marker}]** ${c.description}`);
    }
    lines.push('');
  }

  // Specs summary
  lines.push('### Specs verified');
  lines.push('');
  const satisfied = verificationItems.filter((v) => v.status === 'satisfied');
  for (const v of satisfied) {
    const spec = specItems.find((s) => s.id === v.specId);
    lines.push(`- ${spec?.description || v.specId}`);
  }
  lines.push('');

  // Footer
  lines.push('---');
  lines.push(`*Generated with ${specItems.length} specs and ${constraintItems.length} constraints by [LUCID](https://trylucid.dev)*`);

  return lines.join('\n');
}
