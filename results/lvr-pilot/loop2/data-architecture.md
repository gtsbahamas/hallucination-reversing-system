# Loop 2 -- Data Layer Architecture

*Generated: 2026-02-13*
*Source: 25 accounting hooks + 2 services from Island Biz ERP*
*Agent: B (Data Architecture)*

---

## Current Architecture Analysis

### Summary

The accounting domain uses 25 hooks spanning 26 database tables. The architecture is a mix of two patterns:

1. **Legacy Pattern (majority):** `useState` + `useEffect` + manual Supabase calls. No caching, no deduplication, no optimistic updates. Each hook manages its own loading/error state.
2. **Partial React Query (minority):** Only `usePayments.tsx` uses `@tanstack/react-query` via `useQuery`. No mutations use React Query.

### Common Patterns

| Pattern | Hooks Using It | Example |
|---------|----------------|---------|
| `useState` + `useEffect` for data fetching | 22 of 25 | `useAccounting`, `useInvoices`, `useBills` |
| `useQuery` from React Query | 1 of 25 | `usePayments` (partial -- 5 queries) |
| `useBusiness()` for business context | 25 of 25 | All hooks |
| `useToast()` for user feedback | 25 of 25 | All hooks |
| `supabase.from().select('*')` (select all) | 8 of 25 | `useAccounting`, `useBankAccounts`, `useBankReconciliation` |
| Joins via `.select('*, relation(cols)')` | 15 of 25 | `useInvoices`, `useBills`, `useJournalEntries` |
| `.eq('business_id', id)` filtering | 25 of 25 | All hooks |
| Full list refetch after mutation | 20 of 25 | `createInvoice` -> `loadInvoices()` |
| `usePagination` custom hook | 4 of 25 | `useInvoicesPaginated`, `useBillsPaginated`, `useExpensesPaginated`, `useJournalEntriesPaginated` |
| Custom pagination (inline) | 1 of 25 | `useCustomerPaymentsPaginated` |
| `useCallback` for stable references | 5 of 25 | `useInvoiceAccounting`, `useBillAccounting`, `useExpenseAccounting`, `usePOSAccounting`, `useCustomerPaymentsPaginated` |
| `getBusinessId()` helper | 5 of 25 | `useAccounting`, `useInvoices`, `useExpenses` |
| Direct `currentBusiness.id` access | 20 of 25 | `useBills`, `usePayments`, etc. |

### Anti-Patterns Found

| Anti-Pattern | Severity | Hooks Affected | Description |
|--------------|----------|----------------|-------------|
| **No caching** | Critical | 22 of 25 | Every navigation/mount triggers a full refetch. No stale-while-revalidate. |
| **Full refetch after mutation** | High | 20 of 25 | After creating/updating one record, entire list is re-fetched. Wastes bandwidth, causes UI flicker. |
| **Duplicate queries** | High | Multiple | `useAccounting` fetches invoices AND expenses. `useInvoices` and `useInvoicesPaginated` both fetch invoices independently. |
| **`select('*')` overuse** | Medium | 8 hooks | Fetches all columns when only a subset is needed. |
| **Stats from paginated subset** (BUG-L02) | High | `useInvoicesPaginated` | `loadMetadata` fetches ALL invoices separately for stats -- correct approach but uses a separate query with `select('status, total_amount, balance_due')`. Other paginated hooks do NOT have separate stats queries. |
| **Inconsistent error handling** | Medium | All | Some use `handleError()`, others use `logger.error()` + manual toast. No unified pattern. |
| **Inconsistent delete semantics** (BUG-H03) | Critical | `useBills`, `useBillsPaginated` | Both use hard delete (`.delete()`). No soft-delete anywhere in the codebase for bills, contradicting the bug report expectation. |
| **Missing method on service** | Critical | `usePayments` | Calls `PaymentsService.getPaymentsByType()` which does NOT exist on the class. Will throw at runtime. |
| **Journal entry post/reverse bypass service** (BUG-H04/H05) | High | `useJournalEntries` | `postJournalEntry` directly updates status without validation. Does not use `GeneralLedgerService`. |
| **Simulated processing** | Medium | `useBulkPayments` | `processPaymentBatch` uses `setTimeout(resolve, 2000)` -- fake async. |
| **Type duplication** | Medium | `useBills` + `useBillsPaginated` | Both define identical `Bill` and `BillCreateData` interfaces independently. |
| **Inconsistent business_id access** | Low | Mixed | Some hooks use `getBusinessId(currentBusiness, 'context')`, others use `currentBusiness.id` directly, some cast via `(currentBusiness as any).id`. |
| **No real-time subscriptions** | Low | 0 of 25 | No Supabase realtime subscriptions on any accounting table. |
| **No optimistic updates** | Medium | 25 of 25 | All mutations wait for server response, then refetch. No optimistic UI. |

### Hook Complexity Distribution

| Complexity | Count | Hooks |
|------------|-------|-------|
| **High** (>150 lines, multi-table, journal entries) | 7 | `useAccounting`, `useInvoicesPaginated`, `useBillsPaginated`, `useOnlinePayments`, `useAdvancedPayments`, `usePOSAccounting`, `useUnbilledTime` |
| **Medium** (80-150 lines, CRUD + joins) | 10 | `useInvoices`, `useBills`, `useExpenses`, `useJournalEntries`, `usePayments`, `usePaymentReminders`, `usePaymentPlans`, `useBulkPayments`, `useExpensesPaginated`, `useJournalEntriesPaginated` |
| **Low** (<80 lines, single table, simple CRUD) | 8 | `useBankAccounts`, `useBankReconciliation`, `useAccountingAutomation`, `useBillTemplates`, `useInvoiceAccounting`, `useBillAccounting`, `useExpenseAccounting`, `useCustomerPaymentsPaginated` |

---

## Database Schema Summary (Observed from Hook Queries)

### Core Accounting Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `chart_of_accounts` | id, business_id, account_code, account_name, account_type, is_active, is_system_account, current_balance, parent_account_id, description | parent -> chart_of_accounts (self) | Yes |
| `journal_entries` | id, business_id, entry_number, entry_date, description, total_amount, status, created_by, posted_at, reference_type, reference_id, reference_number, entry_type, notes, created_at | -> account_transactions (1:N) | Yes |
| `account_transactions` | id, journal_entry_id, account_id, debit_amount, credit_amount, description | -> journal_entries (N:1), -> chart_of_accounts (N:1) | Via journal_entry |
| `accounting_settings` | id, business_id, auto_post_invoices, auto_post_bills, auto_post_expenses, auto_post_pos_sales, inventory_valuation_method, default_tax_rate | Singleton per business | Yes |

### Invoicing Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `invoices` | id, business_id, customer_id, invoice_number, invoice_date, due_date, status, subtotal, tax_amount, total_amount, amount_paid, balance_due, notes, created_by, created_at, updated_at | -> customers (N:1), -> invoice_line_items (1:N), -> invoice_payments (1:N) | Yes |
| `invoice_line_items` | id, invoice_id, product_id, description, quantity, unit_price, line_total | -> invoices (N:1), -> products (N:1) | Via invoice |
| `invoice_payments` | id, invoice_id, business_id, payment_amount, payment_method, payment_date, reference_number, check_number, bank_account_id, notes, created_by, created_at, updated_at | -> invoices (N:1), -> invoices.customers (nested) | Yes |
| `invoice_items` | id, invoice_id, description, quantity, unit_price, total | -> invoices (N:1) | Via invoice |

**NOTE:** Both `invoice_line_items` and `invoice_items` exist. `invoice_line_items` is used by `useInvoices`/`useInvoicesPaginated`. `invoice_items` is used by `useUnbilledTime`. These appear to be duplicate/competing tables.

