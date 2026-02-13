// =============================================================================
// JOURNAL ENTRIES — React Query hooks with GeneralLedgerService routing
// Fixes: BUG-H04 (Post bypasses service), BUG-H05 (Reverse bypasses service)
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { GeneralLedgerService } from '@/services/GeneralLedgerService';
import {
  accountingKeys,
  useBusinessId,
  getCurrentUserId,
  applyPagination,
  buildPaginatedResult,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  JournalEntryRow,
  JournalEntryInsert,
  JournalEntryUpdate,
  JournalEntryWithTransactions,
  JournalEntryFilters,
  PaginationParams,
  PaginatedResult,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchJournalEntries(
  businessId: string,
  filters?: JournalEntryFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<JournalEntryWithTransactions>> {
  let query = supabase
    .from('journal_entries')
    .select(
      `
      id, business_id, entry_number, entry_date, description, total_amount,
      status, entry_type, reference_type, reference_id, reference_number,
      notes, posted_at, created_by, created_at, updated_at,
      account_transactions (
        id, journal_entry_id, account_id, debit_amount, credit_amount, description,
        chart_of_accounts (id, account_code, account_name)
      )
    `,
      { count: 'exact' }
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.entry_type) {
    query = query.eq('entry_type', filters.entry_type);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('entry_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('entry_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `entry_number.ilike.%${filters.search}%,description.ilike.%${filters.search}%,reference_number.ilike.%${filters.search}%`
    );
  }

  const { query: paginatedQuery, page, pageSize } = applyPagination(query, pagination);
  const finalQuery = paginatedQuery.order('created_at', { ascending: false });

  const { data, error, count } = await finalQuery;
  if (error) throw error;

  return buildPaginatedResult(data, count, page, pageSize);
}

async function fetchJournalEntry(
  businessId: string,
  entryId: string
): Promise<JournalEntryWithTransactions> {
  const { data, error } = await supabase
    .from('journal_entries')
    .select(
      `
      id, business_id, entry_number, entry_date, description, total_amount,
      status, entry_type, reference_type, reference_id, reference_number,
      notes, posted_at, created_by, created_at, updated_at,
      account_transactions (
        id, journal_entry_id, account_id, debit_amount, credit_amount, description,
        chart_of_accounts (id, account_code, account_name)
      )
    `
    )
    .eq('id', entryId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

/**
 * Create a journal entry through GeneralLedgerService.
 * This ensures proper validation (balanced debits/credits, valid accounts, etc.)
 */
async function createJournalEntry(
  businessId: string,
  data: JournalEntryInsert
): Promise<JournalEntryRow> {
  const userId = await getCurrentUserId();

  const result = await GeneralLedgerService.createJournalEntry({
    business_id: businessId,
    description: data.description || '',
    reference_type: data.reference_type || 'manual',
    reference_id: data.reference_id,
    lines: data.transactions.map((t) => ({
      account_id: t.account_id,
      debit_amount: t.debit_amount,
      credit_amount: t.credit_amount,
      description: t.description,
    })),
    created_by: userId,
    entry_date: data.entry_date,
    entry_type: data.entry_type,
    notes: data.notes,
  });

  return result;
}

async function updateJournalEntry(
  businessId: string,
  entryId: string,
  data: JournalEntryUpdate
): Promise<JournalEntryRow> {
  // Only draft entries can be updated directly
  const { data: existing, error: fetchError } = await supabase
    .from('journal_entries')
    .select('status')
    .eq('id', entryId)
    .eq('business_id', businessId)
    .single();

  if (fetchError) throw fetchError;
  if (existing.status !== 'draft') {
    throw new Error('Only draft journal entries can be edited. Posted entries must be reversed.');
  }

  const { data: entry, error } = await supabase
    .from('journal_entries')
    .update(data)
    .eq('id', entryId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return entry;
}

/**
 * BUG-H04 FIX: Post journal entry through GeneralLedgerService.
 * The old code directly updated status to 'posted' without:
 * - Validating debit/credit balance
 * - Checking account existence
 * - Checking accounting period status
 * - Updating account balances
 */
async function postJournalEntry(
  businessId: string,
  entryId: string
): Promise<JournalEntryRow> {
  const result = await GeneralLedgerService.postJournalEntry(businessId, entryId);
  return result;
}

/**
 * BUG-H05 FIX: Reverse journal entry through GeneralLedgerService.
 * The old code had no reverse function. When implemented, it would need
 * to create reversing entries with swapped debits/credits and update
 * account balances accordingly.
 */
async function reverseJournalEntry(
  businessId: string,
  entryId: string
): Promise<JournalEntryRow> {
  const result = await GeneralLedgerService.reverseJournalEntry(businessId, entryId);
  return result;
}

async function deleteJournalEntry(
  businessId: string,
  entryId: string
): Promise<void> {
  // Only draft entries can be deleted
  const { data: existing, error: fetchError } = await supabase
    .from('journal_entries')
    .select('status')
    .eq('id', entryId)
    .eq('business_id', businessId)
    .single();

  if (fetchError) throw fetchError;
  if (existing.status !== 'draft') {
    throw new Error('Only draft journal entries can be deleted. Posted entries must be reversed.');
  }

  // Delete associated account transactions first
  const { error: txError } = await supabase
    .from('account_transactions')
    .delete()
    .eq('journal_entry_id', entryId);

  if (txError) throw txError;

  const { error } = await supabase
    .from('journal_entries')
    .delete()
    .eq('id', entryId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useJournalEntriesQuery(
  filters?: JournalEntryFilters,
  pagination?: PaginationParams
) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.journalEntries.list(businessId, filters, pagination),
    queryFn: () => fetchJournalEntries(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
    placeholderData: (previousData) => previousData,
  });
}

export function useJournalEntryQuery(entryId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.journalEntries.detail(businessId, entryId),
    queryFn: () => fetchJournalEntry(businessId, entryId),
    enabled: !!businessId && !!entryId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

/** Create journal entry through GeneralLedgerService */
export function useCreateJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: JournalEntryInsert) =>
      createJournalEntry(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Update a draft journal entry */
export function useUpdateJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: JournalEntryUpdate }) =>
      updateJournalEntry(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all });
    },
  });
}

/**
 * BUG-H04 FIX: Post through GeneralLedgerService with validation.
 * NOT a direct status update.
 */
export function usePostJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: string) => postJournalEntry(businessId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/**
 * BUG-H05 FIX: Reverse through GeneralLedgerService.
 * Creates a reversing journal entry with swapped debits/credits.
 */
export function useReverseJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: string) => reverseJournalEntry(businessId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Delete a draft journal entry */
export function useDeleteJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: string) => deleteJournalEntry(businessId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all });
    },
  });
}
