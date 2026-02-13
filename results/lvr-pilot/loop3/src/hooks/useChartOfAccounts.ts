// =============================================================================
// CHART OF ACCOUNTS — React Query hooks for account CRUD
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  ChartOfAccountsRow,
  ChartOfAccountsInsert,
  ChartOfAccountsUpdate,
  ChartOfAccountsWithParent,
  ChartOfAccountsFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchAccounts(
  businessId: string,
  filters?: ChartOfAccountsFilters
): Promise<ChartOfAccountsWithParent[]> {
  let query = supabase
    .from('chart_of_accounts')
    .select(
      `
      id, business_id, account_code, account_name, account_type,
      parent_account_id, description, is_active, is_system_account,
      current_balance, created_at, updated_at,
      parent:chart_of_accounts!parent_account_id (id, account_code, account_name)
    `
    )
    .eq('business_id', businessId);

  if (filters?.account_type && filters.account_type !== 'all') {
    query = query.eq('account_type', filters.account_type);
  }
  if (filters?.is_active !== undefined) {
    query = query.eq('is_active', filters.is_active);
  }
  if (filters?.search) {
    query = query.or(
      `account_code.ilike.%${filters.search}%,account_name.ilike.%${filters.search}%`
    );
  }

  const { data, error } = await query.order('account_code', { ascending: true });

  if (error) throw error;
  return data ?? [];
}

async function fetchAccount(
  businessId: string,
  accountId: string
): Promise<ChartOfAccountsWithParent> {
  const { data, error } = await supabase
    .from('chart_of_accounts')
    .select(
      `
      id, business_id, account_code, account_name, account_type,
      parent_account_id, description, is_active, is_system_account,
      current_balance, created_at, updated_at,
      parent:chart_of_accounts!parent_account_id (id, account_code, account_name)
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

async function createAccount(
  businessId: string,
  data: ChartOfAccountsInsert
): Promise<ChartOfAccountsRow> {
  const { data: account, error } = await supabase
    .from('chart_of_accounts')
    .insert({
      ...data,
      business_id: businessId,
      is_system_account: false,
      current_balance: 0,
    })
    .select()
    .single();

  if (error) throw error;
  return account;
}

async function updateAccount(
  businessId: string,
  accountId: string,
  data: ChartOfAccountsUpdate
): Promise<ChartOfAccountsRow> {
  const { data: account, error } = await supabase
    .from('chart_of_accounts')
    .update(data)
    .eq('id', accountId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return account;
}

async function deleteAccount(
  businessId: string,
  accountId: string
): Promise<void> {
  // Verify account is not a system account and has no balance
  const { data: existing, error: fetchError } = await supabase
    .from('chart_of_accounts')
    .select('is_system_account, current_balance')
    .eq('id', accountId)
    .eq('business_id', businessId)
    .single();

  if (fetchError) throw fetchError;
  if (existing.is_system_account) {
    throw new Error('System accounts cannot be deleted');
  }
  if (existing.current_balance !== 0) {
    throw new Error('Cannot delete an account with a non-zero balance');
  }

  // Deactivate instead of hard delete to preserve audit trail
  const { error } = await supabase
    .from('chart_of_accounts')
    .update({ is_active: false })
    .eq('id', accountId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useAccountsQuery(filters?: ChartOfAccountsFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.accounts.list(businessId, filters),
    queryFn: () => fetchAccounts(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function useAccountQuery(accountId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.accounts.detail(businessId, accountId),
    queryFn: () => fetchAccount(businessId, accountId),
    enabled: !!businessId && !!accountId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ChartOfAccountsInsert) => createAccount(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
    },
  });
}

export function useUpdateAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ChartOfAccountsUpdate }) =>
      updateAccount(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
    },
  });
}

/** Deactivates account (soft delete — preserves audit trail) */
export function useDeleteAccountMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (accountId: string) => deleteAccount(businessId, accountId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
    },
  });
}
