/**
 * Accounting Module Permission Mappings
 *
 * Unified permission system for the accounting domain.
 * Follows the same ModulePermissions interface as LIFE_SAFETY_PERMISSIONS and PAYROLL_PERMISSIONS.
 *
 * Fixes:
 *   BUG-C01: Adds accounting to ALL_MODULE_PERMISSIONS
 *   BUG-C02: Uses underscore-format codes matching permissionMappings.ts convention
 *   BUG-L01: Consistent naming convention across route guard, nav, and permission mappings
 *   BUG-L04: Granular per-route permission codes (replaces single blanket code)
 *
 * Integration:
 *   1. Add ACCOUNTING_PERMISSIONS to ALL_MODULE_PERMISSIONS in permissionMappings.ts
 *   2. Update ROUTE_PERMISSION_MAP in App.tsx to use ACCOUNTING_ROUTE_PERMISSIONS
 *   3. Update NAVIGATION_PERMISSIONS in navigationPermissionsService.ts to use same codes
 */

// ---------------------------------------------------------------------------
// Types (mirrors the existing ModulePermissions interface from permissionMappings.ts)
// ---------------------------------------------------------------------------

export interface PermissionMapping {
  permission: string;
  roles: string[];
  description: string;
}

export interface ModulePermissions {
  module: string;
  description: string;
  permissions: PermissionMapping[];
}

// ---------------------------------------------------------------------------
// Role constants
// ---------------------------------------------------------------------------

/** Roles that bypass all permission checks (handled by roleHasPermission FULL_ACCESS_ROLES) */
// super_admin, owner, operations_manager are NOT listed here because they bypass automatically.

/** All financial roles that should see accounting navigation */
const ALL_FINANCIAL = ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin', 'manager'] as const;

/** Core financial roles (no specialists, no manager) */
const CORE_FINANCIAL = ['finance_manager', 'accountant', 'admin'] as const;

/** AR-focused roles */
const AR_ROLES = ['finance_manager', 'accountant', 'ar_specialist', 'admin'] as const;

/** AP-focused roles */
const AP_ROLES = ['finance_manager', 'accountant', 'ap_specialist', 'admin'] as const;

/** Delete / void / destructive - most restricted */
const DESTRUCTIVE_ROLES = ['finance_manager', 'admin'] as const;

// ---------------------------------------------------------------------------
// ACCOUNTING_PERMISSIONS
// ---------------------------------------------------------------------------

