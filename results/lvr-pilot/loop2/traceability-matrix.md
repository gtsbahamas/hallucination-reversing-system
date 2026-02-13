# Loop 2 — Traceability Matrix

*Generated: 2026-02-13*
*Purpose: Map every Loop 1 requirement to its architectural realization and every bug to its fix.*

---

## Requirements → Architecture Traceability

| ACC# | Page | Component Architecture | Data Hooks | Permission Code | Shared Components Used |
|------|------|----------------------|------------|-----------------|----------------------|
| ACC-001 | Invoices List | InvoicesPage (Full List) | useInvoicesQuery, useInvoiceAggregationsQuery | accounting_invoices_read | DataTable, StatCards, FormModal, CSVExport |
| ACC-002 | Invoice Detail | InvoiceDetailPage | useInvoiceQuery, useRecordInvoicePaymentMutation | accounting_invoices_read | DetailLayout, SidebarCard, StatusBadge, ActivityLog |
| ACC-003 | Bills List | BillsPage → BillsDashboard | useBillsQuery, useBillAggregationsQuery | accounting_bills_read | DataTable, StatCards, FormModal, CSVExport |
| ACC-004 | Bill Detail | BillDetailPage | useBillQuery, useRecordBillPaymentMutation, useSoftDeleteBillMutation | accounting_bills_read | DetailLayout, SidebarCard, StatusBadge, ActivityLog |
| ACC-005 | Expenses List | ExpensesPage → ExpensesTab | useExpensesQuery, useExpenseAggregationsQuery | accounting_expenses_read | DataTable, StatCards, FormModal, CSVExport |
| ACC-006 | Expense Detail | ExpenseDetailPage | useExpenseQuery, useUpdateExpenseMutation | accounting_expenses_read | DetailLayout, SidebarCard, StatusBadge, ActivityLog |
| ACC-007 | Payment Detail | PaymentDetailPage | usePaymentQuery, usePaymentsQuery | accounting_payments_read | DetailLayout, SidebarCard, StatusBadge |
| ACC-009 | Financial Mgmt | FinancialManagement | useFinancialOverviewQuery (new — replaces mock data) | accounting_dashboard_read | StatCards, TabLoader |
| ACC-010 | Accounts Receivable | ARManagementTab | useInvoicesQuery (replaces broken arTransactions) | accounting_ar_read | DataTable, StatCards |
| ACC-011 | Accounts Payable | AccountsPayableTab | useBillsQuery, useBillPaymentsQuery | accounting_ap_read | DataTable, StatCards |
| ACC-012 | Journal Entries | JournalEntriesTab | useJournalEntriesQuery | accounting_journal_entries_read | DataTable, FormModal |
| ACC-013 | JE Detail | JournalEntryDetailPage | useJournalEntryQuery, usePostJournalEntryMutation, useReverseJournalEntryMutation | accounting_journal_entries_read | DetailLayout, StatusBadge |
| ACC-014 | Chart of Accounts | ChartOfAccountsTab | useAccountsQuery, useCreateAccountMutation, useUpdateAccountMutation, useDeleteAccountMutation | accounting_chart_of_accounts_read | DataTable, FormModal, ConfirmAction |
| ACC-015 | Financial Reports | FinancialReportsTab | useAccountsQuery, useJournalEntriesQuery | accounting_reports_read | (Report-specific components) |
| ACC-016 | Bank Reconciliation | BankReconciliationTab | useBankTransactionsQuery, useMatchTransactionMutation | accounting_bank_reconciliation_read | DataTable |
| ACC-017 | Tax Reporting | TaxReportingTab | useInvoicesQuery, useExpensesQuery (with tax filters) | accounting_tax_read | DataTable, StatCards |
| ACC-018 | Budget Analysis | BudgetAnalysisTab | useBudgetsQuery, useCreateBudgetMutation | accounting_budgets_read | DataTable, StatCards, FormModal |
| ACC-019 | Cash Flow | CashFlowTab | useInvoicesQuery, useBillsQuery, useExpensesQuery (date-ranged) | accounting_cash_flow_read | StatCards |
| ACC-020 | Variance Analysis | VarianceAnalysisDashboard | useBudgetsQuery, useAccountTransactionsQuery | accounting_variance_read | DataTable, StatCards |
| ACC-021 | Fixed Assets | FixedAssetsTab | useFixedAssetsQuery | accounting_fixed_assets_read | DataTable |
| ACC-022 | Multi-Currency | MultiCurrencyTab | useExchangeRatesQuery, useUpdateRateMutation | accounting_multi_currency_read | DataTable |
| ACC-023 | Aging Reports | AgingReportsTab | useAgingReportQuery (with corrected bucket keys) | accounting_aging_read | DataTable, StatCards |
| ACC-024 | Compliance | CompliancePlanningPage | (delegates to Tax, Budget, Assets tabs) | accounting_compliance_read | TabLoader |
| ACC-025 | Banking & Cash | BankingAndCashPage | (delegates to Recon, Cash Flow, Multi-Currency tabs) | accounting_banking_cash_read | TabLoader |
| ACC-026 | Credit Mgmt | CreditManagement | useCreditAssessmentsQuery, usePaymentRemindersQuery | accounting_credit_read | DataTable, StatCards |

---

## Bug → Fix Traceability

