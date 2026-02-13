// =============================================================================
// BILLS — React Query hooks for bill CRUD + soft delete
// Fixes: BUG-H03 (soft delete instead of hard delete)
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
} from './useAccountingQueries';
import type {
  BillRow,
  BillInsert,
  BillUpdate,
  BillWithRelations,
  BillFilters,
  PaginationParams,
  PaginatedResult,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchBills(
  businessId: string,
  filters?: BillFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<BillWithRelations>> {
  let query = supabase
    .from('bills')
    .select(
      `
      id, business_id, supplier_id, purchase_order_id, bill_number, bill_date,
      due_date, subtotal, tax_amount, total_amount, amount_paid, balance_due,
      status, notes, processing_status, confidence_score, is_deleted,
      created_at, updated_at, created_by,
      suppliers (name),
      bill_items (id, product_id, description, quantity, unit_price, line_total)
    `,
      { count: 'exact' }
    )
    .eq('business_id', businessId)
    .eq('is_deleted', false);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.supplier_id && filters.supplier_id !== 'all') {
    query = query.eq('supplier_id', filters.supplier_id);
  }
  if (filters?.processing_status && filters.processing_status !== 'all') {
    query = query.eq('processing_status', filters.processing_status);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('bill_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('bill_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `bill_number.ilike.%${filters.search}%,notes.ilike.%${filters.search}%`
    );
  }

  const { query: paginatedQuery, page, pageSize } = applyPagination(query, pagination);
  const finalQuery = paginatedQuery.order('created_at', { ascending: false });

  const { data, error, count } = await finalQuery;
  if (error) throw error;

  return buildPaginatedResult(data, count, page, pageSize);
}

async function fetchBill(
  businessId: string,
  billId: string
): Promise<BillWithRelations> {
  const { data, error } = await supabase
    .from('bills')
    .select(
      `
      id, business_id, supplier_id, purchase_order_id, bill_number, bill_date,
      due_date, subtotal, tax_amount, total_amount, amount_paid, balance_due,
      status, notes, processing_status, confidence_score, is_deleted,
      created_at, updated_at, created_by,
      suppliers (name),
      bill_items (id, product_id, description, quantity, unit_price, line_total)
    `
    )
    .eq('id', billId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createBill(
  businessId: string,
  data: BillInsert
): Promise<BillRow> {
  const userId = await getCurrentUserId();
  const { line_items, ...billData } = data;

  const { data: bill, error: billError } = await supabase
    .from('bills')
    .insert({
      ...billData,
      business_id: businessId,
      amount_paid: 0,
      balance_due: billData.total_amount,
      is_deleted: false,
      created_by: userId,
    })
    .select()
    .single();

  if (billError) throw billError;

  if (line_items && line_items.length > 0) {
    const { error: itemsError } = await supabase
      .from('bill_items')
      .insert(
        line_items.map((item) => ({
          bill_id: bill.id,
          product_id: item.product_id ?? null,
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          line_total: item.line_total,
        }))
      );

    if (itemsError) throw itemsError;
  }

  return bill;
}

async function updateBill(
  businessId: string,
  billId: string,
  data: BillUpdate
): Promise<BillRow> {
  const { data: bill, error } = await supabase
    .from('bills')
    .update(data)
    .eq('id', billId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return bill;
}

/**
 * BUG-H03 FIX: Soft delete — sets is_deleted=true and status=cancelled.
 * The old code used .delete() (hard delete) which permanently removed financial records.
 */
async function softDeleteBill(
  businessId: string,
  billId: string
): Promise<void> {
  const { error } = await supabase
    .from('bills')
    .update({ is_deleted: true, status: 'cancelled' as const })
    .eq('id', billId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useBillsQuery(
  filters?: BillFilters,
  pagination?: PaginationParams
) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bills.list(businessId, filters, pagination),
    queryFn: () => fetchBills(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
    placeholderData: (previousData) => previousData,
  });
}

export function useBillQuery(billId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bills.detail(businessId, billId),
    queryFn: () => fetchBill(businessId, billId),
    enabled: !!businessId && !!billId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateBillMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BillInsert) => createBill(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

export function useUpdateBillMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BillUpdate }) =>
      updateBill(businessId, id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: accountingKeys.bills.all });

      const previousData = queryClient.getQueriesData({
        queryKey: accountingKeys.bills.all,
      });

      queryClient.setQueriesData(
        { queryKey: accountingKeys.bills.all },
        (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const typed = old as PaginatedResult<BillRow>;
          if (!typed.data) return old;
          return {
            ...typed,
            data: typed.data.map((bill: BillRow) =>
              bill.id === id ? { ...bill, ...data } : bill
            ),
          };
        }
      );

      return { previousData };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousData) {
        for (const [key, value] of context.previousData) {
          queryClient.setQueryData(key, value);
        }
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/**
 * BUG-H03 FIX: Soft delete mutation.
 * Uses update (is_deleted=true) instead of hard .delete().
 */
export function useSoftDeleteBillMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (billId: string) => softDeleteBill(businessId, billId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}