### Bills / AP Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `bills` | id, business_id, supplier_id, purchase_order_id, bill_number, bill_date, due_date, subtotal, tax_amount, total_amount, amount_paid, balance_due, status, notes, processing_status, confidence_score, created_at, updated_at, created_by | -> suppliers (N:1), -> bill_items (1:N), -> bill_payments (1:N) | Yes |
| `bill_items` | id, bill_id, product_id, description, quantity, unit_price, line_total | -> bills (N:1) | Via bill |
| `bill_payments` | id, bill_id, business_id, payment_amount, payment_date, payment_method, bank_account_id, reference_number, notes, attachment_url, check_number, journal_entry_id, created_by, created_at, updated_at | -> bills (N:1), -> bills.suppliers (nested) | Yes |
| `bill_templates` | id, business_id, supplier_id, template_data, created_at | -> suppliers (N:1) | Yes |

### Expenses Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `expenses` | id, business_id, expense_number, expense_date, description, amount, total_amount, category, status, vendor, payment_method, reference_number, notes, submitted_by, approved_at, approved_by, supplier_id, employee_id, created_at | -> employees (N:1), -> suppliers (N:1) | Yes |

### Payments Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `payments` | id, business_id, payment_number, payment_date, payment_method, amount, currency, exchange_rate, reference_number, check_number, bank_account_id, payment_type, customer_id, supplier_id, status, posted_to_gl, gl_journal_entry_id, notes, created_by, created_at, updated_at | -> customers (N:1), -> suppliers (N:1), -> payment_applications (1:N) | Yes |
| `payment_applications` | id, payment_id, invoice_id, bill_id, applied_amount, application_date, notes | -> payments (N:1), -> invoices (N:1), -> bills (N:1) | Via payment |
| `payment_reminders` | id, business_id, invoice_id, customer_id, reminder_type, reminder_date, sent_date, sent_by, reminder_method, message_content, status, response_notes, next_reminder_date, created_at, created_by | -> invoices (N:1), -> customers (N:1) | Yes |
| `payment_plans` | id, business_id, customer_id, plan_name, total_amount, remaining_amount, installment_amount, frequency, start_date, end_date, status, created_by, created_at, updated_at | -> customers (N:1), -> payment_plan_installments (1:N) | Yes |
| `payment_plan_installments` | id, payment_plan_id, installment_number, due_date, amount, paid_amount, status, paid_date, created_at | -> payment_plans (N:1) | Via plan |
| `bulk_payment_batches` | id, business_id, batch_name, payment_date, bill_count, total_amount, status, processed_at, created_by, created_at | None observed | Yes |
| `online_payments` | id, business_id, customer_id, payment_amount, payment_method, transaction_id, status, payment_date, applied_to_invoices (jsonb), gateway_response (jsonb), created_at | -> customers (N:1) | Yes |
| `customer_payment_tokens` | id, business_id, customer_id, token, expires_at, is_used, created_at | -> customers (N:1) | Yes |

### Banking Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `bank_accounts` | id, business_id, gl_account_id, created_at, (all columns via select *) | -> chart_of_accounts (N:1) | Yes |
| `bank_transactions` | id, business_id, bank_account_id, transaction_date, is_matched, matched_journal_entry_id, (all columns via select *) | -> bank_accounts (N:1), -> journal_entries (N:1) | Yes |
| `bank_statements` | id, business_id, statement_date, (all columns via select *) | None observed | Yes |

### POS Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `pos_transactions` | id, business_id, transaction_number, cashier_id, customer_id, subtotal, tax_amount, total_amount, amount_tendered, change_amount, status, notes, is_bonded, exemption_reason, authorized_by, created_at | -> pos_transaction_items (1:N) | Yes |
| `pos_transaction_items` | id, transaction_id, product_id, product_name, product_sku, quantity, unit_price, tax_amount, line_total, duty_amount, exemption_type | -> pos_transactions (N:1), -> products (N:1) | Via transaction |
| `pos_payments` | id, transaction_id, payment_method, amount, reference_number, notes | -> pos_transactions (N:1) | Via transaction |

### Time/Project Tables

| Table | Columns Observed | Relationships | business_id? |
|-------|-----------------|---------------|--------------|
| `time_entries` | id, business_id, date, hours, description, billable, hourly_rate, project_id, employee_id, task_id, invoice_id | -> projects (N:1) -> projects.customers (nested), -> employees (N:1), -> tasks (N:1) | Yes |

---

## Target Data Layer Design

### Design Principles

1. **React Query for ALL data fetching** -- replace useState+useEffect entirely
2. **Query keys follow entity hierarchy** -- `['invoices', businessId, filters]`
3. **Explicit column selects** -- no more `select('*')`
4. **Unified error handling** -- single error boundary pattern
5. **Optimistic updates for mutations** -- immediate UI response
6. **Separate aggregate queries** -- stats never derived from paginated subsets
7. **Soft delete by default** -- `is_deleted` flag, not `.delete()`
8. **All mutations route through services** -- hooks never write SQL directly
9. **Consistent business_id enforcement** -- extracted once, never accessed raw

### Type Definitions

