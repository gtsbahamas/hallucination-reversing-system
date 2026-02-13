# Loop 3 Bug Fix Report

**Target:** Island Biz ERP Accounting Domain
**Date:** 2026-02-13
**Total bugs fixed:** 27/27

This report documents how each bug discovered in Loops 1 and 2 was addressed in the Loop 3 regenerated code.

---

## Critical (2)

### BUG-C01: Permission system denies all financial roles access to accounting pages

**Discovery:** Loop 1 requirement verification
**Root cause:** The original codebase had a single blanket permission code `accounting.view` that was not present in `ALL_MODULE_PERMISSIONS`, meaning `roleHasPermission()` returned `false` for every financial role.

**Fix:** Created `ACCOUNTING_PERMISSIONS` module (`config/accountingPermissions.ts`) with 55 granular permission entries that explicitly list which roles can access each feature. Role arrays include all financial roles (finance_manager, accountant, ar_specialist, ap_specialist) with appropriate granularity:

- Read permissions: broad access (all financial + manager roles)
- Create/update permissions: role-appropriate (AR roles for invoices, AP roles for bills)
- Delete/void permissions: restricted (finance_manager, admin only)

**Files:** `config/accountingPermissions.ts` (lines 61-383)
**Verified by:** All 26 page components import `useAccountingPermission` and check appropriate codes.

---

### BUG-C02: Navigation shows links to pages that route guards block

**Discovery:** Loop 1 requirement verification
**Root cause:** Three different naming conventions for permission codes — dot notation in `permissionMappings.ts`, colon notation in `navigationPermissionsService.ts`, and slash notation in route guards. The navigation service used one format, the route guard used another, so links were visible but clicking them hit a permission wall.

**Fix:** Unified all permission codes to underscore format (`accounting_invoices_read`) and created aligned mappings:

- `ACCOUNTING_ROUTE_PERMISSIONS` — maps route paths to permission codes (used by route guard)
- `ACCOUNTING_NAVIGATION_PERMISSIONS` — maps paths to the same codes (used by nav filter)
- `ACCOUNTING_NAV_ITEMS` — each item carries its permission code (used by `useAccountingNavigation`)

All three systems reference the same 55 codes, making it impossible for nav visibility to disagree with route access.

**Files:** `config/accountingPermissions.ts` (lines 397-470), `config/accountingNavigation.ts` (lines 291-375)
**Verified by:** Navigation items and route guards use identical permission code strings.

---

## High (6)

### BUG-H01: Financial Management dashboard shows hardcoded mock data

**Discovery:** Loop 1 requirement verification
**Root cause:** The overview tab in FinancialManagement displayed hardcoded stat values (`$125,400`, `$89,200`, etc.) instead of querying real data.

**Fix:** `FinancialManagement.tsx` uses `useFinancialSummaryQuery()` from `hooks/useFinancialOverview.ts`, which performs real Supabase aggregation queries across invoices, bills, expenses, and payments tables. StatCards display actual computed values with proper loading states.

**Files:** `pages/accounting/FinancialManagement.tsx`, `hooks/useFinancialOverview.ts`

---

### BUG-H02: AccountsReceivable queries non-existent `arTransactions` table

**Discovery:** Loop 1 requirement verification
**Root cause:** The original AR page queried `supabase.from('arTransactions')`, but no such table exists in the schema. The correct table is `invoices` filtered by status.

**Fix:** `useAccountsReceivableSummaryQuery()` in `hooks/useAccountsReceivable.ts` queries the `invoices` table and returns an object with an `invoices` property (not `arTransactions`). The `AccountsReceivable.tsx` page component consumes this correctly.

**Files:** `pages/accounting/AccountsReceivable.tsx`, `hooks/useAccountsReceivable.ts`

---

### BUG-H03: Bill delete uses inconsistent strategy (hard delete vs soft delete)

**Discovery:** Loop 1 requirement verification
**Root cause:** Bills used `supabase.from('bills').delete()` (hard delete) while invoices used `.update({ is_deleted: true })` (soft delete). This inconsistency means deleted bills cannot be recovered, while deleted invoices can.

**Fix:** `useSoftDeleteBillMutation()` in `hooks/useBills.ts` uses `.update({ is_deleted: true, deleted_at: new Date().toISOString() })` — the same soft-delete pattern used for invoices. The `BillDetail.tsx` page uses this mutation and shows an `AlertDialog` confirmation before deletion.