export const ACCOUNTING_PERMISSIONS: ModulePermissions = {
  module: 'accounting',
  description: 'Accounting and Financial Management',
  permissions: [
    // ── Overview / Dashboard ────────────────────────────────────────────
    {
      permission: 'accounting_dashboard_read',
      roles: [...ALL_FINANCIAL],
      description: 'View accounting dashboard and overview',
    },

    // ── Invoices (AR) ───────────────────────────────────────────────────
    {
      permission: 'accounting_invoices_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin', 'manager', 'cashier'],
      description: 'View invoices',
    },
    {
      permission: 'accounting_invoices_create',
      roles: [...AR_ROLES],
      description: 'Create new invoices',
    },
    {
      permission: 'accounting_invoices_update',
      roles: [...AR_ROLES],
      description: 'Update existing invoices',
    },
    {
      permission: 'accounting_invoices_delete',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Delete invoices',
    },

    // ── Bills (AP) ──────────────────────────────────────────────────────
    {
      permission: 'accounting_bills_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager'],
      description: 'View bills',
    },
    {
      permission: 'accounting_bills_create',
      roles: [...AP_ROLES],
      description: 'Create new bills',
    },
    {
      permission: 'accounting_bills_update',
      roles: [...AP_ROLES],
      description: 'Update existing bills',
    },
    {
      permission: 'accounting_bills_delete',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Delete bills',
    },

    // ── Expenses ────────────────────────────────────────────────────────
    {
      permission: 'accounting_expenses_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager', 'employee'],
      description: 'View expenses',
    },
    {
      permission: 'accounting_expenses_create',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager', 'employee'],
      description: 'Submit expenses',
    },
    {
      permission: 'accounting_expenses_update',
      roles: [...AP_ROLES],
      description: 'Update expense records',
    },
    {
      permission: 'accounting_expenses_delete',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Delete expense records',
    },
    {
      permission: 'accounting_expenses_approve',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'Approve submitted expenses',
    },

    // ── Accounts Receivable ─────────────────────────────────────────────
    {
      permission: 'accounting_ar_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'admin', 'manager'],
      description: 'View accounts receivable',
    },
    {
      permission: 'accounting_ar_manage',
      roles: [...AR_ROLES],
      description: 'Manage accounts receivable records',
    },

    // ── Accounts Payable ────────────────────────────────────────────────
    {
      permission: 'accounting_ap_read',
      roles: ['finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager'],
      description: 'View accounts payable',
    },
    {
      permission: 'accounting_ap_manage',
      roles: [...AP_ROLES],
      description: 'Manage accounts payable records',
    },

    // ── Journal Entries ─────────────────────────────────────────────────
    {
      permission: 'accounting_journal_entries_read',
      roles: [...CORE_FINANCIAL],
      description: 'View journal entries',
    },
    {
      permission: 'accounting_journal_entries_create',
      roles: [...CORE_FINANCIAL],
      description: 'Create journal entries',
    },
    {
      permission: 'accounting_journal_entries_update',
      roles: [...CORE_FINANCIAL],
      description: 'Update draft journal entries',
    },
    {
      permission: 'accounting_journal_entries_delete',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Delete draft journal entries',
    },
    {
      permission: 'accounting_journal_entries_post',
      roles: [...CORE_FINANCIAL],
      description: 'Post journal entries to the general ledger',
    },
    {
      permission: 'accounting_journal_entries_void',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Void/reverse posted journal entries',
    },

    // ── Chart of Accounts ───────────────────────────────────────────────
    {
      permission: 'accounting_coa_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'View chart of accounts',
    },
    {
      permission: 'accounting_coa_create',
      roles: [...CORE_FINANCIAL],
      description: 'Create new accounts',
    },
    {
      permission: 'accounting_coa_update',
      roles: [...CORE_FINANCIAL],
      description: 'Update account details',
    },
    {
      permission: 'accounting_coa_delete',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Delete non-system accounts',
    },

    // ── Financial Reports ───────────────────────────────────────────────
    {
      permission: 'accounting_reports_read',
      roles: [...ALL_FINANCIAL],
      description: 'View financial reports',
    },
    {
      permission: 'accounting_reports_export',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Export financial reports',
    },

    // ── Bank Reconciliation ─────────────────────────────────────────────
    {
      permission: 'accounting_bank_reconciliation_read',
      roles: [...CORE_FINANCIAL],
      description: 'View bank reconciliation',
    },
    {
      permission: 'accounting_bank_reconciliation_create',
      roles: [...CORE_FINANCIAL],
      description: 'Perform bank reconciliation',
    },

    // ── Banking & Cash ──────────────────────────────────────────────────
    {
      permission: 'accounting_banking_cash_read',
      roles: ['finance_manager', 'accountant', 'admin', 'cashier'],
      description: 'View banking and cash management',
    },
    {
      permission: 'accounting_banking_cash_manage',
      roles: [...CORE_FINANCIAL],
      description: 'Manage banking and cash records',
    },

    // ── Tax Reporting ───────────────────────────────────────────────────
    {
      permission: 'accounting_tax_read',
      roles: [...CORE_FINANCIAL],
      description: 'View tax reports',
    },
    {
      permission: 'accounting_tax_export',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Export tax filings',
    },

    // ── Credit Management ───────────────────────────────────────────────
    {
      permission: 'accounting_credit_read',
      roles: [...AR_ROLES],
      description: 'View credit management',
    },
    {
      permission: 'accounting_credit_update',
      roles: [...AR_ROLES],
      description: 'Update credit limits and terms',
    },

    // ── Budget Analysis ─────────────────────────────────────────────────
    {
      permission: 'accounting_budgets_read',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'View budgets and budget analysis',
    },
    {
      permission: 'accounting_budgets_create',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Create and manage budgets',
    },
    {
      permission: 'accounting_budgets_update',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Update budget allocations',
    },

    // ── Variance Analysis ───────────────────────────────────────────────
    {
      permission: 'accounting_variance_read',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'View variance analysis reports',
    },

    // ── Cash Flow ───────────────────────────────────────────────────────
    {
      permission: 'accounting_cash_flow_read',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'View cash flow statements and forecasts',
    },

    // ── Fixed Assets ────────────────────────────────────────────────────
    {
      permission: 'accounting_fixed_assets_read',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'View fixed assets and depreciation',
    },
    {
      permission: 'accounting_fixed_assets_manage',
      roles: ['finance_manager', 'accountant', 'admin'],
      description: 'Manage fixed asset records',
    },

    // ── Multi-Currency ──────────────────────────────────────────────────
    {
      permission: 'accounting_multi_currency_read',
      roles: [...CORE_FINANCIAL],
      description: 'View multi-currency settings and conversions',
    },
    {
      permission: 'accounting_multi_currency_manage',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Manage exchange rates and currency settings',
    },

    // ── Aging Reports ───────────────────────────────────────────────────
    {
      permission: 'accounting_aging_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'View aging reports (AR and AP)',
    },

    // ── POS End of Day ──────────────────────────────────────────────────
    {
      permission: 'accounting_pos_eod_read',
      roles: ['finance_manager', 'accountant', 'admin', 'manager', 'cashier'],
      description: 'View POS end-of-day reconciliation',
    },
    {
      permission: 'accounting_pos_eod_manage',
      roles: ['finance_manager', 'accountant', 'admin', 'manager'],
      description: 'Manage POS end-of-day closing',
    },

    // ── Compliance & Planning ───────────────────────────────────────────
    {
      permission: 'accounting_compliance_read',
      roles: [...CORE_FINANCIAL],
      description: 'View compliance and planning reports',
    },
    {
      permission: 'accounting_compliance_manage',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Manage compliance requirements',
    },

    // ── Payments ────────────────────────────────────────────────────────
    {
      permission: 'accounting_payments_read',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin', 'cashier'],
      description: 'View payment records',
    },
    {
      permission: 'accounting_payments_create',
      roles: ['finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
      description: 'Record payments',
    },
    {
      permission: 'accounting_payments_refund',
      roles: [...DESTRUCTIVE_ROLES],
      description: 'Process refunds',
    },
  ],
};

