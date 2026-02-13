/**
 * Accounting Navigation Configuration
 *
 * Defines all accounting navigation items with permission-checked visibility.
 * Permission codes match ACCOUNTING_ROUTE_PERMISSIONS exactly (fixes BUG-C02).
 *
 * Usage:
 *   import { ACCOUNTING_NAV_ITEMS, useAccountingNavigation } from '@/config/accountingNavigation';
 *
 *   const { visibleItems } = useAccountingNavigation();
 *   // Returns only items the current user has permission to see
 */

import { useMemo } from 'react';
import {
  BarChart3,
  BookOpen,
  Building2,
  Calculator,
  CreditCard,
  DollarSign,
  FileText,
  Globe,
  Landmark,
  LayoutDashboard,
  PieChart,
  Receipt,
  Scale,
  ScrollText,
  ShoppingCart,
  TrendingDown,
  TrendingUp,
  Users,
  Wallet,
  type LucideIcon,
} from 'lucide-react';
import { useAccountingPermission } from './accountingPermissions';
import { roleHasPermission } from '@/config/permissionMappings';
import { useEnhancedBusiness } from '@/hooks/useEnhancedBusiness';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AccountingNavItem {
  /** Display label in the navigation */
  label: string;
  /** Route path (relative to app root) */
  path: string;
  /** Lucide icon component */
  icon: LucideIcon;
  /** Permission code required to see this item (underscore format, matches ACCOUNTING_ROUTE_PERMISSIONS) */
  permission: string;
  /** Optional grouping for sidebar sections */
  group: AccountingNavGroup;
  /** Optional description shown in tooltips or expanded nav */
  description?: string;
  /** Child routes (for nested navigation) */
  children?: AccountingNavItem[];
}

export type AccountingNavGroup =
  | 'overview'
  | 'transactions'
  | 'ledger'
  | 'receivables'
  | 'payables'
  | 'banking'
  | 'reporting'
  | 'configuration';

export interface AccountingNavGroup_Meta {
  id: AccountingNavGroup;
  label: string;
  order: number;
}

// ---------------------------------------------------------------------------
// Navigation Groups
// ---------------------------------------------------------------------------

export const ACCOUNTING_NAV_GROUPS: AccountingNavGroup_Meta[] = [
  { id: 'overview', label: 'Overview', order: 0 },
  { id: 'transactions', label: 'Transactions', order: 1 },
  { id: 'receivables', label: 'Receivables', order: 2 },
  { id: 'payables', label: 'Payables', order: 3 },
  { id: 'ledger', label: 'Ledger', order: 4 },
  { id: 'banking', label: 'Banking', order: 5 },
  { id: 'reporting', label: 'Reporting & Analysis', order: 6 },
  { id: 'configuration', label: 'Configuration', order: 7 },
];

// ---------------------------------------------------------------------------
// Navigation Items
// ---------------------------------------------------------------------------

