# Loop 2 — Auth & State Architecture

*Generated: 2026-02-13*
*Agent: C (Auth & State)*
*Source: Island Biz ERP — Accounting Domain*
*Files analyzed: 10 source files across config/, services/, hooks/, components/, contexts/*

---

## Current Architecture Analysis

### System 1: Route Guard (`App.tsx`)

**How it works:**

`App.tsx` defines `ROUTE_PERMISSION_MAP` (line 34), a flat `Record<string, string>` mapping top-level URL segments to a single permission code. The `GuardedRoute` component (line 290) extracts the first URL segment, looks up the permission code, and wraps the page in a `<PermissionGuard>`.

```typescript
// App.tsx:34-80
const ROUTE_PERMISSION_MAP: Record<string, string> = {
  accounting: 'accounting.invoices.read',  // ALL 30 accounting routes use this single code
  // ...other modules
};
```

`GuardedRoute` (line 290-315) strips the leading `/`, splits on `/`, takes `segments[0]` as the module key, and passes the permission string to `<PermissionGuard permissions={permission}>`.

**Where it breaks:**

Every accounting route — `/accounting`, `/accounting/invoices`, `/accounting/bills`, `/accounting/chart-of-accounts`, etc. — resolves to the same module key `"accounting"`, which maps to the single permission code `'accounting.invoices.read'`. This is then passed to `PermissionGuard`.

`PermissionGuard` (line 56-71 of `PermissionGuard.tsx`) calls `roleHasPermission(currentRole, 'accounting.invoices.read')` from `permissionMappings.ts`.

### System 2: Permission Mappings (`permissionMappings.ts`)

**How it works:**

Defines `ModulePermissions` objects for each module, each containing an array of `PermissionMapping` entries (permission code + allowed roles). The two existing modules are:

- `LIFE_SAFETY_PERMISSIONS` — 27 permission entries (lines 21-216)
- `PAYROLL_PERMISSIONS` — 17 permission entries (lines 221-335)

These are combined into `ALL_MODULE_PERMISSIONS` (line 340-343):

```typescript
export const ALL_MODULE_PERMISSIONS: ModulePermissions[] = [
  LIFE_SAFETY_PERMISSIONS,
  PAYROLL_PERMISSIONS
];
```

The critical functions:

- `getRolesForPermission(permission)` (line 365-373): Iterates `ALL_MODULE_PERMISSIONS`, finds the permission by code, returns its roles array. **Returns `[]` for any code not in the two defined modules.**

- `roleHasPermission(role, permission)` (line 387-393): Returns `true` if role is in `FULL_ACCESS_ROLES` (`super_admin`, `owner`, `operations_manager`) OR if `getRolesForPermission(permission)` includes the role.

**Where it breaks:**

`getRolesForPermission('accounting.invoices.read')` returns `[]` because no `ACCOUNTING_PERMISSIONS` module exists. Therefore `roleHasPermission('finance_manager', 'accounting.invoices.read')` returns `false`, and `roleHasPermission('accountant', 'accounting.invoices.read')` returns `false`, etc.

Only `super_admin`, `owner`, and `operations_manager` pass via the `FULL_ACCESS_ROLES` bypass (line 382, 388).

### System 3: Navigation Permissions (`navigationPermissionsService.ts`)

**How it works:**

Defines role group constants and a `NAVIGATION_PERMISSIONS` map from URL paths to `{ requiredPermissions, roles }`.

```typescript
// Line 33
const FINANCIAL_ROLES = ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist'];
```

For accounting routes (lines 142-185), it uses:
- `financial.*` permission codes (e.g., `financial.ar.view`, `financial.ap.view`, `financial.journal_entries.view`)
- `FINANCIAL_ROLES` as the allowed role list

The `hasNavigationAccess` method (line 404-495) checks permissions via `rolesPermissionsService.checkUserPermission()`, which queries the **database** `permissions` table — a completely separate permission source from `permissionMappings.ts`.

**Where it breaks:**

The navigation service uses `financial.*` codes and allows `FINANCIAL_ROLES`. But the route guard uses `accounting.invoices.read` from the static `permissionMappings.ts`. The result: users in `FINANCIAL_ROLES` see the nav links (granted by navigation permissions) but hit "Access Denied" when they click them (denied by route guard).

### The Contradiction

Three systems, three different permission sources, three different naming conventions:

| System | Permission Code Format | Source of Truth | Accounting Roles Allowed |
|--------|----------------------|-----------------|--------------------------|
| Route Guard (`App.tsx`) | `accounting.invoices.read` | `permissionMappings.ts` static map | Only FULL_ACCESS_ROLES (3 roles) |
| Permission Mappings (`permissionMappings.ts`) | `life_safety_*`, `payroll_*` (underscore) | Static TypeScript arrays | N/A (no accounting module exists) |
| Navigation Permissions (`navigationPermissionsService.ts`) | `financial.ar.view`, `financial.ap.view` (dot-notation) | Database `permissions` table via RPC | FINANCIAL_ROLES (6 roles) |

**The root cause is threefold:**
1. No `ACCOUNTING_PERMISSIONS` module exists in `permissionMappings.ts`
2. Route guard uses a single blanket permission code for all 30 routes
3. Navigation permissions use different codes (`financial.*`) than the route guard (`accounting.*`)

### Additional Discovery: `rolesPermissionsService.ts` Fallback Permissions

The `addStandardRolePermissions` method (line 636-703) adds hardcoded permission codes as fallbacks. It includes accounting permissions like `accounting.invoices.read`, `accounting.bills.manage`, etc. However, this method is only used when loading role permissions from the database (for `NavigationPermissionsService`), **not** by `PermissionGuard`, which calls `roleHasPermission` from `permissionMappings.ts` directly.

The fallback only fires for `super_admin`, `admin`, `manager`, `user`, and `viewer` — it does NOT have cases for `finance_manager`, `accountant`, `ar_specialist`, or `ap_specialist`. This means even the database-backed permission system has gaps for accounting-specific roles.

---

## Target: Unified Permission System

### Design Principles

1. **Single source of truth**: `permissionMappings.ts` defines all module permissions and role mappings
2. **Granular per-route codes**: Each accounting sub-domain gets its own CRUD permission set
3. **Consistent naming**: All use underscore format (matching existing `life_safety_*` and `payroll_*` conventions)
4. **Navigation alignment**: Navigation permission codes must match route guard codes exactly
5. **Backward compatibility**: `FULL_ACCESS_ROLES` bypass continues to work unchanged; `PermissionGuard` API unchanged

### ACCOUNTING_PERMISSIONS Module

```typescript
/**
 * Accounting Module Permission Mappings
 */
