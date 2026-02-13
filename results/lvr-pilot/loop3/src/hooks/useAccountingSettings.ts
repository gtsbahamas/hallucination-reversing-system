// =============================================================================
// ACCOUNTING SETTINGS — React Query hooks for settings query + upsert
// =============================================================================

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  AGGREGATION_STALE_TIME,
} from './useAccountingQueries';
import type {
  AccountingSettingsRow,
  AccountingSettingsUpdate,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

async function fetchSettings(
  businessId: string
): Promise<AccountingSettingsRow | null> {
  const { data, error } = await supabase
    .from('accounting_settings')
    .select(
      `
      id, business_id, auto_post_invoices, auto_post_bills,
      auto_post_expenses, auto_post_pos_sales,
      inventory_valuation_method, default_tax_rate
    `
    )
    .eq('business_id', businessId)
    .maybeSingle();

  if (error) throw error;
  return data;
}

// =============================================================================
// MUTATION FUNCTIONS
// =============================================================================

/**
 * Upsert accounting settings — creates if not exists, updates if exists.
 * Settings are a singleton per business (one row per business_id).
 */
async function upsertSettings(
  businessId: string,
  data: AccountingSettingsUpdate
): Promise<AccountingSettingsRow> {
  // Check if settings exist
  const { data: existing } = await supabase
    .from('accounting_settings')
    .select('id')
    .eq('business_id', businessId)
    .maybeSingle();

  if (existing) {
    // Update existing
    const { data: settings, error } = await supabase
      .from('accounting_settings')
      .update(data)
      .eq('business_id', businessId)
      .select()
      .single();

    if (error) throw error;
    return settings;
  } else {
    // Insert new
    const { data: settings, error } = await supabase
      .from('accounting_settings')
      .insert({
        ...data,
        business_id: businessId,
        auto_post_invoices: data.auto_post_invoices ?? false,
        auto_post_bills: data.auto_post_bills ?? false,
        auto_post_expenses: data.auto_post_expenses ?? false,
        auto_post_pos_sales: data.auto_post_pos_sales ?? false,
        inventory_valuation_method: data.inventory_valuation_method ?? 'fifo',
        default_tax_rate: data.default_tax_rate ?? 0,
      })
      .select()
      .single();

    if (error) throw error;
    return settings;
  }
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

export function useAccountingSettingsQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.settings.detail(businessId),
    queryFn: () => fetchSettings(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}

// =============================================================================
// MUTATION HOOKS
// =============================================================================

export function useUpdateSettingsMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AccountingSettingsUpdate) =>
      upsertSettings(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: accountingKeys.settings.all,
      });
    },
  });
}
