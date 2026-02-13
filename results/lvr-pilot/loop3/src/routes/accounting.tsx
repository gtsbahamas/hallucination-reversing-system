/**
 * Accounting Module Route Configuration
 *
 * React Router route definitions for all 26 accounting pages.
 * All page components are lazy-loaded via React.lazy for code splitting.
 *
 * Each route is wrapped with the appropriate permission guard using
 * ACCOUNTING_ROUTE_PERMISSIONS from accountingPermissions.ts.
 *
 * Fixes:
 *   BUG-C01/C02: Permission codes use unified underscore format
 *   BUG-L04: Granular per-route permissions (not a single blanket code)
 *   BUG-L05: Edit routes (/edit suffix) detected by page components to auto-open edit modal
 */

import React, { Suspense } from 'react';
import { type RouteObject } from 'react-router-dom';
import { ACCOUNTING_ROUTE_PERMISSIONS } from '../config/accountingPermissions';

// ---------------------------------------------------------------------------
// Lazy-loaded page components
// ---------------------------------------------------------------------------

const FinancialManagement = React.lazy(
  () => import('../pages/accounting/FinancialManagement')
);
const InvoicesList = React.lazy(
  () => import('../pages/accounting/InvoicesList')
);
const InvoiceDetail = React.lazy(
  () => import('../pages/accounting/InvoiceDetail')
);
const BillsList = React.lazy(
  () => import('../pages/accounting/BillsList')
);
const BillDetail = React.lazy(
  () => import('../pages/accounting/BillDetail')
);
const ExpensesList = React.lazy(
  () => import('../pages/accounting/ExpensesList')
);
const ExpenseDetail = React.lazy(
  () => import('../pages/accounting/ExpenseDetail')
);
const PaymentDetail = React.lazy(
  () => import('../pages/accounting/PaymentDetail')
);
const JournalEntriesList = React.lazy(
  () => import('../pages/accounting/JournalEntriesList')
);
const JournalEntryDetail = React.lazy(
  () => import('../pages/accounting/JournalEntryDetail')
);
const ChartOfAccounts = React.lazy(
  () => import('../pages/accounting/ChartOfAccounts')
);
const AccountsReceivable = React.lazy(
  () => import('../pages/accounting/AccountsReceivable')
);
const AccountsPayable = React.lazy(
  () => import('../pages/accounting/AccountsPayable')
);
const FinancialReports = React.lazy(
  () => import('../pages/accounting/FinancialReports')
);
const BankReconciliation = React.lazy(
  () => import('../pages/accounting/BankReconciliation')
);
const TaxReporting = React.lazy(
  () => import('../pages/accounting/TaxReporting')
);
const BudgetAnalysis = React.lazy(
  () => import('../pages/accounting/BudgetAnalysis')
);
const CashFlow = React.lazy(
  () => import('../pages/accounting/CashFlow')
);
const VarianceAnalysis = React.lazy(
  () => import('../pages/accounting/VarianceAnalysis')
);
const FixedAssets = React.lazy(
  () => import('../pages/accounting/FixedAssets')
);
const MultiCurrency = React.lazy(
  () => import('../pages/accounting/MultiCurrency')
);
const AgingReports = React.lazy(
  () => import('../pages/accounting/AgingReports')
);
const CompliancePlanning = React.lazy(
  () => import('../pages/accounting/CompliancePlanning')
);
const BankingAndCash = React.lazy(
  () => import('../pages/accounting/BankingAndCash')
);
const CreditManagement = React.lazy(
  () => import('../pages/accounting/CreditManagement')
);
const POSEndOfDay = React.lazy(
  () => import('../pages/accounting/POSEndOfDay')
);

// ---------------------------------------------------------------------------
// Loading fallback
// ---------------------------------------------------------------------------

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Permission guard wrapper
// ---------------------------------------------------------------------------

/**
 * Wraps a lazy-loaded page component with:
 *   1. Suspense boundary for code splitting
 *   2. Permission check via GuardedRoute (expected to be provided by the host app)
 *
 * The host app's GuardedRoute component should:
 *   - Read the user's effective role from context
 *   - Check roleHasPermission(role, requiredPermission)
 *   - Render children if authorized, redirect to /unauthorized otherwise
 *
 * For the route definitions below, we attach the required permission as route
 * handle metadata so the host app's GuardedRoute can read it from useMatches().
 */
function withSuspense(Component: React.LazyExoticComponent<React.ComponentType>) {
  return (
    <Suspense fallback={<PageLoader />}>
      <Component />
    </Suspense>
  );
}

// ---------------------------------------------------------------------------
// Route definitions
// ---------------------------------------------------------------------------

/**
 * All accounting routes. Mount under the app's router as:
 *
 *   import { accountingRoutes } from '@/routes/accounting';
 *   const router = createBrowserRouter([
 *     ...otherRoutes,
 *     ...accountingRoutes,
 *   ]);
 *
 * Each route includes a `handle` object with `requiredPermission` for the
 * host app's route guard to enforce access control.
 */
