// =============================================================================
// BULK PAYMENTS — React Query hooks for batch payment operations
// Fix: NO setTimeout fake processing — real bill payment execution
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  getCurrentUserId,
  LIST_STALE_TIME,
} from './useAccountingQueries';
import type {
  BulkPaymentBatchRow,
  BulkPaymentBatchInsert,
  BulkPaymentBatchFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchBatches(
  businessId: string,
  filters?: BulkPaymentBatchFilters
): Promise<BulkPaymentBatchRow[]> {
  let query = supabase
    .from('bulk_payment_batches')
    .select(
      `
      id, business_id, batch_name, payment_date,
      bill_count, total_amount, status, processed_at,
      created_by, created_at
    `
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
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

async function fetchBatch(
  businessId: string,
  batchId: string
): Promise<BulkPaymentBatchRow> {
  const { data, error } = await supabase
    .from('bulk_payment_batches')
    .select(
      `
      id, business_id, batch_name, payment_date,
      bill_count, total_amount, status, processed_at,
      created_by, created_at
    `
    )
    .eq('id', batchId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createBatch(
  businessId: string,
  data: BulkPaymentBatchInsert
): Promise<BulkPaymentBatchRow> {
  const userId = await getCurrentUserId();

  // Fetch bills to calculate totals
  const { data: bills, error: billsError } = await supabase
    .from('bills')
    .select('id, balance_due')
    .eq('business_id', businessId)
    .in('id', data.bill_ids)
    .eq('is_deleted', false)
    .gt('balance_due', 0);

  if (billsError) throw billsError;

  const totalAmount = (bills ?? []).reduce(
    (sum, bill) => sum + (bill.balance_due ?? 0),
    0
  );

  const { data: batch, error } = await supabase
    .from('bulk_payment_batches')
    .insert({
      business_id: businessId,
      batch_name: data.batch_name,
      payment_date: data.payment_date,
      bill_count: (bills ?? []).length,
      total_amount: totalAmount,
      status: 'pending' as const,
      created_by: userId,
    })
    .select()
    .single();

  if (error) throw error;
  return batch;
}

/**
 * Process a payment batch — creates actual bill payments.
 * NO setTimeout fake processing. Each bill gets a real payment record.
 */
async function processBatch(
  businessId: string,
  batchId: string,
  billIds: string[]
): Promise<BulkPaymentBatchRow> {
  const userId = await getCurrentUserId();

  // Set batch to processing
  await supabase
    .from('bulk_payment_batches')
    .update({ status: 'processing' as const })
    .eq('id', batchId)
    .eq('business_id', businessId);

  let allSucceeded = true;

  // Process each bill payment
  for (const billId of billIds) {
    try {
      // Fetch bill details
      const { data: bill, error: billError } = await supabase
        .from('bills')
        .select('id, balance_due, total_amount')
        .eq('id', billId)
        .eq('business_id', businessId)
        .single();

      if (billError || !bill) {
        allSucceeded = false;
        continue;
      }

      if (bill.balance_due <= 0) continue;

      // Create bill payment
      const { error: paymentError } = await supabase
        .from('bill_payments')
        .insert({
          bill_id: billId,
          business_id: businessId,
          payment_amount: bill.balance_due,
          payment_date: new Date().toISOString().split('T')[0],
          payment_method: 'bank_transfer',
          created_by: userId,
        });

      if (paymentError) {
        allSucceeded = false;
        continue;
      }

      // Update bill status and amounts
      const newAmountPaid =
        (bill.total_amount ?? 0) - (bill.balance_due ?? 0) + bill.balance_due;

      await supabase
        .from('bills')
        .update({
          amount_paid: newAmountPaid,
          balance_due: 0,
          status: 'paid' as const,
        })
        .eq('id', billId)
        .eq('business_id', businessId);
    } catch {
      allSucceeded = false;
    }
  }

  // Update batch status
  const { data: batch, error } = await supabase
    .from('bulk_payment_batches')
    .update({
      status: allSucceeded ? ('completed' as const) : ('failed' as const),
      processed_at: new Date().toISOString(),
    })
    .eq('id', batchId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return batch;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useBulkPaymentBatchesQuery(filters?: BulkPaymentBatchFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bulkPayments.list(businessId, filters),
    queryFn: () => fetchBatches(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function useBulkPaymentBatchQuery(batchId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bulkPayments.detail(businessId, batchId),
    queryFn: () => fetchBatch(businessId, batchId),
    enabled: !!businessId && !!batchId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateBatchMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BulkPaymentBatchInsert) =>
      createBatch(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bulkPayments.all,
      });
    },
  });
}

/**
 * Process a batch — real bill payment creation, no setTimeout fake.
 */
export function useProcessBatchMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      batchId,
      billIds,
    }: {
      batchId: string;
      billIds: string[];
    }) => processBatch(businessId, batchId, billIds),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.bulkPayments.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all });
      queryClient.invalidateQueries({
        queryKey: accountingKeys.billPayments.all,
      });
      queryClient.invalidateQueries({ queryKey: accountingKeys.dashboard.all });
    },
  });
}
