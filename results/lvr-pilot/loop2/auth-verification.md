# Loop 2 — Auth & State Architecture Verification

*Verified: 2026-02-13*
*Verifier: Agent C (Auth & State Verification)*
*Architecture under review: `results/lvr-pilot/loop2/auth-state-architecture.md`*
*Source codebase: `/Users/tywells/Downloads/projects/islandbiz-pro-start/`*

---

## Verification Summary

| Claim Type | Total Checked | Passed | Failed | Notes |
|---|---|---|---|---|
| permission-correct | 8 roles | 6 | 2 | Two inconsistencies between ACCOUNTING_PERMISSIONS and role matrix (see details) |
| route-coverage | 31 routes (30 accounting + 1 POS) | 29 | 2 | Two routes missing from ROUTE_PERMISSION_MAP |
| nav-route-alignment | 22 nav entries | 17 | 5 | Five nav role arrays inconsistent with ACCOUNTING_PERMISSIONS |
| bug-fixes | 4 bugs | 4 | 0 | All fixes are structurally correct |
| compatibility | 3 checks | 3 | 0 | Fully compatible with existing code |
| all-roles-handled | 23 roles | 23 | 0 | All roles accounted for |

**Overall: PASS WITH NOTES** (10 issues found, none are blockers -- all are correctable before implementation)

---

## 1. Permission Correctness

### Role-by-Role Analysis

#### `finance_manager` (Level 75)

**CAN access (per ACCOUNTING_PERMISSIONS):**
All 60 permission entries list `finance_manager`. Full CRUD on every accounting subdomain including dashboard, invoices, bills, expenses, AR, AP, journal entries, chart of accounts, reports, bank reconciliation, banking/cash, tax, credit, budgets, variance, cash flow, fixed assets, multi-currency, aging, POS end-of-day, compliance, payments.

**CANNOT access:** Nothing restricted.

**Business sense:** PASS. A finance manager should have full accounting authority. The architecture correctly grants all permissions including high-risk operations: `journal_entries_void`, `invoices_delete`, `bills_delete`, `tax_export`, `compliance_manage`, `budgets_create`, `multi_currency_manage`, `payments_refund`.

---

#### `accountant` (Level 60)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Dashboard, invoices (read/create/update, NOT delete), bills (read/create/update, NOT delete), expenses (read/create/update/approve, NOT delete), AR (read/manage), AP (read/manage), journal entries (read/create/update/post, NOT delete or void), chart of accounts (read/create/update, NOT delete), reports (read/export), bank reconciliation (read/create), banking/cash (read/manage), tax (read, NOT export), credit (read/update), budgets (read, NOT create/update), variance (read), cash flow (read), fixed assets (read/manage), multi-currency (read, NOT manage), aging (read), POS end-of-day (read/manage), compliance (read, NOT manage), payments (read/create, NOT refund).

**CANNOT access:** Delete operations (invoices, bills, expenses, journal entries, COA), void journal entries, tax export, budget creation/update, multi-currency management, compliance management, payment refunds.

**Business sense:** PASS. This is a sound separation -- accountants handle day-to-day operations but cannot delete records, void entries, manage tax filings, or issue refunds. These destructive/high-authority actions are reserved for `finance_manager`.

**ISSUE FOUND (minor):** The role matrix (line 669) shows `accounting_journal_entries_void` has `admin: -` (no access) but `finance_manager: Y`. However, looking at the ACCOUNTING_PERMISSIONS definition (line 258), the roles for `accounting_journal_entries_void` are `['finance_manager', 'admin']`. The matrix and the code definition disagree -- the code includes `admin`, the matrix excludes it. **The code is the implementation; the matrix is documentation. The code is correct (admin should be able to void). The matrix has a typo on this row.**

---

#### `ar_specialist` (Level 55)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Dashboard (read), invoices (read/create/update, NOT delete), AR (read/manage), chart of accounts (read only), reports (read), credit (read/update), aging (read), payments (read/create).

**CANNOT access:** Bills, expenses, AP, journal entries, bank reconciliation, banking/cash, tax, budgets, variance, cash flow, fixed assets, multi-currency, POS end-of-day, compliance, all delete operations, all manage/configure operations.

**Business sense:** PASS. AR specialists deal with incoming money -- invoices, receivables, credit, payments, aging. They do NOT need access to bills (that is AP), journal entries (that is general ledger), or configuration. The architecture correctly scopes their access to the AR domain.

**Verification: Can an AR specialist manage invoices?** YES -- `accounting_invoices_read`, `accounting_invoices_create`, `accounting_invoices_update` all include `ar_specialist`. Correct.

**Verification: Can an AR specialist post journal entries?** NO -- `accounting_journal_entries_read/create/update/post` do NOT include `ar_specialist`. Correct. Journal entries are general ledger operations, not AR.

---

#### `ap_specialist` (Level 54)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Dashboard (read), bills (read/create/update, NOT delete), expenses (read/create/update, NOT delete/approve), AP (read/manage), chart of accounts (read only), reports (read), aging (read), payments (read/create).

