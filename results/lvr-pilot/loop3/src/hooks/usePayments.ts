// =============================================================================
// PAYMENTS — React Query hooks for unified payment management
// Fixes: Missing PaymentsService.getPaymentsByType() method call
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
  PaymentRow,
  PaymentInsert,
  PaymentUpdate,
  PaymentWithRelations,
  PaymentFilters,
  PaymentType,
  PaginationParams,
  PaginatedResult,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchPayments(
  businessId: string,
  filters?: PaymentFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<PaymentWithRelations>> {
  let query = supabase
    .from('payments')
    .select(
      `
      id, business_id, payment_number, payment_date, payment_method,
      amount, currency, exchange_rate, reference_number, check_number,
      bank_account_id, payment_type, customer_id, supplier_id,
      status, posted_to_gl, gl_journal_entry_id, notes,
      created_by, created_at, updated_at,
      customers (first_name, last_name, company_name, email),
      suppliers (name, email),
      payment_applications (id, payment_id, invoice_id, bill_id, applied_amount, application_date, notes)
    `,
      { count: 'exact' }
    )
    .eq('business_id', businessId);

  if (filters?.payment_type && filters.payment_type !== 'all') {
    query = query.eq('payment_type', filters.payment_type);
  }
  if (filters?.payment_method && filters.payment_method !== 'all') {
    query = query.eq('payment_method', filters.payment_method);
  }
  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('payment_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('payment_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `payment_number.ilike.%${filters.search}%,reference_number.ilike.%${filters.search}%,notes.ilike.%${filters.search}%`
    );
  }

  const { query: paginatedQuery, page, pageSize } = applyPagination(query, pagination);
  const finalQuery = paginatedQuery.order('payment_date', { ascending: false });

  const { data, error, count } = await finalQuery;
  if (error) throw error;

  return buildPaginatedResult(data, count, page, pageSize);
}

async function fetchPayment(
  businessId: string,
  paymentId: string
): Promise<PaymentWithRelations> {
  const { data, error } = await supabase
    .from('payments')
    .select(
      `
      id, business_id, payment_number, payment_date, payment_method,
      amount, currency, exchange_rate, reference_number, check_number,
      bank_account_id, payment_type, customer_id, supplier_id,
      status, posted_to_gl, gl_journal_entry_id, notes,
      created_by, created_at, updated_at,
      customers (first_name, last_name, company_name, email),
      suppliers (name, email),
      payment_applications (id, payment_id, invoice_id, bill_id, applied_amount, application_date, notes)
    `
    )
    .eq('id', paymentId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createPayment(
  businessId: string,
  data: PaymentInsert
): Promise<PaymentRow> {
  const userId = await getCurrentUserId();

  // Generate payment number
  const { data: lastPayment } = await supabase
    .from('payments')
    .select('payment_number')
    .eq('business_id', businessId)
    .order('created_at', { ascending: false })
    .limit(1)
    .single();

  const nextNumber = lastPayment
    ? `PAY-${(parseInt(lastPayment.payment_number.replace(/\D/g, '') || '0', 10) + 1)
        .toString()
        .padStart(5, '0')}`
    : 'PAY-00001';

  const { data: payment, error } = await supabase
    .from('payments')
    .insert({
      ...data,
      business_id: businessId,
      payment_number: nextNumber,
      currency: data.currency ?? 'BSD',
      exchange_rate: data.exchange_rate ?? 1,
      status: 'pending' as const,
      posted_to_gl: false,
      created_by: userId,
    })
    .select()
    .single();

  if (error) throw error;
  return payment;
}

async function voidPayment(
  businessId: string,
  paymentId: string
): Promise<PaymentRow> {
  const { data: payment, error } = await supabase
    .from('payments')
    .update({ status: 'cancelled' as const })
    .eq('id', paymentId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return payment;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function usePaymentsQuery(
  filters?: PaymentFilters,
  pagination?: PaginationParams
) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.payments.list(businessId, filters, pagination),
    queryFn: () => fetchPayments(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
    placeholderData: (previousData) => previousData,
  });
}

export function usePaymentQuery(paymentId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.payments.detail(businessId, paymentId),
    queryFn: () => fetchPayment(businessId, paymentId),
    enabled: !!businessId && !!paymentId,
  });
}

/**
 * Payments filtered by type (customer or supplier).
 * Fix: Uses filters parameter instead of non-existent getPaymentsByType() method.
 */
export function usePaymentsByTypeQuery(type: PaymentType) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.payments.byType(businessId, type),
    queryFn: () =>
      fetchPayments(businessId, { payment_type: type }),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreatePaymentMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentInsert) => createPayment(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.payments.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

/** Void/cancel a payment */
export function useVoidPaymentMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (paymentId: string) => voidPayment(businessId, paymentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.payments.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}
