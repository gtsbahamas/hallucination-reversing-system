/**
 * FinancialManagement — ACC-009
 *
 * Main financial management dashboard with tabbed interface.
 *
 * Bug fixes:
 *   BUG-H01: Uses useFinancialSummaryQuery() for REAL data (replaces hardcoded mock stats)
 *
 * Architecture:
 *   - 6 top-level tabs with lazy-loaded sub-tab components
 *   - Overview tab uses StatCards with real aggregated data
 *   - Quick Actions navigate to sibling tabs
 *   - DashboardLayout wrapper for app shell
 */

import React, { useState, Suspense } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Calculator,
  DollarSign,
  TrendingUp,
  CreditCard,
  BarChart3,
  Banknote,
  Receipt,
  Users,
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { StatCards } from '@/components/accounting/shared/StatCards';
import { useFinancialSummaryQuery } from '@/hooks/useFinancialOverview';
import { useAccountingPermission } from '@/config/accountingPermissions';

// Lazy load all tab components
const FinancialReportsTab = React.lazy(() => import('@/components/accounting/FinancialReportsTab'));
const ChartOfAccountsTab = React.lazy(() => import('@/components/accounting/ChartOfAccountsTab'));
const JournalEntriesTab = React.lazy(() => import('@/components/accounting/JournalEntriesTab'));
const InvoicesTab = React.lazy(() => import('@/components/accounting/InvoicesTab'));
const ExpensesTab = React.lazy(() => import('@/components/accounting/ExpensesTab'));
const AccountsPayableTab = React.lazy(() => import('@/components/accounting/AccountsPayableTab'));
const ARManagementTab = React.lazy(() => import('@/components/accounting/ARManagementTab'));
const AgingReportsTab = React.lazy(() => import('@/components/accounting/AgingReportsTab'));
const CashFlowTab = React.lazy(() => import('@/components/accounting/CashFlowTab'));
const BankReconciliationTab = React.lazy(() => import('@/components/accounting/BankReconciliationTab'));
const FixedAssetsTab = React.lazy(() => import('@/components/accounting/FixedAssetsTab'));
const BudgetAnalysisTab = React.lazy(() => import('@/components/accounting/BudgetAnalysisTab'));
const TaxReportingTab = React.lazy(() => import('@/components/accounting/TaxReportingTab'));
const MultiCurrencyTab = React.lazy(() => import('@/components/accounting/MultiCurrencyTab'));
const POSEndOfDayPage = React.lazy(() => import('@/pages/accounting/POSEndOfDayPage'));

const TabLoader = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    <span className="ml-2">Loading...</span>
  </div>
);

