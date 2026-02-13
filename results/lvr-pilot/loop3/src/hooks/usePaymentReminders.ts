// =============================================================================
// PAYMENT REMINDERS — React Query hooks for reminder CRUD
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
  PaymentReminderRow,
  PaymentReminderInsert,
  PaymentReminderUpdate,
  PaymentReminderWithRelations,
  PaymentReminderFilters,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchReminders(
  businessId: string,
  filters?: PaymentReminderFilters
): Promise<PaymentReminderWithRelations[]> {
  let query = supabase
    .from('payment_reminders')
    .select(
      `
      id, business_id, invoice_id, customer_id, reminder_type,
      reminder_date, sent_date, sent_by, reminder_method,
      message_content, status, response_notes, next_reminder_date,
      created_at, created_by,
      invoices (invoice_number, total_amount, balance_due),
      customers (first_name, last_name, company_name, email)
    `
    )
    .eq('business_id', businessId);

  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.reminder_type && filters.reminder_type !== 'all') {
    query = query.eq('reminder_type', filters.reminder_type);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('reminder_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('reminder_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `message_content.ilike.%${filters.search}%,response_notes.ilike.%${filters.search}%`
    );
  }

  const { data, error } = await query.order('reminder_date', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchReminder(
  businessId: string,
  reminderId: string
): Promise<PaymentReminderWithRelations> {
  const { data, error } = await supabase
    .from('payment_reminders')
    .select(
      `
      id, business_id, invoice_id, customer_id, reminder_type,
      reminder_date, sent_date, sent_by, reminder_method,
      message_content, status, response_notes, next_reminder_date,
      created_at, created_by,
      invoices (invoice_number, total_amount, balance_due),
      customers (first_name, last_name, company_name, email)
    `
    )
    .eq('id', reminderId)
    .eq('business_id', businessId)
    .single();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

async function createReminder(
  businessId: string,
  data: PaymentReminderInsert
): Promise<PaymentReminderRow> {
  const userId = await getCurrentUserId();

  const { data: reminder, error } = await supabase
    .from('payment_reminders')
    .insert({
      ...data,
      business_id: businessId,
      status: data.status ?? 'pending',
      created_by: userId,
    })
    .select()
    .single();

  if (error) throw error;
  return reminder;
}

async function updateReminder(
  businessId: string,
  reminderId: string,
  data: PaymentReminderUpdate
): Promise<PaymentReminderRow> {
  const { data: reminder, error } = await supabase
    .from('payment_reminders')
    .update(data)
    .eq('id', reminderId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return reminder;
}

async function markReminderSent(
  businessId: string,
  reminderId: string
): Promise<PaymentReminderRow> {
  const userId = await getCurrentUserId();

  const { data: reminder, error } = await supabase
    .from('payment_reminders')
    .update({
      status: 'sent' as const,
      sent_date: new Date().toISOString(),
      sent_by: userId,
    })
    .eq('id', reminderId)
    .eq('business_id', businessId)
    .select()
    .single();

  if (error) throw error;
  return reminder;
}

async function deleteReminder(
  businessId: string,
  reminderId: string
): Promise<void> {
  const { error } = await supabase
    .from('payment_reminders')
    .delete()
    .eq('id', reminderId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function usePaymentRemindersQuery(filters?: PaymentReminderFilters) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.reminders.list(businessId, filters),
    queryFn: () => fetchReminders(businessId, filters),
    enabled: !!businessId,
    staleTime: LIST_STALE_TIME,
  });
}

export function usePaymentReminderQuery(reminderId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.reminders.detail(businessId, reminderId),
    queryFn: () => fetchReminder(businessId, reminderId),
    enabled: !!businessId && !!reminderId,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useCreateReminderMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PaymentReminderInsert) =>
      createReminder(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.reminders.all });
    },
  });
}

export function useUpdateReminderMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: PaymentReminderUpdate;
    }) => updateReminder(businessId, id, data),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.reminders.all });
    },
  });
}

export function useMarkReminderSentMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reminderId: string) =>
      markReminderSent(businessId, reminderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.reminders.all });
    },
  });
}

export function useDeleteReminderMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reminderId: string) =>
      deleteReminder(businessId, reminderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.reminders.all });
    },
  });
}
