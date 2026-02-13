// =============================================================================
// INVOICES — React Query hooks for invoice CRUD + aggregations
// Fixes: BUG-L02 (separate aggregation queries)
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
  InvoiceRow,
  InvoiceInsert,
  InvoiceUpdate,
  InvoiceWithRelations,
  InvoiceFilters,
  InvoiceAggregations,
  PaginationParams,
  PaginatedResult,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchInvoices(
  businessId: string,
  filters?: InvoiceFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<InvoiceWithRelations>> {
  let query = supabase
    .from('invoices')
    .select(
      `
      id, business_id, customer_id, invoice_number, invoice_date, due_date,
      status, subtotal, tax_amount, total_amount, amount_paid, balance_due,
      notes, is_deleted, created_by, created_at, updated_at,
      customers (id, first_name, last_name, email, company_name),
      invoice_line_items (id, product_id, description, quantity, unit_price, line_total)
    `,
      { count: 'exact' }
    )
    .eq('business_id', businessId)
    .eq('is_deleted', false);

  // Apply filters
  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.customer_id && filters.customer_id !== 'all') {
    query = query.eq('customer_id', filters.customer_id);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('invoice_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('invoice_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `invoice_number.ilike.%${filters.search}%,notes.ilike.%${filters.search}%`
    );
  }

  // Apply pagination and ordering
  const { query: paginatedQuery, page, pageSize } = applyPagination(query, pagination);
  const finalQuery = paginatedQuery.order('created_at', { ascending: false });

  const { data, error, count } = await finalQuery;
  if (error) throw error;

  // Compute overdue status client-side for sent invoices past due date
  const today = new Date().toISOString().split('T')[0];
  const processed = (data ?? []).map((inv) => ({
    ...inv,
    status:
      inv.status === 'sent' && inv.due_date < today && inv.balance_due > 0
        ? ('overdue' as const)
        : inv.status,
  }));

  return buildPaginatedResult(processed, count, page, pageSize);
}

