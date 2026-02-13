## ACC-003 Verification: Bills List

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches bills via useAccountsPayable / AccountsPayableService | data-access | VERIFIED | useAccountsPayable.tsx:22-33 uses React Query calling `AccountsPayableService.getBills(currentBusiness.id)`. accountsPayableService.ts:167-175 — `.from('bills').select('*, suppliers(name, email), bill_line_items(*)').eq('business_id', business_id).is('deleted_at', null)`. |
| 2 | Summary cards: Total Bills, Pending Approval, Overdue, Total Amount | data-access | VERIFIED | BillsDashboard.tsx:168-172 — `totalBills`, `pendingBills`, `overdueBills`, `totalAmount` computed from `bills` array. |
| 3 | Client-side search by bill_number and supplier name | filter-works | VERIFIED | BillsDashboard.tsx:96-101 — `bill.bill_number?.toLowerCase().includes(searchTerm)` and `bill.suppliers?.name?.toLowerCase().includes(searchTerm)`. |
| 4 | Status filter dropdown with 7 options | filter-works | VERIFIED | BillsDashboard.tsx:461-473 — `<select>` with options: all, draft, pending_approval, approved, paid, overdue, cancelled. Filtering at line 99: `statusFilter === 'all' || bill.status === statusFilter`. |
| 5 | Sortable table columns via useSortableData | filter-works | VERIFIED | BillsDashboard.tsx:104-107 — `useSortableData({ data: filteredBills, defaultSort: [{ key: 'due_date', direction: 'desc' }] })`. |
| 6 | Draggable column headers for reorder | crud-complete | VERIFIED | BillsDashboard.tsx:520-531 — `DraggableTableHead` with `onReorder={handleReorder}`. useColumnPreferences hook manages order + persistence. |
| 7 | Column visibility settings via ColumnSettingsModal | crud-complete | VERIFIED | BillsDashboard.tsx:686-694 — `ColumnSettingsModal` with save/reset. |
| 8 | Bulk selection with select-all checkbox | crud-complete | VERIFIED | BillsDashboard.tsx:114-136 — `selectedBillIds` Set, `handleToggleBill`, `handleToggleAll`. Select-all checkbox at lines 489-494. |
| 9 | Bulk payment validates same vendor, not draft/pending, not fully paid | crud-complete | VERIFIED | BillsDashboard.tsx:139-163 — `validationMessage` checks for draft/pending_approval bills, different vendor_ids, and fully paid bills. `canApplyBulkPayment` at line 165. BulkBillPaymentModal rendered at lines 731-739. |
| 10 | Bulk email shows "Coming Soon" toast | scaffolding-free | FALSIFIED (scaffolding) | BillsDashboard.tsx:711-718 — `onClick` shows toast with title "Coming Soon", description "Bulk email sending will be available soon". Feature is a stub. |
| 11 | Bulk delete soft-deletes (deleted_at + deleted_by) | crud-complete | VERIFIED | BillsDashboard.tsx:327-353 — `.from('bills').update({ deleted_at: new Date().toISOString(), deleted_by: user?.id }).in('id', Array.from(selectedBillIds))`. |
| 12 | Single delete checks for payments and requires manager approval for approved/paid | crud-complete | VERIFIED | BillsDashboard.tsx:196-282 — First checks `bill_payments` table (lines 207-229). Then checks bill status + `canManageApprovals` permission (lines 232-246). Finally soft-deletes with `deleted_at`/`deleted_by` (lines 256-261). |
| 13 | View button opens BillDetailsModal | crud-complete | VERIFIED | BillsDashboard.tsx:186-189 — `handleViewBill` sets `selectedBill` + `showViewModal=true`. BillDetailsModal rendered at lines 663-673. |
| 14 | Edit button opens EditBillModal | crud-complete | VERIFIED | BillsDashboard.tsx:191-194 — `handleEditBill` sets `selectedBill` + `showEditModal=true`. EditBillModal rendered at lines 674-683. |
| 15 | Delete button permission-gated | permission-guard | VERIFIED | BillsDashboard.tsx:59 — `usePermission('financial.ap', 'delete')`. Line 611: `{canDeleteBills && (<Button ... onClick={() => handleDeleteBill(bill)}>)}`. |
| 16 | Create Bill opens EnhancedCreateBillModal | crud-complete | VERIFIED | BillsDashboard.tsx:433-437 — Button opens modal. Lines 649-658 — `EnhancedCreateBillModal` with `onOpenChange` that calls `refetch()` on close. |
| 17 | BillsPage is thin wrapper | scaffolding-free | VERIFIED | BillsPage.tsx:1-20 — Only renders DashboardLayout + heading + `<BillsDashboard />`. |

### FALSIFIED Claims (Scaffolding)
1. **Bulk email (Claim 10):** The "Send Emails" button exists but its onClick handler only shows a toast saying "Coming Soon". No email sending logic exists.

### PARTIAL Claims
None.

### Additional Observations
- **Inconsistent delete behavior:** Single delete in BillsDashboard uses soft delete (sets `deleted_at`). But BillDetailPage.tsx (ACC-004) uses hard delete (`.delete()`). This inconsistency means deleting from the list view preserves the record while deleting from the detail view permanently removes it.
- **Component-level permission checks** (canDeleteBills, canManageApprovals) add a second layer of authorization beyond the route guard, which is good practice but creates UX confusion — users who can see the page might still see disabled/hidden actions.

### Summary
- Total claims: 17
- VERIFIED: 16
- PARTIAL: 0
- FALSIFIED: 1 (scaffolding)
- UNVERIFIABLE: 0
