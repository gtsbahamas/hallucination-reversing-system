## ACC-002 Verification: Invoice Detail

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches single invoice by id + business_id | data-access | VERIFIED | InvoiceDetailPage.tsx:62-76 — `.from('invoices').select(...).eq('id', id).eq('business_id', currentBusiness.id).single()` |
| 2 | Tabbed layout: Details, Line Items, Payments, Activity | scaffolding-free | VERIFIED | InvoiceDetailPage.tsx:481-486 — TabsList with four TabsTrigger elements |
| 3 | Line Items tab is placeholder | scaffolding-free | FALSIFIED (scaffolding) | InvoiceDetailPage.tsx:559-561 — "Line items will be displayed here when invoice line items are implemented". The query does NOT join invoice_line_items (unlike the list page hook which does). This is an incomplete feature. |
| 4 | Payments tab is placeholder | scaffolding-free | FALSIFIED (scaffolding) | InvoiceDetailPage.tsx:572-574 — "Payment history will be displayed here when payments are linked to invoices". No payment data is fetched. |
| 5 | Activity tab shows only created_at and updated_at | scaffolding-free | VERIFIED | InvoiceDetailPage.tsx:585-596 — Only two entries shown. Comment "Additional activity items would go here" at line 594. |
| 6 | Customer sidebar with "View Customer" link | crud-complete | VERIFIED | InvoiceDetailPage.tsx:605-633 — Renders customer name, email, phone, company. Button navigates to `/crm/customers/${invoice.customers?.id}`. |
| 7 | Send Invoice: generates PDF, uploads to Storage, sends email, marks as 'sent' | crud-complete | VERIFIED | InvoiceDetailPage.tsx:243-315 — `handleSendInvoice()` calls `generateInvoicePDF()` (jsPDF), uploads via `supabase.storage.from('invoices').upload()`, invokes `supabase.functions.invoke('send-email')`, then calls `handleStatusUpdate('sent')`. Full implementation, no stubs. |
| 8 | Mark Paid button updates status | crud-complete | VERIFIED | InvoiceDetailPage.tsx:434-444 — Button visible for 'sent' or 'overdue' status, calls `handleStatusUpdate('paid')` which does `.update({ status: newStatus })` at line 161-164. |
| 9 | Download PDF generates and saves client-side | crud-complete | VERIFIED | InvoiceDetailPage.tsx:317-344 — `handleDownloadPDF()` calls `generateInvoicePDF()` then `doc.save()`. |
| 10 | Edit button navigates to /accounting/invoices/:id/edit | route-exists | PARTIAL | InvoiceDetailPage.tsx:111-113 — `navigate(/accounting/invoices/${id}/edit)`. Route existence NOT verified — no corresponding edit page was found in the assigned pages. This route likely does not exist, causing a 404 or blank page. |
| 11 | Delete with confirmation dialog and Supabase .delete() | crud-complete | VERIFIED | InvoiceDetailPage.tsx:115-153 — Shows ConfirmDeleteDialog (line 728-734), `confirmDelete()` calls `.from('invoices').delete().eq('id', invoice.id).eq('business_id', currentBusiness.id)`, then navigates to /accounting/invoices. |
| 12 | Duplicate Invoice button has no onClick handler | scaffolding-free | FALSIFIED (scaffolding) | InvoiceDetailPage.tsx:680-683 — `<Button variant="outline" size="sm">` with no onClick. Button renders but does nothing when clicked. |
| 13 | Overdue detection client-side | data-access | VERIFIED | InvoiceDetailPage.tsx:389 — `const isOverdue = invoice.status === 'sent' && new Date(invoice.due_date) < new Date()` |
| 14 | Summary sidebar shows financial details | scaffolding-free | VERIFIED | InvoiceDetailPage.tsx:686-724 — Shows subtotal, tax, total, status, and days overdue calculation. |

### FALSIFIED Claims (Bugs / Scaffolding)
1. **Line Items tab (Claim 3):** The detail page does NOT join `invoice_line_items` in its query (only joins `customers`), so even though the list page hook fetches line items, the detail page cannot display them. The tab is pure placeholder.
2. **Payments tab (Claim 4):** No payment data is fetched or displayed. Pure placeholder.
3. **Duplicate Invoice button (Claim 12):** Button renders with icon and text but has no onClick handler. Silent no-op.

### PARTIAL Claims
- **Edit button (Claim 10):** The navigation call works, but the target route `/accounting/invoices/:id/edit` is not one of the assigned pages. If no separate edit page component exists and is registered in the router, this will fail silently or show a 404.

### Additional Bugs Found
- **Customer field mismatch:** The detail page expects `customers.name` (line 205, 612) but the list page hook fetches `customers.first_name`/`customers.last_name`. The `customers` table likely has `first_name`/`last_name` columns, not a `name` column. This may cause the customer name to display as undefined on the detail page.

### Summary
- Total claims: 14
- VERIFIED: 9
- PARTIAL: 1
- FALSIFIED: 3 (scaffolding)
- UNVERIFIABLE: 0
- Additional bugs: 1 (customer field mismatch)