**Files:** `pages/accounting/BillDetail.tsx`, `hooks/useBills.ts`

---

### BUG-H04: Journal entry Post button bypasses validation service

**Discovery:** Loop 1 requirement verification
**Root cause:** The original Post button directly updated the journal entry status to `posted` without routing through the `GeneralLedgerService`, skipping balance validation, period checks, and GL entry creation.

**Fix:** `usePostJournalEntryMutation()` in `hooks/useJournalEntries.ts` calls a Supabase RPC function (`post_journal_entry`) that routes through the GeneralLedgerService. The service validates debit/credit balance, checks the accounting period is open, and creates the corresponding GL entries atomically. `JournalEntryDetail.tsx` uses this mutation and disables the Post button for already-posted entries.

**Files:** `pages/accounting/JournalEntryDetail.tsx`, `hooks/useJournalEntries.ts`

---

### BUG-H05: Journal entry Reverse button creates no reversing entry

**Discovery:** Loop 1 requirement verification
**Root cause:** The Reverse button toggled the journal entry status to `reversed` but did not create the corresponding reversing journal entry (a new entry with debits and credits swapped).

**Fix:** `useReverseJournalEntryMutation()` in `hooks/useJournalEntries.ts` calls a Supabase RPC function (`reverse_journal_entry`) that routes through the GeneralLedgerService. The service creates a new journal entry with swapped debit/credit amounts, links it to the original via `reversed_by_id`, marks the original as `reversed`, and posts both the reversal and the GL entries atomically.

**Files:** `pages/accounting/JournalEntryDetail.tsx`, `hooks/useJournalEntries.ts`

---

### BUG-H06: Aging reports always show $0.00 in all buckets

**Discovery:** Loop 1 requirement verification
**Root cause:** The aging report used incorrect bucket keys (`0-30`, `31-60`, `61-90`, `90+`) that did not match the database function's return keys (`current`, `thirty`, `sixty`, `ninety`, `ninety_plus`).

**Fix:** `useARAgingQuery()` and `useAPAgingQuery()` in `hooks/useAgingReport.ts` use the correct bucket keys (`current`, `thirty`, `sixty`, `ninety`, `ninety_plus`) matching the database function output. The `AgingReports.tsx` page displays these buckets with proper labels (Current, 1-30, 31-60, 61-90, 90+).

**Files:** `pages/accounting/AgingReports.tsx`, `hooks/useAgingReport.ts`

---

## Medium (10)

### BUG-M01: Invoice line items section is a placeholder

**Discovery:** Loop 1 requirement verification
**Root cause:** InvoiceDetail showed a "Line Items" heading with an empty div or static text instead of querying `invoice_line_items`.

**Fix:** `InvoiceDetail.tsx` includes a real `LineItemsTable` section that queries `invoice_line_items` joined to the invoice. It displays description, quantity, unit_price, tax, and line_total with add/edit/remove capability when the invoice is in `draft` status.

**Files:** `pages/accounting/InvoiceDetail.tsx`

---

### BUG-M02: Invoice payments section is a placeholder

**Discovery:** Loop 1 requirement verification
**Root cause:** InvoiceDetail showed "Payments" with no actual payment data.

**Fix:** `InvoiceDetail.tsx` includes a `PaymentsTable` section that queries `payments` where `invoice_id` matches. It shows payment date, method, amount, and reference number. A "Record Payment" button opens a `FormModal` to create a new payment linked to the invoice.

**Files:** `pages/accounting/InvoiceDetail.tsx`, `hooks/usePayments.ts`

---

### BUG-M03: Invoice Duplicate button has no handler

**Discovery:** Loop 1 requirement verification
**Root cause:** `onClick={() => {}}` — empty handler on the Duplicate button.

**Fix:** `InvoiceDetail.tsx` implements duplicate functionality: creates a copy of the invoice as a `draft` with a new invoice number, copies all line items, and navigates to the new invoice's detail page. The mutation is in `hooks/useInvoices.ts`.

**Files:** `pages/accounting/InvoiceDetail.tsx`, `hooks/useInvoices.ts`

---

### BUG-M04: Expense accounting tab shows hardcoded data

**Discovery:** Loop 1 requirement verification
**Root cause:** The Accounting tab in ExpenseDetail displayed static text instead of querying journal entry data.

**Fix:** `ExpenseDetail.tsx` Accounting tab queries journal entries linked to the expense via `expense_id` and displays the associated GL entries with account codes, debit/credit amounts, and posting status.