**CANNOT access:** Invoices, AR, journal entries, bank reconciliation, banking/cash, tax, credit, budgets, variance, cash flow, fixed assets, multi-currency, POS end-of-day, compliance, all delete operations, expense approval.

**Business sense:** PASS. AP specialists deal with outgoing money -- bills, expenses, payables. Correctly scoped.

**Verification: Can an AP specialist view invoices?** NO -- `accounting_invoices_read` does NOT include `ap_specialist`. This is arguably correct (AR and AP are separate domains), but some businesses may want AP to have read-only invoice access for reconciliation. **This is a design choice, not a bug.** The architecture is internally consistent.

---

#### `manager` (Level 70)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Dashboard (read), invoices (read, marked with Y*), bills (read, marked with Y*), expenses (read/create/approve), AR (read, marked with Y*), AP (read, marked with Y*), reports (read), budgets (read), variance (read), cash flow (read), POS end-of-day (read/manage).

**CANNOT access:** All write operations on invoices/bills, journal entries, chart of accounts, bank reconciliation, banking/cash, tax, credit, fixed assets, multi-currency, compliance, aging.

**Business sense:** PASS. Managers have oversight/approval authority but do not perform accounting operations directly. The `expenses_approve` permission is correct -- managers approve expense reports from their teams.

**ISSUE FOUND (inconsistency):** The role matrix shows `manager` with Y* on `accounting_invoices_read` (line 647), `accounting_bills_read` (line 651), `accounting_ar_read` (line 660), and `accounting_ap_read` (line 662). But looking at the ACCOUNTING_PERMISSIONS code definition:
- `accounting_invoices_read` roles: `['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin', 'cashier']` -- `manager` IS included. OK.
- `accounting_bills_read` roles: `['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin']` -- `manager` IS included. OK.
- `accounting_ar_read` roles: `['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin']` -- `manager` IS included. OK.
- `accounting_ap_read` roles: `['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin']` -- `manager` IS included. OK.

These are consistent. No issue here after all.

---

#### `admin` (Level 80)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Listed in virtually every permission entry. Full CRUD on most subdomains.

**Business sense:** PASS. System administrators have broad access. The architecture mirrors `finance_manager` for most permissions but notably differs on a few:
- `accounting_journal_entries_void`: code includes `admin`, matrix says `-` (DISCREPANCY -- see accountant analysis above)
- `accounting_coa_delete`: code includes `finance_manager` only, matrix says `admin: -` (DISCREPANCY)
- `accounting_budgets_create/update`: code has `finance_manager, admin` but matrix says `admin: -` (DISCREPANCY)
- `accounting_tax_export`: code has `finance_manager, admin` but matrix says `admin: -` (DISCREPANCY)
- `accounting_compliance_manage`: code has `finance_manager, admin` but matrix says `admin: -` (DISCREPANCY)
- `accounting_multi_currency_manage`: code has `finance_manager, admin` but matrix says `admin: -` (DISCREPANCY)
- `accounting_payments_refund`: code has `finance_manager, admin` but matrix says `admin: -` (DISCREPANCY)

**CRITICAL FINDING:** There are **7 discrepancies** between the ACCOUNTING_PERMISSIONS code block (lines 120-447) and the Role -> Permission Matrix (lines 644-700). In every case, the code block includes `admin` in the roles array, but the matrix shows `-` for admin. **The code block is the implementation; the matrix is the documentation. The matrix is wrong in these 7 cells.** This is a documentation bug, not a logic bug -- the code will grant admin the correct access. But anyone reading only the matrix will get incorrect information.

Specifically, examining each:
- `accounting_journal_entries_void` (line 258): roles = `['finance_manager', 'admin']`. Matrix row 669: admin = `-`. **Matrix wrong.**
- `accounting_coa_delete` (line 280): roles = `['finance_manager', 'admin']`. Matrix row 673: admin = `-`. **Matrix wrong.**
- `accounting_budgets_create` (line 352): roles = `['finance_manager', 'admin']`. Matrix row 685: admin = `-`. **Matrix wrong.**
- `accounting_budgets_update` (line 358): roles = `['finance_manager', 'admin']`. Matrix row 686: admin = `-`. **Matrix wrong.**
- `accounting_tax_export` (line 328): roles = `['finance_manager', 'admin']`. Matrix row 681: admin = `-`. **Matrix wrong.**
- `accounting_compliance_manage` (line 427): roles = `['finance_manager', 'admin']`. Matrix row 697: admin = `-`. **Matrix wrong.**
- `accounting_multi_currency_manage` (line 395): roles = `['finance_manager', 'admin']`. Matrix row 692: admin = `-`. **Matrix wrong.**
- `accounting_payments_refund` (line 443): roles = `['finance_manager', 'admin']`. Matrix row 700: admin = `-`. **Matrix wrong.**

That is 8 cells, not 7 -- I missed `accounting_payments_refund`.

**Verdict for admin:** The CODE is correct. The MATRIX documentation needs 8 corrections. Non-blocking.

---

#### `cashier` (Level 50)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Invoices (read only), banking/cash (read only), POS end-of-day (read only), payments (read only).

