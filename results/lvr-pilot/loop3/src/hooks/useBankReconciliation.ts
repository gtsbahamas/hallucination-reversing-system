// =============================================================================
// BANK RECONCILIATION — React Query hooks for transactions, matching, statements
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  BankTransactionRow,
  BankTransactionInsert,
  BankTransactionUpdate,
  BankTransactionFilters,
  BankStatementRow,
  BankStatementFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchBankTransactions(
  businessId: string,
  filters?: BankTransactionFilters
): Promise<BankTransactionRow[]> {
  let query = supabase
    .from('bank_transactions')
    .select(
      `
      id, business_id, bank_account_id, transaction_date,
      description, amount, transaction_type, reference_number,
      is_matched, matched_journal_entry_id, created_at
    `
    )
    .eq('business_id', businessId);

  if (filters?.bank_account_id && filters.bank_account_id !== 'all') {
    query = query.eq('bank_account_id', filters.bank_account_id);
  }
  if (filters?.is_matched !== undefined) {
    query = query.eq('is_matched', filters.is_matched);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('transaction_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('transaction_date', filters.dateRange.to);
  }

  const { data, error } = await query.order('transaction_date', {
    ascending: false,
  });

  if (error) throw error;
  return data ?? [];
}

async function fetchBankTransactionsByAccount(
  businessId: string,
  accountId: string
): Promise<BankTransactionRow[]> {
  const { data, error } = await supabase
    .from('bank_transactions')
    .select(
      `
      id, business_id, bank_account_id, transaction_date,
      description, amount, transaction_type, reference_number,
      is_matched, matched_journal_entry_id, created_at
    `
    )
    .eq('business_id', businessId)
    .eq('bank_account_id', accountId)
    .order('transaction_date', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchBankStatements(
  businessId: string,
  filters?: BankStatementFilters
): Promise<BankStatementRow[]> {
  let query = supabase
    .from('bank_statements')
    .select(
      `
      id, business_id, bank_account_id, statement_date,
      opening_balance, closing_balance, total_deposits,
      total_withdrawals, is_reconciled, created_at
    `
    )
    .eq('business_id', businessId);

  if (filters?.bank_account_id && filters.bank_account_id !== 'all') {
    query = query.eq('bank_account_id', filters.bank_account_id);
  }
  if (filters?.is_reconciled !== undefined) {
    query = query.eq('is_reconciled', filters.is_reconciled);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('statement_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('statement_date', filters.dateRange.to);
  }

  const { data, error } = await query.order('statement_date', {
    ascending: false,
  });

  if (error) throw error;
  return data ?? [];
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function importTransactions(
  businessId: string,
  transactions: BankTransactionInsert[]
): Promise<BankTransactionRow[]> {
  const { data, error } = await supabase
    .from('bank_transactions')
    .insert(
      transactions.map((t) => ({
        ...t,
        business_id: businessId,
        is_matched: false,
        matched_journal_entry_id: null,
      }))
    )
    .select();

  if (error) throw error;
  return data ?? [];
}

async function matchTransaction(
  businessId: string,
  transactionId: string,
  journalEntryId: string
): Promise<BankTransactionRow> {
  const { data, error } = await supabase
    .from('bank_transactions')
    .update({
      is_matched: true,
      matched_journal_entry_id: journalEntryId,
    })
    .eq('id', transactionId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

async function unmatchTransaction(
  businessId: string,
  transactionId: string
): Promise<BankTransactionRow> {
  const { data, error } = await supabase
    .from('bank_transactions')
    .update({
      is_matched: false,
      matched_journal_entry_id: null,
    })
    .eq('id', transactionId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

async function reconcileStatement(
  businessId: string,
  statementId: string
): Promise<BankStatementRow> {
  const { data, error } = await supabase
    .from('bank_statements')
    .update({ is_reconciled: true })
    .eq('id', statementId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useBankTransactionsQuery(filters?: BankTransactionFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bankTransactions.list(businessId, filters),
    queryFn: () => fetchBankTransactions(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function useBankTransactionsByAccountQuery(accountId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bankTransactions.byAccount(businessId, accountId),
    queryFn: () => fetchBankTransactionsByAccount(businessId, accountId),
    enabled: !!businessId && !!accountId,
    staleTime: LIST_STALE_TIME,
  });
}

export function useBankStatementsQuery(filters?: BankStatementFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bankStatements.list(businessId, filters),
    queryFn: () => fetchBankStatements(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useImportTransactionsMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transactions: BankTransactionInsert[]) =>
      importTransactions(businessId, transactions),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankTransactions.all,
      });
    },
  });
}

export function useMatchTransactionMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      transactionId,
      journalEntryId,
    }: {
      transactionId: string;
      journalEntryId: string;
    }) => matchTransaction(businessId, transactionId, journalEntryId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankTransactions.all,
      });
    },
  });
}

export function useUnmatchTransactionMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transactionId: string) =>
      unmatchTransaction(businessId, transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankTransactions.all,
      });
    },
  });
}

export function useReconcileStatementMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (statementId: string) =>
      reconcileStatement(businessId, statementId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankStatements.all,
      });
    },
  });
}
