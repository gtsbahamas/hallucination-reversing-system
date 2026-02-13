// =============================================================================
// PAYMENT PLANS — React Query hooks for plan CRUD + installment management
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
  PaymentPlanRow,
  PaymentPlanInsert,
  PaymentPlanUpdate,
  PaymentPlanWithRelations,
  PaymentPlanInstallmentRow,
  PaymentPlanInstallmentUpdate,
  PaymentPlanFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchPaymentPlans(
  businessId: string,
  filters?: PaymentPlanFilters
): Promise<PaymentPlanWithRelations[]> {
  let query = supabase
    .from('payment_plans')
    .select(
      `
      id, business_id, customer_id, plan_name, total_amount,
      remaining_amount, installment_amount, frequency,
      start_date, end_date, status, created_by, created_at, updated_at,
      customers (first_name, last_name, company_name, email),
      payment_plan_installments (
        id, payment_plan_id, installment_number, due_date,
        amount, paid_amount, status, paid_date, created_at
      )
    `
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.customer_id && filters.customer_id !== 'all') {
    query = query.eq('customer_id', filters.customer_id);
  }
  if (filters?.search) {
    query = query.ilike('plan_name', `%${filters.search}%`);
  }

  const { data, error } = await query.order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchPaymentPlan(
  businessId: string,
  planId: string
): Promise<PaymentPlanWithRelations> {
  const { data, error } = await supabase
    .from('payment_plans')
    .select(
      `
      id, business_id, customer_id, plan_name, total_amount,
      remaining_amount, installment_amount, frequency,
      start_date, end_date, status, created_by, created_at, updated_at,
      customers (first_name, last_name, company_name, email),
      payment_plan_installments (
        id, payment_plan_id, installment_number, due_date,
        amount, paid_amount, status, paid_date, created_at
      )
    `
    )
    .eq('id', planId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

async function fetchInstallments(
  planId: string
): Promise<PaymentPlanInstallmentRow[]> {
  const { data, error } = await supabase
    .from('payment_plan_installments')
    .select(
      `
      id, payment_plan_id, installment_number, due_date,
      amount, paid_amount, status, paid_date, created_at
    `
    )
    .eq('payment_plan_id', planId)
    .order('installment_number', { ascending: true });

  if (error) throw error;
  return data ?? [];
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createPaymentPlan(
  businessId: string,
  data: PaymentPlanInsert
): Promise<PaymentPlanRow> {
  const userId = await getCurrentUserId();

  // Calculate end date based on frequency and installments
  const startDate = new Date(data.start_date);
  let endDate: Date;
  switch (data.frequency) {
    case 'weekly':
      endDate = new Date(startDate.getTime() + data.number_of_installments * 7 * 24 * 60 * 60 * 1000);
      break;
    case 'biweekly':
      endDate = new Date(startDate.getTime() + data.number_of_installments * 14 * 24 * 60 * 60 * 1000);
      break;
    case 'monthly':
    default:
      endDate = new Date(startDate);
      endDate.setMonth(endDate.getMonth() + data.number_of_installments);
      break;
  }

  // Create plan
  const { data: plan, error: planError } = await supabase
    .from('payment_plans')
    .insert({
      business_id: businessId,
      customer_id: data.customer_id,
      plan_name: data.plan_name,
      total_amount: data.total_amount,
      remaining_amount: data.total_amount,
      installment_amount: data.installment_amount,
      frequency: data.frequency,
      start_date: data.start_date,
      end_date: endDate.toISOString().split('T')[0],
      status: 'active' as const,
      created_by: userId,
    })
    .select()
    .single();

  if (planError) throw planError;

  // Create installments
  const installments = [];
  let installmentDate = new Date(data.start_date);

  for (let i = 1; i <= data.number_of_installments; i++) {
    installments.push({
      payment_plan_id: plan.id,
      installment_number: i,
      due_date: installmentDate.toISOString().split('T')[0],
      amount: data.installment_amount,
      paid_amount: 0,
      status: 'pending' as const,
    });

    // Advance date based on frequency
    switch (data.frequency) {
      case 'weekly':
        installmentDate = new Date(installmentDate.getTime() + 7 * 24 * 60 * 60 * 1000);
        break;
      case 'biweekly':
        installmentDate = new Date(installmentDate.getTime() + 14 * 24 * 60 * 60 * 1000);
        break;
      case 'monthly':
        installmentDate.setMonth(installmentDate.getMonth() + 1);
        break;
    }
  }

  const { error: installmentsError } = await supabase
    .from('payment_plan_installments')
    .insert(installments);

  if (installmentsError) throw installmentsError;

  return plan;
}

async function updatePaymentPlan(
  businessId: string,
  planId: string,
  data: PaymentPlanUpdate
): Promise<PaymentPlanRow> {
  const { data: plan, error } = await supabase
    .from('payment_plans')
    .update(data)
    .eq('id', planId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return plan;
}

async function recordInstallmentPayment(
  planId: string,
  installmentId: string,
  paidAmount: number
): Promise<PaymentPlanInstallmentRow> {
  // Update installment
  const { data: installment, error: installmentError } = await supabase
    .from('payment_plan_installments')
    .update({
      paid_amount: paidAmount,
      status: paidAmount >= (await getInstallmentAmount(installmentId))
        ? ('paid' as const)
        : ('partial' as const),
      paid_date: new Date().toISOString().split('T')[0],
    })
    .eq('id', installmentId)
    .eq('payment_plan_id', planId)
    .select()
    .single();

  if (installmentError) throw installmentError;

  // Update plan remaining_amount
  const { data: installments, error: sumError } = await supabase
    .from('payment_plan_installments')
    .select('paid_amount')
    .eq('payment_plan_id', planId);

  if (sumError) throw sumError;

  const totalPaid = (installments ?? []).reduce((sum, i) => sum + (i.paid_amount ?? 0), 0);

  const { data: plan } = await supabase
    .from('payment_plans')
    .select('total_amount')
    .eq('id', planId)
    .single();

  const remaining = (plan?.total_amount ?? 0) - totalPaid;

  await supabase
    .from('payment_plans')
    .update({
      remaining_amount: remaining,
      status: remaining <= 0 ? ('completed' as const) : undefined,
    })
    .eq('id', planId);

  return installment;
}

async function getInstallmentAmount(installmentId: string): Promise<number> {
  const { data } = await supabase
    .from('payment_plan_installments')
    .select('amount')
    .eq('id', installmentId)
    .single();
  return data?.amount ?? 0;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function usePaymentPlansQuery(filters?: PaymentPlanFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.paymentPlans.list(businessId, filters),
    queryFn: () => fetchPaymentPlans(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function usePaymentPlanQuery(planId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.paymentPlans.detail(businessId, planId),
    queryFn: () => fetchPaymentPlan(businessId, planId),
    enabled: !!businessId && !!planId,
  });
}

export function useInstallmentsQuery(planId: string) {
  return useQuery({
    queryKey: accountingKeys.paymentPlans.installments(planId),
    queryFn: () => fetchInstallments(planId),
    enabled: !!planId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreatePaymentPlanMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentPlanInsert) =>
      createPaymentPlan(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.paymentPlans.all });
    },
  });
}

export function useUpdatePaymentPlanMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: PaymentPlanUpdate }) =>
      updatePaymentPlan(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.paymentPlans.all });
    },
  });
}

export function useRecordInstallmentMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      planId,
      installmentId,
      paidAmount,
    }: {
      planId: string;
      installmentId: string;
      paidAmount: number;
    }) => recordInstallmentPayment(planId, installmentId, paidAmount),
    onSuccess: (_, { planId }) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.paymentPlans.all });
      queryClient.invalidateQueries({
        queryKey: accountingKeys.paymentPlans.installments(planId),
      });
    },
  });
}
