## ACC-016 Verification: Bank Reconciliation

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page wraps BankReconciliationTab in DashboardLayout | Structure | VERIFIED | BankReconciliationPage.tsx:6-23 |
| 2 | Fetches bank_transactions filtered by business_id | Data | VERIFIED | useBankReconciliation.tsx:30-35 - `supabase.from('bank_transactions').select('*').eq('business_id', currentBusiness.id)` |
| 3 | Fetches bank_statements filtered by business_id | Data | VERIFIED | useBankReconciliation.tsx:36-40 - `supabase.from('bank_statements').select('*').eq('business_id', currentBusiness.id)` |
| 4 | 3 summary cards showing unmatched count, matched count, reconciliation rate | UI | VERIFIED | BankReconciliationTab.tsx:296-337 |
| 5 | 4 sub-tabs: Workflow, Import, Match, Reports | UI | VERIFIED | BankReconciliationTab.tsx:339-345 |
| 6 | File upload button exists but does not actually process files | Scaffolding | VERIFIED | BankReconciliationTab.tsx:84-86 - `handleFileUpload` only calls `setShowFileUpload(true)`, no file input element exists, `showFileUpload` state is never read |
| 7 | Transaction table limited to first 10 rows | UI | VERIFIED | BankReconciliationTab.tsx:449 - `.slice(0, 10)` |
| 8 | Match button calls BankReconciliationService.markTransactionAsReconciled | Logic | VERIFIED | BankReconciliationTab.tsx:106, bankReconciliationService.ts:481-497 |
| 9 | Field name mismatch between service (is_reconciled) and UI (is_matched) | Bug | VERIFIED | Service updates `is_reconciled` (bankReconciliationService.ts:488), UI reads `is_matched` (BankReconciliationTab.tsx:246,304). Hook query is `select('*')` so both fields would be returned if they exist, but this is a naming inconsistency that could cause match operations to not reflect in UI |
| 10 | Hardcoded adjusted bank balance $24,890.25 | Scaffolding | VERIFIED | BankReconciliationTab.tsx:514 - `<span className="text-lg font-bold">$24,890.25</span>` |
| 11 | TODO comment about PDF generation | Scaffolding | VERIFIED | BankReconciliationTab.tsx:157 - `// TODO: Enhance with PDF generation or better formatting` |
| 12 | showHistory state is never consumed | Scaffolding | VERIFIED | BankReconciliationTab.tsx:43,205-207 - state set but never read in JSX |
| 13 | Report opens in new browser window as raw HTML | Logic | VERIFIED | BankReconciliationTab.tsx:158-184 - `window.open('', '_blank')` with `document.write()` |
| 14 | Column preferences persisted via useColumnPreferences | Feature | VERIFIED | BankReconciliationTab.tsx:49-52 |

### FALSIFIED Claims (Bugs)
1. **Field name mismatch (is_reconciled vs is_matched):** The `markTransactionAsReconciled` service method updates `is_reconciled = true` on the bank_transactions table. However, the UI filters and displays status based on `is_matched`. If these are different database columns, matching a transaction via the service would not update the UI display. If `is_matched` is an alias or the same column, this works. Without seeing the database schema, this is flagged as a likely bug.

### PARTIAL Claims
None.

### Summary
- Total claims: 14
- VERIFIED: 13
- PARTIAL: 0
- FALSIFIED: 1 (field name mismatch is_reconciled vs is_matched)
- UNVERIFIABLE: 0
