## ACC-023 Verification: Aging Reports

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps AgingReportsTab in DashboardLayout | Structure | VERIFIED | AgingReportsPage.tsx:6-25 |
| 2 | As of Date defaults to today | Logic | VERIFIED | AgingReportsTab.tsx:13 |
| 3 | Two sub-tabs: AR and AP | UI | VERIFIED | AgingReportsTab.tsx:124-134 |
| 4 | AR queries invoices with balance_due > 0 | Data | VERIFIED | useAgingReports.tsx:19-28 - `.gt('balance_due', 0)` |
| 5 | Aging buckets: Current, 1-30, 31-60, 61-90, 90+ | Logic | VERIFIED | useAgingReports.tsx:36-42 |
| 6 | AR table with 7 columns | UI | VERIFIED | AgingReportsTab.tsx:176-210 |
| 7 | Summary display uses wrong keys for aging amounts | Bug | VERIFIED | AgingReportsTab.tsx:156-169 - accesses `getAgingSummary(arAging)['1-30 Days']` but getAgingSummary returns `{current, days1to30, days31to60, days61to90, days90plus, total}` - property access returns undefined, displayed as `$0` |
| 8 | CSV export for AR via data URI | Feature | VERIFIED | AgingReportsTab.tsx:29-43 |
| 9 | AP queries expenses with status='approved' | Data | VERIFIED | useAgingReports.tsx:78-86 |
| 10 | AP hardcodes 30-day payment terms | Logic | VERIFIED | useAgingReports.tsx:93-94 - `dueDate.setDate(dueDate.getDate() + 30)` with comment "we'll assume expenses have a 30-day payment term" |
| 11 | AP table with 7 columns | UI | VERIFIED | AgingReportsTab.tsx:260-296 |
| 12 | Rows > 90 days get destructive background | UI | VERIFIED | AgingReportsTab.tsx:189,273 - `${item.daysOverdue > 90 ? 'bg-destructive/10' : ''}` |
| 13 | Summary display missing 61-90 Days bucket | Bug | VERIFIED | AgingReportsTab.tsx:154-169 - shows Current, 1-30, 31-60, and "Over 90 Days" but skips 61-90 |

### FALSIFIED Claims (Bugs)
1. **Summary display always shows $0 for non-current buckets:** The `getAgingSummary()` function returns an object with keys like `days1to30`, `days31to60`, etc. But the display template accesses `getAgingSummary(arAging)['1-30 Days']`, `['31-60 Days']`, `['Over 90 Days']`. These property names don't exist on the returned object, so they return `undefined`, which displays as `$0` or `$undefined`. Only the `current` bucket would work correctly (if accessed as `.current`). Same bug affects AP summary.

2. **Missing 61-90 Days in summary:** The summary grid shows 4 buckets but skips 61-90 Days entirely, going from "31-60 Days" to "Over 90 Days". The underlying data has 5 buckets.

### PARTIAL Claims
None.

### Summary
- Total claims: 13
- VERIFIED: 11
- PARTIAL: 0
- FALSIFIED: 2 (summary key mismatch always shows $0, missing 61-90 bucket in summary)
- UNVERIFIABLE: 0
