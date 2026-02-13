// =============================================================================
// EXPENSES — React Query hooks for expense CRUD + approval workflow
// Fixes: BUG-L03 (employee join), BUG-L02 (separate aggregations)
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  getCurrentUserId,
  applyPagination,
  buildPaginatedResult,
  LIST_STALE_TIME,
  AGGREGATION_STALE_TIME,
} from './useAccountingQueries';
import type {
  ExpenseRow,
  ExpenseInsert,
  ExpenseUpdate,
  ExpenseWithRelations,
  ExpenseFilters,
  ExpenseAggregations,
  PaginationParams,
  PaginatedResult,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchExpenses(
  businessId: string,
  filters?: ExpenseFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<ExpenseWithRelations>> {
  let query = supabase
    .from('expenses')
    .select(
      `
      id, business_id, expense_number, expense_date, description, amount,
      total_amount, category, status, vendor, payment_method, reference_number,
      notes, submitted_by, approved_at, approved_by, supplier_id, employee_id,
      created_at,
      employees (id, first_name, last_name, email),
      suppliers (id, name, email)
    `,
      { count: 'exact' }
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.category && filters.category !== 'all') {
    query = query.eq('category', filters.category);
  }
  if (filters?.payment_method && filters.payment_method !== 'all') {
    query = query.eq('payment_method', filters.payment_method);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('expense_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('expense_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `expense_number.ilike.%${filters.search}%,description.ilike.%${filters.search}%,vendor.ilike.%${filters.search}%`
    );
  }

  const { query: paginatedQuery, page, pageSize } = applyPagination(query, pagination);
  const finalQuery = paginatedQuery.order('created_at', { ascending: false });

  const { data, error, count } = await finalQuery;
  if (error) throw error;

  return buildPaginatedResult(data, count, page, pageSize);
}

async function fetchExpense(
  businessId: string,
  expenseId: string
): Promise<ExpenseWithRelations> {
  const { data, error } = await supabase
    .from('expenses')
    .select(
      `
      id, business_id, expense_number, expense_date, description, amount,
      total_amount, category, status, vendor, payment_method, reference_number,
      notes, submitted_by, approved_at, approved_by, supplier_id, employee_id,
      created_at,
      employees (id, first_name, last_name, email),
      suppliers (id, name, email)
    `
    )
    .eq('id', expenseId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

async function fetchExpenseAggregations(
  businessId: string
): Promise<ExpenseAggregations> {
  const { data, error } = await supabase
    .from('expenses')
    .select('status, total_amount, amount')
    .eq('business_id', businessId);

  if (error) throw error;

  return (data ?? []).reduce(
    (acc, exp) => {
      const amt = exp.total_amount ?? exp.amount ?? 0;
      acc.totalAmount += amt;
      acc.totalCount++;
      switch (exp.status) {
        case 'approved':
          acc.approvedAmount += amt;
          acc.approvedCount++;
          break;
        case 'pending_approval':
          acc.pendingAmount += amt;
          acc.pendingCount++;
          break;
        case 'rejected':
          acc.rejectedAmount += amt;
          acc.rejectedCount++;
          break;
      }
      return acc;
    },
    {
      totalAmount: 0,
      approvedAmount: 0,
      pendingAmount: 0,
      rejectedAmount: 0,
      totalCount: 0,
      approvedCount: 0,
      pendingCount: 0,
      rejectedCount: 0,
    } as ExpenseAggregations
  );
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createExpense(
  businessId: string,
  data: ExpenseInsert
): Promise<ExpenseRow> {
  const userId = await getCurrentUserId();

  // Generate expense number
  const { data: lastExpense } = await supabase
    .from('expenses')
    .select('expense_number')
    .eq('business_id', businessId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  const nextNumber = lastExpense
    ? `EXP-${(parseInt(lastExpense.expense_number.replace(/\D/g, '') || '0', 10) + 1)
        .toString()
        .padStart(5, '0')}`
    : 'EXP-00001';

  const { data: expense, error } = await supabase
    .from('expenses')
    .insert({
      ...data,
      business_id: businessId,
      expense_number: nextNumber,
      total_amount: data.total_amount ?? data.amount,
      submitted_by: userId,
    })
    .select()
    .single();

  if (error) throw error;
  return expense;
}

async function updateExpense(
  businessId: string,
  expenseId: string,
  data: ExpenseUpdate
): Promise<ExpenseRow> {
  const { data: expense, error } = await supabase
    .from('expenses')
    .update(data)
    .eq('id', expenseId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return expense;
}

async function approveExpense(
  businessId: string,
  expenseId: string
): Promise<ExpenseRow> {
  const userId = await getCurrentUserId();

  const { data: expense, error } = await supabase
    .from('expenses')
    .update({
      status: 'approved' as const,
      approved_by: userId,
      approved_at: new Date().toISOString(),
    })
    .eq('id', expenseId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return expense;
}

async function rejectExpense(
  businessId: string,
  expenseId: string
): Promise<ExpenseRow> {
  const userId = await getCurrentUserId();

  const { data: expense, error } = await supabase
    .from('expenses')
    .update({
      status: 'rejected' as const,
      approved_by: userId,
      approved_at: new Date().toISOString(),
    })
    .eq('id', expenseId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return expense;
}

async function deleteExpense(
  businessId: string,
  expenseId: string
): Promise<void> {
  const { error } = await supabase
    .from('expenses')
    .delete()
    .eq('id', expenseId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useExpensesQuery(
  filters?: ExpenseFilters,
  pagination?: PaginationParams
) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.expenses.list(businessId, filters, pagination),
    queryFn: () => fetchExpenses(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
    placeholderData: (previousData) => previousData,
  });
}

export function useExpenseQuery(expenseId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.expenses.detail(businessId, expenseId),
    queryFn: () => fetchExpense(businessId, expenseId),
    enabled: !!businessId && !!expenseId,
  });
}

export function useExpenseAggregationsQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.expenses.aggregations(businessId),
    queryFn: () => fetchExpenseAggregations(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateExpenseMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ExpenseInsert) => createExpense(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.expenses.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

export function useUpdateExpenseMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExpenseUpdate }) =>
      updateExpense(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.expenses.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Approve an expense — sets status to 'approved' with approver info */
export function useApproveExpenseMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (expenseId: string) => approveExpense(businessId, expenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.expenses.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Reject an expense — sets status to 'rejected' */
export function useRejectExpenseMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (expenseId: string) => rejectExpense(businessId, expenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.expenses.all });
    },
  });
}

/** Delete an expense (hard delete — only draft expenses should be deletable) */
export function useDeleteExpenseMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (expenseId: string) => deleteExpense(businessId, expenseId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.expenses.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}
