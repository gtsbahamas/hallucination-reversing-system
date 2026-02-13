function verdictEmoji(verdict) {
    switch (verdict) {
        case 'PASS': return ':white_check_mark:';
        case 'PARTIAL': return ':large_orange_diamond:';
        case 'FAIL': return ':x:';
        case 'N/A': return ':white_circle:';
        default: return ':question:';
    }
}
function severityBadge(severity) {
    switch (severity) {
        case 'critical': return '`CRITICAL`';
        case 'high': return '`HIGH`';
        case 'medium': return '`MEDIUM`';
        case 'low': return '`LOW`';
        default: return severity;
    }
}
export function buildPrComment(summary) {
    const { complianceScore, totalClaims, passCount, failCount, partialCount, naCount, criticalFails, topIssues, verifications, claims, } = summary;
    const claimMap = new Map(claims.map((c) => [c.id, c]));
    const lines = [];
    // Header
    lines.push('## LUCID Verification Report');
    lines.push('');
    // Score badge
    const scoreColor = complianceScore >= 90 ? 'brightgreen'
        : complianceScore >= 70 ? 'yellow'
            : complianceScore >= 50 ? 'orange'
                : 'red';
    lines.push(`![Compliance Score](https://img.shields.io/badge/compliance-${complianceScore.toFixed(1)}%25-${scoreColor})`);
    lines.push('');
    // Summary table
    lines.push('### Summary');
    lines.push('');
    lines.push('| Metric | Count |');
    lines.push('|--------|-------|');
    lines.push(`| :white_check_mark: Pass | ${passCount} |`);
    lines.push(`| :large_orange_diamond: Partial | ${partialCount} |`);
    lines.push(`| :x: Fail | ${failCount} |`);
    lines.push(`| :white_circle: N/A | ${naCount} |`);
    lines.push(`| **Total Claims** | **${totalClaims}** |`);
    lines.push('');
    // Critical failures (always shown)
    if (criticalFails.length > 0) {
        lines.push('### :rotating_light: Critical Failures');
        lines.push('');
        for (const v of criticalFails) {
            lines.push(`- **${v.claimId}**: ${v.claim}`);
            if (v.reasoning) {
                lines.push(`  > ${v.reasoning}`);
            }
        }
        lines.push('');
    }
    // Top issues (failures + partials, up to 10)
    if (topIssues.length > 0) {
        lines.push('<details>');
        lines.push(`<summary><strong>Top Issues (${topIssues.length})</strong></summary>`);
        lines.push('');
        lines.push('| Claim | Verdict | Severity | Issue |');
        lines.push('|-------|---------|----------|-------|');
        for (const v of topIssues.slice(0, 10)) {
            const claim = claimMap.get(v.claimId);
            const sev = claim ? severityBadge(claim.severity) : '';
            const shortClaim = v.claim.length > 80 ? v.claim.slice(0, 80) + '...' : v.claim;
            const shortReason = v.reasoning.length > 100 ? v.reasoning.slice(0, 100) + '...' : v.reasoning;
            lines.push(`| ${v.claimId} | ${verdictEmoji(v.verdict)} | ${sev} | ${shortClaim} — ${shortReason} |`);
        }
        if (topIssues.length > 10) {
            lines.push(`| | | | *...and ${topIssues.length - 10} more* |`);
        }
        lines.push('');
        lines.push('</details>');
        lines.push('');
    }
    // Passing claims (collapsed)
    const passing = verifications.filter((v) => v.verdict === 'PASS');
    if (passing.length > 0) {
        lines.push('<details>');
        lines.push(`<summary><strong>:white_check_mark: Passing Claims (${passing.length})</strong></summary>`);
        lines.push('');
        for (const v of passing) {
            const claim = claimMap.get(v.claimId);
            const sev = claim ? `[${claim.severity}]` : '';
            lines.push(`- **${v.claimId}** ${sev}: ${v.claim}`);
        }
        lines.push('');
        lines.push('</details>');
        lines.push('');
    }
    // Category breakdown
    const byCat = new Map();
    for (const v of verifications) {
        const claim = claimMap.get(v.claimId);
        const cat = claim?.category || 'unknown';
        if (!byCat.has(cat))
            byCat.set(cat, { pass: 0, partial: 0, fail: 0, na: 0 });
        const counts = byCat.get(cat);
        switch (v.verdict) {
            case 'PASS':
                counts.pass++;
                break;
            case 'PARTIAL':
                counts.partial++;
                break;
            case 'FAIL':
                counts.fail++;
                break;
            case 'N/A':
                counts.na++;
                break;
        }
    }
    if (byCat.size > 1) {
        lines.push('<details>');
        lines.push('<summary><strong>Category Breakdown</strong></summary>');
        lines.push('');
        lines.push('| Category | Pass | Partial | Fail | N/A |');
        lines.push('|----------|------|---------|------|-----|');
        for (const [cat, counts] of [...byCat.entries()].sort()) {
            lines.push(`| ${cat} | ${counts.pass} | ${counts.partial} | ${counts.fail} | ${counts.na} |`);
        }
        lines.push('');
        lines.push('</details>');
        lines.push('');
    }
    // Footer
    lines.push('---');
    lines.push('');
    lines.push('*Powered by [LUCID](https://trylucid.dev) — AI code verification that catches what tests miss*');
    lines.push('');
    return lines.join('\n');
}
//# sourceMappingURL=comment-builder.js.map