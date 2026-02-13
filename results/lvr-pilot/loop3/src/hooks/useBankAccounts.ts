// =============================================================================
// BANK ACCOUNTS — React Query hooks for bank account CRUD
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  BankAccountRow,
  BankAccountInsert,
  BankAccountUpdate,
  BankAccountWithGLAccount,
  BankAccountFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchBankAccounts(
  businessId: string,
  filters?: BankAccountFilters
): Promise<BankAccountWithGLAccount[]> {
  let query = supabase
    .from('bank_accounts')
    .select(
      `
      id, business_id, account_name, account_number, bank_name,
      routing_number, account_type, currency, current_balance,
      gl_account_id, is_active, created_at, updated_at,
      chart_of_accounts (id, account_code, account_name)
    `
    )
    .eq('business_id', businessId);

  if (filters?.is_active !== undefined) {
    query = query.eq('is_active', filters.is_active);
  }
  if (filters?.account_type && filters.account_type !== 'all') {
    query = query.eq('account_type', filters.account_type);
  }
  if (filters?.search) {
    query = query.or(
      `account_name.ilike.%${filters.search}%,bank_name.ilike.%${filters.search}%,account_number.ilike.%${filters.search}%`
    );
  }

  const { data, error } = await query.order('account_name', { ascending: true });

  if (error) throw error;
  return data ?? [];
}

async function fetchBankAccount(
  businessId: string,
  accountId: string
): Promise<BankAccountWithGLAccount> {
  const { data, error } = await supabase
    .from('bank_accounts')
    .select(
      `
      id, business_id, account_name, account_number, bank_name,
      routing_number, account_type, currency, current_balance,
      gl_account_id, is_active, created_at, updated_at,
      chart_of_accounts (id, account_code, account_name)
    `
    )
    .eq('id', accountId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createBankAccount(
  businessId: string,
  data: BankAccountInsert
): Promise<BankAccountRow> {
  const { data: account, error } = await supabase
    .from('bank_accounts')
    .insert({
      ...data,
      business_id: businessId,
      currency: data.currency ?? 'BSD',
      current_balance: 0,
      is_active: data.is_active ?? true,
    })
    .select()
    .single();

  if (error) throw error;
  return account;
}

async function updateBankAccount(
  businessId: string,
  accountId: string,
  data: BankAccountUpdate
): Promise<BankAccountRow> {
  const { data: account, error } = await supabase
    .from('bank_accounts')
    .update(data)
    .eq('id', accountId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return account;
}

async function deleteBankAccount(
  businessId: string,
  accountId: string
): Promise<void> {
  // Deactivate instead of hard delete to preserve transaction history
  const { error } = await supabase
    .from('bank_accounts')
    .update({ is_active: false })
    .eq('id', accountId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useBankAccountsQuery(filters?: BankAccountFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bankAccounts.list(businessId, filters),
    queryFn: () => fetchBankAccounts(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function useBankAccountQuery(accountId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bankAccounts.detail(businessId, accountId),
    queryFn: () => fetchBankAccount(businessId, accountId),
    enabled: !!businessId && !!accountId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateBankAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BankAccountInsert) =>
      createBankAccount(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankAccounts.all,
      });
    },
  });
}

export function useUpdateBankAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BankAccountUpdate }) =>
      updateBankAccount(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankAccounts.all,
      });
    },
  });
}

/** Deactivate bank account (preserves transaction history) */
export function useDeleteBankAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: string) =>
      deleteBankAccount(businessId, accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bankAccounts.all,
      });
    },
  });
}
