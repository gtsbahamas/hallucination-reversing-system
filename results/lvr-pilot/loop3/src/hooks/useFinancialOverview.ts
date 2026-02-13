// =============================================================================
// FINANCIAL OVERVIEW — Dashboard aggregation queries
// Fixes: BUG-H01 (dashboard shows mock data → now fetches REAL data from DB)
// =============================================================================

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  AGGREGATION_STALE_TIME,
} from './useAccountingQueries';
import type { FinancialSummary } from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

/**
 * BUG-H01 FIX: Fetch real financial summary from database.
 * The old dashboard showed hardcoded/mock values.
 * This queries invoices, bills, expenses, and chart_of_accounts
 * to compute actual totals.
 */
async function fetchFinancialSummary(
  businessId: string
): Promise<FinancialSummary> {
  const [invoicesResult, billsResult, expensesResult, accountsResult] =
    await Promise.all([
      supabase
        .from('invoices')
        .select('total_amount, amount_paid, balance_due, status')
        .eq('business_id', businessId)
        .eq('is_deleted', false)
        .neq('status', 'cancelled'),
      supabase
        .from('bills')
        .select('total_amount, amount_paid, balance_due, status')
        .eq('business_id', businessId)
        .eq('is_deleted', false)
        .neq('status', 'cancelled'),
      supabase
        .from('expenses')
        .select('total_amount, status')
        .eq('business_id', businessId)
        .eq('status', 'approved'),
      supabase
        .from('chart_of_accounts')
        .select('account_code, account_type, current_balance')
        .eq('business_id', businessId)
        .eq('is_active', true),
    ]);

  if (invoicesResult.error) throw invoicesResult.error;
  if (billsResult.error) throw billsResult.error;
  if (expensesResult.error) throw expensesResult.error;
  if (accountsResult.error) throw accountsResult.error;

  // Revenue = sum of payments received on invoices
  const totalRevenue = (invoicesResult.data ?? []).reduce(
    (sum, inv) => sum + (inv.amount_paid ?? 0),
    0
  );

  // Accounts Receivable = sum of unpaid invoice balances
  const accountsReceivable = (invoicesResult.data ?? []).reduce(
    (sum, inv) => sum + (inv.balance_due ?? 0),
    0
  );

  // Accounts Payable = sum of unpaid bill balances
  const accountsPayable = (billsResult.data ?? []).reduce(
    (sum, bill) => sum + (bill.balance_due ?? 0),
    0
  );

  // Total Expenses = sum of approved expense amounts
  const totalExpenses = (expensesResult.data ?? []).reduce(
    (sum, exp) => sum + (exp.total_amount ?? 0),
    0
  );

  // Cash Balance = current_balance of account code 1000 (Cash)
  const cashAccount = (accountsResult.data ?? []).find(
    (a) => a.account_code === '1000'
  );
  const cashBalance = cashAccount?.current_balance ?? 0;

  return {
    totalRevenue,
    totalExpenses,
    netIncome: totalRevenue - totalExpenses,
    accountsReceivable,
    accountsPayable,
    cashBalance,
  };
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

/**
 * Dashboard financial summary — real aggregated data.
 * Replaces hardcoded/mock values with actual database queries.
 */
export function useFinancialSummaryQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.dashboard.financialSummary(businessId),
    queryFn: () => fetchFinancialSummary(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}
