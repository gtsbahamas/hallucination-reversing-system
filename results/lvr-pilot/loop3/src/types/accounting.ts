// =============================================================================
// ACCOUNTING DOMAIN TYPE DEFINITIONS
// Generated for LVR Loop 3 — covers all 26 accounting tables
// Source: Loop 2 data-architecture.md (observed schema from hook queries)
// =============================================================================

// =============================================================================
// SHARED UTILITY TYPES
// =============================================================================

/** Pagination parameters for list queries */
export interface PaginationParams {
  page: number;
  pageSize: number;
}

/** Paginated result wrapper returned by all list queries */
export interface PaginatedResult<T> {
  data: T[];
  totalCount: number;
  totalPages: number;
  currentPage: number;
  pageSize: number;
}

/** Sort direction for query ordering */
export type SortDirection = 'asc' | 'desc';

/** Supabase filter operators */
export type FilterOperator =
  | 'eq'
  | 'neq'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'like'
  | 'ilike'
  | 'in'
  | 'is';

/** Generic filter for dynamic query building */
export interface Filter {
  column: string;
  operator: FilterOperator;
  value: unknown;
}

/** Date range filter used across all entity filters */
export interface DateRangeFilter {
  from?: string; // ISO date string
  to?: string;   // ISO date string
}

// =============================================================================
// STATUS UNION TYPES
// =============================================================================

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';

export type BillStatus = 'pending' | 'approved' | 'paid' | 'overdue' | 'cancelled';

export type ExpenseStatus = 'draft' | 'pending_approval' | 'approved' | 'rejected';

export type JournalEntryStatus = 'draft' | 'posted' | 'reversed';

export type PaymentStatus = 'pending' | 'cleared' | 'bounced' | 'cancelled';

export type PaymentPlanStatus = 'active' | 'completed' | 'defaulted' | 'cancelled';

export type PaymentPlanInstallmentStatus = 'pending' | 'paid' | 'overdue' | 'partial';

export type PaymentReminderType =
  | 'friendly'
  | 'first_notice'
  | 'second_notice'
  | 'final_notice'
  | 'collection';

export type PaymentReminderMethod = 'email' | 'phone' | 'letter' | 'sms';

export type PaymentReminderStatus = 'pending' | 'sent' | 'failed' | 'responded';

export type PaymentMethod =
  | 'cash'
  | 'check'
  | 'bank_transfer'
  | 'credit_card'
  | 'debit_card'
  | 'other';

export type PaymentType = 'customer_payment' | 'supplier_payment';

export type AccountType = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';

export type BillProcessingStatus = 'manual' | 'automatic' | 'verified';

export type BulkPaymentBatchStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type OnlinePaymentStatus = 'pending' | 'completed' | 'failed' | 'cancelled';

export type POSTransactionStatus = 'completed' | 'pending' | 'refunded' | 'voided';

export type PaymentPlanFrequency = 'weekly' | 'biweekly' | 'monthly';

// =============================================================================
// 1. CHART OF ACCOUNTS
// =============================================================================

export interface ChartOfAccountsRow {
  id: string;
  business_id: string;
  account_code: string;
  account_name: string;
  account_type: AccountType;
  parent_account_id: string | null;
  description: string | null;
  is_active: boolean;
  is_system_account: boolean;
  current_balance: number;
  created_at: string;
  updated_at: string;
}

