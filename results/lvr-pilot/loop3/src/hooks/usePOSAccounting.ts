// =============================================================================
// POS ACCOUNTING — React Query hooks for POS transaction queries + GL posting
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { GeneralLedgerService } from '@/services/GeneralLedgerService';
import {
  accountingKeys,
  useBusinessId,
  getCurrentUserId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  POSTransactionRow,
  POSTransactionWithItems,
  POSTransactionFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchPOSTransactions(
  businessId: string,
  filters?: POSTransactionFilters
): Promise<POSTransactionWithItems[]> {
  let query = supabase
    .from('pos_transactions')
    .select(
      `
      id, business_id, transaction_number, cashier_id, customer_id,
      subtotal, tax_amount, total_amount, amount_tendered, change_amount,
      status, notes, is_bonded, exemption_reason, authorized_by, created_at,
      pos_transaction_items (
        id, transaction_id, product_id, product_name, product_sku,
        quantity, unit_price, tax_amount, line_total, duty_amount, exemption_type
      ),
      pos_payments (
        id, transaction_id, payment_method, amount, reference_number, notes
      )
    `
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.cashier_id && filters.cashier_id !== 'all') {
    query = query.eq('cashier_id', filters.cashier_id);
  }
  if (filters?.is_bonded !== undefined) {
    query = query.eq('is_bonded', filters.is_bonded);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('created_at', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('created_at', filters.dateRange.to);
  }

  const { data, error } = await query.order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchPOSTransaction(
  transactionId: string
): Promise<POSTransactionWithItems> {
  const { data, error } = await supabase
    .from('pos_transactions')
    .select(
      `
      id, business_id, transaction_number, cashier_id, customer_id,
      subtotal, tax_amount, total_amount, amount_tendered, change_amount,
      status, notes, is_bonded, exemption_reason, authorized_by, created_at,
      pos_transaction_items (
        id, transaction_id, product_id, product_name, product_sku,
        quantity, unit_price, tax_amount, line_total, duty_amount, exemption_type
      ),
      pos_payments (
        id, transaction_id, payment_method, amount, reference_number, notes
      )
    `
    )
    .eq('id', transactionId)
    .single();

  if (error) throw error;
  return data;
}

async function fetchUnpostedPOSTransactions(
  businessId: string
): Promise<POSTransactionRow[]> {
  // Fetch completed POS transactions that have not been posted to GL
  // We identify unposted transactions by checking if a journal entry
  // with reference_type='pos_sale' and reference_id=transaction.id exists
  const { data: transactions, error } = await supabase
    .from('pos_transactions')
    .select(
      `
      id, business_id, transaction_number, cashier_id, customer_id,
      subtotal, tax_amount, total_amount, amount_tendered, change_amount,
      status, notes, is_bonded, exemption_reason, authorized_by, created_at
    `
    )
    .eq('business_id', businessId)
    .eq('status', 'completed')
    .order('created_at', { ascending: true });

  if (error) throw error;

  // Filter to only transactions without a corresponding journal entry
  if (!transactions || transactions.length === 0) return [];

  const transactionIds = transactions.map((t) => t.id);
  const { data: journalEntries } = await supabase
    .from('journal_entries')
    .select('reference_id')
    .eq('business_id', businessId)
    .eq('reference_type', 'pos_sale')
    .in('reference_id', transactionIds);

  const postedIds = new Set((journalEntries ?? []).map((je) => je.reference_id));
  return transactions.filter((t) => !postedIds.has(t.id));
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

/**
 * Post a single POS sale to the General Ledger.
 * Creates a journal entry with the POS transaction as reference.
 */
async function postPOSSale(
  businessId: string,
  transactionId: string
): Promise<void> {
  const userId = await getCurrentUserId();

  // Fetch the transaction
  const { data: transaction, error: txError } = await supabase
    .from('pos_transactions')
    .select('id, total_amount, tax_amount, subtotal')
    .eq('id', transactionId)
    .eq('business_id', businessId)
    .single();

  if (txError) throw txError;

  // Fetch the payment methods used
  const { data: payments, error: payError } = await supabase
    .from('pos_payments')
    .select('payment_method, amount')
    .eq('transaction_id', transactionId);

  if (payError) throw payError;

  // Determine debit accounts based on payment methods
  const lines: {
    account_id: string;
    debit_amount: number;
    credit_amount: number;
    description: string;
  }[] = [];

  // Get default accounts for POS
  const { data: accounts } = await supabase
    .from('chart_of_accounts')
    .select('id, account_code, account_name')
    .eq('business_id', businessId)
    .in('account_code', ['1000', '1200', '4000', '2100']);

  const accountMap = new Map(
    (accounts ?? []).map((a) => [a.account_code, a.id])
  );

  const cashAccountId = accountMap.get('1000');
  const arAccountId = accountMap.get('1200');
  const salesRevenueId = accountMap.get('4000');
  const taxPayableId = accountMap.get('2100');

  if (!salesRevenueId) {
    throw new Error('Sales Revenue account (4000) not found. Create default accounts first.');
  }

  // Debit entries (based on payment method)
  for (const payment of payments ?? []) {
    const debitAccountId =
      payment.payment_method === 'cash' ? cashAccountId : arAccountId;

    if (debitAccountId) {
      lines.push({
        account_id: debitAccountId,
        debit_amount: payment.amount,
        credit_amount: 0,
        description: `POS Sale - ${payment.payment_method}`,
      });
    }
  }

  // Credit: Sales Revenue (subtotal)
  lines.push({
    account_id: salesRevenueId,
    debit_amount: 0,
    credit_amount: transaction.subtotal,
    description: 'POS Sale - Revenue',
  });

  // Credit: Tax Payable (if applicable)
  if (transaction.tax_amount > 0 && taxPayableId) {
    lines.push({
      account_id: taxPayableId,
      debit_amount: 0,
      credit_amount: transaction.tax_amount,
      description: 'POS Sale - Tax',
    });
  }

  // Create journal entry through service
  await GeneralLedgerService.createJournalEntry({
    business_id: businessId,
    description: `POS Sale: ${transactionId}`,
    reference_type: 'pos_sale',
    reference_id: transactionId,
    lines,
    created_by: userId,
    entry_date: new Date().toISOString().split('T')[0],
  });
}

/**
 * Bulk post multiple POS sales to the General Ledger.
 */
async function bulkPostPOS(
  businessId: string,
  transactionIds: string[]
): Promise<{ posted: number; failed: number }> {
  let posted = 0;
  let failed = 0;

  for (const transactionId of transactionIds) {
    try {
      await postPOSSale(businessId, transactionId);
      posted++;
    } catch {
      failed++;
    }
  }

  return { posted, failed };
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function usePOSTransactionsQuery(filters?: POSTransactionFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.posTransactions.list(businessId, filters),
    queryFn: () => fetchPOSTransactions(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function usePOSTransactionQuery(transactionId: string) {
  return useQuery({
    queryKey: accountingKeys.posTransactions.detail(transactionId),
    queryFn: () => fetchPOSTransaction(transactionId),
    enabled: !!transactionId,
  });
}

export function useUnpostedPOSTransactionsQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.posTransactions.unposted(businessId),
    queryFn: () => fetchUnpostedPOSTransactions(businessId),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

/** Post a single POS sale to GL */
export function usePostPOSSaleMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transactionId: string) =>
      postPOSSale(businessId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.posTransactions.all,
      });
      queryClient.invalidateQueries({
        queryKey: accountingKeys.journalEntries.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Bulk post multiple POS sales to GL */
export function useBulkPostPOSMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transactionIds: string[]) =>
      bulkPostPOS(businessId, transactionIds),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.posTransactions.all,
      });
      queryClient.invalidateQueries({
        queryKey: accountingKeys.journalEntries.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}