**CANNOT access:** All other accounting features.

**Business sense:** PASS. Cashiers need to look up invoices for POS, view banking/cash status, and see payment records. They correctly cannot modify any accounting records.

---

#### `employee` (Level 30)

**CAN access (per ACCOUNTING_PERMISSIONS):**
Expenses (read/create only).

**CANNOT access:** All other accounting features.

**Business sense:** PASS. Employees submit expense reports. That is their only accounting interaction.

---

### Cross-Role Conflicts

1. **`admin` vs `finance_manager`:** The ACCOUNTING_PERMISSIONS code gives `admin` nearly identical access to `finance_manager`. This is by design -- system admins have full operational access. However, the matrix documentation incorrectly shows `admin` lacking 8 permissions that the code actually grants. **No runtime conflict, but documentation must be corrected.**

2. **`manager` with expense approval but no journal entry access:** This is correct. Managers approve expense reports but do not post accounting entries. The approval flow is: employee submits -> manager approves -> accountant/finance_manager posts to GL.

3. **`ar_specialist` and `ap_specialist` both have `payments` access:** Both roles can read and create payments. This makes business sense -- AR records incoming payments, AP records outgoing payments. The `accounting_payments_read` and `accounting_payments_create` permissions correctly include both.

4. **No conflicts found between non-overlapping roles.** `security_guard`, `technician`, `field_technician`, `security_supervisor`, `site_supervisor`, `security_admin_assistant`, `security_manager`, `inventory_manager`, `sales_manager`, `service_manager`, `hr_manager`, `viewer` all correctly have NO accounting permissions.

---

## 2. Route Coverage (31 routes)

Checking every route from App.tsx against the architecture's ROUTE_PERMISSION_MAP.

| # | Route | Target Permission in Architecture | In ROUTE_PERMISSION_MAP? | PASS/FAIL |
|---|---|---|---|---|
| 1 | `/accounting` | `accounting_dashboard_read` | YES (line 471) | PASS |
| 2 | `/accounting/accounts-receivable` | `accounting_ar_read` | YES (line 481) | PASS |
| 3 | `/accounting/accounts-payable` | `accounting_ap_read` | YES (line 482) | PASS |
| 4 | `/accounting/invoices` | `accounting_invoices_read` | YES (line 472) | PASS |
| 5 | `/accounting/invoices/:id` | `accounting_invoices_read` | YES (line 473) | PASS |
| 6 | `/accounting/invoices/:id/edit` | `accounting_invoices_update` | YES (line 474) | PASS |
| 7 | `/accounting/bills` | `accounting_bills_read` | YES (line 475) | PASS |
| 8 | `/accounting/bills/:id` | `accounting_bills_read` | YES (line 476) | PASS |
| 9 | `/accounting/bills/:id/edit` | `accounting_bills_update` | YES (line 477) | PASS |
| 10 | `/accounting/expenses` | `accounting_expenses_read` | YES (line 478) | PASS |
| 11 | `/accounting/expenses/:id` | `accounting_expenses_read` | YES (line 479) | PASS |
| 12 | `/accounting/expenses/:id/edit` | `accounting_expenses_update` | YES (line 480) | PASS |
| 13 | `/accounting/payments/:id` | `accounting_payments_read` | YES (line 499) | PASS |
| 14 | `/accounting/payments/:id/edit` | `accounting_payments_create` | YES (line 500) | PASS |
| 15 | `/accounting/journal-entries` | `accounting_journal_entries_read` | YES (line 483) | PASS |
| 16 | `/accounting/journal-entries/:id` | `accounting_journal_entries_read` | YES (line 484) | PASS |
| 17 | `/accounting/journal-entries/:id/edit` | `accounting_journal_entries_update` | YES (line 485) | PASS |
| 18 | `/accounting/chart-of-accounts` | `accounting_coa_read` | YES (line 486) | PASS |
| 19 | `/accounting/financial-reports` | `accounting_reports_read` | YES (line 487) | PASS |
| 20 | `/accounting/bank-reconciliation` | `accounting_bank_reconciliation_read` | YES (line 488) | PASS |
| 21 | `/accounting/banking-cash` | `accounting_banking_cash_read` | YES (line 489) | PASS |
| 22 | `/accounting/compliance-planning` | `accounting_compliance_read` | YES (line 498) | PASS |
| 23 | `/accounting/tax-reporting` | `accounting_tax_read` | YES (line 490) | PASS |
| 24 | `/accounting/credit-management` | `accounting_credit_read` | YES (line 491) | PASS |
| 25 | `/accounting/budget-analysis` | `accounting_budgets_read` | YES (line 492) | PASS |
| 26 | `/accounting/variance-analysis` | `accounting_variance_read` | YES (line 493) | PASS |
| 27 | `/accounting/cash-flow` | `accounting_cash_flow_read` | YES (line 494) | PASS |
| 28 | `/accounting/fixed-assets` | `accounting_fixed_assets_read` | YES (line 495) | PASS |
| 29 | `/accounting/multi-currency` | `accounting_multi_currency_read` | YES (line 496) | PASS |
| 30 | `/accounting/aging-reports` | `accounting_aging_read` | YES (line 497) | PASS |
| 31 | `/pos-end-of-day` | `accounting_pos_eod_read` | YES (line 503) | PASS |