export const ACCOUNTING_NAV_ITEMS: AccountingNavItem[] = [
  // ── Overview ──────────────────────────────────────────────────────────
  {
    label: 'Financial Overview',
    path: '/accounting',
    icon: LayoutDashboard,
    permission: 'accounting_dashboard_read',
    group: 'overview',
    description: 'Dashboard with key financial metrics and recent activity',
  },

  // ── Transactions ──────────────────────────────────────────────────────
  {
    label: 'Invoices',
    path: '/accounting/invoices',
    icon: FileText,
    permission: 'accounting_invoices_read',
    group: 'transactions',
    description: 'Create and manage customer invoices',
  },
  {
    label: 'Bills',
    path: '/accounting/bills',
    icon: ScrollText,
    permission: 'accounting_bills_read',
    group: 'transactions',
    description: 'Track and manage supplier bills',
  },
  {
    label: 'Expenses',
    path: '/accounting/expenses',
    icon: Receipt,
    permission: 'accounting_expenses_read',
    group: 'transactions',
    description: 'Submit and approve business expenses',
  },
  {
    label: 'Payments',
    path: '/accounting/payments/:id',
    icon: Wallet,
    permission: 'accounting_payments_read',
    group: 'transactions',
    description: 'View and record payments',
  },

  // ── Receivables ───────────────────────────────────────────────────────
  {
    label: 'Accounts Receivable',
    path: '/accounting/accounts-receivable',
    icon: Users,
    permission: 'accounting_ar_read',
    group: 'receivables',
    description: 'Monitor outstanding customer balances',
  },
  {
    label: 'Credit Management',
    path: '/accounting/credit-management',
    icon: CreditCard,
    permission: 'accounting_credit_read',
    group: 'receivables',
    description: 'Manage customer credit limits and terms',
  },

  // ── Payables ──────────────────────────────────────────────────────────
  {
    label: 'Accounts Payable',
    path: '/accounting/accounts-payable',
    icon: ShoppingCart,
    permission: 'accounting_ap_read',
    group: 'payables',
    description: 'Monitor outstanding supplier balances',
  },

  // ── Ledger ────────────────────────────────────────────────────────────
  {
    label: 'Journal Entries',
    path: '/accounting/journal-entries',
    icon: BookOpen,
    permission: 'accounting_journal_entries_read',
    group: 'ledger',
    description: 'Create and manage general ledger entries',
  },
  {
    label: 'Chart of Accounts',
    path: '/accounting/chart-of-accounts',
    icon: Landmark,
    permission: 'accounting_coa_read',
    group: 'ledger',
    description: 'Manage the account structure',
  },

  // ── Banking ───────────────────────────────────────────────────────────
  {
    label: 'Bank Reconciliation',
    path: '/accounting/bank-reconciliation',
    icon: Scale,
    permission: 'accounting_bank_reconciliation_read',
    group: 'banking',
    description: 'Reconcile bank statements with ledger',
  },
  {
    label: 'Banking & Cash',
    path: '/accounting/banking-cash',
    icon: Building2,
    permission: 'accounting_banking_cash_read',
    group: 'banking',
    description: 'Manage bank accounts and cash positions',
  },

  // ── Reporting & Analysis ──────────────────────────────────────────────
  {
    label: 'Financial Reports',
    path: '/accounting/financial-reports',
    icon: BarChart3,
    permission: 'accounting_reports_read',
    group: 'reporting',
    description: 'Income statement, balance sheet, and more',
  },
  {
    label: 'Budget Analysis',
    path: '/accounting/budget-analysis',
    icon: PieChart,
    permission: 'accounting_budgets_read',
    group: 'reporting',
    description: 'Budget vs actual comparison',
  },
  {
    label: 'Variance Analysis',
    path: '/accounting/variance-analysis',
    icon: TrendingDown,
    permission: 'accounting_variance_read',
    group: 'reporting',
    description: 'Analyze budget variances and trends',
  },
  {
    label: 'Cash Flow',
    path: '/accounting/cash-flow',
    icon: TrendingUp,
    permission: 'accounting_cash_flow_read',
    group: 'reporting',
    description: 'Cash flow statements and forecasting',
  },
  {
    label: 'Aging Reports',
    path: '/accounting/aging-reports',
    icon: Calculator,
    permission: 'accounting_aging_read',
    group: 'reporting',
    description: 'AR and AP aging analysis',
  },
  {
    label: 'Tax Reporting',
    path: '/accounting/tax-reporting',
    icon: Receipt,
    permission: 'accounting_tax_read',
    group: 'reporting',
    description: 'VAT reports and tax compliance',
  },

  // ── Configuration ─────────────────────────────────────────────────────
  {
    label: 'Fixed Assets',
    path: '/accounting/fixed-assets',
    icon: Building2,
    permission: 'accounting_fixed_assets_read',
    group: 'configuration',
    description: 'Track assets and depreciation schedules',
  },
  {
    label: 'Multi-Currency',
    path: '/accounting/multi-currency',
    icon: Globe,
    permission: 'accounting_multi_currency_read',
    group: 'configuration',
    description: 'Exchange rates and currency settings',
  },
  {
    label: 'Compliance & Planning',
    path: '/accounting/compliance-planning',
    icon: Scale,
    permission: 'accounting_compliance_read',
    group: 'configuration',
    description: 'Regulatory compliance and planning tools',
  },
];

