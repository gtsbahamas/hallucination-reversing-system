# LVR Pilot Bug Report — Island Biz Accounting Domain

*Generated: 2026-02-13*
*Methodology: LUCID Verified Reconstruction (LVR) Loop 1*
*Scope: 25 accounting page components, 354 claims verified*

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 2 | Permission system denies legitimate users; accounting data shows hardcoded values |
| HIGH | 6 | Broken data access, inconsistent delete behavior, non-functional buttons |
| MEDIUM | 10 | Scaffolding (placeholder text, stub features), partial implementations |
| LOW | 5 | Naming inconsistencies, minor UX issues |
| **Total** | **23** | |

---

## CRITICAL Bugs

### BUG-C01: Accounting Permission System Completely Broken
**Severity:** CRITICAL | **Impact:** ALL accounting pages | **Category:** permission-guard

**Finding:** Every accounting route is guarded by `accounting.invoices.read`, but this permission code does not exist in `permissionMappings.ts`. The `getRolesForPermission('accounting.invoices.read')` function returns `[]` because `ALL_MODULE_PERMISSIONS` only contains `LIFE_SAFETY_PERMISSIONS` and `PAYROLL_PERMISSIONS`.

**Impact:** `finance_manager`, `accountant`, `ar_specialist`, `ap_specialist` — the four roles specifically designed for financial work — are denied access to ALL 30 accounting routes. Only `super_admin`, `owner`, and `operations_manager` can access accounting (via `FULL_ACCESS_ROLES` bypass).

**Evidence:**
- `src/App.tsx:36` — `accounting: 'accounting.invoices.read'`
- `src/config/permissionMappings.ts:340-343` — `ALL_MODULE_PERMISSIONS` only has life_safety and payroll
- `src/config/permissionMappings.ts:365-373` — `getRolesForPermission` returns `[]` for unknown codes
- `src/config/permissionMappings.ts:387-393` — `roleHasPermission` falls through to empty array

### BUG-C02: Navigation Shows Links That Route Guards Block
**Severity:** CRITICAL | **Impact:** 11 accounting navigation entries | **Category:** permission-guard

**Finding:** `navigationPermissionsService.ts` defines `FINANCIAL_ROLES` (finance_manager, accountant, ar_specialist, ap_specialist) as having access to accounting navigation items. But the route guard denies these roles access. Users see clickable nav links that lead to "Access Denied" pages.

**Evidence:**
- `src/services/navigationPermissionsService.ts:33` — `FINANCIAL_ROLES` includes finance_manager, accountant, etc.
- `src/services/navigationPermissionsService.ts:142-185` — 11 accounting nav entries allow FINANCIAL_ROLES
- `src/components/permissions/PermissionGuard.tsx:56-71` — route guard denies these same roles

---

## HIGH Bugs

### BUG-H01: Financial Management Dashboard Shows Hardcoded Mock Data
**Severity:** HIGH | **ACC-009** | **Category:** scaffolding

**Finding:** The main Financial Management overview page (`/accounting`) displays 4 summary cards with hardcoded values instead of real database data.

**Evidence:** `FinancialManagement.tsx:111-163` — All 4 stat cards use mock data, NOT from database queries.

### BUG-H02: Accounts Receivable Summary Metrics Reference Non-Existent Property
**Severity:** HIGH | **ACC-010** | **Category:** data-access

**Finding:** `ARManagementTab.tsx` destructures `arTransactions` from `useAccountsReceivable`, but the hook returns `invoices` — no `arTransactions` property exists. The variable is `undefined` at runtime, causing the summary metrics to display as $0 or NaN.

**Evidence:**
- `ARManagementTab.tsx:46` — `{ arTransactions, loading }` destructured
- `useAccountsReceivable.tsx:188-222` — returns `{ invoices, ... }` — no `arTransactions`

### BUG-H03: Bill Detail Hard-Deletes While List Soft-Deletes
**Severity:** HIGH | **ACC-004** | **Category:** data-integrity

**Finding:** Deleting a bill from the detail page permanently destroys the record (`.delete()`), while deleting from the list page archives it via `deleted_at`/`deleted_by` fields. Same user action, different outcome depending on which page they're on.

**Evidence:**
- `BillDetailPage.tsx:114-152` — `.from('bills').delete()` (hard delete)
- `BillsDashboard.tsx:327-353` — `.from('bills').update({ deleted_at: ... })` (soft delete)

### BUG-H04: Journal Entry Post Bypasses Validation Service
**Severity:** HIGH | **ACC-013** | **Category:** data-integrity

**Finding:** The Journal Entry detail page's "Post" button does a simple status update (`status: 'posted'`) without validating debit/credit balance, updating the general ledger, validating the accounting period, or creating an audit trail. The list page uses the proper `journalEntryService.postJournalEntry` which does all of these.

**Evidence:** `JournalEntryDetailPage.tsx:223-225` — calls `handleStatusUpdate('posted')` which is just `.update({ status: newStatus })`.

### BUG-H05: Journal Entry Reverse Doesn't Create Reversing Entry
**Severity:** HIGH | **ACC-013** | **Category:** data-integrity

**Finding:** The "Reverse" button on a journal entry just changes the status string to `'reversed'` without creating a reversing journal entry or reversing account balances. The service layer (`journalEntryService.voidJournalEntry`) properly creates `VOID-{number}` reversing entries, but the detail page bypasses it.

**Evidence:** `JournalEntryDetailPage.tsx:227-231` — just calls `handleStatusUpdate('reversed')`.

### BUG-H06: Aging Reports Summary Always Shows $0
**Severity:** HIGH | **ACC-023** | **Category:** data-access