const FinancialManagement = () => {
  const [activeTab, setActiveTab] = useState('overview');

  // BUG-H01 FIX: Real financial data from database queries (replaces hardcoded mock data)
  const { data: financialSummary, isLoading: summaryLoading } = useFinancialSummaryQuery();

  // Permission checks for tab visibility
  const canViewGL = useAccountingPermission('accounting_journal_entries_read');
  const canViewAR = useAccountingPermission('accounting_ar_read');
  const canViewAP = useAccountingPermission('accounting_ap_read');
  const canViewBanking = useAccountingPermission('accounting_banking_cash_read');
  const canViewCompliance = useAccountingPermission('accounting_compliance_read');
  const canViewReports = useAccountingPermission('accounting_reports_read');

  // Build stat cards from real data (BUG-H01 fix)
  const overviewStats = [
    {
      label: 'Net Income',
      value: financialSummary?.netIncome ?? 0,
      format: 'currency' as const,
      icon: <DollarSign className="h-4 w-4" />,
      subtitle: `Revenue: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(financialSummary?.totalRevenue ?? 0)}`,
    },
    {
      label: 'Total Revenue',
      value: financialSummary?.totalRevenue ?? 0,
      format: 'currency' as const,
      icon: <TrendingUp className="h-4 w-4" />,
      subtitle: `Expenses: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(financialSummary?.totalExpenses ?? 0)}`,
    },
    {
      label: 'Cash Balance',
      value: financialSummary?.cashBalance ?? 0,
      format: 'currency' as const,
      icon: <Banknote className="h-4 w-4" />,
      subtitle: 'Available for operations',
    },
    {
      label: 'Accounts Receivable',
      value: financialSummary?.accountsReceivable ?? 0,
      format: 'currency' as const,
      icon: <Users className="h-4 w-4" />,
      subtitle: `Payable: ${new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(financialSummary?.accountsPayable ?? 0)}`,
    },
  ];

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Financial Management</h1>
          <p className="text-muted-foreground">
            Comprehensive accounting and financial management system
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="general-ledger" disabled={!canViewGL}>
              General Ledger
            </TabsTrigger>
            <TabsTrigger value="accounts-receivable" disabled={!canViewAR}>
              Accounts Receivable
            </TabsTrigger>
            <TabsTrigger value="accounts-payable" disabled={!canViewAP}>
              Accounts Payable
            </TabsTrigger>
            <TabsTrigger value="banking-cash" disabled={!canViewBanking}>
              Banking & Cash
            </TabsTrigger>
            <TabsTrigger value="compliance-planning" disabled={!canViewCompliance}>
              Compliance & Planning
            </TabsTrigger>
          </TabsList>

          {/* ── Overview Tab ──────────────────────────────────────────────────── */}
          <TabsContent value="overview" className="space-y-6">
            {/* BUG-H01 FIX: Real financial overview statistics */}
            <StatCards stats={overviewStats} isLoading={summaryLoading} columns={4} />

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common financial management tasks</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-4">
                {canViewGL && (
                  <Button onClick={() => setActiveTab('general-ledger')}>
                    <Calculator className="h-4 w-4 mr-2" />
                    Create Journal Entry
                  </Button>
                )}
                {canViewAR && (
                  <Button onClick={() => setActiveTab('accounts-receivable')}>
                    <Receipt className="h-4 w-4 mr-2" />
                    Create Invoice
                  </Button>
                )}
                {canViewAP && (
                  <Button onClick={() => setActiveTab('accounts-payable')}>
                    <CreditCard className="h-4 w-4 mr-2" />
                    Record Expense
                  </Button>
                )}
                {canViewBanking && (
                  <Button onClick={() => setActiveTab('banking-cash')}>
                    <Banknote className="h-4 w-4 mr-2" />
                    Reconcile Bank
                  </Button>
                )}
                {canViewReports && (
                  <Button
                    variant="outline"
                    onClick={() => setActiveTab('general-ledger')}
                  >
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Generate Report
                  </Button>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── General Ledger Tab ──────────────────────────────────────────── */}
          <TabsContent value="general-ledger">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">General Ledger</h2>
                <p className="text-muted-foreground">
                  Chart of accounts, journal entries, and financial reports
                </p>
              </div>

              <Tabs defaultValue="chart-of-accounts" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="chart-of-accounts">Chart of Accounts</TabsTrigger>
                  <TabsTrigger value="journal-entries">Journal Entries</TabsTrigger>
                  <TabsTrigger value="financial-reports">Financial Reports</TabsTrigger>
                </TabsList>

                <TabsContent value="chart-of-accounts">
                  <Suspense fallback={<TabLoader />}>
                    <ChartOfAccountsTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="journal-entries">
                  <Suspense fallback={<TabLoader />}>
                    <JournalEntriesTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="financial-reports">
                  <Suspense fallback={<TabLoader />}>
                    <FinancialReportsTab />
                  </Suspense>
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>

          {/* ── Accounts Receivable Tab ─────────────────────────────────────── */}
          <TabsContent value="accounts-receivable">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Accounts Receivable</h2>
                <p className="text-muted-foreground">
                  Customer invoices, collections, and aging reports
                </p>
              </div>

              <Tabs defaultValue="invoices" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="invoices">Customer Invoices</TabsTrigger>
                  <TabsTrigger value="collections">Collections Management</TabsTrigger>
                  <TabsTrigger value="aging">Aging Reports</TabsTrigger>
                </TabsList>

                <TabsContent value="invoices">
                  <Suspense fallback={<TabLoader />}>
                    <InvoicesTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="collections">
                  <Suspense fallback={<TabLoader />}>
                    <ARManagementTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="aging">
                  <Suspense fallback={<TabLoader />}>
                    <AgingReportsTab />
                  </Suspense>
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>

          {/* ── Accounts Payable Tab ────────────────────────────────────────── */}
          <TabsContent value="accounts-payable">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Accounts Payable</h2>
                <p className="text-muted-foreground">
                  Vendor bills, payment management, and expense tracking
                </p>
              </div>

              <Tabs defaultValue="bills" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="bills">Vendor Bills</TabsTrigger>
                  <TabsTrigger value="payments">Payment Management</TabsTrigger>
                  <TabsTrigger value="expenses">Expense Tracking</TabsTrigger>
                </TabsList>

                <TabsContent value="bills">
                  <Suspense fallback={<TabLoader />}>
                    <AccountsPayableTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="payments">
                  <Suspense fallback={<TabLoader />}>
                    <AccountsPayableTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="expenses">
                  <Suspense fallback={<TabLoader />}>
                    <ExpensesTab />
                  </Suspense>
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>

          {/* ── Banking & Cash Tab ──────────────────────────────────────────── */}
          <TabsContent value="banking-cash">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Banking & Cash</h2>
                <p className="text-muted-foreground">
                  Bank reconciliation, cash flow analysis, multi-currency management, and POS shift closeouts
                </p>
              </div>

              <Tabs defaultValue="reconciliation" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="reconciliation">Bank Reconciliation</TabsTrigger>
                  <TabsTrigger value="cash-flow">Cash Flow Analysis</TabsTrigger>
                  <TabsTrigger value="multi-currency">Multi-Currency</TabsTrigger>
                  <TabsTrigger value="pos-eod">POS End of Day</TabsTrigger>
                </TabsList>

                <TabsContent value="reconciliation">
                  <Suspense fallback={<TabLoader />}>
                    <BankReconciliationTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="cash-flow">
                  <Suspense fallback={<TabLoader />}>
                    <CashFlowTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="multi-currency">
                  <Suspense fallback={<TabLoader />}>
                    <MultiCurrencyTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="pos-eod">
                  <Suspense fallback={<TabLoader />}>
                    <POSEndOfDayPage />
                  </Suspense>
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>

          {/* ── Compliance & Planning Tab ───────────────────────────────────── */}
          <TabsContent value="compliance-planning">
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold">Compliance & Planning</h2>
                <p className="text-muted-foreground">
                  Tax reporting, budget analysis, and fixed assets management
                </p>
              </div>

              <Tabs defaultValue="tax" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="tax">Tax Reporting</TabsTrigger>
                  <TabsTrigger value="budget">Budget Analysis</TabsTrigger>
                  <TabsTrigger value="assets">Fixed Assets</TabsTrigger>
                </TabsList>

                <TabsContent value="tax">
                  <Suspense fallback={<TabLoader />}>
                    <TaxReportingTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="budget">
                  <Suspense fallback={<TabLoader />}>
                    <BudgetAnalysisTab />
                  </Suspense>
                </TabsContent>
                <TabsContent value="assets">
                  <Suspense fallback={<TabLoader />}>
                    <FixedAssetsTab />
                  </Suspense>
                </TabsContent>
              </Tabs>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default FinancialManagement;