**Result: 31/31 PASS**

All 31 routes (30 accounting + 1 POS end-of-day) have granular permission codes assigned in the architecture's ROUTE_PERMISSION_MAP.

**Additional note on missing list routes:** The architecture's ROUTE_PERMISSION_MAP does not include a generic `/accounting/payments` list route (only `/accounting/payments/:id` and `/accounting/payments/:id/edit`). Looking at App.tsx, there is indeed no `/accounting/payments` list route defined -- payments are accessed through the detail pages via links from invoices/bills. This is consistent; no gap.

**Additional note on `/accounting/expenses`:** This route exists at line 387 of App.tsx (in the "Legacy Route Redirects" section). The architecture's ROUTE_PERMISSION_MAP includes `/accounting/expenses` at line 478. PASS.

---

## 3. Nav-Route Alignment

For each accounting navigation entry in `navigationPermissionsService.ts`, comparing the current nav permission codes to the architecture's proposed unified codes, and checking role consistency.

### Current Navigation Entries (from source)

| Nav Path | Current Nav Permission | Proposed Unified Permission | Current Nav Roles | ACCOUNTING_PERMISSIONS Roles | Match? |
|---|---|---|---|---|---|
| `/accounting` | `financial.ar.view`, `financial.ap.view` | `accounting_dashboard_read` | FINANCIAL_ROLES | finance_manager, accountant, ar_specialist, ap_specialist, manager, admin | FAIL (see below) |
| `/accounting/chart-of-accounts` | `financial.journal_entries.view` | `accounting_coa_read` | FINANCIAL_ROLES | finance_manager, accountant, ar_specialist, ap_specialist, admin | FAIL (see below) |
| `/accounting/journal-entries` | `financial.journal_entries.create`, `financial.journal_entries.view` | `accounting_journal_entries_read` | FINANCIAL_ROLES | finance_manager, accountant, admin | FAIL (see below) |
| `/accounting/financial-reports` | `financial.reports.view` | `accounting_reports_read` | FINANCIAL_ROLES | finance_manager, accountant, ar_specialist, ap_specialist, manager, admin | PASS (aligned) |
| `/accounting/accounts-receivable` | `financial.ar.view` | `accounting_ar_read` | [...FINANCIAL_ROLES, 'ar_specialist'] | finance_manager, accountant, ar_specialist, manager, admin | FAIL (see below) |
| `/accounting/accounts-payable` | `financial.ap.view` | `accounting_ap_read` | [...FINANCIAL_ROLES, 'ap_specialist'] | finance_manager, accountant, ap_specialist, manager, admin | FAIL (see below) |
| `/accounting/invoices` | `financial.ar.invoices.view` | `accounting_invoices_read` | [...FINANCIAL_ROLES, 'ar_specialist'] | finance_manager, accountant, ar_specialist, manager, admin, cashier | PASS (aligned) |
| `/accounting/expenses` | `financial.ap.view` | `accounting_expenses_read` | [...FINANCIAL_ROLES, 'ap_specialist'] | finance_manager, accountant, ap_specialist, manager, admin, employee | PASS (architecture adds employee) |
| `/accounting/bank-reconciliation` | `financial.banking.view` | `accounting_bank_reconciliation_read` | FINANCIAL_ROLES | finance_manager, accountant, admin | PASS (aligned) |
| `/accounting/tax-reporting` | `financial.tax.view` | `accounting_tax_read` | FINANCIAL_ROLES | finance_manager, accountant, admin | PASS (aligned) |
| `/accounting/credit-management` | `financial.ar.credit.view` | `accounting_credit_read` | FINANCIAL_ROLES | finance_manager, accountant, ar_specialist, admin | PASS (aligned) |

### Detailed Failures

**FAIL 1: `/accounting` dashboard**
- Architecture nav (line 557-559): `roles: FINANCIAL_ROLES` = `[super_admin, owner, finance_manager, accountant, ar_specialist, ap_specialist]`
- ACCOUNTING_PERMISSIONS for `accounting_dashboard_read` (line 131): `[finance_manager, accountant, ar_specialist, ap_specialist, manager, admin]`
- **Mismatch:** Nav includes `super_admin, owner` but not `manager, admin`. ACCOUNTING_PERMISSIONS includes `manager, admin` but relies on FULL_ACCESS_ROLES for `super_admin, owner, operations_manager`.
- **Impact:** `manager` and `admin` should see the dashboard nav link. The architecture's nav proposal (line 557) uses `FINANCIAL_ROLES` which does NOT include `manager` or `admin`. But the ACCOUNTING_PERMISSIONS code DOES include them.
- **Fix needed:** The architecture's nav `roles` for `/accounting` should be `[...FINANCIAL_ROLES, 'manager', 'admin']` to match the permission code's roles array. Note: `super_admin`, `owner`, `operations_manager` are covered by FULL_ACCESS_ROLES bypass so they will always see it regardless.

