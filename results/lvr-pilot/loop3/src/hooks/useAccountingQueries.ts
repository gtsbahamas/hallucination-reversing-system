// =============================================================================
// QUERY KEY FACTORY + SHARED UTILITIES
// Central query key management for all accounting hooks
// =============================================================================

import { useBusiness } from '@/hooks/useBusiness';
import { supabase } from '@/lib/supabase';
import type {
  InvoiceFilters,
  BillFilters,
  ExpenseFilters,
  JournalEntryFilters,
  PaymentFilters,
  PaymentReminderFilters,
  PaymentPlanFilters,
  BulkPaymentBatchFilters,
  OnlinePaymentFilters,
  BankAccountFilters,
  BankTransactionFilters,
  BankStatementFilters,
  POSTransactionFilters,
  ChartOfAccountsFilters,
  TimeEntryFilters,
  PaginationParams,
  PaymentType,
} from '../types/accounting';

// =============================================================================
// QUERY KEY FACTORY
// Hierarchical keys enable granular cache invalidation:
//   invalidateQueries({ queryKey: accountingKeys.invoices.all })
//   → invalidates list, detail, AND aggregation queries for invoices
// =============================================================================

export const accountingKeys = {
  // Top-level: invalidate everything accounting-related
  all: ['accounting'] as const,

  // Chart of Accounts
  accounts: {
    all: ['accounting', 'accounts'] as const,
    list: (businessId: string, filters?: ChartOfAccountsFilters) =>
      ['accounting', 'accounts', 'list', businessId, filters] as const,
    detail: (businessId: string, accountId: string) =>
      ['accounting', 'accounts', 'detail', businessId, accountId] as const,
  },

  // Journal Entries
  journalEntries: {
    all: ['accounting', 'journal-entries'] as const,
    list: (businessId: string, filters?: JournalEntryFilters, pagination?: PaginationParams) =>
      ['accounting', 'journal-entries', 'list', businessId, filters, pagination] as const,
    detail: (businessId: string, entryId: string) =>
      ['accounting', 'journal-entries', 'detail', businessId, entryId] as const,
  },

  // Invoices
  invoices: {
    all: ['accounting', 'invoices'] as const,
    list: (businessId: string, filters?: InvoiceFilters, pagination?: PaginationParams) =>
      ['accounting', 'invoices', 'list', businessId, filters, pagination] as const,
    detail: (businessId: string, invoiceId: string) =>
      ['accounting', 'invoices', 'detail', businessId, invoiceId] as const,
    aggregations: (businessId: string) =>
      ['accounting', 'invoices', 'aggregations', businessId] as const,
  },

  // Invoice Payments
  invoicePayments: {
    all: ['accounting', 'invoice-payments'] as const,
    byInvoice: (businessId: string, invoiceId: string) =>
      ['accounting', 'invoice-payments', 'by-invoice', businessId, invoiceId] as const,
    byCustomer: (businessId: string, customerId: string) =>
      ['accounting', 'invoice-payments', 'by-customer', businessId, customerId] as const,
  },

  // Bills
  bills: {
    all: ['accounting', 'bills'] as const,
    list: (businessId: string, filters?: BillFilters, pagination?: PaginationParams) =>
      ['accounting', 'bills', 'list', businessId, filters, pagination] as const,
    detail: (businessId: string, billId: string) =>
      ['accounting', 'bills', 'detail', businessId, billId] as const,
    aggregations: (businessId: string) =>
      ['accounting', 'bills', 'aggregations', businessId] as const,
  },

  // Bill Payments
  billPayments: {
    all: ['accounting', 'bill-payments'] as const,
    byBill: (businessId: string, billId: string) =>
      ['accounting', 'bill-payments', 'by-bill', businessId, billId] as const,
  },

  // Bill Templates
  billTemplates: {
    all: ['accounting', 'bill-templates'] as const,
    list: (businessId: string) =>
      ['accounting', 'bill-templates', 'list', businessId] as const,
    bySupplier: (businessId: string, supplierId: string) =>
      ['accounting', 'bill-templates', 'by-supplier', businessId, supplierId] as const,
  },

  // Expenses
  expenses: {
    all: ['accounting', 'expenses'] as const,
    list: (businessId: string, filters?: ExpenseFilters, pagination?: PaginationParams) =>
      ['accounting', 'expenses', 'list', businessId, filters, pagination] as const,
    detail: (businessId: string, expenseId: string) =>
      ['accounting', 'expenses', 'detail', businessId, expenseId] as const,
    aggregations: (businessId: string) =>
      ['accounting', 'expenses', 'aggregations', businessId] as const,
  },

  // Payments (unified)
  payments: {
    all: ['accounting', 'payments'] as const,
    list: (businessId: string, filters?: PaymentFilters, pagination?: PaginationParams) =>
      ['accounting', 'payments', 'list', businessId, filters, pagination] as const,
    detail: (businessId: string, paymentId: string) =>
      ['accounting', 'payments', 'detail', businessId, paymentId] as const,
    byType: (businessId: string, type: PaymentType) =>
      ['accounting', 'payments', 'by-type', businessId, type] as const,
    unapplied: (businessId: string, type: PaymentType) =>
      ['accounting', 'payments', 'unapplied', businessId, type] as const,
  },

  // Payment Reminders
  reminders: {
    all: ['accounting', 'payment-reminders'] as const,
    list: (businessId: string, filters?: PaymentReminderFilters) =>
      ['accounting', 'payment-reminders', 'list', businessId, filters] as const,
    detail: (businessId: string, reminderId: string) =>
      ['accounting', 'payment-reminders', 'detail', businessId, reminderId] as const,
  },

  // Payment Plans
  paymentPlans: {
    all: ['accounting', 'payment-plans'] as const,
    list: (businessId: string, filters?: PaymentPlanFilters) =>
      ['accounting', 'payment-plans', 'list', businessId, filters] as const,
    detail: (businessId: string, planId: string) =>
      ['accounting', 'payment-plans', 'detail', businessId, planId] as const,
    installments: (planId: string) =>
      ['accounting', 'payment-plan-installments', planId] as const,
  },

  // Bulk Payments
  bulkPayments: {
    all: ['accounting', 'bulk-payment-batches'] as const,
    list: (businessId: string, filters?: BulkPaymentBatchFilters) =>
      ['accounting', 'bulk-payment-batches', 'list', businessId, filters] as const,
    detail: (businessId: string, batchId: string) =>
      ['accounting', 'bulk-payment-batches', 'detail', businessId, batchId] as const,
  },

  // Online Payments
  onlinePayments: {
    all: ['accounting', 'online-payments'] as const,
    list: (businessId: string, filters?: OnlinePaymentFilters) =>
      ['accounting', 'online-payments', 'list', businessId, filters] as const,
    tokens: (businessId: string) =>
      ['accounting', 'customer-payment-tokens', businessId] as const,
    tokenByCustomer: (businessId: string, customerId: string) =>
      ['accounting', 'customer-payment-tokens', businessId, customerId] as const,
  },

  // Banking
  bankAccounts: {
    all: ['accounting', 'bank-accounts'] as const,
    list: (businessId: string, filters?: BankAccountFilters) =>
      ['accounting', 'bank-accounts', 'list', businessId, filters] as const,
    detail: (businessId: string, accountId: string) =>
      ['accounting', 'bank-accounts', 'detail', businessId, accountId] as const,
  },

  bankTransactions: {
    all: ['accounting', 'bank-transactions'] as const,
    list: (businessId: string, filters?: BankTransactionFilters) =>
      ['accounting', 'bank-transactions', 'list', businessId, filters] as const,
    byAccount: (businessId: string, accountId: string) =>
      ['accounting', 'bank-transactions', 'by-account', businessId, accountId] as const,
  },

  bankStatements: {
    all: ['accounting', 'bank-statements'] as const,
    list: (businessId: string, filters?: BankStatementFilters) =>
      ['accounting', 'bank-statements', 'list', businessId, filters] as const,
  },

  // POS
  posTransactions: {
    all: ['accounting', 'pos-transactions'] as const,
    list: (businessId: string, filters?: POSTransactionFilters) =>
      ['accounting', 'pos-transactions', 'list', businessId, filters] as const,
    detail: (transactionId: string) =>
      ['accounting', 'pos-transactions', 'detail', transactionId] as const,
    unposted: (businessId: string) =>
      ['accounting', 'pos-transactions', 'unposted', businessId] as const,
  },

  // Time Entries / Unbilled Time
  unbilledTime: {
    all: ['accounting', 'unbilled-time'] as const,
    list: (businessId: string, filters?: TimeEntryFilters) =>
      ['accounting', 'unbilled-time', 'list', businessId, filters] as const,
    byCustomer: (businessId: string, customerId: string) =>
      ['accounting', 'unbilled-time', 'by-customer', businessId, customerId] as const,
  },

  // Accounting Settings
  settings: {
    all: ['accounting', 'settings'] as const,
    detail: (businessId: string) =>
      ['accounting', 'settings', 'detail', businessId] as const,
  },

  // Dashboard aggregations (BUG-H01 fix)
  dashboard: {
    all: ['accounting', 'dashboard'] as const,
    financialSummary: (businessId: string) =>
      ['accounting', 'dashboard', 'financial-summary', businessId] as const,
    arAging: (businessId: string) =>
      ['accounting', 'dashboard', 'ar-aging', businessId] as const,
    apAging: (businessId: string) =>
      ['accounting', 'dashboard', 'ap-aging', businessId] as const,
  },

  // Accounts Receivable
  accountsReceivable: {
    all: ['accounting', 'accounts-receivable'] as const,
    summary: (businessId: string) =>
      ['accounting', 'accounts-receivable', 'summary', businessId] as const,
  },
} as const;

