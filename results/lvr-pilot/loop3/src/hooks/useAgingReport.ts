// =============================================================================
// AGING REPORT — AR and AP aging calculation with CORRECT bucket keys
// Fixes: BUG-H06 (inconsistent bucket keys between query and component)
// Bucket keys: 'current', '30', '60', '90', '90+' (as specified)
// =============================================================================

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  AGGREGATION_STALE_TIME,
} from './useAccountingQueries';
import type { AgingBucket } from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

/**
 * BUG-H06 FIX: AR Aging Report with consistent bucket keys.
 *
 * Old code used inconsistent keys across different files:
 *   - 'days_30', 'days_60', 'days_90' in one place
 *   - 'thirtyDays', 'sixtyDays' in another
 *   - '30_days', '60_days' in yet another
 *
 * This uses the correct, consistent keys:
 *   'current' (0-30 days), '30' (31-60), '60' (61-90), '90' (91-120), '90+' (120+)
 */
async function fetchARAgingReport(
  businessId: string
): Promise<AgingBucket> {
  const { data, error } = await supabase
    .from('invoices')
    .select('due_date, balance_due, status')
    .eq('business_id', businessId)
    .eq('is_deleted', false)
    .gt('balance_due', 0)
    .neq('status', 'cancelled')
    .neq('status', 'paid');

  if (error) throw error;

  const today = new Date();
  const result: AgingBucket = {
    current: 0,
    '30': 0,
    '60': 0,
    '90': 0,
    '90+': 0,
    total: 0,
  };

  for (const inv of data ?? []) {
    const dueDate = new Date(inv.due_date);
    const daysOverdue = Math.floor(
      (today.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    const amount = inv.balance_due ?? 0;
    result.total += amount;

    if (daysOverdue <= 30) {
      result.current += amount;
    } else if (daysOverdue <= 60) {
      result['30'] += amount;
    } else if (daysOverdue <= 90) {
      result['60'] += amount;
    } else if (daysOverdue <= 120) {
      result['90'] += amount;
    } else {
      result['90+'] += amount;
    }
  }

  return result;
}

/**
 * AP Aging Report — same bucket keys, applied to bills instead of invoices.
 */
async function fetchAPAgingReport(
  businessId: string
): Promise<AgingBucket> {
  const { data, error } = await supabase
    .from('bills')
    .select('due_date, balance_due, status')
    .eq('business_id', businessId)
    .eq('is_deleted', false)
    .gt('balance_due', 0)
    .neq('status', 'cancelled')
    .neq('status', 'paid');

  if (error) throw error;

  const today = new Date();
  const result: AgingBucket = {
    current: 0,
    '30': 0,
    '60': 0,
    '90': 0,
    '90+': 0,
    total: 0,
  };

  for (const bill of data ?? []) {
    const dueDate = new Date(bill.due_date);
    const daysOverdue = Math.floor(
      (today.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24)
    );
    const amount = bill.balance_due ?? 0;
    result.total += amount;

    if (daysOverdue <= 30) {
      result.current += amount;
    } else if (daysOverdue <= 60) {
      result['30'] += amount;
    } else if (daysOverdue <= 90) {
      result['60'] += amount;
    } else if (daysOverdue <= 120) {
      result['90'] += amount;
    } else {
      result['90+'] += amount;
    }
  }

  return result;
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

/** AR Aging Report with correct bucket keys */
export function useARAgingQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.dashboard.arAging(businessId),
    queryFn: () => fetchARAgingReport(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}

/** AP Aging Report with correct bucket keys */
export function useAPAgingQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.dashboard.apAging(businessId),
    queryFn: () => fetchAPAgingReport(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}
