/**
 * BankingAndCash.tsx — ACC-025
 *
 * Banking & Cash Management hub with four sub-tabs composing existing components:
 *   - Bank Reconciliation (renders BankReconciliation)
 *   - Cash Flow (renders CashFlow)
 *   - Multi-Currency (renders MultiCurrency)
 *   - POS End of Day (renders POSEndOfDay)
 *
 * This is a composition page that provides tab navigation and summary statistics
 * from the banking domain. All detailed data fetching and mutations live in child components.
 *
 * Architecture notes:
 *   - Uses React.lazy + Suspense for code-splitting child tabs
 *   - Summary stats aggregate key metrics from bank accounts and cash position
 *   - Permission guard using accounting_banking_read
 */

import React, { Suspense, useState, useMemo } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { StatCards, type StatCardData } from '../components/accounting/shared/StatCards';
import { useAccountingPermission } from '../config/accountingPermissions';
import { useBusinessId, AGGREGATION_STALE_TIME } from '../hooks/useAccountingQueries';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';
import {
  Landmark,
  RefreshCcw,
  TrendingUp,
  Globe,
  ShoppingCart,
  DollarSign,
  Banknote,
  CreditCard,
  Loader2,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Lazy-loaded tab content — each child page renders its own content
// ---------------------------------------------------------------------------

import BankReconciliationContent from './BankReconciliation';
import CashFlowContent from './CashFlow';
import MultiCurrencyContent from './MultiCurrency';
import POSEndOfDayContent from './POSEndOfDay';

// ---------------------------------------------------------------------------
// Loading Fallback
// ---------------------------------------------------------------------------

function TabLoadingFallback() {
  return (
    <div className="flex items-center justify-center p-12">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      <span className="ml-3 text-muted-foreground">Loading...</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Banking Summary Query
// ---------------------------------------------------------------------------

interface BankingSummary {
  totalBankBalance: number;
  accountCount: number;
  unreconciledCount: number;
  currencyCount: number;
}

async function fetchBankingSummary(businessId: string): Promise<BankingSummary> {
  const [accountsResult, unreconciledResult, currenciesResult] = await Promise.all([
    // Bank accounts with balances
    supabase
      .from('bank_accounts')
      .select('id, current_balance, is_active')
      .eq('business_id', businessId)
      .eq('is_active', true),

    // Unreconciled statements
    supabase
      .from('bank_statements')
      .select('id')
      .eq('business_id', businessId)
      .eq('is_reconciled', false),

    // Active currencies
    supabase
      .from('currency_rates')
      .select('id')
      .eq('business_id', businessId),
  ]);

  const accounts = accountsResult.data ?? [];
  const totalBankBalance = accounts.reduce(
    (sum, acc) => sum + (acc.current_balance ?? 0),
    0
  );

  return {
    totalBankBalance,
    accountCount: accounts.length,
    unreconciledCount: unreconciledResult.data?.length ?? 0,
    currencyCount: currenciesResult.data?.length ?? 0,
  };
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const BankingAndCash = () => {
  const canRead = useAccountingPermission('accounting_banking_read');
  const businessId = useBusinessId();
  const [activeTab, setActiveTab] = useState('bank-reconciliation');

  const { data: summary, isLoading } = useQuery({
    queryKey: ['accounting', 'banking-summary', businessId],
    queryFn: () => fetchBankingSummary(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const stats = useMemo<StatCardData[]>(() => {
    if (!summary) return [];
    return [
      {
        label: 'Total Bank Balance',
        value: summary.totalBankBalance,
        icon: <Banknote className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${summary.accountCount} active account${summary.accountCount !== 1 ? 's' : ''}`,
      },
      {
        label: 'Unreconciled Statements',
        value: summary.unreconciledCount,
        icon: <RefreshCcw className="h-4 w-4" />,
        format: 'number',
        alert: summary.unreconciledCount > 0,
        subtitle: summary.unreconciledCount > 0 ? 'Needs reconciliation' : 'All reconciled',
      },
      {
        label: 'Active Currencies',
        value: summary.currencyCount,
        icon: <Globe className="h-4 w-4" />,
        format: 'number',
        subtitle: 'Configured exchange rates',
      },
    ];
  }, [summary]);

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view banking & cash management.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Landmark className="h-8 w-8" />
            Banking & Cash Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage bank accounts, reconciliation, cash flow, and multi-currency operations
          </p>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} columns={3} />

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList>
            <TabsTrigger value="bank-reconciliation">
              <RefreshCcw className="h-4 w-4 mr-1" />
              Bank Reconciliation
            </TabsTrigger>
            <TabsTrigger value="cash-flow">
              <TrendingUp className="h-4 w-4 mr-1" />
              Cash Flow
            </TabsTrigger>
            <TabsTrigger value="multi-currency">
              <Globe className="h-4 w-4 mr-1" />
              Multi-Currency
            </TabsTrigger>
            <TabsTrigger value="pos-eod">
              <ShoppingCart className="h-4 w-4 mr-1" />
              POS End of Day
            </TabsTrigger>
          </TabsList>

          <TabsContent value="bank-reconciliation">
            <Suspense fallback={<TabLoadingFallback />}>
              <Card>
                <CardContent className="pt-6">
                  <BankReconciliationContent />
                </CardContent>
              </Card>
            </Suspense>
          </TabsContent>

          <TabsContent value="cash-flow">
            <Suspense fallback={<TabLoadingFallback />}>
              <Card>
                <CardContent className="pt-6">
                  <CashFlowContent />
                </CardContent>
              </Card>
            </Suspense>
          </TabsContent>

          <TabsContent value="multi-currency">
            <Suspense fallback={<TabLoadingFallback />}>
              <Card>
                <CardContent className="pt-6">
                  <MultiCurrencyContent />
                </CardContent>
              </Card>
            </Suspense>
          </TabsContent>

          <TabsContent value="pos-eod">
            <Suspense fallback={<TabLoadingFallback />}>
              <Card>
                <CardContent className="pt-6">
                  <POSEndOfDayContent />
                </CardContent>
              </Card>
            </Suspense>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default BankingAndCash;
