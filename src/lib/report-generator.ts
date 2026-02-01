import type {
  ExtractionResult,
  VerificationReport,
  ClaimVerification,
  Claim,
} from '../types.js';

interface ReportInput {
  extraction: ExtractionResult;
  verification: VerificationReport;
  projectName?: string;
}

export function generateGapReport(input: ReportInput): string {
  const { extraction, verification, projectName } = input;
  const { verdicts, verifications } = verification;
  const total = verifications.length;
  const assessed = total - verdicts.na;
  const complianceScore =
    assessed > 0
      ? ((verdicts.pass + verdicts.partial * 0.5) / assessed) * 100
      : 0;

  const claimMap = new Map(extraction.claims.map((c) => [c.id, c]));
  const now = new Date().toISOString().split('T')[0];

  const lines: string[] = [];

  // --- Executive Summary ---
  lines.push(`# LUCID Gap Report — ${projectName || 'Audit Results'}`);
  lines.push('');
  lines.push(`*Generated: ${now}*`);
  lines.push(`*Iteration: ${extraction.iteration}*`);
  lines.push(`*Codebase: ${verification.codebasePath}*`);
  lines.push('');
  lines.push('---');
  lines.push('');
  lines.push('## Executive Summary');
  lines.push('');
  lines.push(`LUCID extracted **${extraction.totalClaims} claims** from the ${extraction.documentType} document and verified each against the codebase.`);
  lines.push('');
  lines.push(`| Metric | Value |`);
  lines.push(`|--------|-------|`);
  lines.push(`| Total claims | ${total} |`);
  lines.push(`| PASS | ${verdicts.pass} |`);
  lines.push(`| PARTIAL | ${verdicts.partial} |`);
  lines.push(`| FAIL | ${verdicts.fail} |`);
  lines.push(`| N/A | ${verdicts.na} |`);
  lines.push(`| **Compliance score** | **${complianceScore.toFixed(1)}%** |`);
  lines.push('');

  // Risk summary
  const criticalFails = getVerificationsByVerdictAndSeverity(
    verifications, claimMap, 'FAIL', 'critical',
  );
  const highFails = getVerificationsByVerdictAndSeverity(
    verifications, claimMap, 'FAIL', 'high',
  );

  if (criticalFails.length > 0 || highFails.length > 0) {
    lines.push(`**Risk Assessment:** ${criticalFails.length} critical and ${highFails.length} high-severity failures require immediate attention.`);
  } else if (verdicts.fail > 0) {
    lines.push(`**Risk Assessment:** ${verdicts.fail} failures found, none at critical severity.`);
  } else {
    lines.push(`**Risk Assessment:** No failures found. Claims are well-supported by codebase.`);
  }
  lines.push('');

  // --- Methodology ---
  lines.push('---');
  lines.push('');
  lines.push('## Methodology');
  lines.push('');
  lines.push('This report was generated using the LUCID framework:');
  lines.push('');
  lines.push('1. **Extract** — Every declarative claim was identified from the document');
  lines.push('2. **Classify** — Claims were categorized by type and severity');
  lines.push('3. **Verify** — Each testable claim was evaluated against the actual codebase');
  lines.push('4. **Report** — Results compiled with evidence and fix recommendations');
  lines.push('');
  lines.push('**Verdicts:**');
  lines.push('- **PASS** — Code fully implements the claim');
  lines.push('- **PARTIAL** — Code partially implements the claim');
  lines.push('- **FAIL** — Code does not implement the claim or contradicts it');
  lines.push('- **N/A** — Claim cannot be verified from code alone');
  lines.push('');

  // --- Priority Matrix ---
  lines.push('---');
  lines.push('');
  lines.push('## Priority Matrix');
  lines.push('');
  lines.push('| Severity | FAIL | PARTIAL | PASS | N/A |');
  lines.push('|----------|------|---------|------|-----|');

  for (const severity of ['critical', 'high', 'medium', 'low'] as const) {
    const counts = {
      FAIL: getVerificationsByVerdictAndSeverity(verifications, claimMap, 'FAIL', severity).length,
      PARTIAL: getVerificationsByVerdictAndSeverity(verifications, claimMap, 'PARTIAL', severity).length,
      PASS: getVerificationsByVerdictAndSeverity(verifications, claimMap, 'PASS', severity).length,
      'N/A': getVerificationsByVerdictAndSeverity(verifications, claimMap, 'N/A', severity).length,
    };
    lines.push(
      `| ${severity} | ${counts.FAIL} | ${counts.PARTIAL} | ${counts.PASS} | ${counts['N/A']} |`,
    );
  }
  lines.push('');

  // --- Detailed Findings ---
  lines.push('---');
  lines.push('');
  lines.push('## Detailed Findings');
  lines.push('');

  // Group by section
  const sections = new Map<string, ClaimVerification[]>();
  for (const v of verifications) {
    const claim = claimMap.get(v.claimId);
    const section = claim?.section || 'Unknown';
    if (!sections.has(section)) sections.set(section, []);
    sections.get(section)!.push(v);
  }

  for (const [section, sectionVerifications] of sections) {
    lines.push(`### ${section}`);
    lines.push('');

    // Sort: FAIL first, then PARTIAL, then PASS, then N/A
    const verdictOrder = { FAIL: 0, PARTIAL: 1, PASS: 2, 'N/A': 3 };
    sectionVerifications.sort(
      (a, b) =>
        (verdictOrder[a.verdict] ?? 4) - (verdictOrder[b.verdict] ?? 4),
    );

    for (const v of sectionVerifications) {
      const claim = claimMap.get(v.claimId);
      const icon = verdictIcon(v.verdict);

      lines.push(`${icon} **${v.claimId}** [${claim?.severity || 'medium'}] — ${v.claim || claim?.text || ''}`);

      if (v.reasoning) {
        lines.push(`> ${v.reasoning}`);
      }

      if (v.evidence.length > 0) {
        for (const e of v.evidence) {
          const loc = e.lineNumber ? `${e.file}:${e.lineNumber}` : e.file;
          lines.push(`> \`${loc}\`: \`${e.snippet.trim().slice(0, 120)}\``);
        }
      }

      lines.push('');
    }
  }

  // --- Fix Recommendations ---
  const fails = verifications.filter((v) => v.verdict === 'FAIL');
  const partials = verifications.filter((v) => v.verdict === 'PARTIAL');

  if (fails.length > 0 || partials.length > 0) {
    lines.push('---');
    lines.push('');
    lines.push('## Fix Recommendations');
    lines.push('');

    if (criticalFails.length > 0) {
      lines.push('### Immediate (Critical)');
      lines.push('');
      for (const v of criticalFails) {
        lines.push(`- [ ] **${v.claimId}**: ${v.claim}`);
      }
      lines.push('');
    }

    if (highFails.length > 0) {
      lines.push('### High Priority');
      lines.push('');
      for (const v of highFails) {
        lines.push(`- [ ] **${v.claimId}**: ${v.claim}`);
      }
      lines.push('');
    }

    const mediumFails = getVerificationsByVerdictAndSeverity(
      verifications, claimMap, 'FAIL', 'medium',
    );
    if (mediumFails.length > 0) {
      lines.push('### Medium Priority');
      lines.push('');
      for (const v of mediumFails) {
        lines.push(`- [ ] **${v.claimId}**: ${v.claim}`);
      }
      lines.push('');
    }

    if (partials.length > 0) {
      lines.push('### Partial Implementations (Quick Wins)');
      lines.push('');
      for (const v of partials) {
        lines.push(`- [ ] **${v.claimId}**: ${v.claim}`);
      }
      lines.push('');
    }
  }

  // --- Footer ---
  lines.push('---');
  lines.push('');
  lines.push(`*Report generated by LUCID v0.1.0 — Leveraging Unverified Claims Into Deliverables*`);
  lines.push(`*https://franklabs.io/lucid*`);
  lines.push('');

  return lines.join('\n');
}

function verdictIcon(verdict: string): string {
  switch (verdict) {
    case 'PASS':
      return '[PASS]';
    case 'PARTIAL':
      return '[PARTIAL]';
    case 'FAIL':
      return '[FAIL]';
    case 'N/A':
      return '[N/A]';
    default:
      return `[${verdict}]`;
  }
}

function getVerificationsByVerdictAndSeverity(
  verifications: ClaimVerification[],
  claimMap: Map<string, Claim>,
  verdict: string,
  severity: string,
): ClaimVerification[] {
  return verifications.filter((v) => {
    if (v.verdict !== verdict) return false;
    const claim = claimMap.get(v.claimId);
    return claim?.severity === severity;
  });
}