```typescript
// =============================================================================
// SHARED TYPES
// =============================================================================

/** Business context -- extracted once by useBusiness(), passed to all queries */
type BusinessId = string & { readonly __brand: 'BusinessId' };

/** Pagination parameters */
interface PaginationParams {
  page: number;
  pageSize: number;
}

/** Pagination result metadata */
interface PaginatedResult<T> {
  data: T[];
  totalCount: number;
  totalPages: number;
  currentPage: number;
  pageSize: number;
}

/** Sort direction */
type SortDirection = 'asc' | 'desc';

/** Generic filter operator */
type FilterOperator = 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'ilike' | 'in' | 'is';

/** Generic filter */
interface Filter {
  column: string;
  operator: FilterOperator;
  value: unknown;
}

/** Date range filter (common across all entities) */
interface DateRangeFilter {
  from?: string; // ISO date
  to?: string;   // ISO date
}

// =============================================================================
// CHART OF ACCOUNTS
// =============================================================================

interface ChartOfAccountsRow {
  id: string;
  business_id: string;
  account_code: string;
  account_name: string;
  account_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
  parent_account_id: string | null;
  description: string | null;
  is_active: boolean;
  is_system_account: boolean;
  current_balance: number;
  created_at: string;
  updated_at: string;
}

interface ChartOfAccountsInsert {
  account_code: string;
  account_name: string;
  account_type: ChartOfAccountsRow['account_type'];
  parent_account_id?: string | null;
  description?: string | null;
  is_active?: boolean;
}

interface ChartOfAccountsUpdate {
  account_name?: string;
  account_type?: ChartOfAccountsRow['account_type'];
  parent_account_id?: string | null;
  description?: string | null;
  is_active?: boolean;
}

// =============================================================================
// JOURNAL ENTRIES
// =============================================================================

interface JournalEntryRow {
  id: string;
  business_id: string;
  entry_number: string;
  entry_date: string;
  description: string | null;
  total_amount: number;
  status: 'draft' | 'posted' | 'reversed';
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

interface JournalEntryWithTransactions extends JournalEntryRow {
  account_transactions: AccountTransactionWithAccount[];
}

interface AccountTransactionRow {
  id: string;
  journal_entry_id: string;
  account_id: string;
  debit_amount: number;
  credit_amount: number;
  description: string | null;
}

interface AccountTransactionWithAccount extends AccountTransactionRow {
  chart_of_accounts: {
    id: string;
    account_code: string;
    account_name: string;
  };
}

interface JournalEntryInsert {
  entry_date: string;
  description?: string;
  entry_type?: string;
  reference_type?: string;
  reference_id?: string;
  notes?: string;
  transactions: {
    account_id: string;
    debit_amount: number;
    credit_amount: number;
    description?: string;
  }[];
}

interface JournalEntryFilters {
  search?: string;
  entry_type?: string;
  status?: string;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// INVOICES
// =============================================================================

interface InvoiceRow {
  id: string;
  business_id: string;
  customer_id: string | null;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  amount_paid: number;
  balance_due: number;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface InvoiceWithRelations extends InvoiceRow {
  customers: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    company_name: string | null;
  } | null;
  invoice_line_items: InvoiceLineItemRow[];
}

interface InvoiceLineItemRow {
  id: string;
  invoice_id: string;
  product_id: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

interface InvoiceInsert {
  customer_id?: string;
  invoice_date: string;
  due_date: string;
  status?: InvoiceRow['status'];
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

interface InvoiceUpdate {
  customer_id?: string;
  invoice_date?: string;
  due_date?: string;
  status?: InvoiceRow['status'];
  subtotal?: number;
  tax_amount?: number;
  total_amount?: number;
  amount_paid?: number;
  balance_due?: number;
  notes?: string;
}

interface InvoiceFilters {
  search?: string;
  status?: string;
  customer_id?: string;
  dateRange?: DateRangeFilter;
}

/** Separate type for invoice aggregations -- never derived from paginated data */
interface InvoiceAggregations {
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
// INVOICE PAYMENTS
// =============================================================================

interface InvoicePaymentRow {
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

interface InvoicePaymentInsert {
  invoice_id: string;
  payment_amount: number;
  payment_method: string;
  payment_date?: string;
  reference_number?: string;
  bank_account_id?: string;
  notes?: string;
}

// =============================================================================
// BILLS
// =============================================================================

interface BillRow {
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
  status: 'pending' | 'approved' | 'paid' | 'overdue' | 'cancelled';
  notes: string | null;
  processing_status: 'manual' | 'automatic' | 'verified';
  confidence_score: number | null;
  is_deleted: boolean; // NEW: soft delete flag
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface BillWithRelations extends BillRow {
  suppliers: { name: string } | null;
  bill_items: BillItemRow[];
}

interface BillItemRow {
  id: string;
  bill_id: string;
  product_id: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
}

interface BillInsert {
  supplier_id: string;
  purchase_order_id?: string;
  bill_number: string;
  bill_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  status?: BillRow['status'];
  notes?: string;
  processing_status?: BillRow['processing_status'];
  confidence_score?: number;
  line_items?: {
    product_id?: string;
    description: string;
    quantity: number;
    unit_price: number;
    line_total: number;
  }[];
}

interface BillUpdate {
  supplier_id?: string;
  bill_date?: string;
  due_date?: string;
  status?: BillRow['status'];
  notes?: string;
  amount_paid?: number;
  balance_due?: number;
  is_deleted?: boolean;
}

interface BillFilters {
  search?: string;
  status?: string;
  supplier_id?: string;
  processing_status?: string;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// BILL PAYMENTS
// =============================================================================

interface BillPaymentRow {
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
}

interface BillPaymentInsert {
  bill_id: string;
  payment_amount: number;
  payment_date: string;
  payment_method: string;
  bank_account_id?: string;
  reference_number?: string;
  notes?: string;
  attachment_url?: string;
}

// =============================================================================
// BILL TEMPLATES
// =============================================================================

interface BillTemplateRow {
  id: string;
  business_id: string;
  supplier_id: string;
  template_data: Record<string, unknown>; // ExtractedBillData
  created_at: string;
}

interface BillTemplateWithSupplier extends BillTemplateRow {
  supplier: { name: string } | null;
}

// =============================================================================
// EXPENSES
// =============================================================================

interface ExpenseRow {
  id: string;
  business_id: string;
  expense_number: string;
  expense_date: string;
  description: string | null;
  amount: number;
  total_amount: number;
  category: string | null;
  status: 'draft' | 'pending_approval' | 'approved' | 'rejected';
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

interface ExpenseWithRelations extends ExpenseRow {
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

interface ExpenseInsert {
  expense_date: string;
  description?: string;
  amount: number;
  total_amount?: number;
  category?: string;
  status?: ExpenseRow['status'];
  vendor?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  supplier_id?: string;
  employee_id?: string;
}

interface ExpenseUpdate {
  expense_date?: string;
  description?: string;
  amount?: number;
  total_amount?: number;
  category?: string;
  status?: ExpenseRow['status'];
  vendor?: string;
  payment_method?: string;
  reference_number?: string;
  notes?: string;
  approved_at?: string;
  approved_by?: string;
}

interface ExpenseFilters {
  search?: string;
  category?: string;
  status?: string;
  payment_method?: string;
  dateRange?: DateRangeFilter;
}

// =============================================================================
// PAYMENTS (Unified)
// =============================================================================

interface PaymentRow {
  id: string;
  business_id: string;
  payment_number: string;
  payment_date: string;
  payment_method: 'cash' | 'check' | 'bank_transfer' | 'credit_card' | 'debit_card' | 'other';
  amount: number;
  currency: string;
  exchange_rate: number;
  reference_number: string | null;
  check_number: string | null;
  bank_account_id: string | null;
  payment_type: 'customer_payment' | 'supplier_payment';
  customer_id: string | null;
  supplier_id: string | null;
  status: 'pending' | 'cleared' | 'bounced' | 'cancelled';
  posted_to_gl: boolean;
  gl_journal_entry_id: string | null;
  notes: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface PaymentWithRelations extends PaymentRow {
  customers: { first_name: string; last_name: string; company_name: string | null; email: string } | null;
  suppliers: { name: string; email: string } | null;
  payment_applications: PaymentApplicationRow[];
}

interface PaymentApplicationRow {
  id: string;
  payment_id: string;
  invoice_id: string | null;
  bill_id: string | null;
  applied_amount: number;
  application_date: string;
  notes: string | null;
}

// =============================================================================
// PAYMENT REMINDERS
// =============================================================================

interface PaymentReminderRow {
  id: string;
  business_id: string;
  invoice_id: string;
  customer_id: string;
  reminder_type: 'friendly' | 'first_notice' | 'second_notice' | 'final_notice' | 'collection';
  reminder_date: string;
  sent_date: string | null;
  sent_by: string | null;
  reminder_method: 'email' | 'phone' | 'letter' | 'sms';
  message_content: string | null;
  status: 'pending' | 'sent' | 'failed' | 'responded';
  response_notes: string | null;
  next_reminder_date: string | null;
  created_at: string;
  created_by: string;
}

interface PaymentReminderWithRelations extends PaymentReminderRow {
  invoices: { invoice_number: string; total_amount: number } | null;
  customers: { first_name: string; last_name: string; company_name: string | null } | null;
}

interface PaymentReminderInsert {
  invoice_id: string;
  customer_id: string;
  reminder_type: PaymentReminderRow['reminder_type'];
  reminder_date: string;
  reminder_method: PaymentReminderRow['reminder_method'];
  message_content?: string;
  status?: PaymentReminderRow['status'];
}

// =============================================================================
// PAYMENT PLANS
// =============================================================================

interface PaymentPlanRow {
  id: string;
  business_id: string;
  customer_id: string;
  plan_name: string;
  total_amount: number;
  remaining_amount: number;
  installment_amount: number;
  frequency: 'weekly' | 'biweekly' | 'monthly';
  start_date: string;
  end_date: string;
  status: 'active' | 'completed' | 'defaulted' | 'cancelled';
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface PaymentPlanWithRelations extends PaymentPlanRow {
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
}

interface PaymentPlanInstallmentRow {
  id: string;
  payment_plan_id: string;
  installment_number: number;
  due_date: string;
  amount: number;
  paid_amount: number;
  status: 'pending' | 'paid' | 'overdue' | 'partial';
  paid_date: string | null;
  created_at: string;
}

interface PaymentPlanInsert {
  customer_id: string;
  plan_name: string;
  total_amount: number;
  installment_amount: number;
  frequency: PaymentPlanRow['frequency'];
  start_date: string;
  number_of_installments: number;
}

// =============================================================================
// BULK PAYMENTS
// =============================================================================

interface BulkPaymentBatchRow {
  id: string;
  business_id: string;
  batch_name: string;
  payment_date: string;
  bill_count: number;
  total_amount: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processed_at: string | null;
  created_by: string;
  created_at: string;
}

interface BulkPaymentBatchInsert {
  batch_name: string;
  payment_date: string;
  bill_ids: string[];
}

// =============================================================================
// ONLINE PAYMENTS
// =============================================================================

interface OnlinePaymentRow {
  id: string;
  business_id: string;
  customer_id: string;
  payment_amount: number;
  payment_method: string;
  transaction_id: string | null;
  status: 'pending' | 'completed' | 'failed' | 'cancelled';
  payment_date: string;
  applied_to_invoices: string[]; // jsonb array of invoice IDs
  gateway_response: Record<string, unknown>;
  created_at: string;
}

interface OnlinePaymentWithCustomer extends OnlinePaymentRow {
  customers: {
    first_name: string;
    last_name: string;
    company_name: string | null;
    email: string;
  } | null;
}

// =============================================================================
// CUSTOMER PAYMENT TOKENS
// =============================================================================

interface CustomerPaymentTokenRow {
  id: string;
  business_id: string;
  customer_id: string;
  token: string;
  expires_at: string;
  is_used: boolean;
  created_at: string;
}

// =============================================================================
// BANKING
// =============================================================================

interface BankAccountRow {
  id: string;
  business_id: string;
  gl_account_id: string | null;
  // Additional columns from select('*') -- exact schema unknown
  created_at: string;
}

interface BankTransactionRow {
  id: string;
  business_id: string;
  bank_account_id: string;
  transaction_date: string;
  is_matched: boolean;
  matched_journal_entry_id: string | null;
  // Additional columns from select('*')
}

interface BankStatementRow {
  id: string;
  business_id: string;
  statement_date: string;
  // Additional columns from select('*')
}

// =============================================================================
// POS
// =============================================================================

interface POSTransactionRow {
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
  status: 'completed' | 'pending' | 'refunded' | 'voided';
  notes: string | null;
  is_bonded: boolean | null;
  exemption_reason: string | null;
  authorized_by: string | null;
  created_at: string;
}

interface POSTransactionItemRow {
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

interface POSPaymentRow {
  id: string;
  transaction_id: string;
  payment_method: string;
  amount: number;
  reference_number: string | null;
  notes: string | null;
}

// =============================================================================
// TIME ENTRIES
// =============================================================================

interface TimeEntryRow {
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
```

