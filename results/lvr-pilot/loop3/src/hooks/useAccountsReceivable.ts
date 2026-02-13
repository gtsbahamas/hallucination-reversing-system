// =============================================================================
// ACCOUNTS RECEIVABLE — AR summary returning `invoices` NOT `arTransactions`
// Fixes: BUG-H02 (component expects arTransactions but hook returns invoices)
// =============================================================================

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import {
  accountingKeys,
  useBusinessId,
  AGGREGATION_STALE_TIME,
} from './useAccountingQueries';
import type {
  AccountsReceivableSummary,
  InvoiceWithRelations,
  AgingBucket,
} from '../types/accounting';

// =============================================================================
// QUERY FUNCTIONS
// =============================================================================

/**
 * BUG-H02 FIX: AR summary returns `invoices` property, NOT `arTransactions`.
 *
 * The old code had a mismatch:
 *   - The hook returned data under `invoices` key
 *   - The component destructured `arTransactions` from the hook
 *   - Result: component got `undefined`, rendered nothing
 *
 * This hook explicitly returns `invoices` and the component must use that key.
 * The AccountsReceivableSummary type enforces this contract.
 */
async function fetchARSummary(
  businessId: string
): Promise<AccountsReceivableSummary> {
  // Fetch all outstanding invoices (balance_due > 0, not cancelled/paid)
  const { data: invoices, error } = await supabase
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
    .eq('business_id', businessId)
    .eq('is_deleted', false)
    .gt('balance_due', 0)
    .neq('status', 'cancelled')
    .neq('status', 'paid')
    .order('due_date', { ascending: true });

  if (error) throw error;

  const invoiceList = (invoices ?? []) as InvoiceWithRelations[];
  const today = new Date();

  // Calculate totals
  let totalOutstanding = 0;
  let totalOverdue = 0;

  const aging: AgingBucket = {
    current: 0,
    '30': 0,
    '60': 0,
    '90': 0,
    '90+': 0,
    total: 0,
  };

  for (const inv of invoiceList) {
    const amount = inv.balance_due ?? 0;
    totalOutstanding += amount;
    aging.total += amount;

    const dueDate = new Date(inv.due_date);
    const daysOverdue = Math.floor(
      (today.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysOverdue > 0) {
      totalOverdue += amount;
    }

    if (daysOverdue <= 30) {
      aging.current += amount;
    } else if (daysOverdue <= 60) {
      aging['30'] += amount;
    } else if (daysOverdue <= 90) {
      aging['60'] += amount;
    } else if (daysOverdue <= 120) {
      aging['90'] += amount;
    } else {
      aging['90+'] += amount;
    }
  }

  return {
    invoices: invoiceList,
    totalOutstanding,
    totalOverdue,
    aging,
  };
}

// =============================================================================
// QUERY HOOKS
// =============================================================================

/**
 * AR Summary — returns `invoices` (not `arTransactions`).
 * Components consuming this hook should destructure:
 *   const { data } = useAccountsReceivableSummaryQuery();
 *   const { invoices, totalOutstanding, totalOverdue, aging } = data;
 */
export function useAccountsReceivableSummaryQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.accountsReceivable.summary(businessId),
    queryFn: () => fetchARSummary(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });
}