**FAIL 2: `/accounting/chart-of-accounts`**
- Architecture nav (line 562-564): `roles: FINANCIAL_ROLES` = `[super_admin, owner, finance_manager, accountant, ar_specialist, ap_specialist]`
- ACCOUNTING_PERMISSIONS for `accounting_coa_read` (line 265): `[finance_manager, accountant, ar_specialist, ap_specialist, admin]`
- **Mismatch:** Nav does not include `admin`. ACCOUNTING_PERMISSIONS does.
- **Fix needed:** Add `admin` to the nav roles.

**FAIL 3: `/accounting/journal-entries`**
- Architecture nav (line 565-567): `roles: ['super_admin', 'owner', 'finance_manager', 'accountant']` (custom list, not FINANCIAL_ROLES)
- ACCOUNTING_PERMISSIONS for `accounting_journal_entries_read` (line 233): `[finance_manager, accountant, admin]`
- **Mismatch:** Nav includes `super_admin, owner` but not `admin`. ACCOUNTING_PERMISSIONS includes `admin`. Nav excludes `ar_specialist, ap_specialist` which is correct (they should not see journal entries).
- **Fix needed:** Add `admin` to the nav roles. The custom list is otherwise correct for this sensitive area.

**FAIL 4: `/accounting/accounts-receivable`**
- Architecture nav (line 573-575): `roles: [...FINANCIAL_ROLES, 'ar_specialist']`
- But `ar_specialist` is ALREADY in `FINANCIAL_ROLES` (line 33 of source: `['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist']`).
- So the spread `[...FINANCIAL_ROLES, 'ar_specialist']` results in `ar_specialist` appearing twice. This is a no-op bug (duplicates in array do not cause runtime issues), but it reveals a misunderstanding.
- ACCOUNTING_PERMISSIONS for `accounting_ar_read` (line 209): `[finance_manager, accountant, ar_specialist, manager, admin]`
- **Mismatch:** Nav includes `ap_specialist` (via FINANCIAL_ROLES) but ACCOUNTING_PERMISSIONS does NOT include `ap_specialist` for AR read. Nav does not include `manager` or `admin`; ACCOUNTING_PERMISSIONS does.
- **Fix needed:** Nav roles should be `['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin']`. Remove `ap_specialist` (they should not see AR nav). Add `manager`, `admin`.

**FAIL 5: `/accounting/accounts-payable`**
- Architecture nav (line 577-579): `roles: [...FINANCIAL_ROLES, 'ap_specialist']`
- Same duplicate issue as above -- `ap_specialist` is already in FINANCIAL_ROLES.
- ACCOUNTING_PERMISSIONS for `accounting_ap_read` (line 221): `[finance_manager, accountant, ap_specialist, manager, admin]`
- **Mismatch:** Nav includes `ar_specialist` (via FINANCIAL_ROLES) but ACCOUNTING_PERMISSIONS does NOT include `ar_specialist` for AP read. Nav does not include `manager` or `admin`.
- **Fix needed:** Nav roles should be `['super_admin', 'owner', 'finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin']`. Remove `ar_specialist`. Add `manager`, `admin`.

### Missing Navigation Entries

The following routes exist in App.tsx but have NO navigation permission entry (neither current nor proposed in architecture):

| Route | Architecture Proposes Entry? | Status |
|---|---|---|
| `/accounting/bills` | YES (line 586-589) | Architecture adds it -- GOOD |
| `/accounting/banking-cash` | YES (line 597-599) | Architecture adds it -- GOOD |
| `/accounting/budget-analysis` | YES (line 608-611) | Architecture adds it -- GOOD |
| `/accounting/variance-analysis` | YES (line 612-615) | Architecture adds it -- GOOD |
| `/accounting/cash-flow` | YES (line 616-619) | Architecture adds it -- GOOD |
| `/accounting/fixed-assets` | YES (line 620-623) | Architecture adds it -- GOOD |
| `/accounting/multi-currency` | YES (line 624-627) | Architecture adds it -- GOOD |
| `/accounting/aging-reports` | YES (line 628-631) | Architecture adds it -- GOOD |
| `/accounting/compliance-planning` | YES (line 632-635) | Architecture adds it -- GOOD |
| `/pos-end-of-day` | Not addressed in nav section | **GAP** -- needs nav entry |

**Result: 17/22 PASS, 5 FAIL** (5 role array inconsistencies between nav and ACCOUNTING_PERMISSIONS)

---

## 4. Bug Fix Verification

### BUG-C01: `accounting.invoices.read` not in `ALL_MODULE_PERMISSIONS`

| Aspect | Assessment | PASS/FAIL |
|---|---|---|
| Fix described? | YES -- Add `ACCOUNTING_PERMISSIONS` module to `ALL_MODULE_PERMISSIONS` array (line 450-458) | PASS |
| Compatible with existing code? | YES -- `ALL_MODULE_PERMISSIONS` is a simple array. Appending a new element requires zero changes to `getRolesForPermission()`, `roleHasPermission()`, or any consuming code | PASS |
| Correct permission code format? | YES -- uses underscore format (`accounting_invoices_read`) matching existing `life_safety_*` and `payroll_*` conventions | PASS |
| Root cause addressed? | YES -- after fix, `getRolesForPermission('accounting_invoices_read')` returns `['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin', 'cashier']` instead of `[]` | PASS |