### Query Keys

```typescript
// =============================================================================
// QUERY KEY FACTORY
// =============================================================================

const accountingKeys = {
  // Chart of Accounts
  accounts: {
    all: (businessId: string) => ['accounts', businessId] as const,
    list: (businessId: string, filters?: { type?: string; active?: boolean }) =>
      ['accounts', businessId, 'list', filters] as const,
    detail: (businessId: string, accountId: string) =>
      ['accounts', businessId, 'detail', accountId] as const,
  },

  // Journal Entries
  journalEntries: {
    all: (businessId: string) => ['journal-entries', businessId] as const,
    list: (businessId: string, filters?: JournalEntryFilters, pagination?: PaginationParams) =>
      ['journal-entries', businessId, 'list', filters, pagination] as const,
    detail: (businessId: string, entryId: string) =>
      ['journal-entries', businessId, 'detail', entryId] as const,
  },

  // Invoices
  invoices: {
    all: (businessId: string) => ['invoices', businessId] as const,
    list: (businessId: string, filters?: InvoiceFilters, pagination?: PaginationParams) =>
      ['invoices', businessId, 'list', filters, pagination] as const,
    detail: (businessId: string, invoiceId: string) =>
      ['invoices', businessId, 'detail', invoiceId] as const,
    aggregations: (businessId: string) =>
      ['invoices', businessId, 'aggregations'] as const,
  },

  // Invoice Payments
  invoicePayments: {
    byInvoice: (businessId: string, invoiceId: string) =>
      ['invoice-payments', businessId, 'by-invoice', invoiceId] as const,
    byCustomer: (businessId: string, customerId: string) =>
      ['invoice-payments', businessId, 'by-customer', customerId] as const,
  },

  // Bills
  bills: {
    all: (businessId: string) => ['bills', businessId] as const,
    list: (businessId: string, filters?: BillFilters, pagination?: PaginationParams) =>
      ['bills', businessId, 'list', filters, pagination] as const,
    detail: (businessId: string, billId: string) =>
      ['bills', businessId, 'detail', billId] as const,
  },

  // Bill Payments
  billPayments: {
    byBill: (businessId: string, billId: string) =>
      ['bill-payments', businessId, 'by-bill', billId] as const,
  },

  // Bill Templates
  billTemplates: {
    all: (businessId: string) => ['bill-templates', businessId] as const,
    bySupplier: (businessId: string, supplierId: string) =>
      ['bill-templates', businessId, 'by-supplier', supplierId] as const,
  },

  // Expenses
  expenses: {
    all: (businessId: string) => ['expenses', businessId] as const,
    list: (businessId: string, filters?: ExpenseFilters, pagination?: PaginationParams) =>
      ['expenses', businessId, 'list', filters, pagination] as const,
    detail: (businessId: string, expenseId: string) =>
      ['expenses', businessId, 'detail', expenseId] as const,
  },

  // Payments (unified)
  payments: {
    all: (businessId: string) => ['payments', businessId] as const,
    byType: (businessId: string, type: 'customer_payment' | 'supplier_payment') =>
      ['payments', businessId, 'by-type', type] as const,
    billPayments: (businessId: string) => ['payments', businessId, 'bill-payments'] as const,
    invoicePayments: (businessId: string) => ['payments', businessId, 'invoice-payments'] as const,
    unapplied: (businessId: string, type: string) => ['payments', businessId, 'unapplied', type] as const,
  },

  // Payment Reminders
  reminders: {
    all: (businessId: string) => ['payment-reminders', businessId] as const,
  },

  // Payment Plans
  paymentPlans: {
    all: (businessId: string) => ['payment-plans', businessId] as const,
    installments: (planId: string) => ['payment-plan-installments', planId] as const,
  },

  // Bulk Payments
  bulkPayments: {
    all: (businessId: string) => ['bulk-payment-batches', businessId] as const,
  },

  // Online Payments
  onlinePayments: {
    all: (businessId: string) => ['online-payments', businessId] as const,
    tokens: (businessId: string) => ['customer-payment-tokens', businessId] as const,
  },

  // Banking
  bankAccounts: {
    all: (businessId: string) => ['bank-accounts', businessId] as const,
    detail: (businessId: string, accountId: string) =>
      ['bank-accounts', businessId, 'detail', accountId] as const,
  },

  bankTransactions: {
    all: (businessId: string) => ['bank-transactions', businessId] as const,
    byAccount: (businessId: string, accountId: string) =>
      ['bank-transactions', businessId, 'by-account', accountId] as const,
  },

  bankStatements: {
    all: (businessId: string) => ['bank-statements', businessId] as const,
  },

  // POS
  posTransactions: {
    all: (businessId: string) => ['pos-transactions', businessId] as const,
    detail: (transactionId: string) => ['pos-transactions', 'detail', transactionId] as const,
    unposted: (businessId: string) => ['pos-transactions', businessId, 'unposted'] as const,
  },

  // Time Entries
  unbilledTime: {
    all: (businessId: string) => ['unbilled-time', businessId] as const,
    byCustomer: (businessId: string, customerId: string) =>
      ['unbilled-time', businessId, 'by-customer', customerId] as const,
  },

  // Settings
  accountingSettings: {
    all: (businessId: string) => ['accounting-settings', businessId] as const,
  },

  // Dashboard aggregations (BUG-H01 fix)
  dashboard: {
    financialSummary: (businessId: string) => ['dashboard', businessId, 'financial-summary'] as const,
    arAging: (businessId: string) => ['dashboard', businessId, 'ar-aging'] as const,
    apAging: (businessId: string) => ['dashboard', businessId, 'ap-aging'] as const,
  },
};
```