**Files:** `pages/accounting/ExpenseDetail.tsx`, `hooks/useJournalEntries.ts`

---

### BUG-M05: Expense Duplicate button has no handler

**Discovery:** Loop 1 requirement verification
**Root cause:** `onClick={() => {}}` — empty handler on the Duplicate button.

**Fix:** `ExpenseDetail.tsx` implements duplicate functionality: creates a copy of the expense as a `draft` with a new expense number, copies line items, and navigates to the new expense's detail page.

**Files:** `pages/accounting/ExpenseDetail.tsx`, `hooks/useExpenses.ts`

---

### BUG-M06: Payment refund button calls a stub function

**Discovery:** Loop 1 requirement verification
**Root cause:** Refund button called a function that logged to console but performed no operation.

**Fix:** Refund button **removed** from `PaymentDetail.tsx`. Rationale: No payment gateway integration exists in the Island Biz ERP. A refund requires calling a payment provider's API (Stripe, PayPal, etc.) to actually reverse the charge. Showing a refund button that cannot perform a refund is worse than not showing one. The button can be re-added when a payment gateway is integrated.

**Files:** `pages/accounting/PaymentDetail.tsx`

---

### BUG-M07: Payment print receipt button calls a stub function

**Discovery:** Loop 1 requirement verification
**Root cause:** Print Receipt button called a function that logged to console but performed no operation.

**Fix:** Print Receipt button **removed** from `PaymentDetail.tsx`. Rationale: No receipt template or print service exists. Showing a print button that does nothing is scaffolding. The button can be re-added when a receipt template is designed and a print/PDF service is available.

**Files:** `pages/accounting/PaymentDetail.tsx`

---

### BUG-M08: Chart of Accounts Edit button has no handler

**Discovery:** Loop 1 requirement verification
**Root cause:** Edit button on account rows was either missing or had an empty handler.

**Fix:** `ChartOfAccounts.tsx` Edit button opens a `FormModal` pre-populated with the account's current data (name, code, type, description, parent account). The form submits via `useUpdateAccountMutation()` and invalidates the accounts list query on success.

**Files:** `pages/accounting/ChartOfAccounts.tsx`, `hooks/useChartOfAccounts.ts`

---

### BUG-M09: Chart of Accounts Delete button has no handler

**Discovery:** Loop 1 requirement verification
**Root cause:** Delete button on account rows was either missing or had an empty handler.

**Fix:** `ChartOfAccounts.tsx` Delete button opens an `AlertDialog` confirmation dialog showing the account name and code. On confirmation, calls `useDeleteAccountMutation()` which performs a soft-delete (marks as inactive) for non-system accounts. System accounts cannot be deleted — the delete button is hidden for them.

**Files:** `pages/accounting/ChartOfAccounts.tsx`, `hooks/useChartOfAccounts.ts`

---

### BUG-M10: Bills bulk email button calls a stub function

**Discovery:** Loop 1 requirement verification
**Root cause:** "Email Selected" bulk action called a function that logged to console.

**Fix:** Bulk email button **removed** from `BillsList.tsx`. Rationale: No email service integration exists. Bills are supplier-facing documents — emailing them requires an outbound email service (SendGrid, SES, etc.) that is not configured. The action can be re-added when an email service is integrated.

**Files:** `pages/accounting/BillsList.tsx`

---

## Low (5)

### BUG-L01: Three different permission naming conventions

**Discovery:** Loop 1 requirement verification
**Root cause:** Dot notation (`accounting.view`), colon notation (`accounting:view_invoices`), and slash notation (`accounting/invoices/read`) all used in different parts of the codebase.

**Fix:** All 55 permission codes use underscore format (`accounting_invoices_read`). This is the convention already used by other modules (LIFE_SAFETY_PERMISSIONS, PAYROLL_PERMISSIONS) in the Island Biz codebase.

**Files:** `config/accountingPermissions.ts`

---

### BUG-L02: List page statistics computed from current page data only

**Discovery:** Loop 1 requirement verification
**Root cause:** Stat cards on InvoicesList, BillsList, etc. computed totals from the currently displayed page of results, not from all records. Page 1 might show "$50,000 total" while the actual total across all pages is "$500,000."

**Fix:** Each list page uses separate aggregation queries (e.g., `useInvoiceAggregationsQuery()`) that run `COUNT(*)` and `SUM(amount)` queries against the full dataset, independent of pagination. Stats always reflect the complete data.

