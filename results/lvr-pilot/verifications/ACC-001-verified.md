## ACC-001 Verification: Invoices List

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Lists all invoices for the current business with server-side pagination (default 20 per page) | data-access | VERIFIED | useInvoicesPaginated.tsx:82-101 — `.from('invoices').select(...).eq('business_id', currentBusiness.id)` with `.range()` at line 131. Default page size 20 at line 60. |
| 2 | Supports client-side search filtering by invoice_number, customer name, and customer email | filter-works | VERIFIED | InvoicesPage.tsx:58-62 — `filteredInvoices` filters on `invoice.invoice_number`, `customers.first_name`, `customers.last_name`, `customers.email` |
| 3 | Supports server-side search filtering by invoice_number and notes (via ilike) | filter-works | VERIFIED | useInvoicesPaginated.tsx:121-127 — `query.or('invoice_number.ilike.%${searchTerm}%,notes.ilike.%${searchTerm}%')` |
| 4 | Displays summary stats: total, draft, sent, paid, overdue counts and values | data-access | PARTIAL | InvoicesPage.tsx:64-72 — stats computed from `invoices` array (current page only). Separate metadata query at useInvoicesPaginated.tsx:176-221 loads ALL invoices for totals, but the page component doesn't use `metadata` — it computes stats from the paginated `invoices` array. |
| 5 | Provides two view modes: list view and kanban view | scaffolding-free | VERIFIED | InvoicesPage.tsx:23 — `viewMode` state, line 74 `renderKanbanView()`, line 130 `renderListView()`, toggle buttons at lines 257-273. |
| 6 | Clicking an invoice opens InvoiceViewModal (not navigation to detail page) | crud-complete | VERIFIED | InvoicesPage.tsx:47-50 — `handleInvoiceClick` sets `selectedInvoice` and `showViewModal=true`. InvoiceViewModal rendered at lines 308-314. |
| 7 | "New Invoice" button opens CreateInvoiceModal | crud-complete | VERIFIED | InvoicesPage.tsx:199 — `onClick={() => setShowCreateModal(true)}`. CreateInvoiceModal at lines 302-306 with `onSuccess={refetch}`. |
| 8 | Edit flow: from InvoiceViewModal, user can click edit to open EditInvoiceModal | crud-complete | VERIFIED | InvoicesPage.tsx:52-56 — `handleEditInvoice` closes view modal and opens edit modal. EditInvoiceModal rendered at lines 316-320. |
| 9 | Automatically marks sent invoices as overdue if due_date < today and balance_due > 0 | data-access | VERIFIED | useInvoicesPaginated.tsx:139-145 — client-side status rewrite: `invoice.status === 'sent' && invoice.due_date < today && invoice.balance_due > 0 ? 'overdue'`. Note: this only affects display, not the database status. |
| 10 | Pagination controls with page size options [10, 20, 50, 100] | pagination-works | VERIFIED | InvoicesPage.tsx:323-342 — PaginationControls with `pageSizeOptions={[10, 20, 50, 100]}`, wired to `pagination.goToPage` and `pagination.setPageSize`. Server-side `.range()` at useInvoicesPaginated.tsx:131. |
| 11 | Hook exposes createInvoice, updateInvoice, deleteInvoice functions with real Supabase calls | crud-complete | VERIFIED | useInvoicesPaginated.tsx:313-448 — All three functions make real Supabase `.insert()`, `.update()`, `.delete()` calls with `.eq('business_id', currentBusiness.id)` filtering. |
| 12 | createInvoice generates invoice number client-side | crud-complete | VERIFIED | useInvoicesPaginated.tsx:64-70 — `generateInvoiceNumber()` returns `INV-${year}${month}-${timestamp}`. Note: timestamp-based, not sequential — potential for collisions under concurrent use. |

### PARTIAL Claims
- **Claim 4 (Summary stats):** The page computes stats from `invoices` (the paginated array, not all invoices). This means stats only reflect the current page's data, not all invoices in the business. The hook exposes `metadata` with business-wide totals (useInvoicesPaginated.tsx:176-221), but the page component doesn't use it — it recomputes from the paginated subset. Stats will be inaccurate when there are more invoices than fit on one page.

### FALSIFIED Claims
None.

### Summary
- Total claims: 12
- VERIFIED: 11
- PARTIAL: 1
- FALSIFIED: 0
- UNVERIFIABLE: 0