### React Query Hooks

```typescript
// =============================================================================
// EXAMPLE: INVOICES (same pattern for all entity groups)
// =============================================================================

// --- Queries ---

/** List invoices with pagination and filters */
function useInvoicesQuery(filters?: InvoiceFilters, pagination?: PaginationParams) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.list(businessId, filters, pagination),
    queryFn: () => invoiceQueryFn(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: 30_000, // 30s stale time
  });
}

/** Single invoice detail */
function useInvoiceQuery(invoiceId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.detail(businessId, invoiceId),
    queryFn: () => invoiceDetailQueryFn(businessId, invoiceId),
    enabled: !!businessId && !!invoiceId,
  });
}

/** Invoice aggregations -- separate query, NEVER from paginated data (BUG-L02 fix) */
function useInvoiceAggregationsQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoices.aggregations(businessId),
    queryFn: () => invoiceAggregationsQueryFn(businessId),
    enabled: !!businessId,
    staleTime: 60_000, // 1min stale -- stats change less frequently
  });
}

// --- Mutations ---

function useCreateInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InvoiceInsert) => createInvoice(businessId, data),
    onSuccess: () => {
      // Invalidate list + aggregation queries
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all(businessId) });
    },
  });
}

function useUpdateInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InvoiceUpdate }) =>
      updateInvoice(businessId, id, data),
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: accountingKeys.invoices.all(businessId) });

      // Snapshot previous value
      const previousInvoices = queryClient.getQueryData(
        accountingKeys.invoices.all(businessId)
      );

      // Optimistically update
      queryClient.setQueriesData(
        { queryKey: accountingKeys.invoices.all(businessId) },
        (old: any) => {
          if (!old?.data) return old;
          return {
            ...old,
            data: old.data.map((inv: InvoiceRow) =>
              inv.id === id ? { ...inv, ...data } : inv
            ),
          };
        }
      );

      return { previousInvoices };
    },
    onError: (_err, _vars, context) => {
      // Rollback on error
      if (context?.previousInvoices) {
        queryClient.setQueriesData(
          { queryKey: accountingKeys.invoices.all(businessId) },
          context.previousInvoices
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all(businessId) });
    },
  });
}

function useDeleteInvoiceMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invoiceId: string) => deleteInvoice(businessId, invoiceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all(businessId) });
    },
  });
}

function useUpdateInvoiceStatusMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: InvoiceRow['status'] }) =>
      updateInvoiceStatus(businessId, id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all(businessId) });
    },
  });
}

/** Record payment against invoice -- also invalidates payments queries */
function useRecordInvoicePaymentMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: InvoicePaymentInsert) =>
      recordInvoicePayment(businessId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.invoices.all(businessId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.payments.all(businessId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all(businessId) });
    },
  });
}

// =============================================================================
// BILLS -- same pattern
// =============================================================================

function useBillsQuery(filters?: BillFilters, pagination?: PaginationParams) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.bills.list(businessId, filters, pagination),
    queryFn: () => billQueryFn(businessId, filters, pagination),
    enabled: !!businessId,
    staleTime: 30_000,
  });
}

function useDeleteBillMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    // BUG-H03 FIX: Soft delete, not hard delete
    mutationFn: (billId: string) => softDeleteBill(businessId, billId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.bills.all(businessId) });
    },
  });
}

// =============================================================================
// JOURNAL ENTRIES -- routes through GeneralLedgerService
// =============================================================================

function useCreateJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    // BUG-H04/H05 FIX: All journal entries route through GeneralLedgerService
    mutationFn: (data: JournalEntryInsert) =>
      GeneralLedgerService.createJournalEntry({
        business_id: businessId,
        description: data.description || '',
        reference_type: 'manual',
        lines: data.transactions,
        created_by: getCurrentUserId(),
        entry_date: data.entry_date,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all(businessId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all(businessId) });
    },
  });
}

function usePostJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    // BUG-H04 FIX: Post through service with validation, not direct update
    mutationFn: (entryId: string) =>
      GeneralLedgerService.postJournalEntry(businessId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all(businessId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all(businessId) });
    },
  });
}

function useReverseJournalEntryMutation() {
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  return useMutation({
    // BUG-H05 FIX: Reverse through service, not direct status update
    mutationFn: (entryId: string) =>
      GeneralLedgerService.reverseJournalEntry(businessId, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntries.all(businessId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts.all(businessId) });
    },
  });
}

// =============================================================================
// DASHBOARD -- Real aggregation queries (BUG-H01 fix)
// =============================================================================

function useFinancialSummaryQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.dashboard.financialSummary(businessId),
    queryFn: () => fetchFinancialSummary(businessId),
    enabled: !!businessId,
    staleTime: 60_000,
  });
}

function useARAgingQuery() {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.dashboard.arAging(businessId),
    // BUG-H06 FIX: Consistent bucket key naming
    queryFn: () => fetchARAgingReport(businessId),
    enabled: !!businessId,
    staleTime: 60_000,
  });
}

// =============================================================================
// PATTERNS FOR REMAINING ENTITIES
// =============================================================================

// Each entity group follows the same structure:
// - useXxxQuery(filters, pagination)  -- list
// - useXxxDetailQuery(id)             -- detail
// - useCreateXxxMutation()            -- create
// - useUpdateXxxMutation()            -- update
// - useDeleteXxxMutation()            -- delete (soft where applicable)
//
// Entity groups:
// - Expenses        (useExpensesQuery, useCreateExpenseMutation, etc.)
// - Payments        (usePaymentsQuery -- unified across 3 payment tables)
// - PaymentReminders (usePaymentRemindersQuery, useCreateReminderMutation, etc.)
// - PaymentPlans    (usePaymentPlansQuery, useInstallmentsQuery, etc.)
// - BulkPayments    (useBulkPaymentBatchesQuery, useCreateBatchMutation, etc.)
// - OnlinePayments  (useOnlinePaymentsQuery, useProcessOnlinePaymentMutation, etc.)
// - BankAccounts    (useBankAccountsQuery, useCreateBankAccountMutation, etc.)
// - BankReconciliation (useBankTransactionsQuery, useMatchTransactionMutation, etc.)
// - AccountingSettings (useAccountingSettingsQuery, useUpdateSettingsMutation)
// - BillTemplates   (useBillTemplatesQuery, useDeleteTemplateMutation)
// - POS Accounting  (usePostPOSSaleMutation, useBulkPostPOSMutation)
// - UnbilledTime    (useUnbilledTimeQuery, useCreateInvoicesFromTimeMutation)
```

### Query Functions (Backend Layer)

