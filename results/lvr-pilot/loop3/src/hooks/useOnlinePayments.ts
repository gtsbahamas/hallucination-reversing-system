// =============================================================================
// ONLINE PAYMENTS — React Query hooks for token management + payment processing
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  OnlinePaymentRow,
  OnlinePaymentInsert,
  OnlinePaymentUpdate,
  OnlinePaymentWithCustomer,
  OnlinePaymentFilters,
  CustomerPaymentTokenRow,
  CustomerPaymentTokenInsert,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchOnlinePayments(
  businessId: string,
  filters?: OnlinePaymentFilters
): Promise<OnlinePaymentWithCustomer[]> {
  let query = supabase
    .from('online_payments')
    .select(
      `
      id, business_id, customer_id, payment_amount, payment_method,
      transaction_id, status, payment_date, applied_to_invoices,
      gateway_response, created_at,
      customers (first_name, last_name, company_name, email)
    `
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.customer_id && filters.customer_id !== 'all') {
    query = query.eq('customer_id', filters.customer_id);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('payment_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('payment_date', filters.dateRange.to);
  }

  const { data, error } = await query.order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchTokens(
  businessId: string
): Promise<CustomerPaymentTokenRow[]> {
  const { data, error } = await supabase
    .from('customer_payment_tokens')
    .select(
      `
      id, business_id, customer_id, token, expires_at, is_used, created_at
    `
    )
    .eq('business_id', businessId)
    .eq('is_used', false)
    .gte('expires_at', new Date().toISOString())
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchTokenByCustomer(
  businessId: string,
  customerId: string
): Promise<CustomerPaymentTokenRow | null> {
  const { data, error } = await supabase
    .from('customer_payment_tokens')
    .select(
      `
      id, business_id, customer_id, token, expires_at, is_used, created_at
    `
    )
    .eq('business_id', businessId)
    .eq('customer_id', customerId)
    .eq('is_used', false)
    .gte('expires_at', new Date().toISOString())
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function processOnlinePayment(
  businessId: string,
  data: OnlinePaymentInsert
): Promise<OnlinePaymentRow> {
  // Create online payment record
  const { data: payment, error } = await supabase
    .from('online_payments')
    .insert({
      ...data,
      business_id: businessId,
      status: 'pending' as const,
      payment_date: new Date().toISOString(),
      gateway_response: {},
    })
    .select()
    .single();

  if (error) throw error;

  // Apply to invoices if specified
  if (data.applied_to_invoices.length > 0) {
    for (const invoiceId of data.applied_to_invoices) {
      const { data: invoice } = await supabase
        .from('invoices')
        .select('id, balance_due, amount_paid, total_amount')
        .eq('id', invoiceId)
        .eq('business_id', businessId)
        .single();

      if (!invoice) continue;

      // Create invoice payment
      await supabase.from('invoice_payments').insert({
        invoice_id: invoiceId,
        business_id: businessId,
        payment_amount: Math.min(data.payment_amount, invoice.balance_due),
        payment_method: data.payment_method,
        payment_date: new Date().toISOString().split('T')[0],
        created_by: data.customer_id,
      });

      // Update invoice balances
      const appliedAmount = Math.min(data.payment_amount, invoice.balance_due);
      await supabase
        .from('invoices')
        .update({
          amount_paid: (invoice.amount_paid ?? 0) + appliedAmount,
          balance_due: (invoice.balance_due ?? 0) - appliedAmount,
          status:
            (invoice.balance_due ?? 0) - appliedAmount <= 0
              ? ('paid' as const)
              : undefined,
        })
        .eq('id', invoiceId)
        .eq('business_id', businessId);
    }
  }

  // Mark as completed
  const { data: completedPayment, error: updateError } = await supabase
    .from('online_payments')
    .update({ status: 'completed' as const })
    .eq('id', payment.id)
    .select()
    .single();

  if (updateError) throw updateError;
  return completedPayment;
}

async function generatePaymentToken(
  businessId: string,
  data: CustomerPaymentTokenInsert
): Promise<CustomerPaymentTokenRow> {
  const { data: token, error } = await supabase
    .from('customer_payment_tokens')
    .insert({
      ...data,
      business_id: businessId,
      is_used: false,
    })
    .select()
    .single();

  if (error) throw error;
  return token;
}

async function markTokenUsed(
  businessId: string,
  tokenId: string
): Promise<void> {
  const { error } = await supabase
    .from('customer_payment_tokens')
    .update({ is_used: true })
    .eq('id', tokenId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useOnlinePaymentsQuery(filters?: OnlinePaymentFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.onlinePayments.list(businessId, filters),
    queryFn: () => fetchOnlinePayments(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function usePaymentTokensQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.onlinePayments.tokens(businessId),
    queryFn: () => fetchTokens(businessId),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function usePaymentTokenByCustomerQuery(customerId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.onlinePayments.tokenByCustomer(businessId, customerId),
    queryFn: () => fetchTokenByCustomer(businessId, customerId),
    enabled: !!businessId && !!customerId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useProcessOnlinePaymentMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: OnlinePaymentInsert) =>
      processOnlinePayment(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.onlinePayments.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all });
      queryClient.invalidateQueries({
        queryKey: accountingKeys.invoicePayments.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}

export function useGenerateTokenMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CustomerPaymentTokenInsert) =>
      generatePaymentToken(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.onlinePayments.tokens(businessId),
      });
    },
  });
}

export function useMarkTokenUsedMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tokenId: string) => markTokenUsed(businessId, tokenId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.onlinePayments.tokens(businessId),
      });
    },
  });
}