// ---------------------------------------------------------------------------
// Route -> Permission Mapping
// ---------------------------------------------------------------------------

/**
 * Maps each accounting route path to the permission code required for access.
 * Used by the updated GuardedRoute in App.tsx.
 *
 * Keys use full path format ('/accounting/invoices') for granular matching.
 * The GuardedRoute should try exact match first, then fall back to module-level.
 */
export const ACCOUNTING_ROUTE_PERMISSIONS: Record<string, string> = {
  // Dashboard / Overview
  '/accounting': 'accounting_dashboard_read',

  // Invoices (AR)
  '/accounting/invoices': 'accounting_invoices_read',
  '/accounting/invoices/:id': 'accounting_invoices_read',
  '/accounting/invoices/:id/edit': 'accounting_invoices_update',

  // Bills (AP)
  '/accounting/bills': 'accounting_bills_read',
  '/accounting/bills/:id': 'accounting_bills_read',
  '/accounting/bills/:id/edit': 'accounting_bills_update',

  // Expenses
  '/accounting/expenses': 'accounting_expenses_read',
  '/accounting/expenses/:id': 'accounting_expenses_read',
  '/accounting/expenses/:id/edit': 'accounting_expenses_update',

  // AR / AP
  '/accounting/accounts-receivable': 'accounting_ar_read',
  '/accounting/accounts-payable': 'accounting_ap_read',

  // Journal Entries
  '/accounting/journal-entries': 'accounting_journal_entries_read',
  '/accounting/journal-entries/:id': 'accounting_journal_entries_read',
  '/accounting/journal-entries/:id/edit': 'accounting_journal_entries_update',

  // Chart of Accounts
  '/accounting/chart-of-accounts': 'accounting_coa_read',

  // Reports
  '/accounting/financial-reports': 'accounting_reports_read',

  // Bank Reconciliation
  '/accounting/bank-reconciliation': 'accounting_bank_reconciliation_read',

  // Banking & Cash
  '/accounting/banking-cash': 'accounting_banking_cash_read',

  // Tax Reporting
  '/accounting/tax-reporting': 'accounting_tax_read',

  // Credit Management
  '/accounting/credit-management': 'accounting_credit_read',

  // Budgets
  '/accounting/budget-analysis': 'accounting_budgets_read',

  // Variance Analysis
  '/accounting/variance-analysis': 'accounting_variance_read',

  // Cash Flow
  '/accounting/cash-flow': 'accounting_cash_flow_read',

  // Fixed Assets
  '/accounting/fixed-assets': 'accounting_fixed_assets_read',

  // Multi-Currency
  '/accounting/multi-currency': 'accounting_multi_currency_read',

  // Aging Reports
  '/accounting/aging-reports': 'accounting_aging_read',

  // Compliance & Planning
  '/accounting/compliance-planning': 'accounting_compliance_read',

  // Payments
  '/accounting/payments/:id': 'accounting_payments_read',
  '/accounting/payments/:id/edit': 'accounting_payments_create',

  // POS End of Day (top-level path)
  '/pos-end-of-day': 'accounting_pos_eod_read',
};