```typescript
// =============================================================================
// INVOICES -- query functions (all explicit column selects)
// =============================================================================

async function invoiceQueryFn(
  businessId: string,
  filters?: InvoiceFilters,
  pagination?: PaginationParams
): Promise<PaginatedResult<InvoiceWithRelations>> {
  let query = supabase
    .from('invoices')
    .select(`
      id, business_id, customer_id, invoice_number, invoice_date, due_date,
      status, subtotal, tax_amount, total_amount, amount_paid, balance_due,
      notes, created_by, created_at, updated_at,
      customers (id, first_name, last_name, email, company_name),
      invoice_line_items (id, product_id, description, quantity, unit_price, line_total)
    `, { count: 'exact' })
    .eq('business_id', businessId);

  // Apply filters
  if (filters?.status && filters.status !== 'all') {
    query = query.eq('status', filters.status);
  }
  if (filters?.customer_id && filters.customer_id !== 'all') {
    query = query.eq('customer_id', filters.customer_id);
  }
  if (filters?.dateRange?.from) {
    query = query.gte('invoice_date', filters.dateRange.from);
  }
  if (filters?.dateRange?.to) {
    query = query.lte('invoice_date', filters.dateRange.to);
  }
  if (filters?.search) {
    query = query.or(
      `invoice_number.ilike.%${filters.search}%,notes.ilike.%${filters.search}%`
    );
  }

  // Apply pagination
  const page = pagination?.page ?? 1;
  const pageSize = pagination?.pageSize ?? 20;
  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  query = query.range(from, to).order('created_at', { ascending: false });

  const { data, error, count } = await query;
  if (error) throw error;

  // Compute overdue status client-side
  const today = new Date().toISOString().split('T')[0];
  const processed = (data ?? []).map(inv => ({
    ...inv,
    status: inv.status === 'sent' && inv.due_date < today && inv.balance_due > 0
      ? 'overdue' as const
      : inv.status,
  }));

  return {
    data: processed,
    totalCount: count ?? 0,
    totalPages: Math.ceil((count ?? 0) / pageSize),
    currentPage: page,
    pageSize,
  };
}

/** BUG-L02 FIX: Separate aggregation query -- never derived from page data */
async function invoiceAggregationsQueryFn(businessId: string): Promise<InvoiceAggregations> {
  const { data, error } = await supabase
    .from('invoices')
    .select('status, total_amount, balance_due')
    .eq('business_id', businessId);

  if (error) throw error;

  return (data ?? []).reduce(
    (acc, inv) => {
      acc.totalAmount += inv.total_amount ?? 0;
      acc.totalCount++;
      if (inv.status === 'paid') {
        acc.paidAmount += inv.total_amount ?? 0;
        acc.paidCount++;
      } else if (inv.status === 'overdue') {
        acc.overdueAmount += inv.balance_due ?? 0;
        acc.overdueCount++;
        acc.outstandingAmount += inv.balance_due ?? 0;
        acc.outstandingCount++;
      } else if (inv.status !== 'cancelled') {
        acc.outstandingAmount += inv.balance_due ?? 0;
        acc.outstandingCount++;
      }
      return acc;
    },
    {
      totalAmount: 0, paidAmount: 0, outstandingAmount: 0, overdueAmount: 0,
      totalCount: 0, paidCount: 0, outstandingCount: 0, overdueCount: 0,
    }
  );
}

// =============================================================================
// FINANCIAL SUMMARY (BUG-H01 FIX -- real data, not mock)
// =============================================================================

interface FinancialSummary {
  totalRevenue: number;
  totalExpenses: number;
  netIncome: number;
  accountsReceivable: number;
  accountsPayable: number;
  cashBalance: number;
}

async function fetchFinancialSummary(businessId: string): Promise<FinancialSummary> {
  const [invoicesResult, billsResult, expensesResult, accountsResult] = await Promise.all([
    supabase
      .from('invoices')
      .select('total_amount, amount_paid, balance_due, status')
      .eq('business_id', businessId)
      .neq('status', 'cancelled'),
    supabase
      .from('bills')
      .select('total_amount, amount_paid, balance_due, status')
      .eq('business_id', businessId)
      .neq('status', 'cancelled'),
    supabase
      .from('expenses')
      .select('total_amount, status')
      .eq('business_id', businessId)
      .eq('status', 'approved'),
    supabase
      .from('chart_of_accounts')
      .select('account_code, account_type, current_balance')
      .eq('business_id', businessId)
      .eq('is_active', true),
  ]);

  if (invoicesResult.error) throw invoicesResult.error;
  if (billsResult.error) throw billsResult.error;
  if (expensesResult.error) throw expensesResult.error;
  if (accountsResult.error) throw accountsResult.error;

  const totalRevenue = (invoicesResult.data ?? []).reduce(
    (sum, inv) => sum + (inv.amount_paid ?? 0), 0
  );
  const accountsReceivable = (invoicesResult.data ?? []).reduce(
    (sum, inv) => sum + (inv.balance_due ?? 0), 0
  );
  const accountsPayable = (billsResult.data ?? []).reduce(
    (sum, bill) => sum + (bill.balance_due ?? 0), 0
  );
  const totalExpenses = (expensesResult.data ?? []).reduce(
    (sum, exp) => sum + (exp.total_amount ?? 0), 0
  );

  const cashAccount = (accountsResult.data ?? []).find(a => a.account_code === '1000');
  const cashBalance = cashAccount?.current_balance ?? 0;

  return {
    totalRevenue,
    totalExpenses,
    netIncome: totalRevenue - totalExpenses,
    accountsReceivable,
    accountsPayable,
    cashBalance,
  };
}

// =============================================================================
// AR AGING REPORT (BUG-H06 FIX -- consistent bucket keys)
// =============================================================================

interface AgingBucket {
  current: number;       // 0-30 days
  thirtyDays: number;    // 31-60 days
  sixtyDays: number;     // 61-90 days
  ninetyDays: number;    // 91+ days
  total: number;
}

async function fetchARAgingReport(businessId: string): Promise<AgingBucket> {
  const { data, error } = await supabase
    .from('invoices')
    .select('due_date, balance_due, status')
    .eq('business_id', businessId)
    .gt('balance_due', 0)
    .neq('status', 'cancelled')
    .neq('status', 'paid');

  if (error) throw error;

  const today = new Date();
  const result: AgingBucket = { current: 0, thirtyDays: 0, sixtyDays: 0, ninetyDays: 0, total: 0 };

  for (const inv of data ?? []) {
    const daysOverdue = Math.floor(
      (today.getTime() - new Date(inv.due_date).getTime()) / (1000 * 60 * 60 * 24)
    );
    const amount = inv.balance_due ?? 0;
    result.total += amount;

    if (daysOverdue <= 30) result.current += amount;
    else if (daysOverdue <= 60) result.thirtyDays += amount;
    else if (daysOverdue <= 90) result.sixtyDays += amount;
    else result.ninetyDays += amount;
  }

  return result;
}

// =============================================================================
// BILL SOFT DELETE (BUG-H03 FIX)
// =============================================================================

async function softDeleteBill(businessId: string, billId: string): Promise<void> {
  const { error } = await supabase
    .from('bills')
    .update({ is_deleted: true, status: 'cancelled' })
    .eq('id', billId)
    .eq('business_id', businessId);

  if (error) throw error;
}
```

### Shared Utilities

```typescript
// =============================================================================
// useBusinessId() -- extracted once, typed, never nullable when enabled
// =============================================================================

function useBusinessId(): string {
  const { currentBusiness } = useBusiness();
  if (!currentBusiness?.id) {
    throw new Error('useBusinessId called without business context');
  }
  return currentBusiness.id;
}

// Optional: safe version that returns undefined (for enabled checks)
function useBusinessIdSafe(): string | undefined {
  const { currentBusiness } = useBusiness();
  return currentBusiness?.id;
}

// =============================================================================
// getCurrentUserId() -- for mutations that need created_by
// =============================================================================

async function getCurrentUserId(): Promise<string> {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) throw new Error('No authenticated user');
  return user.id;
}

// =============================================================================
// Pagination utility (keep existing usePagination, it is well-designed)
// =============================================================================

// The existing usePagination hook at /src/hooks/usePagination.tsx is well-implemented.
// Retain it. React Query's keepPreviousData option replaces the need for
// manual loading state management during page transitions.

// =============================================================================
// Filter builder
// =============================================================================

function applyFilters<T extends { eq: Function; gte: Function; lte: Function; or: Function }>(
  query: T,
  filters: Filter[]
): T {
  for (const filter of filters) {
    switch (filter.operator) {
      case 'eq': query = query.eq(filter.column, filter.value); break;
      case 'neq': query = query.neq(filter.column, filter.value); break;
      case 'gt': query = query.gt(filter.column, filter.value); break;
      case 'gte': query = query.gte(filter.column, filter.value); break;
      case 'lt': query = query.lt(filter.column, filter.value); break;
      case 'lte': query = query.lte(filter.column, filter.value); break;
      case 'like': query = query.like(filter.column, filter.value as string); break;
      case 'ilike': query = query.ilike(filter.column, filter.value as string); break;
      case 'in': query = query.in(filter.column, filter.value as unknown[]); break;
      case 'is': query = query.is(filter.column, filter.value); break;
    }
  }
  return query;
}
```

