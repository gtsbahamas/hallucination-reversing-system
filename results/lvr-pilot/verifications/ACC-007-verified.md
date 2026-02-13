## ACC-007 Verification: Payment Detail

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches single payment by id + business_id with joins | data-access | VERIFIED | PaymentDetailPage.tsx:61-69 — `.from('payments').select('*, customers(id, name, email), invoices(id, invoice_number, total_amount)').eq('id', id).eq('business_id', currentBusiness.id).single()` |
| 2 | Tabbed layout: Details, Allocation, Activity | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:222-226 — TabsList with three TabsTrigger elements. |
| 3 | Details tab shows payment info | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:228-279 — Grid with amount, status, payment_date, payment_method, reference_number, customer. Notes conditional at lines 271-278. |
| 4 | Allocation tab shows invoice link or placeholder | scaffolding-free | PARTIAL | PaymentDetailPage.tsx:283-307 — If `payment.invoices` exists, shows invoice_number, total_amount, payment amount. Else shows placeholder "Payment allocation details will be displayed here". Only supports single invoice allocation (not split payments). |
| 5 | Activity tab shows timestamps | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:310-329 — Shows created_at and updated_at. Comment at line 325. |
| 6 | Status badges for 5 statuses | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:92-102 — `getStatusBadge` handles pending, completed, failed, cancelled, refunded. |
| 7 | Payment method badges for 5 methods | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:104-114 — `getMethodBadge` handles cash, check, credit_card, bank_transfer, online. |
| 8 | Related Records: View Customer and View Invoice links | crud-complete | VERIFIED | PaymentDetailPage.tsx:340-363 — Conditional buttons for customer (`/crm/customers/${id}`) and invoice (`/accounting/invoices/${id}`). |
| 9 | Edit navigates to /accounting/payments/:id/edit | route-exists | PARTIAL | PaymentDetailPage.tsx:207-213 — `navigate(/accounting/payments/${id}/edit)`. Route existence not verified. Likely does not exist. |
| 10 | Process Refund shows "coming in v2.0" toast | scaffolding-free | FALSIFIED (scaffolding) | PaymentDetailPage.tsx:116-121 — `handleProcessRefund()` only shows toast "Refund processing coming in v2.0". No actual refund logic. |
| 11 | Print Receipt shows "coming in v2.0" toast | scaffolding-free | FALSIFIED (scaffolding) | PaymentDetailPage.tsx:123-128 — `handlePrintReceipt()` only shows toast "Receipt printing coming in v2.0". No actual print logic. |
| 12 | Back button goes to /accounting/accounts-payable | route-exists | VERIFIED | PaymentDetailPage.tsx:148-149 and 181-185 — `navigate('/accounting/accounts-payable')`. Note: this is an inconsistency — the page is a payment detail but navigates back to accounts payable, not a payments list. |
| 13 | Error state "Go to Payments List" goes to /accounting/payments | route-exists | VERIFIED | PaymentDetailPage.tsx:162 — `navigate('/accounting/payments')`. Different from the back button which goes to /accounting/accounts-payable. Inconsistent navigation. |
| 14 | No delete functionality | scaffolding-free | VERIFIED | No delete button, handler, or confirm dialog exists in the component. |
| 15 | Summary sidebar | scaffolding-free | VERIFIED | PaymentDetailPage.tsx:396-429 — Shows amount, method badge, status badge, date, reference number. |

### FALSIFIED Claims (Scaffolding)
1. **Process Refund (Claim 10):** Button exists but handler only shows a toast with "coming in v2.0". No refund logic implemented.
2. **Print Receipt (Claim 11):** Button exists but handler only shows a toast with "coming in v2.0". No receipt printing logic implemented.

### PARTIAL Claims
- **Allocation tab (Claim 4):** Only supports displaying a single linked invoice. No support for split payments or multiple invoice allocations. Placeholder text shown when no invoice is linked.
- **Edit route (Claim 9):** Navigation call exists but target route may not be registered.

### Additional Bugs Found
- **Inconsistent back navigation:** The "Back" button goes to `/accounting/accounts-payable` (line 148, 181) but the error state "Go to Payments List" goes to `/accounting/payments` (line 162). These are different routes — user may end up in different places depending on how they navigate back.
- **Customer field name:** Query uses `customers(id, name, email)` with `name` field. If the customers table uses `first_name`/`last_name` instead of `name`, this will fail silently and show "Not specified".

### Summary
- Total claims: 15
- VERIFIED: 10
- PARTIAL: 2
- FALSIFIED: 2 (scaffolding)
- UNVERIFIABLE: 0
- Additional bugs: 2 (inconsistent navigation, potential field mismatch)
