# LVR Pilot — Permission Inventory (Accounting Domain)

*Generated: 2026-02-13*

## Three Overlapping Permission Systems

Island Biz has THREE independent permission mechanisms that operate on accounting routes. They use different naming conventions, different role sets, and make contradictory access decisions.

---

### System 1: Route Guard (`ROUTE_PERMISSION_MAP` + `PermissionGuard`)

**Source:** `src/App.tsx` lines 34-80, `src/components/permissions/PermissionGuard.tsx`

**How it works:**
1. `GuardedRoute` extracts first path segment from route (e.g., `accounting`)
2. Looks up `ROUTE_PERMISSION_MAP['accounting']` → `'accounting.invoices.read'`
3. Passes to `<PermissionGuard permissions="accounting.invoices.read">`
4. `PermissionGuard` calls `roleHasPermission(currentRole, 'accounting.invoices.read')`

**`roleHasPermission` logic** (from `permissionMappings.ts`):
```
if FULL_ACCESS_ROLES.includes(role) → return true
else → return getRolesForPermission(permission).includes(role)
```

**FULL_ACCESS_ROLES:** `['super_admin', 'owner', 'operations_manager']`

**CRITICAL:** `getRolesForPermission('accounting.invoices.read')` returns `[]` because `ALL_MODULE_PERMISSIONS` only contains `LIFE_SAFETY_PERMISSIONS` and `PAYROLL_PERMISSIONS`. No accounting permissions are defined.

**Result:** Only `super_admin`, `owner`, `operations_manager` can access ANY accounting route. All other roles — including `finance_manager`, `accountant`, `ar_specialist`, `ap_specialist` — are denied.

---

### System 2: Static Permission Mappings (`permissionMappings.ts`)

**Source:** `src/config/permissionMappings.ts`

**Modules defined:** ONLY `life_safety` and `payroll`
**Modules NOT defined:** accounting, inventory, crm, sales, service, hr, admin, security

**Permission naming convention:** Underscore-separated (e.g., `life_safety_inspections_read`)

**FULL_ACCESS_ROLES:** `['super_admin', 'owner', 'operations_manager']`

**Custom roles defined:** `life_safety_inspector`, `safety_compliance_manager`, `payroll_processor`, `hr_manager`, `field_technician`

**Impact on accounting:** Since no accounting module exists, `roleHasPermission` for any `accounting.*` permission code will always return `false` (unless role is in FULL_ACCESS_ROLES).

---

### System 3: Navigation Permissions (`navigationPermissionsService.ts`)

**Source:** `src/services/navigationPermissionsService.ts`

**Role groups:**
| Group | Roles |
|-------|-------|
| ALL_ROLES | super_admin, owner, operations_manager, finance_manager, security_manager, hr_manager, sales_manager, accountant, ar_specialist, ap_specialist, inventory_manager, cashier, security_guard, technician, employee, viewer |
| FINANCIAL_ROLES | super_admin, owner, finance_manager, accountant, ar_specialist, ap_specialist |
| MANAGER_ROLES | super_admin, owner, operations_manager, finance_manager, security_manager, hr_manager, sales_manager |

**Accounting navigation entries:**

| Path | Required Permissions | Allowed Roles |
|------|---------------------|---------------|
| `/accounting` | `financial.ar.view`, `financial.ap.view` | FINANCIAL_ROLES |
| `/accounting/chart-of-accounts` | `financial.journal_entries.view` | FINANCIAL_ROLES |
| `/accounting/journal-entries` | `financial.journal_entries.create`, `financial.journal_entries.view` | FINANCIAL_ROLES |
| `/accounting/financial-reports` | `financial.reports.view` | FINANCIAL_ROLES |
| `/accounting/accounts-receivable` | `financial.ar.view` | FINANCIAL_ROLES + ar_specialist |
| `/accounting/accounts-payable` | `financial.ap.view` | FINANCIAL_ROLES + ap_specialist |
| `/accounting/invoices` | `financial.ar.invoices.view` | FINANCIAL_ROLES + ar_specialist |
| `/accounting/expenses` | `financial.ap.view` | FINANCIAL_ROLES + ap_specialist |
| `/accounting/bank-reconciliation` | `financial.banking.view` | FINANCIAL_ROLES |
| `/accounting/tax-reporting` | `financial.tax.view` | FINANCIAL_ROLES |
| `/accounting/credit-management` | `financial.ar.credit.view` | FINANCIAL_ROLES |

**Permission naming convention:** Dot-separated with `financial.*` prefix (NOT `accounting.*`)

**Note:** Many accounting routes have NO navigation permission entry (e.g., bills, payments, budget-analysis, variance-analysis, cash-flow, fixed-assets, multi-currency, aging-reports, banking-cash, compliance-planning). These default to `allow` in navigation but are still blocked by the route guard.

---

## Bug Summary

### BUG-001 (CRITICAL): Accounting Permission Code Not Defined
- **Route guard checks:** `accounting.invoices.read`
- **permissionMappings.ts defines:** Only `life_safety_*` and `payroll_*`
- **Result:** `getRolesForPermission('accounting.invoices.read')` → `[]`
- **Impact:** `finance_manager`, `accountant`, `ar_specialist`, `ap_specialist` cannot access ANY accounting page
- **Only access:** `super_admin`, `owner`, `operations_manager` (via FULL_ACCESS_ROLES bypass)

### BUG-002 (HIGH): Navigation vs Route Guard Conflict
- **Navigation says:** `finance_manager`, `accountant`, `ar_specialist`, `ap_specialist` CAN see accounting nav items (FINANCIAL_ROLES)
- **Route guard says:** These roles CANNOT access accounting pages
- **Result:** Users see nav links they cannot access. Clicking leads to "Access Denied" page.

### BUG-003 (MEDIUM): Permission Code Naming Inconsistency
- **App.tsx:** Uses `accounting.invoices.read` (dot-notation, `accounting.*` prefix)
- **permissionMappings.ts:** Uses underscore convention (`life_safety_inspections_read`)
- **navigationPermissionsService.ts:** Uses dot-notation with `financial.*` prefix (`financial.ar.view`)
- **Three different conventions** across three systems for what should be the same domain

### BUG-004 (MEDIUM): Owner Role Structurally Absent from Explicit Permission Arrays
- **FULL_ACCESS_ROLES** includes `owner` → always bypasses
- **FINANCIAL_ROLES** includes `owner` → appears in navigation
- **permissionMappings.ts** permission arrays: `owner` never listed explicitly
- Not a functional bug (bypass works), but structurally misleading

### BUG-005 (LOW): Single Permission Code for All Accounting Routes
- **All 30 routes** map to `accounting.invoices.read` (via the `accounting` key)
- No granularity: can't grant access to expenses but not invoices, or reports but not journal entries
- A user who can view invoices can view everything in accounting (or nothing)