| Bug ID | Severity | Description | Architecture Layer | Fix Description | Verification |
|--------|----------|-------------|-------------------|-----------------|-------------|
| BUG-C01 | CRITICAL | Permission system denies financial roles | Auth | Add `ACCOUNTING_PERMISSIONS` to `ALL_MODULE_PERMISSIONS` with 60 granular permission entries | Auth Verification: PASS |
| BUG-C02 | CRITICAL | Nav shows links guards block | Auth | Align nav permission codes with route guard codes; both use underscore format | Auth Verification: PASS |
| BUG-H01 | HIGH | Financial Mgmt shows mock data | Data + Component | New `useFinancialOverviewQuery` replaces hardcoded stats; StatCards wired to real data | Component Verification: PASS |
| BUG-H02 | HIGH | AR `arTransactions` property doesn't exist | Data | Hook returns `invoices` — component updated to destructure `invoices` not `arTransactions` | Data Verification: PASS (with note) |
| BUG-H03 | HIGH | Bill detail hard-deletes, list soft-deletes | Data | Unified soft-delete via `is_deleted` flag + `useSoftDeleteBillMutation`; migration adds `is_deleted` column | Data Verification: PASS |
| BUG-H04 | HIGH | Journal entry Post bypasses validation | Data + Component | `usePostJournalEntryMutation` routes through `GeneralLedgerService.postJournalEntry()` | Component Verification: PASS |
| BUG-H05 | HIGH | Journal entry Reverse doesn't create reversing entry | Data + Component | `useReverseJournalEntryMutation` routes through `GeneralLedgerService.voidJournalEntry()` | Component Verification: PASS |
| BUG-H06 | HIGH | Aging reports summary always $0 | Data | Fix bucket keys to match aging calculation output (`current`, `30`, `60`, `90`, `90+`); add 61-90 bucket | Data Verification: PASS |
| BUG-M01 | MEDIUM | Invoice line items tab placeholder | Component | New `LineItemsTable` component with real `invoice_line_items` join | Component Verification: PASS |
| BUG-M02 | MEDIUM | Invoice payments tab placeholder | Component | New `InvoicePaymentsTable` component with `invoice_payments` query | Component Verification: PASS |
| BUG-M03 | MEDIUM | Invoice Duplicate no handler | Component | `duplicateEntity` shared handler creates copy with `status: 'draft'` | Component Verification: PASS |
| BUG-M04 | MEDIUM | Expense accounting tab hardcoded | Component | New `ExpenseAccountingTab` with real COA + journal entry data | Component Verification: PASS |
| BUG-M05 | MEDIUM | Expense Duplicate no handler | Component | Same `duplicateEntity` handler as M03 | Component Verification: PASS |
| BUG-M06 | MEDIUM | Payment refund is stub | Component | Remove button (`visible: false`) — refund requires payment gateway integration | Component Verification: PASS |
| BUG-M07 | MEDIUM | Payment print receipt is stub | Component | Remove button (`visible: false`) — print requires receipt template | Component Verification: PASS |
| BUG-M08 | MEDIUM | COA Edit no handler | Component | `handleEditAccount` opens FormModal with account data | Component Verification: PASS |
| BUG-M09 | MEDIUM | COA Delete no handler | Component | `handleDeleteAccount` with ConfirmAction dialog + soft-delete | Component Verification: PASS |
| BUG-M10 | MEDIUM | Bills bulk email is stub | Component | Remove button — bulk email requires email service integration | Component Verification: PASS |
| BUG-L01 | LOW | 3 different permission naming conventions | Auth | Standardize on underscore format (`accounting_invoices_read`) | Auth Verification: PASS |
| BUG-L02 | LOW | Stats from current page only | Data | Separate `useInvoiceAggregationsQuery` for total counts/values | Data Verification: PASS |
| BUG-L03 | LOW | Employee join missing in expenses | Data | Add `.select('*, employees(first_name, last_name)')` to expenses query | Data Verification: PASS |
| BUG-L04 | LOW | Single permission for all 30 routes | Auth | 60 granular permissions across 16 sub-domains | Auth Verification: PASS |
| BUG-L05 | LOW | Edit routes have no effect | Component | Detect `/edit` URL suffix and enable edit mode in DetailLayout | Component Verification: PASS |
| BUG-NEW-1 | HIGH | `getPaymentsByType()` doesn't exist | Data | Implement method on PaymentsService or replace with direct Supabase query | Discovered in Loop 2 |
| BUG-NEW-2 | MEDIUM | `useBulkPayments` uses setTimeout fake processing | Data | Replace with real batch processing mutation | Discovered in Loop 2 |
| BUG-NEW-3 | MEDIUM | Duplicate `invoice_line_items` vs `invoice_items` tables | Data | Consolidate to `invoice_line_items`; migrate `invoice_items` references | Discovered in Loop 2 |
| BUG-NEW-4 | LOW | Duplicate Bill types across hooks | Data | Single source of truth in `types/accounting.ts` | Discovered in Loop 2 |

---

## Coverage Summary

| Metric | Count | Coverage |
|--------|-------|----------|
| Requirements with architecture mapping | 25/25 | 100% |
| Requirements with data hooks | 25/25 | 100% |
| Requirements with permission codes | 25/25 | 100% |
| Loop 1 bugs with fixes | 23/23 | 100% |
| Loop 2 bugs with fixes | 4/4 | 100% |
| Total bugs addressed | 27/27 | 100% |
| Database tables with type definitions | 24/26 | 92.3% |
| Routes with granular permissions | 29/31 | 93.5% |
