# LVR Pilot — Route Inventory (Accounting Domain)

*Generated: 2026-02-13*
*Source: `/Users/tywells/Downloads/projects/islandbiz-pro-start/src/App.tsx`*

## Route Guard Mechanism

All `/accounting/*` routes use `GuardedRoute` which:
1. Extracts the first path segment (`accounting`)
2. Looks up `ROUTE_PERMISSION_MAP['accounting']` → `'accounting.invoices.read'`
3. Wraps in `<PermissionGuard permissions="accounting.invoices.read">`

**Every accounting route uses the same permission code: `accounting.invoices.read`**

## Routes (30 total, 25 unique page components)

| # | Route | Component | File |
|---|-------|-----------|------|
| 1 | `/accounting` | FinancialManagement | `src/pages/FinancialManagement.tsx` |
| 2 | `/accounting/accounts-receivable` | AccountsReceivablePage | `src/pages/accounting/AccountsReceivablePage.tsx` |
| 3 | `/accounting/accounts-payable` | AccountsPayablePage | `src/pages/accounting/AccountsPayablePage.tsx` |
| 4 | `/accounting/invoices` | InvoicesPage | `src/pages/accounting/InvoicesPage.tsx` |
| 5 | `/accounting/invoices/:id` | InvoiceDetailPage | `src/pages/accounting/InvoiceDetailPage.tsx` |
| 6 | `/accounting/invoices/:id/edit` | InvoiceDetailPage | `src/pages/accounting/InvoiceDetailPage.tsx` |
| 7 | `/accounting/bills` | BillsPage | `src/pages/accounting/BillsPage.tsx` |
| 8 | `/accounting/bills/:id` | BillDetailPage | `src/pages/accounting/BillDetailPage.tsx` |
| 9 | `/accounting/bills/:id/edit` | BillDetailPage | `src/pages/accounting/BillDetailPage.tsx` |
| 10 | `/accounting/expenses` | ExpensesPage | `src/pages/accounting/ExpensesPage.tsx` |
| 11 | `/accounting/expenses/:id` | ExpenseDetailPage | `src/pages/accounting/ExpenseDetailPage.tsx` |
| 12 | `/accounting/expenses/:id/edit` | ExpenseDetailPage | `src/pages/accounting/ExpenseDetailPage.tsx` |
| 13 | `/accounting/payments/:id` | PaymentDetailPage | `src/pages/accounting/PaymentDetailPage.tsx` |
| 14 | `/accounting/payments/:id/edit` | PaymentDetailPage | `src/pages/accounting/PaymentDetailPage.tsx` |
| 15 | `/accounting/journal-entries` | JournalEntriesPage | `src/pages/accounting/JournalEntriesPage.tsx` |
| 16 | `/accounting/journal-entries/:id` | JournalEntryDetailPage | `src/pages/accounting/JournalEntryDetailPage.tsx` |
| 17 | `/accounting/journal-entries/:id/edit` | JournalEntryDetailPage | `src/pages/accounting/JournalEntryDetailPage.tsx` |
| 18 | `/accounting/chart-of-accounts` | ChartOfAccountsPage | `src/pages/accounting/ChartOfAccountsPage.tsx` |
| 19 | `/accounting/financial-reports` | FinancialReportsPage | `src/pages/accounting/FinancialReportsPage.tsx` |
| 20 | `/accounting/bank-reconciliation` | BankReconciliationPage | `src/pages/accounting/BankReconciliationPage.tsx` |
| 21 | `/accounting/banking-cash` | BankingAndCashPage | `src/pages/accounting/BankingAndCashPage.tsx` |
| 22 | `/accounting/compliance-planning` | CompliancePlanningPage | `src/pages/accounting/CompliancePlanningPage.tsx` |
| 23 | `/accounting/tax-reporting` | TaxReportingPage | `src/pages/accounting/TaxReportingPage.tsx` |
| 24 | `/accounting/credit-management` | CreditManagement | `src/pages/accounting/CreditManagement.tsx` |
| 25 | `/accounting/budget-analysis` | BudgetAnalysisPage | `src/pages/accounting/BudgetAnalysisPage.tsx` |
| 26 | `/accounting/variance-analysis` | VarianceAnalysisPage | `src/pages/accounting/VarianceAnalysisPage.tsx` |
| 27 | `/accounting/cash-flow` | CashFlowPage | `src/pages/accounting/CashFlowPage.tsx` |
| 28 | `/accounting/fixed-assets` | FixedAssetsPage | `src/pages/accounting/FixedAssetsPage.tsx` |
| 29 | `/accounting/multi-currency` | MultiCurrencyPage | `src/pages/accounting/MultiCurrencyPage.tsx` |
| 30 | `/accounting/aging-reports` | AgingReportsPage | `src/pages/accounting/AgingReportsPage.tsx` |

## Related Routes (outside `/accounting/` prefix)

| Route | Component | Guard Permission |
|-------|-----------|-----------------|
| `/pos-end-of-day` | POSEndOfDayPage | `accounting.invoices.read` (via `pos-end-of-day` key) |

## Notes

- Routes 5/6, 8/9, 11/12, 13/14, 16/17 are view/edit pairs sharing the same component
- For requirements generation, we produce one requirement per unique page component (25 total)
- The `:id` and `:id/edit` variants are covered in the detail page requirement