async function fetchInvoice(
  businessId: string,
  invoiceId: string
): Promise<InvoiceWithRelations> {
  const { data, error } = await supabase
    .from('invoices')
    .select(
      `
      id, business_id, customer_id, invoice_number, invoice_date, due_date,
      status, subtotal, tax_amount, total_amount, amount_paid, balance_due,
      notes, is_deleted, created_by, created_at, updated_at,
      customers (id, first_name, last_name, email, company_name),
      invoice_line_items (id, product_id, description, quantity, unit_price, line_total)
    `
    )
    .eq('id', invoiceId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

/**
 * BUG-L02 FIX: Separate aggregation query.
 * Never derived from paginated page data.
 */
async function fetchInvoiceAggregations(
  businessId: string
): Promise<InvoiceAggregations> {
  const { data, error } = await supabase
    .from('invoices')
    .select('status, total_amount, balance_due')
    .eq('business_id', businessId)
    .eq('is_deleted', false);

  if (error) throw error;

  return (data ?? []).reduce(
    (acc, inv) => {
      acc.totalAmount += inv.total_amount ?? 0;
      acc.totalCount++;
      if (inv.status === 'paid') {
        acc.paidAmount += inv.total_amount ?? 0;
        acc.paidCount++;
      } else if (inv.status === 'overdue') {
        acc.overdueAmount += inv.balance_due ?? 0;
        acc.overdueCount++;
        acc.outstandingAmount += inv.balance_due ?? 0;
        acc.outstandingCount++;
      } else if (inv.status !== 'cancelled') {
        acc.outstandingAmount += inv.balance_due ?? 0;
        acc.outstandingCount++;
      }
      return acc;
    },
    {
      totalAmount: 0,
      paidAmount: 0,
      outstandingAmount: 0,
      overdueAmount: 0,
      totalCount: 0,
      paidCount: 0,
      outstandingCount: 0,
      overdueCount: 0,
    } as InvoiceAggregations
  );
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createInvoice(
  businessId: string,
  data: InvoiceInsert
): Promise<InvoiceRow> {
  const userId = await getCurrentUserId();
  const { line_items, ...invoiceData } = data;

  // Generate invoice number
  const { data: lastInvoice } = await supabase
    .from('invoices')
    .select('invoice_number')
    .eq('business_id', businessId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  const nextNumber = lastInvoice
    ? `INV-${(parseInt(lastInvoice.invoice_number.replace(/\D/g, '') || '0', 10) + 1)
        .toString()
        .padStart(5, '0')}`
    : 'INV-00001';

  // Insert invoice
  const { data: invoice, error: invoiceError } = await supabase
    .from('invoices')
    .insert({
      ...invoiceData,
      business_id: businessId,
      invoice_number: nextNumber,
      amount_paid: 0,
      balance_due: invoiceData.total_amount,
      is_deleted: false,
      created_by: userId,
    })
    .select()
    .single();

  if (invoiceError) throw invoiceError;

  // Insert line items
  if (line_items.length > 0) {
    const { error: lineItemsError } = await supabase
      .from('invoice_line_items')
      .insert(
        line_items.map((item) => ({
          invoice_id: invoice.id,
          product_id: item.product_id ?? null,
          description: item.description,
          quantity: item.quantity,
          unit_price: item.unit_price,
          line_total: item.line_total,
        }))
      );

    if (lineItemsError) throw lineItemsError;
  }

  return invoice;
}

async function updateInvoice(
  businessId: string,
  invoiceId: string,
  data: InvoiceUpdate
): Promise<InvoiceRow> {
  const { data: invoice, error } = await supabase
    .from('invoices')
    .update(data)
    .eq('id', invoiceId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return invoice;
}

async function softDeleteInvoice(
  businessId: string,
  invoiceId: string
): Promise<void> {
  const { error } = await supabase
    .from('invoices')
    .update({ is_deleted: true, status: 'cancelled' as const })
    .eq('id', invoiceId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

/** List invoices with pagination and filters */
export function useInvoicesQuery(
  filters?: InvoiceFilters,
  pagination?: PaginationParams
) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.list(businessId, filters, pagination),
    queryFn: () => fetchInvoices(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
    placeholderData: (previousData) => previousData,
  });
}

/** Single invoice detail with relations */
export function useInvoiceQuery(invoiceId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.detail(businessId, invoiceId),
    queryFn: () => fetchInvoice(businessId, invoiceId),
    enabled: !!businessId && !!invoiceId,
  });
}

/** Invoice aggregations -- separate from list query (BUG-L02 fix) */
export function useInvoiceAggregationsQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.aggregations(businessId),
    queryFn: () => fetchInvoiceAggregations(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

/** Create a new invoice with line items */
export function useCreateInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InvoiceInsert) => createInvoice(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accountsReceivable.all });
    },
  });
}

/** Update an existing invoice */
export function useUpdateInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InvoiceUpdate }) =>
      updateInvoice(businessId, id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: accountingKeys.invoices.all });

      const previousData = queryClient.getQueriesData({
        queryKey: accountingKeys.invoices.all,
      });

      // Optimistic update on list queries
      queryClient.setQueriesData(
        { queryKey: accountingKeys.invoices.all },
        (old: unknown) => {
          if (!old || typeof old !== 'object') return old;
          const typed = old as PaginatedResult<InvoiceRow>;
          if (!typed.data) return old;
          return {
            ...typed,
            data: typed.data.map((inv: InvoiceRow) =>
              inv.id === id ? { ...inv, ...data } : inv
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
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accountsReceivable.all });
    },
  });
}

/** Soft-delete an invoice (sets is_deleted=true and status=cancelled) */
export function useSoftDeleteInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invoiceId: string) => softDeleteInvoice(businessId, invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accountsReceivable.all });
    },
  });
}