export interface ChartOfAccountsInsert {
  account_code: string;
  account_name: string;
  account_type: AccountType;
  parent_account_id?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface ChartOfAccountsUpdate {
  account_name?: string;
  account_type?: AccountType;
  parent_account_id?: string | null;
  description?: string | null;
  is_active?: boolean;
}

export interface ChartOfAccountsWithParent extends ChartOfAccountsRow {
  parent: {
    id: string;
    account_code: string;
    account_name: string;
  } | null;
}

export interface ChartOfAccountsFilters {
  search?: string;
  account_type?: AccountType | 'all';
  is_active?: boolean;
}

// =============================================================================
// 2. JOURNAL ENTRIES
// =============================================================================

export interface JournalEntryRow {
  id: string;
  business_id: string;
  entry_number: string;
  entry_date: string;
  description: string | null;
  total_amount: number;
  status: JournalEntryStatus;
  entry_type: string | null;
  reference_type: string | null;
  reference_id: string | null;
  reference_number: string | null;
  notes: string | null;
  posted_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryInsert {
  entry_date: string;
  description?: string;
  entry_type?: string;
  reference_type?: string;
  reference_id?: string;
  reference_number?: string;
  notes?: string;
  transactions: {
    account_id: string;
    debit_amount: number;
    credit_amount: number;
    description?: string;
  }[];
}

export interface JournalEntryUpdate {
  entry_date?: string;
  description?: string;
  entry_type?: string;
  notes?: string;
}

export interface JournalEntryWithTransactions extends JournalEntryRow {
  account_transactions: AccountTransactionWithAccount[];
}

export interface JournalEntryFilters {
  search?: string;
  entry_type?: string;
  status?: JournalEntryStatus | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 3. ACCOUNT TRANSACTIONS
// =============================================================================

export interface AccountTransactionRow {
  id: string;
  journal_entry_id: string;
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string | null;
}

export interface AccountTransactionWithAccount extends AccountTransactionRow {
  chart_of_accounts: {
    id: string;
    account_code: string;
    account_name: string;
  };
}

// =============================================================================
// 4. ACCOUNTING SETTINGS
// =============================================================================

export interface AccountingSettingsRow {
  id: string;
  business_id: string;
  auto_post_invoices: boolean;
  auto_post_bills: boolean;
  auto_post_expenses: boolean;
  auto_post_pos_sales: boolean;
  inventory_valuation_method: string;
  default_tax_rate: number;
}

export interface AccountingSettingsInsert {
  auto_post_invoices?: boolean;
  auto_post_bills?: boolean;
  auto_post_expenses?: boolean;
  auto_post_pos_sales?: boolean;
  inventory_valuation_method?: string;
  default_tax_rate?: number;
}

export type AccountingSettingsUpdate = AccountingSettingsInsert;

// =============================================================================
// 5. INVOICES
// =============================================================================

export interface InvoiceRow {
  id: string;
  business_id: string;
  customer_id: string | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  status: InvoiceStatus;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  balance_due: number;
  notes: string | null;
  is_deleted: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface InvoiceInsert {
  customer_id?: string;
  invoice_date: string;
  due_date: string;
  status?: InvoiceStatus;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  notes?: string;
  line_items: {
    product_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }[];
}

export interface InvoiceUpdate {
  customer_id?: string;
  invoice_date?: string;
  due_date?: string;
  status?: InvoiceStatus;
  subtotal?: number;
  tax_amount?: number;
  total_amount?: number;
  amount_paid?: number;
  balance_due?: number;
  notes?: string;
}

export interface InvoiceWithRelations extends InvoiceRow {
  customers: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    company_name: string | null;
  } | null;
  invoice_line_items: InvoiceLineItemRow[];
}

export interface InvoiceFilters {
  search?: string;
  status?: InvoiceStatus | 'all';
  customer_id?: string | 'all';
  dateRange?: DateRangeFilter;
}

/** Separate type for invoice aggregations -- never derived from paginated data (BUG-L02 fix) */
export interface InvoiceAggregations {
  totalAmount: number;
  paidAmount: number;
  outstandingAmount: number;
  overdueAmount: number;
  totalCount: number;
  paidCount: number;
  outstandingCount: number;
  overdueCount: number;
}

// =============================================================================
// 6. INVOICE LINE ITEMS
// =============================================================================

export interface InvoiceLineItemRow {
  id: string;
  invoice_id: string;
  product_id: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

// =============================================================================
// 7. INVOICE PAYMENTS
// =============================================================================

export interface InvoicePaymentRow {
  id: string;
  invoice_id: string;
  business_id: string;
  payment_amount: number;
  payment_method: string;
  payment_date: string;
  reference_number: string | null;
  check_number: string | null;
  bank_account_id: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface InvoicePaymentInsert {
  invoice_id: string;
  payment_amount: number;
  payment_method: string;
  payment_date?: string;
  reference_number?: string;
  check_number?: string;
  bank_account_id?: string;
  notes?: string;
}

export interface InvoicePaymentWithInvoice extends InvoicePaymentRow {
  invoices: {
    invoice_number: string;
    customer_id: string | null;
    customers: {
      first_name: string;
      last_name: string;
      company_name: string | null;
    } | null;
  } | null;
}

// =============================================================================
// 8. BILLS
// =============================================================================

export interface BillRow {
  id: string;
  business_id: string;
  supplier_id: string;
  purchase_order_id: string | null;
  bill_number: string;
  bill_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  balance_due: number;
  status: BillStatus;
  notes: string | null;
  processing_status: BillProcessingStatus;
  confidence_score: number | null;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface BillInsert {
  supplier_id: string;
  purchase_order_id?: string;
  bill_number: string;
  bill_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  status?: BillStatus;
  notes?: string;
  processing_status?: BillProcessingStatus;
  confidence_score?: number;
  line_items?: {
    product_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }[];
}

export interface BillUpdate {
  supplier_id?: string;
  bill_date?: string;
  due_date?: string;
  status?: BillStatus;
  notes?: string;
  amount_paid?: number;
  balance_due?: number;
  is_deleted?: boolean;
}

export interface BillWithRelations extends BillRow {
  suppliers: { name: string } | null;
  bill_items: BillItemRow[];
}

export interface BillFilters {
  search?: string;
  status?: BillStatus | 'all';
  supplier_id?: string | 'all';
  processing_status?: BillProcessingStatus | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 9. BILL ITEMS
// =============================================================================

export interface BillItemRow {
  id: string;
  bill_id: string;
  product_id: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

// =============================================================================
// 10. BILL PAYMENTS
// =============================================================================

export interface BillPaymentRow {
  id: string;
  bill_id: string;
  business_id: string;
  payment_amount: number;
  payment_date: string;
  payment_method: string;
  bank_account_id: string | null;
  reference_number: string | null;
  check_number: string | null;
  notes: string | null;
  attachment_url: string | null;
  journal_entry_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BillPaymentInsert {
  bill_id: string;
  payment_amount: number;
  payment_date: string;
  payment_method: string;
  bank_account_id?: string;
  reference_number?: string;
  check_number?: string;
  notes?: string;
  attachment_url?: string;
}

export interface BillPaymentWithBill extends BillPaymentRow {
  bills: {
    bill_number: string;
    supplier_id: string;
    suppliers: {
      name: string;
    } | null;
  } | null;
}

// =============================================================================
// 11. BILL TEMPLATES
// =============================================================================

export interface BillTemplateRow {
  id: string;
  business_id: string;
  supplier_id: string;
  template_data: Record<string, unknown>;
  created_at: string;
}

export interface BillTemplateInsert {
  supplier_id: string;
  template_data: Record<string, unknown>;
}

export interface BillTemplateUpdate {
  template_data?: Record<string, unknown>;
}

export interface BillTemplateWithSupplier extends BillTemplateRow {
  suppliers: { name: string } | null;
}

// =============================================================================
// 12. EXPENSES
// =============================================================================

export interface ExpenseRow {
  id: string;
  business_id: string;
  expense_number: string;
  expense_date: string;
  description: string | null;
  amount: number;
  total_amount: number;
  category: string | null;
  status: ExpenseStatus;
  vendor: string | null;
  payment_method: string | null;
  reference_number: string | null;
  notes: string | null;
  submitted_by: string;
  approved_at: string | null;
  approved_by: string | null;
  supplier_id: string | null;
  employee_id: string | null;
  created_at: string;
}

export interface ExpenseInsert {
  expense_date: string;
  description?: string;
  amount: number;
  total_amount?: number;
  category?: string;
  status?: ExpenseStatus;
  vendor?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  supplier_id?: string;
  employee_id?: string;
}

export interface ExpenseUpdate {
  expense_date?: string;
  description?: string;
  amount?: number;
  total_amount?: number;
  category?: string;
  status?: ExpenseStatus;
  vendor?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  approved_at?: string;
  approved_by?: string;
}

export interface ExpenseWithRelations extends ExpenseRow {
  employees: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
  } | null;
  suppliers: {
    id: string;
    name: string;
    email: string;
  } | null;
}

export interface ExpenseFilters {
  search?: string;
  category?: string | 'all';
  status?: ExpenseStatus | 'all';
  payment_method?: string | 'all';
  dateRange?: DateRangeFilter;
}

export interface ExpenseAggregations {
  totalAmount: number;
  approvedAmount: number;
  pendingAmount: number;
  rejectedAmount: number;
  totalCount: number;
  approvedCount: number;
  pendingCount: number;
  rejectedCount: number;
}

// =============================================================================
// 13. PAYMENTS (Unified)
// =============================================================================

export interface PaymentRow {
  id: string;
  business_id: string;
  payment_number: string;
  payment_date: string;
  payment_method: PaymentMethod;
  amount: number;
  currency: string;
  exchange_rate: number;
  reference_number: string | null;
  check_number: string | null;
  bank_account_id: string | null;
  payment_type: PaymentType;
  customer_id: string | null;
  supplier_id: string | null;
  status: PaymentStatus;
  posted_to_gl: boolean;
  gl_journal_entry_id: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentInsert {
  payment_date: string;
  payment_method: PaymentMethod;
  amount: number;
  currency?: string;
  exchange_rate?: number;
  reference_number?: string;
  check_number?: string;
  bank_account_id?: string;
  payment_type: PaymentType;
  customer_id?: string;
  supplier_id?: string;
  notes?: string;
}

export interface PaymentUpdate {
  payment_date?: string;
  payment_method?: PaymentMethod;
  amount?: number;
  status?: PaymentStatus;
  notes?: string;
}

export interface PaymentWithRelations extends PaymentRow {
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
  suppliers: {
    name: string;
    email: string;
  } | null;
  payment_applications: PaymentApplicationRow[];
}

export interface PaymentFilters {
  search?: string;
  payment_type?: PaymentType | 'all';
  payment_method?: PaymentMethod | 'all';
  status?: PaymentStatus | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 14. PAYMENT APPLICATIONS
// =============================================================================

export interface PaymentApplicationRow {
  id: string;
  payment_id: string;
  invoice_id: string | null;
  bill_id: string | null;
  applied_amount: number;
  application_date: string;
  notes: string | null;
}

export interface PaymentApplicationInsert {
  payment_id: string;
  invoice_id?: string;
  bill_id?: string;
  applied_amount: number;
  application_date?: string;
  notes?: string;
}

// =============================================================================
// 15. PAYMENT REMINDERS
// =============================================================================

export interface PaymentReminderRow {
  id: string;
  business_id: string;
  invoice_id: string;
  customer_id: string;
  reminder_type: PaymentReminderType;
  reminder_date: string;
  sent_date: string | null;
  sent_by: string | null;
  reminder_method: PaymentReminderMethod;
  message_content: string | null;
  status: PaymentReminderStatus;
  response_notes: string | null;
  next_reminder_date: string | null;
  created_at: string;
  created_by: string;
}

export interface PaymentReminderInsert {
  invoice_id: string;
  customer_id: string;
  reminder_type: PaymentReminderType;
  reminder_date: string;
  reminder_method: PaymentReminderMethod;
  message_content?: string;
  status?: PaymentReminderStatus;
}

export interface PaymentReminderUpdate {
  reminder_type?: PaymentReminderType;
  reminder_date?: string;
  reminder_method?: PaymentReminderMethod;
  message_content?: string;
  status?: PaymentReminderStatus;
  sent_date?: string;
  sent_by?: string;
  response_notes?: string;
  next_reminder_date?: string;
}

export interface PaymentReminderWithRelations extends PaymentReminderRow {
  invoices: {
    invoice_number: string;
    total_amount: number;
    balance_due: number;
  } | null;
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
}

export interface PaymentReminderFilters {
  search?: string;
  status?: PaymentReminderStatus | 'all';
  reminder_type?: PaymentReminderType | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 16. PAYMENT PLANS
// =============================================================================

export interface PaymentPlanRow {
  id: string;
  business_id: string;
  customer_id: string;
  plan_name: string;
  total_amount: number;
  remaining_amount: number;
  installment_amount: number;
  frequency: PaymentPlanFrequency;
  start_date: string;
  end_date: string;
  status: PaymentPlanStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentPlanInsert {
  customer_id: string;
  plan_name: string;
  total_amount: number;
  installment_amount: number;
  frequency: PaymentPlanFrequency;
  start_date: string;
  number_of_installments: number;
}

export interface PaymentPlanUpdate {
  plan_name?: string;
  installment_amount?: number;
  frequency?: PaymentPlanFrequency;
  status?: PaymentPlanStatus;
  end_date?: string;
}

export interface PaymentPlanWithRelations extends PaymentPlanRow {
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
  payment_plan_installments: PaymentPlanInstallmentRow[];
}

export interface PaymentPlanFilters {
  search?: string;
  status?: PaymentPlanStatus | 'all';
  customer_id?: string | 'all';
}

// =============================================================================
// 17. PAYMENT PLAN INSTALLMENTS
// =============================================================================

export interface PaymentPlanInstallmentRow {
  id: string;
  payment_plan_id: string;
  installment_number: number;
  due_date: string;
  amount: number;
  paid_amount: number;
  status: PaymentPlanInstallmentStatus;
  paid_date: string | null;
  created_at: string;
}

export interface PaymentPlanInstallmentUpdate {
  paid_amount?: number;
  status?: PaymentPlanInstallmentStatus;
  paid_date?: string;
}

// =============================================================================
// 18. BULK PAYMENT BATCHES
// =============================================================================

export interface BulkPaymentBatchRow {
  id: string;
  business_id: string;
  batch_name: string;
  payment_date: string;
  bill_count: number;
  total_amount: number;
  status: BulkPaymentBatchStatus;
  processed_at: string | null;
  created_by: string;
  created_at: string;
}

export interface BulkPaymentBatchInsert {
  batch_name: string;
  payment_date: string;
  bill_ids: string[];
}

export interface BulkPaymentBatchUpdate {
  status?: BulkPaymentBatchStatus;
  processed_at?: string;
}

export interface BulkPaymentBatchFilters {
  status?: BulkPaymentBatchStatus | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 19. ONLINE PAYMENTS
// =============================================================================

export interface OnlinePaymentRow {
  id: string;
  business_id: string;
  customer_id: string;
  payment_amount: number;
  payment_method: string;
  transaction_id: string | null;
  status: OnlinePaymentStatus;
  payment_date: string;
  applied_to_invoices: string[];
  gateway_response: Record<string, unknown>;
  created_at: string;
}

export interface OnlinePaymentInsert {
  customer_id: string;
  payment_amount: number;
  payment_method: string;
  transaction_id?: string;
  applied_to_invoices: string[];
}

export interface OnlinePaymentUpdate {
  status?: OnlinePaymentStatus;
  transaction_id?: string;
  gateway_response?: Record<string, unknown>;
}

export interface OnlinePaymentWithCustomer extends OnlinePaymentRow {
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
}

export interface OnlinePaymentFilters {
  status?: OnlinePaymentStatus | 'all';
  customer_id?: string | 'all';
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 20. CUSTOMER PAYMENT TOKENS
// =============================================================================

export interface CustomerPaymentTokenRow {
  id: string;
  business_id: string;
  customer_id: string;
  token: string;
  expires_at: string;
  is_used: boolean;
  created_at: string;
}

export interface CustomerPaymentTokenInsert {
  customer_id: string;
  token: string;
  expires_at: string;
}

// =============================================================================
// 21. BANK ACCOUNTS
// =============================================================================

export interface BankAccountRow {
  id: string;
  business_id: string;
  account_name: string;
  account_number: string;
  bank_name: string;
  routing_number: string | null;
  account_type: string;
  currency: string;
  current_balance: number;
  gl_account_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BankAccountInsert {
  account_name: string;
  account_number: string;
  bank_name: string;
  routing_number?: string;
  account_type: string;
  currency?: string;
  gl_account_id?: string;
  is_active?: boolean;
}

export interface BankAccountUpdate {
  account_name?: string;
  bank_name?: string;
  routing_number?: string;
  account_type?: string;
  currency?: string;
  gl_account_id?: string;
  is_active?: boolean;
}

export interface BankAccountWithGLAccount extends BankAccountRow {
  chart_of_accounts: {
    id: string;
    account_code: string;
    account_name: string;
  } | null;
}

export interface BankAccountFilters {
  search?: string;
  is_active?: boolean;
  account_type?: string | 'all';
}

// =============================================================================
// 22. BANK TRANSACTIONS
// =============================================================================

export interface BankTransactionRow {
  id: string;
  business_id: string;
  bank_account_id: string;
  transaction_date: string;
  description: string;
  amount: number;
  transaction_type: string;
  reference_number: string | null;
  is_matched: boolean;
  matched_journal_entry_id: string | null;
  created_at: string;
}

export interface BankTransactionInsert {
  bank_account_id: string;
  transaction_date: string;
  description: string;
  amount: number;
  transaction_type: string;
  reference_number?: string;
}

export interface BankTransactionUpdate {
  is_matched?: boolean;
  matched_journal_entry_id?: string | null;
}

export interface BankTransactionFilters {
  bank_account_id?: string | 'all';
  is_matched?: boolean;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 23. BANK STATEMENTS
// =============================================================================

export interface BankStatementRow {
  id: string;
  business_id: string;
  bank_account_id: string;
  statement_date: string;
  opening_balance: number;
  closing_balance: number;
  total_deposits: number;
  total_withdrawals: number;
  is_reconciled: boolean;
  created_at: string;
}

export interface BankStatementFilters {
  bank_account_id?: string | 'all';
  is_reconciled?: boolean;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// 24. POS TRANSACTIONS
// =============================================================================

export interface POSTransactionRow {
  id: string;
  business_id: string;
  transaction_number: string;
  cashier_id: string;
  customer_id: string | null;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount_tendered: number;
  change_amount: number;
  status: POSTransactionStatus;
  notes: string | null;
  is_bonded: boolean | null;
  exemption_reason: string | null;
  authorized_by: string | null;
  created_at: string;
}

export interface POSTransactionWithItems extends POSTransactionRow {
  pos_transaction_items: POSTransactionItemRow[];
  pos_payments: POSPaymentRow[];
}

export interface POSTransactionFilters {
  status?: POSTransactionStatus | 'all';
  cashier_id?: string | 'all';
  dateRange?: DateRangeFilter;
  is_bonded?: boolean;
}

// =============================================================================
// 25. POS TRANSACTION ITEMS
// =============================================================================

export interface POSTransactionItemRow {
  id: string;
  transaction_id: string;
  product_id: string;
  product_name: string;
  product_sku: string;
  quantity: number;
  unit_price: number;
  tax_amount: number;
  line_total: number;
  duty_amount: number | null;
  exemption_type: string | null;
}

// =============================================================================
// 26. POS PAYMENTS
// =============================================================================

export interface POSPaymentRow {
  id: string;
  transaction_id: string;
  payment_method: string;
  amount: number;
  reference_number: string | null;
  notes: string | null;
}

// =============================================================================
// TIME ENTRIES (used by unbilled time hooks)
// =============================================================================

export interface TimeEntryRow {
  id: string;
  business_id: string;
  date: string;
  hours: number;
  description: string | null;
  billable: boolean;
  hourly_rate: number;
  project_id: string;
  employee_id: string;
  task_id: string | null;
  invoice_id: string | null;
}

export interface TimeEntryWithRelations extends TimeEntryRow {
  projects: {
    id: string;
    name: string;
    customers: {
      id: string;
      first_name: string;
      last_name: string;
      company_name: string | null;
    } | null;
  } | null;
  employees: {
    id: string;
    first_name: string;
    last_name: string;
  } | null;
  tasks: {
    id: string;
    name: string;
  } | null;
}

export interface TimeEntryFilters {
  employee_id?: string | 'all';
  project_id?: string | 'all';
  billable?: boolean;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// DASHBOARD / AGGREGATION TYPES
// =============================================================================

/** Financial summary for the accounting dashboard (BUG-H01 fix: real data, not mock) */
export interface FinancialSummary {
  totalRevenue: number;
  totalExpenses: number;
  netIncome: number;
  accountsReceivable: number;
  accountsPayable: number;
  cashBalance: number;
}

/** Aging report buckets (BUG-H06 fix: consistent keys 'current', '30', '60', '90', '90+') */
export interface AgingBucket {
  current: number;   // 0-30 days
  '30': number;      // 31-60 days
  '60': number;      // 61-90 days
  '90': number;      // 91-120 days
  '90+': number;     // 120+ days
  total: number;
}

/** AR summary that returns invoices, NOT arTransactions (BUG-H02 fix) */
export interface AccountsReceivableSummary {
  invoices: InvoiceWithRelations[];
  totalOutstanding: number;
  totalOverdue: number;
  aging: AgingBucket;
}