---

## Hook -> Table Coverage Matrix

| Table | Current Hooks | Target Hooks |
|-------|--------------|--------------|
| `chart_of_accounts` | `useAccounting`, `useInvoiceAccounting`, `useBillAccounting`, `useExpenseAccounting`, `usePOSAccounting` | `useAccountsQuery`, `useCreateAccountMutation` |
| `journal_entries` | `useAccounting`, `useJournalEntries`, `useJournalEntriesPaginated`, `useAccountingAutomation`, `useInvoiceAccounting`, `useBillAccounting`, `useExpenseAccounting`, `usePOSAccounting` | `useJournalEntriesQuery`, `useCreateJournalEntryMutation`, `usePostJournalEntryMutation`, `useReverseJournalEntryMutation` |
| `account_transactions` | `useAccounting`, `useJournalEntries`, `useJournalEntriesPaginated`, `useInvoiceAccounting`, `useBillAccounting`, `useExpenseAccounting` | (Created via GeneralLedgerService, queried via journal entry joins) |
| `accounting_settings` | `useAccountingAutomation` | `useAccountingSettingsQuery`, `useUpdateSettingsMutation` |
| `invoices` | `useAccounting`, `useInvoices`, `useInvoicesPaginated`, `useCustomerPaymentsPaginated`, `useOnlinePayments`, `useUnbilledTime`, `usePaymentReminders` | `useInvoicesQuery`, `useInvoiceAggregationsQuery`, `useCreateInvoiceMutation`, `useUpdateInvoiceMutation`, `useDeleteInvoiceMutation` |
| `invoice_line_items` | `useInvoices`, `useInvoicesPaginated` | (Created/deleted via invoice mutations) |
| `invoice_items` | `useUnbilledTime` | (Created via time-entry-to-invoice mutation) |
| `invoice_payments` | `useInvoiceAccounting`, `usePayments`, `useOnlinePayments`, `useCustomerPaymentsPaginated` | `useRecordInvoicePaymentMutation` |
| `bills` | `useBills`, `useBillsPaginated`, `useBulkPayments`, `usePayments` | `useBillsQuery`, `useCreateBillMutation`, `useUpdateBillMutation`, `useDeleteBillMutation` (soft) |
| `bill_items` | `useBills`, `useBillsPaginated` | (Created/deleted via bill mutations) |
| `bill_payments` | `useBills`, `useBillAccounting`, `useAccountingAutomation`, `usePayments` | `useRecordBillPaymentMutation` |
| `bill_templates` | `useBillTemplates` | `useBillTemplatesQuery`, `useDeleteTemplateMutation` |
| `expenses` | `useAccounting`, `useExpenses`, `useExpensesPaginated`, `useExpenseAccounting` | `useExpensesQuery`, `useCreateExpenseMutation`, `useUpdateExpenseMutation`, `useDeleteExpenseMutation` |
| `payments` | `usePayments` (via PaymentsService) | `usePaymentsQuery`, `useCreatePaymentMutation`, `useVoidPaymentMutation` |
| `payment_applications` | `usePayments` (via PaymentsService) | (Created via payment mutations) |
| `payment_reminders` | `usePaymentReminders` | `usePaymentRemindersQuery`, `useCreateReminderMutation`, `useMarkReminderSentMutation` |
| `payment_plans` | `usePaymentPlans` | `usePaymentPlansQuery`, `useCreatePaymentPlanMutation` |
| `payment_plan_installments` | `usePaymentPlans` | `useInstallmentsQuery`, `useRecordInstallmentMutation` |
| `bulk_payment_batches` | `useBulkPayments` | `useBulkPaymentBatchesQuery`, `useCreateBatchMutation`, `useProcessBatchMutation` |
| `online_payments` | `useOnlinePayments` | `useOnlinePaymentsQuery`, `useProcessOnlinePaymentMutation` |
| `customer_payment_tokens` | `useOnlinePayments` | `useGenerateTokenMutation`, `useValidateTokenQuery` |
| `bank_accounts` | `useBankAccounts` | `useBankAccountsQuery`, `useCreateBankAccountMutation`, `useUpdateBankAccountMutation`, `useDeleteBankAccountMutation` |
| `bank_transactions` | `useBankReconciliation` | `useBankTransactionsQuery`, `useImportTransactionsMutation`, `useMatchTransactionMutation` |
| `bank_statements` | `useBankReconciliation` | `useBankStatementsQuery` |
| `pos_transactions` | `useAdvancedPayments`, `usePOSAccounting` | `usePOSTransactionsQuery`, `usePostPOSSaleMutation`, `useBulkPostPOSMutation` |
| `pos_transaction_items` | `useAdvancedPayments`, `usePOSAccounting` | (Created via POS transaction, queried via joins) |
| `pos_payments` | `useAdvancedPayments` | (Created via POS transaction) |
| `time_entries` | `useUnbilledTime` | `useUnbilledTimeQuery`, `useCreateInvoicesFromTimeMutation` |

**Coverage: All 26 tables have at least one target hook.**

---

## Bug Fix Data Layer

| Bug ID | Bug Description | Root Cause in Current Data Layer | Fix in Target Data Layer |
|--------|----------------|----------------------------------|--------------------------|
| **BUG-H01** | Financial Management shows mock data | No real aggregation queries exist. Dashboard likely renders hardcoded values. | `useFinancialSummaryQuery()` fetches real aggregations from `invoices`, `bills`, `expenses`, and `chart_of_accounts` tables via `fetchFinancialSummary()`. |
| **BUG-H02** | AR tab uses `arTransactions` but hook returns `invoices` | Interface mismatch -- component expects `arTransactions` property, hook exposes `invoices`. | Target hook `useInvoicesQuery()` returns typed `InvoiceWithRelations[]`. Component must be updated to consume `invoices` (or alias in the hook return). |
| **BUG-H03** | Bill detail hard-deletes while list soft-deletes | Both `useBills.deleteBill()` and `useBillsPaginated.deleteBill()` use `.delete()` (hard delete). Neither uses soft delete. | `useDeleteBillMutation` calls `softDeleteBill()` which sets `is_deleted: true, status: 'cancelled'`. All bill queries add `.eq('is_deleted', false)` filter. Database migration needed to add `is_deleted` column. |
| **BUG-H04** | Journal entry Post bypasses validation service | `useJournalEntries.postJournalEntry()` directly does `.update({ status: 'posted' })` without validating debit/credit balance, account existence, or period status. | `usePostJournalEntryMutation` routes through `GeneralLedgerService.postJournalEntry()` which validates balance, checks period, updates account balances. |
| **BUG-H05** | Journal entry Reverse bypasses validation service | No reverse function exists in `useJournalEntries`. If implemented, it would need to create reversing entries with proper GL impact. | `useReverseJournalEntryMutation` routes through `GeneralLedgerService.reverseJournalEntry()` which creates a reversing journal entry with swapped debits/credits. |
| **BUG-H06** | Aging report key mismatch | Aging bucket keys inconsistent between query and component (`days_30` vs `thirtyDays` vs `30_days`). | `AgingBucket` type uses consistent keys: `current`, `thirtyDays`, `sixtyDays`, `ninetyDays`, `total`. Single source of truth. |
| **BUG-L02** | Stats from paginated subset | `useInvoicesPaginated.loadMetadata()` correctly uses a separate query, but other paginated hooks (bills, expenses, journal entries) do NOT have separate stats queries. | Every entity with summary stats gets a dedicated `useXxxAggregationsQuery()` that runs a separate Supabase query selecting only the columns needed for aggregation. Never derived from paginated page data. |
| **BUG-L03** | Employee join missing | `useExpensesPaginated` does `select('*')` with no employee join. Employee name unavailable in expense list. | Expense query function explicitly joins `employees(id, first_name, last_name, email)` and `suppliers(id, name, email)`. |
| **NEW** | `PaymentsService.getPaymentsByType()` does not exist | `usePayments` calls `PaymentsService.getPaymentsByType()` at lines 144 and 157, but this method is not defined on the class. Will throw at runtime. | `PaymentsService.getPayments()` already accepts a `filters` param with `payment_type`. Target hook uses `PaymentsService.getPayments(businessId, { payment_type: 'supplier_payment' })` instead. |
| **NEW** | `useBulkPayments.processPaymentBatch()` uses fake `setTimeout` | `setTimeout(resolve, 2000)` simulates processing. No real bill payment processing occurs. | `useProcessBatchMutation` iterates bill IDs in the batch, calls `recordBillPayment()` for each, and updates batch status based on actual results. |
| **NEW** | Duplicate invoice line item tables | Both `invoice_line_items` and `invoice_items` exist. `useInvoices` uses the former, `useUnbilledTime` uses the latter. | Consolidate to `invoice_line_items` only. Update `useUnbilledTime.createInvoicesFromTimeEntries()` to insert into `invoice_line_items` instead of `invoice_items`. |

