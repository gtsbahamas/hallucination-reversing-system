## ACC-017 Verification: Tax Reporting

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps TaxReportingTab in DashboardLayout | Structure | VERIFIED | TaxReportingPage.tsx:6-25 |
| 2 | Date range defaults to Jan 1 current year through today | Logic | VERIFIED | TaxReportingTab.tsx:13-14 - `format(new Date(new Date().getFullYear(), 0, 1), 'yyyy-MM-dd')` and `format(new Date(), 'yyyy-MM-dd')` |
| 3 | Two sub-tabs: VAT Report and Income Tax | UI | VERIFIED | TaxReportingTab.tsx:91-95 |
| 4 | VAT queries invoices table filtered by business_id, date range, status != draft | Data | VERIFIED | useTaxReporting.tsx:20-27 |
| 5 | VAT queries expenses table filtered by business_id, date range, status != draft | Data | VERIFIED | useTaxReporting.tsx:30-37 |
| 6 | VAT calculation: salesVAT from invoice tax_amount, purchaseVAT from expense tax_amount | Logic | VERIFIED | useTaxReporting.tsx:41-43 |
| 7 | CSV export for VAT report via data URI | Feature | VERIFIED | TaxReportingTab.tsx:30-52 |
| 8 | Income tax queries account_transactions with chart_of_accounts and journal_entries joins | Data | VERIFIED | useTaxReporting.tsx:72-81 |
| 9 | Income tax groups revenue (credit-debit) and expense (debit-credit) | Logic | VERIFIED | useTaxReporting.tsx:86-95 |
| 10 | References "Bahamas tax regulations" | UI | VERIFIED | TaxReportingTab.tsx:88 |
| 11 | No export for income tax tab | Gap | VERIFIED | No export button or function exists for income tax |
| 12 | Income tax query filters on chart_of_accounts.business_id in join | Bug | VERIFIED | useTaxReporting.tsx:79 - `.eq('chart_of_accounts.business_id', ...)` - this filters the join, not the main table. PostgREST may return account_transactions rows without matching chart_of_accounts, leading to incomplete or incorrect filtering |

### FALSIFIED Claims (Bugs)
1. **Income tax query filter issue:** The query `.eq('chart_of_accounts.business_id', currentBusiness.id)` applies the filter to the joined table, not account_transactions directly. In Supabase PostgREST, this means account_transactions rows are still returned even if chart_of_accounts doesn't match. The subsequent `.filter()` on `t.chart_of_accounts.account_type` would then fail on rows where chart_of_accounts is null. This could cause runtime errors or incorrect totals.

### PARTIAL Claims
None.

### Summary
- Total claims: 12
- VERIFIED: 11
- PARTIAL: 0
- FALSIFIED: 1 (income tax query filter on join)
- UNVERIFIABLE: 0