// ---------------------------------------------------------------------------
// Navigation Permissions Map (for navigationPermissionsService.ts alignment)
// ---------------------------------------------------------------------------

/**
 * Drop-in replacement for the accounting entries in NAVIGATION_PERMISSIONS.
 * All codes use underscore format matching permissionMappings.ts.
 */
export const ACCOUNTING_NAVIGATION_PERMISSIONS: Record<
  string,
  { requiredPermissions: string[]; roles: string[] }
> = {
  '/accounting': {
    requiredPermissions: ['accounting_dashboard_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin', 'manager'],
  },
  '/accounting/invoices': {
    requiredPermissions: ['accounting_invoices_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'admin', 'manager', 'cashier'],
  },
  '/accounting/bills': {
    requiredPermissions: ['accounting_bills_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager'],
  },
  '/accounting/expenses': {
    requiredPermissions: ['accounting_expenses_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager', 'employee'],
  },
  '/accounting/accounts-receivable': {
    requiredPermissions: ['accounting_ar_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'admin', 'manager'],
  },
  '/accounting/accounts-payable': {
    requiredPermissions: ['accounting_ap_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ap_specialist', 'admin', 'manager'],
  },
  '/accounting/journal-entries': {
    requiredPermissions: ['accounting_journal_entries_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
  '/accounting/chart-of-accounts': {
    requiredPermissions: ['accounting_coa_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
  },
  '/accounting/financial-reports': {
    requiredPermissions: ['accounting_reports_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin', 'manager'],
  },
  '/accounting/bank-reconciliation': {
    requiredPermissions: ['accounting_bank_reconciliation_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
  '/accounting/banking-cash': {
    requiredPermissions: ['accounting_banking_cash_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin', 'cashier'],
  },
  '/accounting/tax-reporting': {
    requiredPermissions: ['accounting_tax_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
  '/accounting/credit-management': {
    requiredPermissions: ['accounting_credit_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'admin'],
  },
  '/accounting/budget-analysis': {
    requiredPermissions: ['accounting_budgets_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin', 'manager'],
  },
  '/accounting/variance-analysis': {
    requiredPermissions: ['accounting_variance_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin', 'manager'],
  },
  '/accounting/cash-flow': {
    requiredPermissions: ['accounting_cash_flow_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin', 'manager'],
  },
  '/accounting/fixed-assets': {
    requiredPermissions: ['accounting_fixed_assets_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
  '/accounting/multi-currency': {
    requiredPermissions: ['accounting_multi_currency_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
  '/accounting/aging-reports': {
    requiredPermissions: ['accounting_aging_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'ar_specialist', 'ap_specialist', 'admin'],
  },
  '/accounting/compliance-planning': {
    requiredPermissions: ['accounting_compliance_read'],
    roles: ['super_admin', 'owner', 'finance_manager', 'accountant', 'admin'],
  },
};

// ---------------------------------------------------------------------------
// Hook: useAccountingNavigation
// ---------------------------------------------------------------------------

/**
 * Returns only the accounting navigation items the current user has permission to access.
 * Groups items by their nav group and filters out groups with no visible items.
 */
export function useAccountingNavigation(): {
  visibleItems: AccountingNavItem[];
  groupedItems: { group: AccountingNavGroup_Meta; items: AccountingNavItem[] }[];
} {
  const { effectiveRole } = useEnhancedBusiness();

  return useMemo(() => {
    if (!effectiveRole) {
      return { visibleItems: [], groupedItems: [] };
    }

    const visibleItems = ACCOUNTING_NAV_ITEMS.filter((item) =>
      roleHasPermission(effectiveRole, item.permission)
    );

    const groupMap = new Map<AccountingNavGroup, AccountingNavItem[]>();
    for (const item of visibleItems) {
      const existing = groupMap.get(item.group) ?? [];
      existing.push(item);
      groupMap.set(item.group, existing);
    }

    const groupedItems = ACCOUNTING_NAV_GROUPS
      .filter((g) => groupMap.has(g.id))
      .map((g) => ({
        group: g,
        items: groupMap.get(g.id)!,
      }));

    return { visibleItems, groupedItems };
  }, [effectiveRole]);
}