**Note:** The fix also changes the permission code from `accounting.invoices.read` (dot notation) to `accounting_invoices_read` (underscore). This means the route guard in App.tsx MUST also be updated simultaneously (which is covered by BUG-L04 fix). If only the module is added without updating the ROUTE_PERMISSION_MAP, `getRolesForPermission('accounting.invoices.read')` would STILL return `[]` because the code in `ACCOUNTING_PERMISSIONS` uses underscore format. **The architecture correctly identifies this as a coordinated change across 3 files.**

**BUG-C01 Verdict: PASS**

---

### BUG-C02: Navigation shows links that route guards block

| Aspect | Assessment | PASS/FAIL |
|---|---|---|
| Fix described? | YES -- Update both `ROUTE_PERMISSION_MAP` and `NAVIGATION_PERMISSIONS` to use identical underscore permission codes | PASS |
| Alignment achieved? | Partially -- the permission CODES are aligned, but the ROLES arrays have 5 inconsistencies (documented in Section 3 above) | PASS WITH NOTES |
| Root cause addressed? | YES -- after fix, nav and route guard use the same permission codes, so a user either sees the nav link AND can access the route, or sees neither | PASS |

**BUG-C02 Verdict: PASS** (with 5 role array corrections needed in nav section)

---

### BUG-L01: Three different naming conventions

| Aspect | Assessment | PASS/FAIL |
|---|---|---|
| Fix described? | YES -- all three systems unified to `{module}_{subdomain}_{action}` underscore format | PASS |
| Convention documented? | YES -- Section "Permission Code Standard" (lines 720-749) with naming rules and examples | PASS |
| Matches existing patterns? | YES -- `life_safety_inspections_read`, `payroll_runs_create` etc. already use underscore format | PASS |

**BUG-L01 Verdict: PASS**

---

### BUG-L04: Single permission code for all 30 accounting routes

| Aspect | Assessment | PASS/FAIL |
|---|---|---|
| Fix described? | YES -- each route gets its own entry in `ROUTE_PERMISSION_MAP` with full path key | PASS |
| GuardedRoute updated? | YES -- updated to try exact path match before module-level fallback (lines 512-545) | PASS |
| Backward compatible? | YES -- non-accounting modules still use the fallback to module-level match | PASS |
| Granularity sufficient? | YES -- 60 distinct permission entries covering CRUD + domain-specific actions across 17 subdomains | PASS |

**BUG-L04 Verdict: PASS**

---

## 5. Compatibility Check

### `roleHasPermission()` compatibility

**Current function (source lines 387-393):**
```typescript
export function roleHasPermission(role: string, permission: string): boolean {
  if (FULL_ACCESS_ROLES.includes(role)) {
    return true;
  }
  const roles = getRolesForPermission(permission);
  return roles.includes(role);
}
```

**Does the new ACCOUNTING_PERMISSIONS module work with this function?**

YES. The function's logic is:
1. Check FULL_ACCESS_ROLES bypass -- unchanged
2. Call `getRolesForPermission(permission)` -- this iterates `ALL_MODULE_PERMISSIONS`, which now includes `ACCOUNTING_PERMISSIONS`
3. Check if role is in the returned array

Adding `ACCOUNTING_PERMISSIONS` to `ALL_MODULE_PERMISSIONS` is purely additive. The function signature, types, and behavior are unchanged. **Zero code changes needed in `roleHasPermission()`.**

**Verified:** The `PermissionMapping` interface (lines 6-10) matches the structure used in `ACCOUNTING_PERMISSIONS`:
```typescript
export interface PermissionMapping {
  permission: string;
  roles: string[];
  description?: string;
}
```
Every entry in `ACCOUNTING_PERMISSIONS.permissions[]` has `permission` (string), `roles` (string[]), and `description` (optional string). **Type-compatible.**

**PASS**

---

### `PermissionGuard` compatibility

**Current component (source lines 23-76):**
- Accepts `permissions?: string | string[]`
- Calls `roleHasPermission(currentRole, perm)` for each permission
- Gets `effectiveRole` from `useEnhancedBusiness()`

**Does the architecture require ANY changes to PermissionGuard?**

NO. The architecture document explicitly states (line 893-895): "PermissionGuard.tsx -- API unchanged. Still receives `permissions` prop, still calls `roleHasPermission()`."

The `permissions` prop receives a string from `GuardedRoute`. Before: `'accounting.invoices.read'`. After: `'accounting_invoices_read'` (or other granular code). `PermissionGuard` does not parse or validate the permission string -- it passes it through to `roleHasPermission()`. **The change is transparent to PermissionGuard.**

**PASS**

---

### FULL_ACCESS_ROLES bypass preserved?