export const accountingRoutes: RouteObject[] = [
  // ── Dashboard ─────────────────────────────────────────────────────────
  {
    path: '/accounting',
    element: withSuspense(FinancialManagement),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting'],
    },
  },

  // ── Invoices (AR) ─────────────────────────────────────────────────────
  {
    path: '/accounting/invoices',
    element: withSuspense(InvoicesList),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/invoices'],
    },
  },
  {
    path: '/accounting/invoices/:id',
    element: withSuspense(InvoiceDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/invoices/:id'],
    },
  },
  {
    path: '/accounting/invoices/:id/edit',
    element: withSuspense(InvoiceDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/invoices/:id/edit'],
    },
  },

  // ── Bills (AP) ────────────────────────────────────────────────────────
  {
    path: '/accounting/bills',
    element: withSuspense(BillsList),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/bills'],
    },
  },
  {
    path: '/accounting/bills/:id',
    element: withSuspense(BillDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/bills/:id'],
    },
  },
  {
    path: '/accounting/bills/:id/edit',
    element: withSuspense(BillDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/bills/:id/edit'],
    },
  },

  // ── Expenses ──────────────────────────────────────────────────────────
  {
    path: '/accounting/expenses',
    element: withSuspense(ExpensesList),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/expenses'],
    },
  },
  {
    path: '/accounting/expenses/:id',
    element: withSuspense(ExpenseDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/expenses/:id'],
    },
  },
  {
    path: '/accounting/expenses/:id/edit',
    element: withSuspense(ExpenseDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/expenses/:id/edit'],
    },
  },

  // ── Payments ──────────────────────────────────────────────────────────
  {
    path: '/accounting/payments/:id',
    element: withSuspense(PaymentDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/payments/:id'],
    },
  },

  // ── Journal Entries ───────────────────────────────────────────────────
  {
    path: '/accounting/journal-entries',
    element: withSuspense(JournalEntriesList),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/journal-entries'],
    },
  },
  {
    path: '/accounting/journal-entries/:id',
    element: withSuspense(JournalEntryDetail),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/journal-entries/:id'],
    },
  },

  // ── Chart of Accounts ─────────────────────────────────────────────────
  {
    path: '/accounting/chart-of-accounts',
    element: withSuspense(ChartOfAccounts),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/chart-of-accounts'],
    },
  },

  // ── Accounts Receivable ───────────────────────────────────────────────
  {
    path: '/accounting/accounts-receivable',
    element: withSuspense(AccountsReceivable),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/accounts-receivable'],
    },
  },

  // ── Accounts Payable ──────────────────────────────────────────────────
  {
    path: '/accounting/accounts-payable',
    element: withSuspense(AccountsPayable),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/accounts-payable'],
    },
  },

  // ── Financial Reports ─────────────────────────────────────────────────
  {
    path: '/accounting/financial-reports',
    element: withSuspense(FinancialReports),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/financial-reports'],
    },
  },

  // ── Bank Reconciliation ───────────────────────────────────────────────
  {
    path: '/accounting/bank-reconciliation',
    element: withSuspense(BankReconciliation),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/bank-reconciliation'],
    },
  },

  // ── Tax Reporting ─────────────────────────────────────────────────────
  {
    path: '/accounting/tax-reporting',
    element: withSuspense(TaxReporting),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/tax-reporting'],
    },
  },

  // ── Budget Analysis ───────────────────────────────────────────────────
  {
    path: '/accounting/budget-analysis',
    element: withSuspense(BudgetAnalysis),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/budget-analysis'],
    },
  },

  // ── Cash Flow ─────────────────────────────────────────────────────────
  {
    path: '/accounting/cash-flow',
    element: withSuspense(CashFlow),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/cash-flow'],
    },
  },

  // ── Variance Analysis ─────────────────────────────────────────────────
  {
    path: '/accounting/variance-analysis',
    element: withSuspense(VarianceAnalysis),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/variance-analysis'],
    },
  },

  // ── Fixed Assets ──────────────────────────────────────────────────────
  {
    path: '/accounting/fixed-assets',
    element: withSuspense(FixedAssets),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/fixed-assets'],
    },
  },

  // ── Multi-Currency ────────────────────────────────────────────────────
  {
    path: '/accounting/multi-currency',
    element: withSuspense(MultiCurrency),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/multi-currency'],
    },
  },

  // ── Aging Reports ─────────────────────────────────────────────────────
  {
    path: '/accounting/aging-reports',
    element: withSuspense(AgingReports),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/aging-reports'],
    },
  },

  // ── Compliance & Planning ─────────────────────────────────────────────
  {
    path: '/accounting/compliance-planning',
    element: withSuspense(CompliancePlanning),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/compliance-planning'],
    },
  },

  // ── Banking & Cash ────────────────────────────────────────────────────
  {
    path: '/accounting/banking-cash',
    element: withSuspense(BankingAndCash),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/banking-cash'],
    },
  },

  // ── Credit Management ─────────────────────────────────────────────────
  {
    path: '/accounting/credit-management',
    element: withSuspense(CreditManagement),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/accounting/credit-management'],
    },
  },

  // ── POS End of Day ────────────────────────────────────────────────────
  {
    path: '/accounting/pos-end-of-day',
    element: withSuspense(POSEndOfDay),
    handle: {
      requiredPermission: ACCOUNTING_ROUTE_PERMISSIONS['/pos-end-of-day'],
    },
  },
];

export default accountingRoutes;
