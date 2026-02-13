/**
 * Accounting Module — Barrel Exports
 *
 * Single entry point for the entire accounting module.
 * Import from '@/modules/accounting' (or wherever this module is mounted).
 *
 * Usage:
 *   import {
 *     accountingRoutes,
 *     ACCOUNTING_PERMISSIONS,
 *     ACCOUNTING_ROUTE_PERMISSIONS,
 *     useAccountingPermission,
 *     useAccountingPermissions,
 *     ACCOUNTING_NAV_ITEMS,
 *     useAccountingNavigation,
 *   } from '@/modules/accounting';
 */

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export { accountingRoutes, default as accountingRoutesDefault } from './routes/accounting';

// ---------------------------------------------------------------------------
// Permissions
// ---------------------------------------------------------------------------

export {
  ACCOUNTING_PERMISSIONS,
  ACCOUNTING_ROUTE_PERMISSIONS,
  useAccountingPermission,
  useAccountingPermissions,
  type PermissionMapping,
  type ModulePermissions,
} from './config/accountingPermissions';

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

export {
  ACCOUNTING_NAV_ITEMS,
  ACCOUNTING_NAV_GROUPS,
  ACCOUNTING_NAVIGATION_PERMISSIONS,
  useAccountingNavigation,
  type AccountingNavItem,
  type AccountingNavGroup,
  type AccountingNavGroup_Meta,
} from './config/accountingNavigation';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type * from './types/accounting';

// ---------------------------------------------------------------------------
// Hooks — Invoices
// ---------------------------------------------------------------------------

export {
  useInvoicesQuery,
  useInvoiceQuery,
  useInvoiceAggregationsQuery,
  useCreateInvoiceMutation,
  useUpdateInvoiceMutation,
  useSoftDeleteInvoiceMutation,
} from './hooks/useInvoices';

// ---------------------------------------------------------------------------
// Hooks — Bills
// ---------------------------------------------------------------------------

export {
  useBillsQuery,
  useBillQuery,
  useCreateBillMutation,
  useUpdateBillMutation,
  useSoftDeleteBillMutation,
} from './hooks/useBills';

// ---------------------------------------------------------------------------
// Hooks — Expenses
// ---------------------------------------------------------------------------

export {
  useExpensesQuery,
  useExpenseQuery,
  useExpenseAggregationsQuery,
  useCreateExpenseMutation,
  useUpdateExpenseMutation,
  useApproveExpenseMutation,
  useRejectExpenseMutation,
  useDeleteExpenseMutation,
} from './hooks/useExpenses';

// ---------------------------------------------------------------------------
// Hooks — Payments
// ---------------------------------------------------------------------------

export {
  usePaymentsQuery,
  usePaymentQuery,
  usePaymentsByTypeQuery,
  useCreatePaymentMutation,
  useVoidPaymentMutation,
} from './hooks/usePayments';

// ---------------------------------------------------------------------------
// Hooks — Journal Entries
// ---------------------------------------------------------------------------

export {
  useJournalEntriesQuery,
  useJournalEntryQuery,
  useCreateJournalEntryMutation,
  useUpdateJournalEntryMutation,
  usePostJournalEntryMutation,
  useReverseJournalEntryMutation,
} from './hooks/useJournalEntries';

// ---------------------------------------------------------------------------
// Hooks — Chart of Accounts
// ---------------------------------------------------------------------------

export {
  useAccountsQuery,
  useAccountQuery,
  useCreateAccountMutation,
  useUpdateAccountMutation,
  useDeleteAccountMutation,
} from './hooks/useChartOfAccounts';

// ---------------------------------------------------------------------------
// Hooks — Accounts Receivable
// ---------------------------------------------------------------------------

export {
  useAccountsReceivableSummaryQuery,
} from './hooks/useAccountsReceivable';

// ---------------------------------------------------------------------------
// Hooks — Aging Reports
// ---------------------------------------------------------------------------