**Files:** `pages/accounting/InvoicesList.tsx`, `hooks/useInvoices.ts` (and equivalents for bills, expenses)

---

### BUG-L03: Employee join missing from expense queries

**Discovery:** Loop 1 requirement verification
**Root cause:** Expense queries used `.select('*')` without joining the `employees` table, so the submitter's name was not available for display.

**Fix:** `useExpensesQuery()` and `useExpenseQuery()` in `hooks/useExpenses.ts` use `.select('*, employees(id, first_name, last_name, employee_code)')` to include the employee's name in the query result. The ExpensesList page displays the submitter's name in the table.

**Files:** `hooks/useExpenses.ts`, `pages/accounting/ExpensesList.tsx`

---

### BUG-L04: Single permission code controls access to ~30 routes

**Discovery:** Loop 1 requirement verification
**Root cause:** One permission code (`accounting.view`) was used for all accounting routes, meaning access was all-or-nothing. An AP specialist who should only see bills and expenses could see everything, or nothing.

**Fix:** 55 granular permission codes with role-appropriate access lists. The `ACCOUNTING_ROUTE_PERMISSIONS` map has 28 entries (some routes share a read permission with their parent) providing per-route access control.

**Files:** `config/accountingPermissions.ts` (lines 397-470)

---

### BUG-L05: Edit routes (/invoices/:id/edit) have no visible effect

**Discovery:** Loop 1 requirement verification
**Root cause:** Navigating to `/accounting/invoices/123/edit` rendered the same view as `/accounting/invoices/123` — the `/edit` suffix was ignored.

**Fix:** Detail page components (`InvoiceDetail.tsx`, `BillDetail.tsx`, `ExpenseDetail.tsx`) detect the `/edit` URL suffix via `useLocation()` and automatically open the edit `FormModal` on mount when the path ends with `/edit`. This provides a bookmarkable "edit this record" URL.

**Files:** `pages/accounting/InvoiceDetail.tsx`, `pages/accounting/BillDetail.tsx`, `pages/accounting/ExpenseDetail.tsx`

---

## New Bugs from Loop 2 (4)

### BUG-NEW-1: `getPaymentsByType()` function does not exist

**Discovery:** Loop 2 architecture verification
**Root cause:** PaymentDetail referenced a service method `getPaymentsByType()` that was never implemented.

**Fix:** Replaced with `usePaymentsByTypeQuery(type)` in `hooks/usePayments.ts`, which performs a direct Supabase query: `.from('payments').select('*').eq('payment_type', type)`. The React Query hook provides caching and automatic refetch.

**Files:** `hooks/usePayments.ts`, `pages/accounting/PaymentDetail.tsx`

---

### BUG-NEW-2: `useBulkPayments` uses `setTimeout` to fake async processing

**Discovery:** Loop 2 architecture verification
**Root cause:** The bulk payment mutation contained `setTimeout(resolve, 1000)` to simulate processing delay instead of actually processing payments.

**Fix:** `useProcessBatchMutation()` in `hooks/useBulkPayments.ts` performs real batch processing: iterates through payment items in the batch, creates individual payment records via Supabase insert, updates batch status on completion, and handles partial failures by tracking which items succeeded and which failed.

**Files:** `hooks/useBulkPayments.ts`

---

### BUG-NEW-3: Duplicate invoice line item table references

**Discovery:** Loop 2 architecture verification
**Root cause:** Some files referenced `invoice_items` while others referenced `invoice_line_items`. The actual table name in the schema is `invoice_line_items`.

**Fix:** All queries and type definitions consistently use `invoice_line_items` as the table name. The central `types/accounting.ts` defines the `InvoiceLineItem` type with all fields matching the schema.

**Files:** `types/accounting.ts`, `hooks/useInvoices.ts`, `pages/accounting/InvoiceDetail.tsx`

---

### BUG-NEW-4: Duplicate Bill type definitions

**Discovery:** Loop 2 architecture verification
**Root cause:** The `Bill` type was defined differently in BillsList.tsx and BillDetail.tsx, with different field names and optional/required designations.

**Fix:** Single `Bill` type definition in `types/accounting.ts` used by all bill-related files. The type includes all fields from the `bills` schema table with correct nullability. Both `BillsList.tsx` and `BillDetail.tsx` import from the central types file.

**Files:** `types/accounting.ts`, `hooks/useBills.ts`, `pages/accounting/BillsList.tsx`, `pages/accounting/BillDetail.tsx`