export const ACCOUNTING_PERMISSIONS: ModulePermissions = {
  module: 'accounting',
  description: 'Accounting and Financial Management',
  permissions: [
    // ── Overview / Dashboard ──────────────────────────────────────────
    {
      permission: 'accounting_dashboard_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'manager', 'admin'],
      description: 'View accounting dashboard and overview'
    },

    // ── Invoices (AR) ─────────────────────────────────────────────────
    {
      permission: 'accounting_invoices_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin', 'cashier'],
      description: 'View invoices'
    },
    {
      permission: 'accounting_invoices_create',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin'],
      description: 'Create new invoices'
    },
    {
      permission: 'accounting_invoices_update',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin'],
      description: 'Update existing invoices'
    },
    {
      permission: 'accounting_invoices_delete',
      roles: ['finance_manager', 'admin'],
      description: 'Delete invoices'
    },

    // ── Bills (AP) ────────────────────────────────────────────────────
    {
      permission: 'accounting_bills_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin'],
      description: 'View bills'
    },
    {
      permission: 'accounting_bills_create',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin'],
      description: 'Create new bills'
    },
    {
      permission: 'accounting_bills_update',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin'],
      description: 'Update existing bills'
    },
    {
      permission: 'accounting_bills_delete',
      roles: ['finance_manager', 'admin'],
      description: 'Delete bills'
    },

    // ── Expenses ──────────────────────────────────────────────────────
    {
      permission: 'accounting_expenses_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin', 'employee'],
      description: 'View expenses'
    },
    {
      permission: 'accounting_expenses_create',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin', 'employee'],
      description: 'Submit expenses'
    },
    {
      permission: 'accounting_expenses_update',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin'],
      description: 'Update expense records'
    },
    {
      permission: 'accounting_expenses_delete',
      roles: ['finance_manager', 'admin'],
      description: 'Delete expense records'
    },
    {
      permission: 'accounting_expenses_approve',
      roles: ['finance_manager', 'accountant', 'manager', 'admin'],
      description: 'Approve submitted expenses'
    },

    // ── Accounts Receivable ───────────────────────────────────────────
    {
      permission: 'accounting_ar_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin'],
      description: 'View accounts receivable'
    },
    {
      permission: 'accounting_ar_manage',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin'],
      description: 'Manage accounts receivable records'
    },

    // ── Accounts Payable ──────────────────────────────────────────────
    {
      permission: 'accounting_ap_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'manager', 'admin'],
      description: 'View accounts payable'
    },
    {
      permission: 'accounting_ap_manage',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin'],
      description: 'Manage accounts payable records'
    },

    // ── Journal Entries ───────────────────────────────────────────────
    {
      permission: 'accounting_journal_entries_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View journal entries'
    },
    {
      permission: 'accounting_journal_entries_create',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Create journal entries'
    },
    {
      permission: 'accounting_journal_entries_update',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Update draft journal entries'
    },
    {
      permission: 'accounting_journal_entries_delete',
      roles: ['finance_manager', 'admin'],
      description: 'Delete draft journal entries'
    },
    {
      permission: 'accounting_journal_entries_post',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Post journal entries to the general ledger'
    },
    {
      permission: 'accounting_journal_entries_void',
      roles: ['finance_manager', 'admin'],
      description: 'Void/reverse posted journal entries'
    },

    // ── Chart of Accounts ─────────────────────────────────────────────
    {
      permission: 'accounting_coa_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'View chart of accounts'
    },
    {
      permission: 'accounting_coa_create',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Create new accounts'
    },
    {
      permission: 'accounting_coa_update',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Update account details'
    },
    {
      permission: 'accounting_coa_delete',
      roles: ['finance_manager', 'admin'],
      description: 'Delete non-system accounts'
    },

    // ── Financial Reports ─────────────────────────────────────────────
    {
      permission: 'accounting_reports_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'manager', 'admin'],
      description: 'View financial reports'
    },
    {
      permission: 'accounting_reports_export',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Export financial reports'
    },

    // ── Bank Reconciliation ───────────────────────────────────────────
    {
      permission: 'accounting_bank_reconciliation_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View bank reconciliation'
    },
    {
      permission: 'accounting_bank_reconciliation_create',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Perform bank reconciliation'
    },

    // ── Banking & Cash ────────────────────────────────────────────────
    {
      permission: 'accounting_banking_cash_read',
      roles: ['finance_manager', 'accountant', 'admin', 'cashier'],
      description: 'View banking and cash management'
    },
    {
      permission: 'accounting_banking_cash_manage',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Manage banking and cash records'
    },

    // ── Tax Reporting ─────────────────────────────────────────────────
    {
      permission: 'accounting_tax_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View tax reports'
    },
    {
      permission: 'accounting_tax_export',
      roles: ['finance_manager', 'admin'],
      description: 'Export tax filings'
    },

    // ── Credit Management ─────────────────────────────────────────────
    {
      permission: 'accounting_credit_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin'],
      description: 'View credit management'
    },
    {
      permission: 'accounting_credit_update',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin'],
      description: 'Update credit limits and terms'
    },

    // ── Budget Analysis ───────────────────────────────────────────────
    {
      permission: 'accounting_budgets_read',
      roles: ['finance_manager', 'accountant', 'manager', 'admin'],
      description: 'View budgets and budget analysis'
    },
    {
      permission: 'accounting_budgets_create',
      roles: ['finance_manager', 'admin'],
      description: 'Create and manage budgets'
    },
    {
      permission: 'accounting_budgets_update',
      roles: ['finance_manager', 'admin'],
      description: 'Update budget allocations'
    },

    // ── Variance Analysis ─────────────────────────────────────────────
    {
      permission: 'accounting_variance_read',
      roles: ['finance_manager', 'accountant', 'manager', 'admin'],
      description: 'View variance analysis reports'
    },

    // ── Cash Flow ─────────────────────────────────────────────────────
    {
      permission: 'accounting_cash_flow_read',
      roles: ['finance_manager', 'accountant', 'manager', 'admin'],
      description: 'View cash flow statements and forecasts'
    },

    // ── Fixed Assets ──────────────────────────────────────────────────
    {
      permission: 'accounting_fixed_assets_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View fixed assets and depreciation'
    },
    {
      permission: 'accounting_fixed_assets_manage',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Manage fixed asset records'
    },

    // ── Multi-Currency ────────────────────────────────────────────────
    {
      permission: 'accounting_multi_currency_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View multi-currency settings and conversions'
    },
    {
      permission: 'accounting_multi_currency_manage',
      roles: ['finance_manager', 'admin'],
      description: 'Manage exchange rates and currency settings'
    },

    // ── Aging Reports ─────────────────────────────────────────────────
    {
      permission: 'accounting_aging_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'View aging reports (AR and AP)'
    },

    // ── POS End of Day ────────────────────────────────────────────────
    {
      permission: 'accounting_pos_eod_read',
      roles: ['finance_manager', 'accountant', 'admin', 'cashier', 'manager'],
      description: 'View POS end-of-day reconciliation'
    },
    {
      permission: 'accounting_pos_eod_manage',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'Manage POS end-of-day closing'
    },

    // ── Compliance & Planning ─────────────────────────────────────────
    {
      permission: 'accounting_compliance_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View compliance and planning reports'
    },
    {
      permission: 'accounting_compliance_manage',
      roles: ['finance_manager', 'admin'],
      description: 'Manage compliance requirements'
    },

    // ── Payments ──────────────────────────────────────────────────────
    {
      permission: 'accounting_payments_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin', 'cashier'],
      description: 'View payment records'
    },
    {
      permission: 'accounting_payments_create',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'Record payments'
    },
    {
      permission: 'accounting_payments_refund',
      roles: ['finance_manager', 'admin'],
      description: 'Process refunds'
    },
  ]
};
```

**Integration point**: Add to `ALL_MODULE_PERMISSIONS` (line 340):

```typescript
export const ALL_MODULE_PERMISSIONS: ModulePermissions[] = [
  LIFE_SAFETY_PERMISSIONS,
  PAYROLL_PERMISSIONS,
  ACCOUNTING_PERMISSIONS   // <-- ADD THIS
];
```

This immediately makes all `accounting_*` permission codes resolvable by `getRolesForPermission()` and `roleHasPermission()`.

### Route -> Permission Mapping

Replace the single `accounting: 'accounting.invoices.read'` entry in `ROUTE_PERMISSION_MAP` with a per-route map. Since `GuardedRoute` currently extracts only the top-level module key, we need to update it to support deeper path matching.

**Updated `ROUTE_PERMISSION_MAP`** (replaces the single `accounting` entry):

```typescript
const ROUTE_PERMISSION_MAP: Record<string, string> = {
  // ── Accounting / Financial (GRANULAR) ─────────────────────────────
  '/accounting':                           'accounting_dashboard_read',
  '/accounting/invoices':                  'accounting_invoices_read',
  '/accounting/invoices/:id':              'accounting_invoices_read',
  '/accounting/invoices/:id/edit':         'accounting_invoices_update',
  '/accounting/bills':                     'accounting_bills_read',
  '/accounting/bills/:id':                 'accounting_bills_read',
  '/accounting/bills/:id/edit':            'accounting_bills_update',
  '/accounting/expenses':                  'accounting_expenses_read',
  '/accounting/expenses/:id':              'accounting_expenses_read',
  '/accounting/expenses/:id/edit':         'accounting_expenses_update',
  '/accounting/accounts-receivable':       'accounting_ar_read',
  '/accounting/accounts-payable':          'accounting_ap_read',
  '/accounting/journal-entries':           'accounting_journal_entries_read',
  '/accounting/journal-entries/:id':       'accounting_journal_entries_read',
  '/accounting/journal-entries/:id/edit':  'accounting_journal_entries_update',
  '/accounting/chart-of-accounts':         'accounting_coa_read',
  '/accounting/financial-reports':         'accounting_reports_read',
  '/accounting/bank-reconciliation':       'accounting_bank_reconciliation_read',
  '/accounting/banking-cash':              'accounting_banking_cash_read',
  '/accounting/tax-reporting':             'accounting_tax_read',
  '/accounting/credit-management':         'accounting_credit_read',
  '/accounting/budget-analysis':           'accounting_budgets_read',
  '/accounting/variance-analysis':         'accounting_variance_read',
  '/accounting/cash-flow':                 'accounting_cash_flow_read',
  '/accounting/fixed-assets':              'accounting_fixed_assets_read',
  '/accounting/multi-currency':            'accounting_multi_currency_read',
  '/accounting/aging-reports':             'accounting_aging_read',
  '/accounting/compliance-planning':       'accounting_compliance_read',
  '/accounting/payments/:id':              'accounting_payments_read',
  '/accounting/payments/:id/edit':         'accounting_payments_create',

  // ── POS End of Day (top-level path) ───────────────────────────────
  '/pos-end-of-day':                       'accounting_pos_eod_read',

  // ... (other non-accounting modules remain unchanged)
};
```

**Updated `GuardedRoute`** to support full-path matching with param normalization:

```typescript
function GuardedRoute({ path, element }: { path: string; element: React.ReactNode }) {
  // Normalize path: replace :param segments with :id for matching
  const normalizedPath = path.replace(/:[^/]+/g, ':id');

  // Try exact path match first (for granular accounting permissions)
  let permission = ROUTE_PERMISSION_MAP[normalizedPath];

  // Fall back to module-level match (for non-accounting modules)
  if (!permission) {
    const segments = path.replace(/^\//, '').split('/');
    const moduleKey = segments[0];
    permission = ROUTE_PERMISSION_MAP[moduleKey];
  }

  if (!permission) {
    return <>{element}</>;
  }

  return (
    <PermissionGuard
      permissions={permission}
      fallback={
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center space-y-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Access Denied</h2>
            <p className="text-gray-600 dark:text-gray-400">You do not have permission to access this page.</p>
          </div>
        </div>
      }
    >
      {element}
    </PermissionGuard>
  );
}
```

**Note:** The `ROUTE_PERMISSION_MAP` keys now use full path format (`'/accounting/invoices'`) instead of module-only format (`'accounting'`). Non-accounting modules continue to use the module-only fallback until they are migrated.

### Navigation -> Permission Mapping

Update `navigationPermissionsService.ts` to use the same underscore-format permission codes as `permissionMappings.ts`. The `roles` arrays should also match. Here is the complete replacement for accounting entries in `NAVIGATION_PERMISSIONS`:

```typescript
// Financial Management — UNIFIED: codes match permissionMappings.ts exactly
'/accounting': {
  requiredPermissions: ['accounting_dashboard_read'],
  roles: FINANCIAL_ROLES
},
'/accounting/chart-of-accounts': {
  requiredPermissions: ['accounting_coa_read'],
  roles: FINANCIAL_ROLES
},
'/accounting/journal-entries': {
  requiredPermissions: ['accounting_journal_entries_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
'/accounting/financial-reports': {
  requiredPermissions: ['accounting_reports_read'],
  roles: FINANCIAL_ROLES
},
'/accounting/accounts-receivable': {
  requiredPermissions: ['accounting_ar_read'],
  roles: [...FINANCIAL_ROLES, 'ar_specialist']
},
'/accounting/accounts-payable': {
  requiredPermissions: ['accounting_ap_read'],
  roles: [...FINANCIAL_ROLES, 'ap_specialist']
},
'/accounting/invoices': {
  requiredPermissions: ['accounting_invoices_read'],
  roles: [...FINANCIAL_ROLES, 'ar_specialist']
},
'/accounting/bills': {
  requiredPermissions: ['accounting_bills_read'],
  roles: [...FINANCIAL_ROLES, 'ap_specialist']
},
'/accounting/expenses': {
  requiredPermissions: ['accounting_expenses_read'],
  roles: [...FINANCIAL_ROLES, 'ap_specialist']
},
'/accounting/bank-reconciliation': {
  requiredPermissions: ['accounting_bank_reconciliation_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
'/accounting/banking-cash': {
  requiredPermissions: ['accounting_banking_cash_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'cashier']
},
'/accounting/tax-reporting': {
  requiredPermissions: ['accounting_tax_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
'/accounting/credit-management': {
  requiredPermissions: ['accounting_credit_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist']
},
'/accounting/budget-analysis': {
  requiredPermissions: ['accounting_budgets_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'manager']
},
'/accounting/variance-analysis': {
  requiredPermissions: ['accounting_variance_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'manager']
},
'/accounting/cash-flow': {
  requiredPermissions: ['accounting_cash_flow_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'manager']
},
'/accounting/fixed-assets': {
  requiredPermissions: ['accounting_fixed_assets_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
'/accounting/multi-currency': {
  requiredPermissions: ['accounting_multi_currency_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
'/accounting/aging-reports': {
  requiredPermissions: ['accounting_aging_read'],
  roles: FINANCIAL_ROLES
},
'/accounting/compliance-planning': {
  requiredPermissions: ['accounting_compliance_read'],
  roles: ['super_admin', 'owner', 'finance_manager', 'accountant']
},
```

**Key alignment:** Every `requiredPermissions` value now matches exactly one code in `ACCOUNTING_PERMISSIONS.permissions[].permission`. The `roles` arrays are consistent between navigation and route guard.

### Role -> Permission Matrix

Complete matrix for all accounting permissions. Roles not listed below (security_guard, technician, field_technician, etc.) have NO accounting access.

| Permission Code | super_admin | owner | ops_manager | admin | finance_manager | accountant | ar_specialist | ap_specialist | manager | cashier | employee |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `accounting_dashboard_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | Y | - | - |
| `accounting_invoices_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | Y* | Y | - |
| `accounting_invoices_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | - | - | - |
| `accounting_invoices_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | - | - | - |
| `accounting_invoices_delete` | BYPASS | BYPASS | BYPASS | Y | Y | - | - | - | - | - | - |
| `accounting_bills_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | Y* | - | - |
| `accounting_bills_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | - | - | - |
| `accounting_bills_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | - | - | - |
| `accounting_bills_delete` | BYPASS | BYPASS | BYPASS | Y | Y | - | - | - | - | - | - |
| `accounting_expenses_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | Y | - | Y |
| `accounting_expenses_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | Y | - | Y |
| `accounting_expenses_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | - | - | - |
| `accounting_expenses_delete` | BYPASS | BYPASS | BYPASS | Y | Y | - | - | - | - | - | - |
| `accounting_expenses_approve` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | - | - |
| `accounting_ar_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | Y* | - | - |
| `accounting_ar_manage` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | - | - | - |
| `accounting_ap_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | Y* | - | - |
| `accounting_ap_manage` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | Y | - | - | - |
| `accounting_journal_entries_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_journal_entries_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_journal_entries_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_journal_entries_delete` | BYPASS | BYPASS | BYPASS | Y | Y | - | - | - | - | - | - |
| `accounting_journal_entries_post` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_journal_entries_void` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_coa_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | - | - | - |
| `accounting_coa_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_coa_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_coa_delete` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_reports_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | Y | - | - |
| `accounting_reports_export` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_bank_reconciliation_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_bank_reconciliation_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_banking_cash_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | Y | - |
| `accounting_banking_cash_manage` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_tax_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_tax_export` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_credit_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | - | - | - |
| `accounting_credit_update` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | - | - | - | - |
| `accounting_budgets_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | - | - |
| `accounting_budgets_create` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_budgets_update` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_variance_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | - | - |
| `accounting_cash_flow_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | - | - |
| `accounting_fixed_assets_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_fixed_assets_manage` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_multi_currency_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_multi_currency_manage` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_aging_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | - | - | - |
| `accounting_pos_eod_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | Y | - |
| `accounting_pos_eod_manage` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | Y | - | - |
| `accounting_compliance_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | - | - | - | - | - |
| `accounting_compliance_manage` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |
| `accounting_payments_read` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | - | Y | - |
| `accounting_payments_create` | BYPASS | BYPASS | BYPASS | Y | Y | Y | Y | Y | - | - | - |
| `accounting_payments_refund` | BYPASS | BYPASS | BYPASS | - | Y | - | - | - | - | - | - |

**BYPASS** = `super_admin`, `owner`, `operations_manager` always pass via `FULL_ACCESS_ROLES` check in `roleHasPermission()`. No explicit role entry needed.

**Y*** = `manager` has read-only access to AR/AP overview and invoices/bills lists. Cannot create, update, or delete.

### Role Summary

| Role | Access Level | Primary Accounting Scope |
|------|-------------|--------------------------|
| `finance_manager` | Full read/write | All accounting features including configuration, budgets, tax export, compliance, void/reverse |
| `accountant` | Full read, most write | All accounting features except budget management, tax export, compliance management, void journal entries |
| `ar_specialist` | AR-focused | Invoices, accounts receivable, credit management, payments, aging reports, chart of accounts (read) |
| `ap_specialist` | AP-focused | Bills, expenses, accounts payable, payments, aging reports, chart of accounts (read) |
| `manager` | Read + oversight | Dashboard, reports, budget/variance/cash-flow read, expense approval, POS end-of-day |
| `admin` | Full read/write | Same as finance_manager (system admin has full access) |
| `cashier` | Minimal | Invoice read, banking/cash read, POS end-of-day, payment read |
| `employee` | Expense submission only | Submit and view own expenses |

---

## Permission Code Standard

### Naming Convention

```
{module}_{subdomain}_{action}
```

- **module**: Always `accounting` for this domain (matches `ModulePermissions.module`)
- **subdomain**: The entity/feature area (`invoices`, `bills`, `coa`, `ar`, `ap`, `journal_entries`, etc.)
- **action**: The CRUD/domain operation (`read`, `create`, `update`, `delete`, `post`, `void`, `approve`, `export`, `manage`)

### Rules

1. All segments separated by underscores (consistent with `life_safety_*` and `payroll_*`)
2. No dot-notation in permission codes (dots are NOT used in `permissionMappings.ts` format)
3. `read` is always the minimum permission for a route (view the page)
4. `manage` is a composite permission when `create` + `update` + `delete` would be redundant
5. Domain-specific actions (`post`, `void`, `approve`, `export`, `refund`) are separate from CRUD

### Adding New Permissions

When a new accounting feature is added:

1. Add permission entries to `ACCOUNTING_PERMISSIONS.permissions[]` in `permissionMappings.ts`
2. Add the route entry to `ROUTE_PERMISSION_MAP` in `App.tsx`
3. Add the nav entry to `NAVIGATION_PERMISSIONS` in `navigationPermissionsService.ts`
4. Use the same permission code in all three places
5. Run the verification: confirm `roleHasPermission('finance_manager', 'new_code')` returns `true`

---

## Bug Fixes

### BUG-C01: Add accounting to ALL_MODULE_PERMISSIONS

**File:** `/Users/tywells/Downloads/projects/islandbiz-pro-start/src/config/permissionMappings.ts`

**Change:** Add `ACCOUNTING_PERMISSIONS` module definition (full definition above), then add it to `ALL_MODULE_PERMISSIONS`:

```typescript
// Line 340-343: Replace
export const ALL_MODULE_PERMISSIONS: ModulePermissions[] = [
  LIFE_SAFETY_PERMISSIONS,
  PAYROLL_PERMISSIONS
];

// With:
export const ALL_MODULE_PERMISSIONS: ModulePermissions[] = [
  LIFE_SAFETY_PERMISSIONS,
  PAYROLL_PERMISSIONS,
  ACCOUNTING_PERMISSIONS
];
```

**Effect:** `getRolesForPermission('accounting_invoices_read')` now returns `['finance_manager', 'accountant', 'ar_specialist', 'manager', 'admin', 'cashier']` instead of `[]`. `roleHasPermission` works correctly for all accounting roles.

### BUG-C02: Align nav + route guard permissions

**Files:**
- `App.tsx` — update `ROUTE_PERMISSION_MAP` to use underscore codes and full-path keys
- `navigationPermissionsService.ts` — update accounting entries to use same underscore codes

**Current mismatch:**
- Route guard: `accounting.invoices.read` (dot-notation, `accounting.*`)
- Nav service: `financial.ar.view` (dot-notation, `financial.*`)
- Permission mappings: `life_safety_inspections_read` (underscore format)

**After fix:**
- Route guard: `accounting_invoices_read` (underscore, matches mappings)
- Nav service: `accounting_invoices_read` (underscore, matches mappings)
- Permission mappings: `accounting_invoices_read` (underscore, source of truth)

All three systems use the same code. No translation needed.

### BUG-L01: Unify naming convention

Resolved by BUG-C02 fix. The unified convention is `{module}_{subdomain}_{action}` using underscores. This matches the existing `life_safety_*` and `payroll_*` patterns.

### BUG-L04: Replace single permission with granular codes

**File:** `App.tsx`

**Current:** All 30 accounting routes map to `accounting: 'accounting.invoices.read'` (module-level key).

**After fix:** Each route has its own entry in `ROUTE_PERMISSION_MAP` with a full path key (`'/accounting/invoices': 'accounting_invoices_read'`). The `GuardedRoute` function is updated to try exact path match before falling back to module-level match.

**Effect:** Administrators can control access at the sub-domain level. An `ar_specialist` can access invoices and receivables but not journal entries or tax reporting.

---

## State Management Architecture

### Current State Patterns (From Source Analysis)

The application uses a hybrid state management approach discovered from reading the context files and hooks:

| State Type | Current Implementation | Location |
|---|---|---|
| **Auth state** | `AuthContext` via `useAuth` hook | `src/hooks/useAuth.tsx` |
| **Business selection** | `useBusiness` hook (local state) | `src/hooks/useBusiness.tsx` |
| **Role switching** | `RoleSwitchingProvider` + `useEnhancedBusiness` | `src/hooks/useRoleSwitching.tsx`, `useEnhancedBusiness.tsx` |
| **Server data** | React Query (`QueryClient`) | `App.tsx` line 247 |
| **Theme** | `ThemeContext`, `DarkModeContext` | `src/contexts/ThemeContext.tsx`, `DarkModeContext.tsx` |
| **Onboarding** | `OnboardingContext` | `src/contexts/OnboardingContext.tsx` |
| **AI Chat** | `AIChatProvider` | `src/hooks/useAIChat.tsx` |

### Server State (React Query) -- Preserved

The app already uses `@tanstack/react-query` (line 9 of `App.tsx`) with configured defaults:

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // 5 minutes
      gcTime: 10 * 60 * 1000,      // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

All accounting data should flow through React Query hooks (e.g., `useAccountsReceivable`, `useQuery` for invoices, bills, expenses). This is already the pattern in use. No change needed.

### Auth State (AuthContext) -- Preserved

`AuthProvider` wraps the entire app (line 547 of `App.tsx`). It provides:
- `user: User | null` (Supabase auth user)
- `session: Session | null`
- `loading: boolean`
- `signIn`, `signUp`, `signOut`, `resetPassword`

The auth flow:
1. `AuthProvider` listens to `supabase.auth.onAuthStateChange`
2. `useBusiness` reads `user` from `useAuth`, fetches business memberships
3. `useEnhancedBusiness` combines business context with role switching
4. `PermissionGuard` reads `effectiveRole` from `useEnhancedBusiness`

This chain is correct. No changes needed to the auth state architecture.

### Permission State -- Fixed Path

The critical fix is in how `PermissionGuard` resolves permissions:

**Current path:** `PermissionGuard` -> `roleHasPermission()` from `permissionMappings.ts` -> `getRolesForPermission()` -> searches `ALL_MODULE_PERMISSIONS` -> returns `[]` for accounting -> DENIED

**Fixed path:** `PermissionGuard` -> `roleHasPermission()` from `permissionMappings.ts` -> `getRolesForPermission()` -> searches `ALL_MODULE_PERMISSIONS` (now includes `ACCOUNTING_PERMISSIONS`) -> returns correct roles -> ALLOWED/DENIED based on role match

`PermissionGuard` itself needs zero code changes. The fix is entirely in the data it consumes.

### UI State (local useState) -- No Changes

Form state, modal open/close, selected tabs, filters, sorting — all use local `useState` in individual components. This is the correct pattern. No global state needed for UI-only concerns.

### No New Global Contexts Needed

The accounting domain does NOT need new context providers. Rationale:

| Potential Context | Why It's Not Needed |
|---|---|
| "AccountingContext" for shared accounting state | React Query handles server state; no cross-component client state needed |
| "PermissionContext" for caching permissions | `permissionMappings.ts` is already an in-memory static map; `useEnhancedBusiness` provides the role |
| "FilterContext" for shared filters | Filters are page-specific; no cross-page filter persistence required |
| "AccountingConfigContext" for settings | Settings are server state, fetched via React Query when needed |

---

## Implementation Compatibility

### What Changes

| File | Change Type | Scope |
|---|---|---|
| `src/config/permissionMappings.ts` | Add `ACCOUNTING_PERMISSIONS`, update `ALL_MODULE_PERMISSIONS` | ~60 new permission entries |
| `src/App.tsx` | Update `ROUTE_PERMISSION_MAP` keys/values, update `GuardedRoute` | Key format change + path matching logic |
| `src/services/navigationPermissionsService.ts` | Update accounting entries in `NAVIGATION_PERMISSIONS` | Replace `financial.*` codes with `accounting_*` codes |

### What Does NOT Change

| File/Component | Why No Change |
|---|---|
| `PermissionGuard.tsx` | API unchanged. Still receives `permissions` prop, still calls `roleHasPermission()` |
| `useAuth.tsx` | Auth flow unchanged |
| `useBusiness.tsx` | Business/role resolution unchanged |
| `useEnhancedBusiness.tsx` | Role switching unchanged |
| `rolesPermissionsService.ts` | Database permission layer unaffected (separate system) |
| `roles.ts` / `constants/roles.ts` | Role definitions unchanged |
| All accounting page components | No component changes needed for permission fix |
| `FULL_ACCESS_ROLES` bypass | Still works: `super_admin`, `owner`, `operations_manager` bypass all checks |

### Migration Safety

The fix is **additive**:
- We ADD a new module to `ALL_MODULE_PERMISSIONS` (no existing modules removed)
- We ADD granular entries to `ROUTE_PERMISSION_MAP` (non-accounting modules untouched)
- We REPLACE navigation codes (only accounting routes affected)
- `FULL_ACCESS_ROLES` bypass means the 3 admin roles are unaffected regardless

### Dual-System Consideration

The app has two permission systems running in parallel:

1. **Static (`permissionMappings.ts`)**: Used by `PermissionGuard` (route guard). This is what we fix.
2. **Database (`rolesPermissionsService.ts`)**: Used by `NavigationPermissionsService` for nav filtering. Queries `permissions`, `role_permissions`, `standard_role_permissions` tables.

After this fix, the static system correctly resolves accounting permissions. The database system (`rolesPermissionsService`) is separate and may have its own `financial.*` codes in the database. The `addStandardRolePermissions` fallback in that service (line 636-703) also needs to be updated for financial roles (`finance_manager`, `accountant`, `ar_specialist`, `ap_specialist`) to include accounting permission codes. However, this is a **lower priority** because:

1. The route guard (static system) is the primary access gate -- if that works, users can access pages
2. The database system is secondary (used for nav filtering and can fall back to role arrays)
3. The nav service checks `roles` arrays as fallback when database permissions aren't found (line 459-473)

For full consistency, add a case block to `addStandardRolePermissions`:

```typescript
case 'finance_manager':
  // Full accounting access
  permissions.add('accounting.invoices.read');
  permissions.add('accounting.invoices.create');
  permissions.add('accounting.invoices.update');
  permissions.add('accounting.invoices.delete');
  permissions.add('accounting.bills.manage');
  permissions.add('accounting.journal_entries.create');
  permissions.add('accounting.journal_entries.post');
  permissions.add('accounting.journal_entries.void');
  permissions.add('accounting.reports.view');
  permissions.add('accounting.reports.export');
  // ... all accounting permissions
  break;

case 'accountant':
  // Most accounting access, no void/delete/tax export
  permissions.add('accounting.invoices.read');
  permissions.add('accounting.invoices.create');
  permissions.add('accounting.invoices.update');
  permissions.add('accounting.bills.manage');
  permissions.add('accounting.journal_entries.create');
  permissions.add('accounting.journal_entries.post');
  permissions.add('accounting.reports.view');
  permissions.add('accounting.reports.export');
  break;

case 'ar_specialist':
  permissions.add('accounting.invoices.read');
  permissions.add('accounting.invoices.create');
  permissions.add('accounting.invoices.update');
  break;

case 'ap_specialist':
  permissions.add('accounting.bills.manage');
  break;
```

This ensures the database-backed navigation system also grants accounting permissions when the database `role_permissions` table has no entries for these roles.

---

## Appendix: Complete Accounting Route Inventory

All 30 accounting routes from `App.tsx` (lines 334-403):

| # | Route | Page Component | Current Permission | Target Permission |
|---|---|---|---|---|
| 1 | `/accounting` | `FinancialManagement` | `accounting.invoices.read` | `accounting_dashboard_read` |
| 2 | `/accounting/accounts-receivable` | `AccountsReceivablePage` | `accounting.invoices.read` | `accounting_ar_read` |
| 3 | `/accounting/accounts-payable` | `AccountsPayablePage` | `accounting.invoices.read` | `accounting_ap_read` |
| 4 | `/accounting/invoices` | `InvoicesPage` | `accounting.invoices.read` | `accounting_invoices_read` |
| 5 | `/accounting/bills` | `BillsPage` | `accounting.invoices.read` | `accounting_bills_read` |
| 6 | `/accounting/bills/:id` | `BillDetailPage` | `accounting.invoices.read` | `accounting_bills_read` |
| 7 | `/accounting/bills/:id/edit` | `BillDetailPage` | `accounting.invoices.read` | `accounting_bills_update` |
| 8 | `/accounting/invoices/:id` | `InvoiceDetailPage` | `accounting.invoices.read` | `accounting_invoices_read` |
| 9 | `/accounting/invoices/:id/edit` | `InvoiceDetailPage` | `accounting.invoices.read` | `accounting_invoices_update` |
| 10 | `/accounting/expenses/:id` | `ExpenseDetailPage` | `accounting.invoices.read` | `accounting_expenses_read` |
| 11 | `/accounting/expenses/:id/edit` | `ExpenseDetailPage` | `accounting.invoices.read` | `accounting_expenses_update` |
| 12 | `/accounting/payments/:id` | `PaymentDetailPage` | `accounting.invoices.read` | `accounting_payments_read` |
| 13 | `/accounting/payments/:id/edit` | `PaymentDetailPage` | `accounting.invoices.read` | `accounting_payments_create` |
| 14 | `/accounting/journal-entries/:id` | `JournalEntryDetailPage` | `accounting.invoices.read` | `accounting_journal_entries_read` |
| 15 | `/accounting/journal-entries/:id/edit` | `JournalEntryDetailPage` | `accounting.invoices.read` | `accounting_journal_entries_update` |
| 16 | `/accounting/expenses` | `ExpensesPage` | `accounting.invoices.read` | `accounting_expenses_read` |
| 17 | `/accounting/chart-of-accounts` | `ChartOfAccountsPage` | `accounting.invoices.read` | `accounting_coa_read` |
| 18 | `/accounting/journal-entries` | `JournalEntriesPage` | `accounting.invoices.read` | `accounting_journal_entries_read` |
| 19 | `/accounting/financial-reports` | `FinancialReportsPage` | `accounting.invoices.read` | `accounting_reports_read` |
| 20 | `/accounting/bank-reconciliation` | `BankReconciliationPage` | `accounting.invoices.read` | `accounting_bank_reconciliation_read` |
| 21 | `/accounting/banking-cash` | `BankingAndCashPage` | `accounting.invoices.read` | `accounting_banking_cash_read` |
| 22 | `/accounting/compliance-planning` | `CompliancePlanningPage` | `accounting.invoices.read` | `accounting_compliance_read` |
| 23 | `/accounting/tax-reporting` | `TaxReportingPage` | `accounting.invoices.read` | `accounting_tax_read` |
| 24 | `/accounting/credit-management` | `CreditManagement` | `accounting.invoices.read` | `accounting_credit_read` |
| 25 | `/accounting/budget-analysis` | `BudgetAnalysisPage` | `accounting.invoices.read` | `accounting_budgets_read` |
| 26 | `/accounting/variance-analysis` | `VarianceAnalysisPage` | `accounting.invoices.read` | `accounting_variance_read` |
| 27 | `/accounting/cash-flow` | `CashFlowPage` | `accounting.invoices.read` | `accounting_cash_flow_read` |
| 28 | `/accounting/fixed-assets` | `FixedAssetsPage` | `accounting.invoices.read` | `accounting_fixed_assets_read` |
| 29 | `/accounting/multi-currency` | `MultiCurrencyPage` | `accounting.invoices.read` | `accounting_multi_currency_read` |
| 30 | `/accounting/aging-reports` | `AgingReportsPage` | `accounting.invoices.read` | `accounting_aging_read` |
| 31 | `/pos-end-of-day` | `POSEndOfDayPage` | `accounting.invoices.read` | `accounting_pos_eod_read` |