---

## Migration Path

### Phase 1: Install and Configure React Query

```bash
# Already installed (usePayments uses it)
# Ensure QueryClientProvider wraps app root
```

### Phase 2: Create Query Key Factory + Type Definitions

New file: `src/lib/accounting/keys.ts` -- query key factory
New file: `src/lib/accounting/types.ts` -- all type definitions (replaces inline types across 25 hooks)

### Phase 3: Create Query Functions

New file: `src/lib/accounting/queries/invoices.ts`
New file: `src/lib/accounting/queries/bills.ts`
New file: `src/lib/accounting/queries/expenses.ts`
New file: `src/lib/accounting/queries/journal-entries.ts`
New file: `src/lib/accounting/queries/payments.ts`
New file: `src/lib/accounting/queries/banking.ts`
New file: `src/lib/accounting/queries/dashboard.ts`
New file: `src/lib/accounting/queries/pos.ts`
New file: `src/lib/accounting/queries/time-entries.ts`
New file: `src/lib/accounting/queries/settings.ts`

### Phase 4: Create React Query Hooks (1:1 replacement)

| Old Hook | New Hook(s) | Notes |
|----------|-------------|-------|
| `useAccounting` | `useAccountsQuery` + `useJournalEntriesQuery` + `useInvoicesQuery` + `useExpensesQuery` | Split god-hook into 4 focused hooks. Components import only what they need. |
| `useInvoices` | `useInvoicesQuery` + `useCreateInvoiceMutation` + `useUpdateInvoiceMutation` + `useDeleteInvoiceMutation` + `useUpdateInvoiceStatusMutation` | Queries and mutations separated. |
| `useInvoicesPaginated` | `useInvoicesQuery(filters, pagination)` + `useInvoiceAggregationsQuery` | Single query hook handles both paginated and non-paginated via optional params. Aggregations separate. |
| `useInvoiceAccounting` | `useRecordInvoicePaymentMutation` | Mutation hook only. Journal entry creation stays in service layer. |
| `useBills` | `useBillsQuery` + `useCreateBillMutation` + `useUpdateBillMutation` + `useDeleteBillMutation` (soft) | |
| `useBillsPaginated` | `useBillsQuery(filters, pagination)` | Same query hook with pagination params. |
| `useBillAccounting` | `useRecordBillPaymentMutation` | |
| `useBillTemplates` | `useBillTemplatesQuery` + `useDeleteTemplateMutation` | |
| `useExpenses` | `useExpensesQuery` + `useCreateExpenseMutation` + `useUpdateExpenseMutation` + `useDeleteExpenseMutation` + `useUpdateExpenseStatusMutation` | |
| `useExpensesPaginated` | `useExpensesQuery(filters, pagination)` | |
| `useExpenseAccounting` | `usePostExpenseMutation` + `useRecordExpensePaymentMutation` | |
| `useJournalEntries` | `useJournalEntriesQuery` + `useCreateJournalEntryMutation` + `usePostJournalEntryMutation` | All mutations route through GeneralLedgerService. |
| `useJournalEntriesPaginated` | `useJournalEntriesQuery(filters, pagination)` | |
| `usePayments` | `usePaymentsQuery` | Already uses React Query -- just normalize query keys and remove missing method call. |
| `usePaymentReminders` | `usePaymentRemindersQuery` + `useCreateReminderMutation` + `useMarkReminderSentMutation` + `useScheduleAutoRemindersMutation` | |
| `usePaymentPlans` | `usePaymentPlansQuery` + `useCreatePlanMutation` + `useRecordInstallmentMutation` + `useInstallmentsQuery` | |
| `useBulkPayments` | `useBulkPaymentBatchesQuery` + `useCreateBatchMutation` + `useProcessBatchMutation` | Remove setTimeout fake processing. |
| `useOnlinePayments` | `useOnlinePaymentsQuery` + `useProcessOnlinePaymentMutation` + `useGenerateTokenMutation` | |
| `useAdvancedPayments` | `useProcessSplitPaymentMutation` + `useProcessRefundMutation` | POS-specific. |
| `useBankAccounts` | `useBankAccountsQuery` + `useCreateBankAccountMutation` + `useUpdateBankAccountMutation` + `useDeleteBankAccountMutation` | |
| `useBankReconciliation` | `useBankTransactionsQuery` + `useBankStatementsQuery` + `useImportTransactionsMutation` + `useMatchTransactionMutation` | |
| `useAccountingAutomation` | `useAccountingSettingsQuery` + `useUpdateSettingsMutation` + `useAutoPostBillPaymentMutation` | |
| `usePOSAccounting` | `usePostPOSSaleMutation` + `useBulkPostPOSMutation` + `useCreateDefaultAccountsMutation` | |
| `useUnbilledTime` | `useUnbilledTimeQuery` + `useCreateInvoicesFromTimeMutation` | |
| `useCustomerPaymentsPaginated` | `useCustomerPaymentsQuery(filters, pagination)` | Replace inline pagination with usePagination. |

### Phase 5: Database Migrations Required

1. **Add `is_deleted` column to `bills` table** -- `ALTER TABLE bills ADD COLUMN is_deleted BOOLEAN DEFAULT false;`
2. **Consolidate `invoice_items` into `invoice_line_items`** -- migrate data, update references, drop `invoice_items`.
3. **Add `is_deleted` to `invoices` and `expenses`** (optional, for consistency).
4. **Verify `payments` table exists** -- referenced by `PaymentsService` but not verified in migration history.

### Phase 6: Component Updates

Components that consume these hooks will need updates:
1. Destructure from new hook return shapes (queries return `{ data, isLoading, error }` instead of `{ invoices, loading }`)
2. Call mutation hooks separately from query hooks
3. Handle loading/error states from React Query

### Phase 7: Remove Old Hooks

After all components are migrated, delete the 25 old hook files and the duplicate type definitions.

---

## Summary Statistics

| Metric | Current | Target |
|--------|---------|--------|
| Hook files | 25 | ~12 (query + mutation files) |
| Lines of code (hooks) | ~4,500 | ~2,000 (less boilerplate) |
| Caching strategy | None (22 of 25) | React Query stale-while-revalidate |
| Deduplication | None | Automatic via query keys |
| Optimistic updates | None | All mutations |
| Type definitions | Duplicated across files | Single source of truth |
| Error handling patterns | 3 different patterns | 1 unified pattern |
| `select('*')` usage | 8 hooks | 0 hooks |
| Fake async (`setTimeout`) | 1 hook | 0 hooks |
| Missing methods called | 1 (`getPaymentsByType`) | 0 |
| Hard deletes on financial records | All hooks | Soft delete (bills, optionally others) |
| Journal entry service bypass | 2 operations (post, reverse) | All route through GeneralLedgerService |
