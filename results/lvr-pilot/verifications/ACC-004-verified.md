## ACC-004 Verification: Bill Detail

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches single bill by id + business_id | data-access | VERIFIED | BillDetailPage.tsx:57-71 — `.from('bills').select('*, suppliers(id, name, email, phone, contact_person)').eq('id', id).eq('business_id', currentBusiness.id).single()` |
| 2 | Displays bill header with bill_number, supplier name, status badge | scaffolding-free | VERIFIED | BillDetailPage.tsx:282-287 — `<h1>Bill {bill.bill_number}</h1>`, supplier name, status badge via `getStatusBadge()`. |
| 3 | Shows bill details: bill_number, status, dates, amount, notes | scaffolding-free | VERIFIED | BillDetailPage.tsx:346-386 — Grid layout with all fields rendered. Notes in conditional block at lines 379-386. |
| 4 | Supplier info sidebar | scaffolding-free | VERIFIED | BillDetailPage.tsx:392-426 — Conditional render of supplier name, email, phone, contact_person. Falls back to "No supplier information available". |
| 5 | Activity shows created_at and updated_at | scaffolding-free | VERIFIED | BillDetailPage.tsx:436-444 — Two entries showing timestamps formatted with date-fns. |
| 6 | Approve button for pending_approval status | crud-complete | VERIFIED | BillDetailPage.tsx:294-304 — Button visible when `bill.status === 'pending_approval'`. `handleApprove()` at lines 154-187 calls `.update({ status: 'approved' }).eq('id', bill.id).eq('business_id', currentBusiness.id)`. |
| 7 | Reject button sets status to 'cancelled' | crud-complete | VERIFIED | BillDetailPage.tsx:305-313 — Button visible for pending_approval. `handleReject()` at lines 189-222 calls `.update({ status: 'cancelled' })`. Note: sets status to 'cancelled', not 'rejected' — this may be intentional (no 'rejected' status in the Bill type). |
| 8 | Edit button opens EditBillModal | crud-complete | VERIFIED | BillDetailPage.tsx:316-323 — `onClick={handleEdit}` which calls `setShowEditModal(true)`. Modal rendered at lines 451-458 with `onSuccess={handleEditSuccess}` which refetches. |
| 9 | Delete uses hard delete (not soft delete) | crud-complete | FALSIFIED (bug) | BillDetailPage.tsx:114-152 — Uses `.from('bills').delete().eq('id', bill.id).eq('business_id', currentBusiness.id)`. This is a HARD DELETE, unlike BillsDashboard which soft-deletes via `deleted_at`. Inconsistent behavior: deleting from detail page permanently destroys the record, while deleting from list page archives it. |
| 10 | Error/not-found state | scaffolding-free | VERIFIED | BillDetailPage.tsx:234-264 — Shows error message, "Back to Bills" button, and "Go to Bills List" button. |
| 11 | No line items display | scaffolding-free | VERIFIED | The select query at line 59-68 does NOT join `bill_line_items`. No line items section exists in the page. The list page (via AccountsPayableService) does join `bill_line_items(*)` but the detail page does not. |
| 12 | No payment history display | scaffolding-free | VERIFIED | No payment-related query or UI exists in the component. |

### FALSIFIED Claims (Bugs)
1. **Hard delete vs soft delete inconsistency (Claim 9):** BillDetailPage uses `.delete()` (permanent) while BillsDashboard uses `.update({ deleted_at })` (soft delete). This means:
   - Deleting from list view: record is archived, can be restored, query with `is('deleted_at', null)` hides it
   - Deleting from detail view: record is permanently destroyed, cannot be restored
   - Additionally, the detail page does not check for `bill_payments` before deleting, unlike the list page which prevents deletion of bills with payments. This could lead to orphaned payment records.

### PARTIAL Claims
None.

### Additional Observations
- **No permission check on delete:** Unlike BillsDashboard which checks `canDeleteBills` (financial.ap delete permission), the detail page delete handler has no permission check. Any user who can access the page can delete the bill.
- **No permission check on approve/reject:** The approve/reject buttons are shown to anyone viewing a pending_approval bill. No role-based gating exists on these actions in the detail page, unlike the list page which checks `canManageApprovals`.
- **Simple confirm() dialog:** Uses `window.confirm()` instead of ConfirmDeleteDialog component used by InvoiceDetailPage. Inconsistent UX.

### Summary
- Total claims: 12
- VERIFIED: 10
- PARTIAL: 0
- FALSIFIED: 1 (hard delete inconsistency)
- UNVERIFIABLE: 0
- Additional bugs: 3 (missing permission checks on delete/approve/reject, no payment check before delete)
