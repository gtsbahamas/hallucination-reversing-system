# LVR Pilot — Database Table Inventory (Accounting Domain)

*Generated: 2026-02-13*
*Method: Grep for `.from('table_name')` in accounting-related hooks*

## Primary Tables

| Table | Used By | Operations |
|-------|---------|------------|
| `invoices` | useInvoices, useInvoiceAccounting, useInvoicesPaginated, useOnlinePayments, useCustomerPaymentsPaginated, useUnbilledTime | CRUD, filtering, status updates |
| `invoice_payments` | useInvoiceAccounting, usePayments, useOnlinePayments | Create, read |
| `invoice_line_items` | useInvoices, useInvoicesPaginated | Create, update, delete |
| `invoice_items` | useUnbilledTime | Create |
| `bills` | useBills, useBillAccounting, useBillsPaginated, useBulkPayments | CRUD, filtering, status updates |
| `bill_payments` | useBillAccounting, usePayments, useAccountingAutomation | Create, read |
| `bill_items` | useBills, useBillsPaginated | Create, read |
| `bill_templates` | useBillTemplates | CRUD |
| `expenses` | useExpenses, useExpenseAccounting, useExpensesPaginated | CRUD, filtering |
| `journal_entries` | useJournalEntries, useJournalEntriesPaginated, useAccounting, useInvoiceAccounting, useBillAccounting, useExpenseAccounting, useAccountingAutomation, usePOSAccounting | CRUD |
| `account_transactions` | useAccounting, useInvoiceAccounting, useBillAccounting, useExpenseAccounting, useJournalEntries | Create, read |
| `chart_of_accounts` | useAccounting, useInvoiceAccounting, useBillAccounting, useExpenseAccounting, usePOSAccounting | CRUD, read |
| `bank_accounts` | useBankAccounts | CRUD |
| `bank_transactions` | useBankReconciliation | Read, update |
| `bank_statements` | useBankReconciliation | Read |
| `accounting_settings` | useAccountingAutomation | Read, upsert |
| `payment_reminders` | usePaymentReminders | CRUD |
| `payment_plans` | usePaymentPlans | CRUD |
| `payment_plan_installments` | usePaymentPlans | CRUD |
| `bulk_payment_batches` | useBulkPayments | Create, read, update |
| `online_payments` | useOnlinePayments | Create, read |
| `customer_payment_tokens` | useOnlinePayments | CRUD |
| `pos_transactions` | usePOSAccounting, useAdvancedPayments | Read, create |
| `pos_transaction_items` | useAdvancedPayments | Create |
| `pos_payments` | useAdvancedPayments | Create |
| `time_entries` | useUnbilledTime | Read, update |

## Table Count: 26 tables

## Cross-Domain Tables
These tables are shared with non-accounting domains:
- `pos_transactions`, `pos_transaction_items`, `pos_payments` — POS domain
- `time_entries` — HR/Service domain
- `inventory`, `inventory_movements` — Inventory domain (via useAdvancedPayments)

## Hooks Inventory

| Hook | Primary Tables | Location |
|------|---------------|----------|
| useAccounting | chart_of_accounts, journal_entries, invoices, expenses, account_transactions | src/hooks/useAccounting.tsx |
| useInvoices | invoices, invoice_line_items | src/hooks/useInvoices.tsx |
| useInvoicesPaginated | invoices, invoice_line_items | src/hooks/useInvoicesPaginated.tsx |
| useInvoiceAccounting | invoices, invoice_payments, chart_of_accounts, journal_entries, account_transactions | src/hooks/useInvoiceAccounting.tsx |
| useBills | bills, bill_items, bill_payments | src/hooks/useBills.tsx |
| useBillsPaginated | bills, bill_items | src/hooks/useBillsPaginated.tsx |
| useBillAccounting | bills, bill_payments, chart_of_accounts, journal_entries, account_transactions | src/hooks/useBillAccounting.tsx |
| useBillTemplates | bill_templates | src/hooks/useBillTemplates.tsx |
| useExpenses | expenses | src/hooks/useExpenses.tsx |
| useExpensesPaginated | expenses | src/hooks/useExpensesPaginated.tsx |
| useExpenseAccounting | expenses, journal_entries, chart_of_accounts, account_transactions | src/hooks/useExpenseAccounting.tsx |
| useJournalEntries | journal_entries, account_transactions | src/hooks/useJournalEntries.tsx |
| useJournalEntriesPaginated | journal_entries | src/hooks/useJournalEntriesPaginated.tsx |
| usePayments | bill_payments, invoice_payments | src/hooks/usePayments.tsx |
| usePaymentReminders | payment_reminders | src/hooks/usePaymentReminders.tsx |
| usePaymentPlans | payment_plans, payment_plan_installments | src/hooks/usePaymentPlans.tsx |
| useBulkPayments | bulk_payment_batches, bills | src/hooks/useBulkPayments.tsx |
| useOnlinePayments | online_payments, customer_payment_tokens, invoice_payments, invoices | src/hooks/useOnlinePayments.tsx |
| useAdvancedPayments | pos_transactions, pos_transaction_items, pos_payments, inventory, inventory_movements | src/hooks/useAdvancedPayments.tsx |
| useBankAccounts | bank_accounts | src/hooks/useBankAccounts.tsx |
| useBankReconciliation | bank_transactions, bank_statements | src/hooks/useBankReconciliation.tsx |
| useAccountingAutomation | accounting_settings, journal_entries, bill_payments | src/hooks/useAccountingAutomation.tsx |
| usePOSAccounting | pos_transactions, journal_entries, chart_of_accounts | src/hooks/usePOSAccounting.tsx |
| useCustomerPaymentsPaginated | invoices | src/hooks/useCustomerPaymentsPaginated.tsx |
| useUnbilledTime | time_entries, invoices, invoice_items | src/hooks/useUnbilledTime.tsx |