export {
  useARAgingQuery,
  useAPAgingQuery,
} from './hooks/useAgingReport';

// ---------------------------------------------------------------------------
// Hooks — Bank Accounts
// ---------------------------------------------------------------------------

export {
  useBankAccountsQuery,
  useBankAccountQuery,
  useCreateBankAccountMutation,
  useUpdateBankAccountMutation,
  useDeleteBankAccountMutation,
} from './hooks/useBankAccounts';

// ---------------------------------------------------------------------------
// Hooks — Bank Reconciliation
// ---------------------------------------------------------------------------

export {
  useBankTransactionsQuery,
  useBankTransactionsByAccountQuery,
  useBankStatementsQuery,
  useImportTransactionsMutation,
  useMatchTransactionMutation,
  useUnmatchTransactionMutation,
  useReconcileStatementMutation,
} from './hooks/useBankReconciliation';

// ---------------------------------------------------------------------------
// Hooks — Bulk Payments
// ---------------------------------------------------------------------------

export {
  useBulkPaymentBatchesQuery,
  useBulkPaymentBatchQuery,
  useCreateBatchMutation,
  useProcessBatchMutation,
} from './hooks/useBulkPayments';

// ---------------------------------------------------------------------------
// Hooks — Financial Overview
// ---------------------------------------------------------------------------

export {
  useFinancialSummaryQuery,
} from './hooks/useFinancialOverview';

// ---------------------------------------------------------------------------
// Hooks — Online Payments
// ---------------------------------------------------------------------------

export {
  useOnlinePaymentsQuery,
  usePaymentTokensQuery,
  usePaymentTokenByCustomerQuery,
  useProcessOnlinePaymentMutation,
  useGenerateTokenMutation,
  useMarkTokenUsedMutation,
} from './hooks/useOnlinePayments';

// ---------------------------------------------------------------------------
// Hooks — Payment Plans
// ---------------------------------------------------------------------------

export {
  usePaymentPlansQuery,
  usePaymentPlanQuery,
  useInstallmentsQuery,
  useCreatePaymentPlanMutation,
  useUpdatePaymentPlanMutation,
  useRecordInstallmentMutation,
} from './hooks/usePaymentPlans';

// ---------------------------------------------------------------------------
// Hooks — Payment Reminders
// ---------------------------------------------------------------------------

export {
  usePaymentRemindersQuery,
  usePaymentReminderQuery,
  useCreateReminderMutation,
  useUpdateReminderMutation,
  useMarkReminderSentMutation,
  useDeleteReminderMutation,
} from './hooks/usePaymentReminders';

// ---------------------------------------------------------------------------
// Hooks — POS Accounting
// ---------------------------------------------------------------------------

export {
  usePOSTransactionsQuery,
  usePOSTransactionQuery,
  useUnpostedPOSTransactionsQuery,
  usePostPOSSaleMutation,
  useBulkPostPOSMutation,
} from './hooks/usePOSAccounting';

// ---------------------------------------------------------------------------
// Hooks — Accounting Settings
// ---------------------------------------------------------------------------

export {
  useAccountingSettingsQuery,
  useUpdateSettingsMutation,
} from './hooks/useAccountingSettings';

// ---------------------------------------------------------------------------
// Hooks — Shared Query Utilities
// ---------------------------------------------------------------------------

export {
  accountingKeys,
  useBusinessId,
  useBusinessIdSafe,
  getCurrentUserId,
  applyPagination,
  buildPaginatedResult,
  LIST_STALE_TIME,
  AGGREGATION_STALE_TIME,
} from './hooks/useAccountingQueries';

// ---------------------------------------------------------------------------
// Shared Components
// ---------------------------------------------------------------------------

export { DataTable, default as DataTableDefault } from './components/accounting/shared/DataTable';
export { default as DetailLayout } from './components/accounting/shared/DetailLayout';
export { default as FormModal } from './components/accounting/shared/FormModal';
export { default as StatCards } from './components/accounting/shared/StatCards';