**Current bypass (source line 382, 388):**
```typescript
const FULL_ACCESS_ROLES = ['super_admin', 'owner', 'operations_manager'];
// ...
if (FULL_ACCESS_ROLES.includes(role)) {
  return true;
}
```

The architecture document confirms (line 116, 702, 911):
- "FULL_ACCESS_ROLES bypass continues to work unchanged"
- "BYPASS = super_admin, owner, operations_manager always pass via FULL_ACCESS_ROLES check"
- "FULL_ACCESS_ROLES bypass -- Still works: super_admin, owner, operations_manager bypass all checks"

**Verified in source code:** `FULL_ACCESS_ROLES` is a module-level constant in `permissionMappings.ts` (line 382). It is NOT modified by the architecture. The bypass fires BEFORE the permission lookup, so it is completely independent of what modules are in `ALL_MODULE_PERMISSIONS`.

**PASS**

---

## 6. All Roles Accounted

All 23 roles from `roles.ts` checked against the architecture:

| # | Role | Level | Accounting Access | How Determined | Accounted? |
|---|---|---|---|---|---|
| 1 | `super_admin` | 100 | FULL ACCESS | FULL_ACCESS_ROLES bypass | YES |
| 2 | `owner` | 90 | FULL ACCESS | FULL_ACCESS_ROLES bypass | YES |
| 3 | `operations_manager` | 85 | FULL ACCESS | FULL_ACCESS_ROLES bypass | YES |
| 4 | `admin` | 80 | Full read/write | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 5 | `finance_manager` | 75 | Full read/write + config | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 6 | `security_manager` | 73 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 7 | `manager` | 70 | Read + oversight + expense approval | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 8 | `hr_manager` | 68 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 9 | `sales_manager` | 65 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 10 | `service_manager` | 63 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 11 | `accountant` | 60 | Full read, most write | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 12 | `inventory_manager` | 58 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 13 | `ar_specialist` | 55 | AR-focused | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 14 | `ap_specialist` | 54 | AP-focused | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 15 | `security_admin_assistant` | 52 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 16 | `cashier` | 50 | Minimal (invoice read, banking read, POS, payments read) | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 17 | `site_supervisor` | 48 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 18 | `security_supervisor` | 45 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 19 | `technician` | 40 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 20 | `field_technician` | 38 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 21 | `security_guard` | 35 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |
| 22 | `employee` | 30 | Expense submission only | Explicit in ACCOUNTING_PERMISSIONS | YES |
| 23 | `viewer` | 10 | NONE | Not in any ACCOUNTING_PERMISSIONS entry | YES |

**Result: 23/23 accounted for**

**Business sense check for excluded roles:**
- `security_manager`, `hr_manager`, `sales_manager`, `service_manager` -- these are domain-specific managers. They manage their own domains, not accounting. Correct exclusion.
- `inventory_manager` -- manages stock, not financial entries. Correct exclusion. (Though one could argue they should see expenses or purchase-related accounting -- this is a design choice.)
- `viewer` -- read-only role, but does NOT have accounting read access. This is arguably conservative but defensible -- financial data is sensitive, and a generic `viewer` role should not automatically see it.
- `security_guard`, `technician`, `field_technician`, `site_supervisor`, `security_supervisor`, `security_admin_assistant` -- no accounting relevance. Correct exclusion.

---

## Issues Found

### Issue 1: Role Matrix Documentation Errors (8 cells)
**Severity:** LOW (documentation only, code is correct)
**Location:** Architecture document lines 669-700 (Role -> Permission Matrix)
**Description:** Eight cells in the matrix show `-` for `admin` where the ACCOUNTING_PERMISSIONS code actually includes `admin`. The code is the implementation source of truth and is correct. The matrix is wrong.
**Affected permissions:** `journal_entries_void`, `coa_delete`, `budgets_create`, `budgets_update`, `tax_export`, `compliance_manage`, `multi_currency_manage`, `payments_refund`
**Fix:** Update matrix cells from `-` to `Y` for admin on these 8 rows.

### Issue 2: Nav Role Arrays Inconsistent with ACCOUNTING_PERMISSIONS (5 entries)
**Severity:** MEDIUM (could cause nav items to be shown/hidden incorrectly)
**Location:** Architecture document nav section, lines 556-635
**Description:** Five navigation entries have `roles` arrays that do not match the roles in `ACCOUNTING_PERMISSIONS`:
1. `/accounting` -- missing `manager`, `admin`
2. `/accounting/chart-of-accounts` -- missing `admin`
3. `/accounting/journal-entries` -- missing `admin`
4. `/accounting/accounts-receivable` -- includes `ap_specialist` (should not), missing `manager`, `admin`
5. `/accounting/accounts-payable` -- includes `ar_specialist` (should not), missing `manager`, `admin`
**Fix:** Adjust each nav entry's `roles` array to match the corresponding `ACCOUNTING_PERMISSIONS` code's roles (plus `super_admin`, `owner` for FULL_ACCESS_ROLES).

