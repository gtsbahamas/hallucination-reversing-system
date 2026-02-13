## ACC-020 Verification: Variance Analysis

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps VarianceAnalysisDashboard in DashboardLayout | Structure | VERIFIED | VarianceAnalysisPage.tsx:4-12 |
| 2 | Loads departments on mount filtered by business_id, is_active | Data | VERIFIED | VarianceAnalysisDashboard.tsx:89-111 |
| 3 | 5 filters: Year, Start Date, End Date, Department, Variance Threshold | UI | VERIFIED | VarianceAnalysisDashboard.tsx:431-503 |
| 4 | Queries approved budgets for selected year | Data | VERIFIED | VarianceAnalysisDashboard.tsx:119-138 - `.eq('budget_year', parseInt(selectedYear)).eq('status', 'approved')` |
| 5 | Iterates budget line items, queries transactions per account per month (N+1) | Performance | VERIFIED | VarianceAnalysisDashboard.tsx:161-162,199-212 - nested loops with individual supabase queries |
| 6 | Monthly budget from individual columns (jan_amount...dec_amount) | Logic | VERIFIED | VarianceAnalysisDashboard.tsx:183-196 - switch statement for months 1-12 |
| 7 | Revenue: credit-debit, other: debit-credit, then Math.abs() | Logic | VERIFIED | VarianceAnalysisDashboard.tsx:220-228 |
| 8 | Two views: Summary and Monthly Trends | UI | VERIFIED | VarianceAnalysisDashboard.tsx:588-704 |
| 9 | Drill-down dialog with transaction details | Feature | VERIFIED | VarianceAnalysisDashboard.tsx:291-355,719-795 |
| 10 | Summary cards: Revenue, Expense, Net Income variances | UI | VERIFIED | VarianceAnalysisDashboard.tsx:506-583 |
| 11 | Favorable/unfavorable logic correct for revenue vs expense | Logic | VERIFIED | VarianceAnalysisDashboard.tsx:364-390 |
| 12 | On Track badge for < 5% variance | Logic | VERIFIED | VarianceAnalysisDashboard.tsx:376-378 |
| 13 | Direct Supabase queries in component, no hook | Architecture | VERIFIED | VarianceAnalysisDashboard.tsx:33,95-289 - imports supabase directly, all queries inline |
| 14 | Math.abs() on actual amounts may mask negatives | Bug | VERIFIED | VarianceAnalysisDashboard.tsx:228 - `monthActual = Math.abs(monthActual)` always makes actual positive, hiding credit balances or net-negative accounts |

### FALSIFIED Claims (Bugs)
1. **Math.abs() on actuals (line 228):** After calculating `monthActual` as the net of debits/credits based on account type, the code applies `Math.abs()`. This means if an expense account has net credits exceeding debits (a refund scenario), it would appear as positive spending rather than negative. This distorts variance calculations for accounts with unusual transaction patterns.

### PARTIAL Claims
None.

### Summary
- Total claims: 14
- VERIFIED: 13
- PARTIAL: 0
- FALSIFIED: 1 (Math.abs masking negative actuals)
- UNVERIFIABLE: 0