**Finding:** The aging reports summary card uses key `'0-30'` but the aging calculation produces keys like `'current'`, `'30'`, `'60'`, `'90'`, `'90+'`. The key mismatch causes the summary to always display $0. Additionally, the 61-90 day bucket is missing from the summary display.

**Evidence:** ACC-023 verification — summary key mismatch between summary card labels and aging bucket keys.

---

## MEDIUM Bugs

### BUG-M01: Invoice Detail — Line Items Tab is Placeholder
**ACC-002** | The Line Items tab displays: "Line items will be displayed here when invoice line items are implemented." The query does NOT join `invoice_line_items`.
**Evidence:** `InvoiceDetailPage.tsx:559-561`

### BUG-M02: Invoice Detail — Payments Tab is Placeholder
**ACC-002** | The Payments tab displays: "Payment history will be displayed here when payments are linked to invoices." No payment data is fetched.
**Evidence:** `InvoiceDetailPage.tsx:572-574`

### BUG-M03: Invoice Detail — Duplicate Button Has No Handler
**ACC-002** | `<Button>` with "Duplicate" text but no `onClick` prop. Renders as clickable but does nothing.
**Evidence:** `InvoiceDetailPage.tsx:680-683`

### BUG-M04: Expense Detail — Accounting Tab is Hardcoded
**ACC-006** | Account shows hardcoded `"Expenses : {category || 'General'}"`. "Tax Deductible: Yes" is hardcoded. Placeholder text: "Accounting integration details will be displayed here when chart of accounts is linked."
**Evidence:** `ExpenseDetailPage.tsx:479-495`

### BUG-M05: Expense Detail — Duplicate Button Has No Handler
**ACC-006** | Same pattern as BUG-M03.
**Evidence:** `ExpenseDetailPage.tsx:604-611`

### BUG-M06: Payment Detail — "Process Refund" is Stub
**ACC-007** | Shows toast "Refund processing coming in v2.0". No actual refund logic.
**Evidence:** `PaymentDetailPage.tsx:116-121`

### BUG-M07: Payment Detail — "Print Receipt" is Stub
**ACC-007** | Shows toast "Receipt printing coming in v2.0". No actual print logic.
**Evidence:** `PaymentDetailPage.tsx:123-128`

### BUG-M08: Chart of Accounts — Edit Button Has No Handler
**ACC-014** | `<Button>` with Edit icon but no `onClick`. Renders as clickable, does nothing.
**Evidence:** `ChartOfAccountsTab.tsx:175-176`

### BUG-M09: Chart of Accounts — Delete Button Has No Handler
**ACC-014** | `<Button>` with Trash icon, enabled for non-system accounts, but no `onClick`.
**Evidence:** `ChartOfAccountsTab.tsx:177-179`

### BUG-M10: Bills List — Bulk Email is Stub
**ACC-003** | Shows toast "Coming Soon. Bulk email sending will be available soon."
**Evidence:** `BillsDashboard.tsx:711-718`

---

## LOW Bugs

### BUG-L01: Permission Code Naming Inconsistency (3 different conventions)
- `App.tsx` uses `accounting.invoices.read` (dot-notation, `accounting.*` prefix)
- `permissionMappings.ts` uses `life_safety_inspections_read` (underscore)
- `navigationPermissionsService.ts` uses `financial.ar.view` (dot-notation, `financial.*` prefix)

### BUG-L02: Stats Computed from Current Page Only (2 pages affected)
**ACC-001, ACC-005** | Summary statistics (total count, total value) are computed from the paginated subset (current page only), not the full dataset. Becomes inaccurate when records exceed one page.

### BUG-L03: Employee Column Missing Join
**ACC-005** | ExpensesTab references `expense.employees.first_name` but the hook uses `select('*')` without joining the employees table.

### BUG-L04: Single Permission Code for All 30 Accounting Routes
All routes map to `accounting.invoices.read`. No granularity — can't grant access to expenses but not invoices.

### BUG-L05: Edit Navigation Links May Lead to Nowhere
**ACC-002, ACC-006, ACC-007** | Edit buttons navigate to `/accounting/{type}/:id/edit` routes. While these routes exist in App.tsx (they render the same detail component), the component doesn't detect edit mode vs view mode — the URL change has no effect.

---

## Bug Distribution by Category

| Category | Count | % |
|----------|-------|---|
| Permission/Access Control | 3 | 13% |
| Data Integrity | 3 | 13% |
| Scaffolding (stub features) | 10 | 43% |
| Data Access (wrong/missing data) | 4 | 17% |
| Naming/Consistency | 3 | 13% |

---

## Recommendations (Priority Order)

1. **Add accounting permissions to `permissionMappings.ts`** (fixes BUG-C01, C02) — Define `ACCOUNTING_PERMISSIONS` module with granular codes matching what `App.tsx` and `navigationPermissionsService.ts` expect.

2. **Wire journal entry Post/Reverse to service layer** (fixes BUG-H04, H05) — Replace direct status updates with `journalEntryService.postJournalEntry()` and `journalEntryService.voidJournalEntry()`.

3. **Unify bill delete behavior** (fixes BUG-H03) — Use soft-delete consistently in both list and detail views.

4. **Fix AR summary metrics** (fixes BUG-H02) — Change destructured property name from `arTransactions` to `invoices`.

5. **Replace Financial Management mock data** (fixes BUG-H01) — Wire summary cards to real aggregation queries.

6. **Fix aging report key mismatch** (fixes BUG-H06) — Align summary card keys with aging bucket keys.

7. **Remove or implement stub features** (fixes BUG-M01-M10) — Either implement the placeholder features or remove the buttons/tabs to avoid user confusion.