// =============================================================================
// SHARED HOOKS
// =============================================================================

/**
 * Extract business ID from context. Throws if no business context available.
 * Use this in hooks where the query is always enabled when the hook is mounted.
 */
export function useBusinessId(): string {
  const { currentBusiness } = useBusiness();
  if (!currentBusiness?.id) {
    throw new Error('useBusinessId called without business context');
  }
  return currentBusiness.id;
}

/**
 * Safe version that returns undefined instead of throwing.
 * Use this for conditional query enabling: enabled: !!businessId
 */
export function useBusinessIdSafe(): string | undefined {
  const { currentBusiness } = useBusiness();
  return currentBusiness?.id;
}

// =============================================================================
// SHARED UTILITIES
// =============================================================================

/**
 * Get the current authenticated user's ID for created_by fields.
 */
export async function getCurrentUserId(): Promise<string> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('No authenticated user');
  return user.id;
}

/**
 * Apply pagination range to a Supabase query builder.
 */
export function applyPagination<T extends { range: (from: number, to: number) => T }>(
  query: T,
  pagination?: PaginationParams
): { query: T; page: number; pageSize: number } {
  const page = pagination?.page ?? 1;
  const pageSize = pagination?.pageSize ?? 20;
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;
  return { query: query.range(from, to), page, pageSize };
}

/**
 * Build a PaginatedResult from Supabase query response.
 */
export function buildPaginatedResult<T>(
  data: T[] | null,
  count: number | null,
  page: number,
  pageSize: number
) {
  const totalCount = count ?? 0;
  return {
    data: data ?? [],
    totalCount,
    totalPages: Math.ceil(totalCount / pageSize),
    currentPage: page,
    pageSize,
  };
}

/** Default stale time for list queries (30 seconds) */
export const LIST_STALE_TIME = 30_000;

/** Stale time for aggregation/dashboard queries (60 seconds) */
export const AGGREGATION_STALE_TIME = 60_000;