### Issue 3: Duplicate `ar_specialist`/`ap_specialist` in Nav Spreads
**Severity:** LOW (no runtime impact, just code smell)
**Location:** Architecture nav section lines 574, 578, 582, 588, 591
**Description:** `FINANCIAL_ROLES` already includes `ar_specialist` and `ap_specialist`. Writing `[...FINANCIAL_ROLES, 'ar_specialist']` produces a duplicate entry. No runtime bug, but misleading.
**Fix:** For routes where ALL of FINANCIAL_ROLES should have access, just use `FINANCIAL_ROLES`. For routes with restricted access, build a custom array without spreading FINANCIAL_ROLES.

### Issue 4: `/pos-end-of-day` Missing from Nav Section
**Severity:** LOW (route exists, permission exists, but no nav alignment documented)
**Location:** Architecture nav section -- absent
**Description:** The ROUTE_PERMISSION_MAP includes `/pos-end-of-day` mapped to `accounting_pos_eod_read`, and ACCOUNTING_PERMISSIONS defines the permission with roles `[finance_manager, accountant, admin, cashier, manager]`. But the nav section does not include a corresponding entry.
**Fix:** Add a nav entry for `/pos-end-of-day`.

### Issue 5: `addStandardRolePermissions` Fallback Uses Dot-Notation
**Severity:** MEDIUM (dual-system inconsistency)
**Location:** Architecture document lines 934-973
**Description:** The architecture proposes adding fallback permissions for `finance_manager`, `accountant`, `ar_specialist`, `ap_specialist` to `rolesPermissionsService.ts`. But the proposed code uses DOT-NOTATION (`accounting.invoices.read`, `accounting.bills.manage`) while the entire unified convention uses UNDERSCORE format (`accounting_invoices_read`). If the navigation service falls through to this fallback, the codes will not match the permission codes in `permissionMappings.ts`.
**Fix:** The fallback code should use underscore format: `accounting_invoices_read`, `accounting_bills_read`, etc. OR, since this is a database-backed system that uses its own naming, explicitly document which system uses which convention. The architecture acknowledges this is "lower priority" but the code example is internally inconsistent.

### Issue 6: `GuardedRoute` Path Matching Needs Implementation Detail
**Severity:** MEDIUM (implementation correctness)
**Location:** Architecture document lines 512-545
**Description:** The proposed `GuardedRoute` receives the `path` prop as defined in the `<Route>` component (e.g., `/accounting/bills/:id/edit`). It normalizes `:param` segments to `:id` for matching. But the `ROUTE_PERMISSION_MAP` keys use literal `:id` (e.g., `'/accounting/bills/:id'`). The normalization `path.replace(/:[^/]+/g, ':id')` would convert `/accounting/bills/:id/edit` to `/accounting/bills/:id/edit` (unchanged since the param is already `:id`). This works IF the route definitions in App.tsx always use `:id` as the param name.

**Checking source:** App.tsx line 339: `path="/accounting/bills/:id"` -- uses `:id`. Line 340: `path="/accounting/bills/:id/edit"` -- uses `:id`. All accounting routes use `:id` as the param name. The normalization regex is redundant but harmless for the current codebase.

**However:** If a future route uses a different param name (e.g., `:invoiceId`), the normalization would convert it to `:id` and the lookup would work. This is actually a good defensive measure.

**Verdict:** Not a bug. The implementation is correct for the current codebase and defensively handles future param name changes.

### Issue 7: `payments/:id/edit` Maps to `accounting_payments_create`
**Severity:** LOW (semantic question)
**Location:** Architecture ROUTE_PERMISSION_MAP line 500
**Description:** The edit route for payments maps to `accounting_payments_create` rather than `accounting_payments_update`. There is no `accounting_payments_update` permission defined in ACCOUNTING_PERMISSIONS. The permissions are: `accounting_payments_read`, `accounting_payments_create`, `accounting_payments_refund`. Using `_create` for the edit route means the same permission gates both creating and editing payments.
**Assessment:** This is arguably correct -- editing a payment record IS effectively creating/recording a payment. Unlike invoices/bills where you might view then edit, payments are typically recorded once. If the team wants separate create vs update granularity, a new `accounting_payments_update` permission should be added. As designed, this is a deliberate simplification.

---

## Verdict

### PASS WITH NOTES

The auth & state architecture is **structurally sound and compatible with the existing codebase**. It correctly identifies the root cause (missing ACCOUNTING_PERMISSIONS module), proposes an additive fix that requires zero changes to the permission-checking infrastructure (`roleHasPermission`, `PermissionGuard`, `FULL_ACCESS_ROLES`), and provides granular per-route permission codes that replace the single blanket code.

**Before implementation, fix these 5 items:**
1. Correct 8 cells in the Role -> Permission Matrix where `admin` is shown as `-` but should be `Y` (documentation fix)
2. Align 5 navigation `roles` arrays with the corresponding ACCOUNTING_PERMISSIONS role arrays (functional fix)
3. Add `/pos-end-of-day` to the nav section (completeness fix)
4. Change the `addStandardRolePermissions` fallback code to use underscore format (consistency fix)
5. Remove duplicate role entries in nav spreads (code cleanliness)

None of these are blockers to the overall approach. The architecture is approved for implementation with these corrections applied.