// ---------------------------------------------------------------------------
// Permission Hook
// ---------------------------------------------------------------------------

/**
 * Hook to check if the current user has a specific accounting permission.
 *
 * Uses the existing roleHasPermission function from permissionMappings.ts.
 * The hook reads the current role from useEnhancedBusiness context.
 *
 * Usage:
 *   const canCreateInvoice = useAccountingPermission('accounting_invoices_create');
 *   const canDeleteBill = useAccountingPermission('accounting_bills_delete');
 */
import { useMemo } from 'react';

// These imports reference the existing app modules.
// In the actual Island Biz codebase, these paths resolve to the real implementations.
// For Loop 3 output, we define the expected import paths.
import { roleHasPermission } from '@/config/permissionMappings';
import { useEnhancedBusiness } from '@/hooks/useEnhancedBusiness';

export function useAccountingPermission(permission: string): boolean {
  const { effectiveRole } = useEnhancedBusiness();

  return useMemo(() => {
    if (!effectiveRole) return false;
    return roleHasPermission(effectiveRole, permission);
  }, [effectiveRole, permission]);
}

/**
 * Hook to check multiple accounting permissions at once.
 *
 * Usage:
 *   const perms = useAccountingPermissions([
 *     'accounting_invoices_create',
 *     'accounting_invoices_delete',
 *   ]);
 *   if (perms['accounting_invoices_create']) { ... }
 */
export function useAccountingPermissions(
  permissions: string[]
): Record<string, boolean> {
  const { effectiveRole } = useEnhancedBusiness();

  return useMemo(() => {
    if (!effectiveRole) {
      return Object.fromEntries(permissions.map((p) => [p, false]));
    }
    return Object.fromEntries(
      permissions.map((p) => [p, roleHasPermission(effectiveRole, p)])
    );
  }, [effectiveRole, permissions]);
}
