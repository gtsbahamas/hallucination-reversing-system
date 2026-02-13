## ACC-005 Verification: Expenses List

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches expenses via useExpensesPaginated with server-side pagination | data-access | VERIFIED | useExpensesPaginated.tsx:46-49 — `.from('expenses').select('*', { count: 'exact' }).eq('business_id', currentBusiness.id)`. Pagination via `.range()` (pattern from usePagination). Default page size 20 at line 31-33. |
| 2 | Summary stats: Total, Approved, Pending, This Month | data-access | PARTIAL | ExpensesTab.tsx:92-101 — Stats computed from `expenses` array. However, this is the paginated subset (current page only), not all expenses. Stats will be inaccurate when expenses exceed one page. Same bug as ACC-001 claim 4. |
| 3 | Status filter applied server-side | filter-works | VERIFIED | ExpensesTab.tsx:33-35 — `filters: { status: statusFilter === 'all' ? undefined : statusFilter }`. useExpensesPaginated.tsx:56-58 — `query.eq('status', filters.status)`. |
| 4 | Sortable columns with default expense_date desc | filter-works | VERIFIED | ExpensesTab.tsx:63-66 — `useSortableData({ data: filteredExpenses, defaultSort: [{ key: 'expense_date', direction: 'desc' }] })`. |
| 5 | Draggable column headers | crud-complete | VERIFIED | ExpensesTab.tsx:244-255 — `DraggableTableHead` with `onReorder={handleReorder}`, `useColumnPreferences('expenses', EXPENSE_COLUMNS)` at lines 42-48. |
| 6 | Column visibility settings | crud-complete | VERIFIED | ExpensesTab.tsx:367-375 — `ColumnSettingsModal` with save/reset. Button at lines 192-198. |
| 7 | Table columns match spec | scaffolding-free | VERIFIED | ExpensesTab.tsx:19-28 — EXPENSE_COLUMNS defines: expense_number, expense_date, description, category, total_amount, status, employee, actions. |
| 8 | Clicking row opens ExpenseDetailsModal | crud-complete | VERIFIED | ExpensesTab.tsx:329-334 — `onClick={() => handleViewExpense(expense, index)}`. ExpenseDetailsModal rendered at lines 356-364. |
| 9 | View button (eye icon) opens details modal | crud-complete | VERIFIED | ExpensesTab.tsx:301-306 — `<Eye>` icon button with `onClick={() => handleViewExpense(expense, index)}`. |
| 10 | Edit button only for draft, opens CreateExpenseModal | crud-complete | VERIFIED | ExpensesTab.tsx:308-318 — `{expense.status === 'draft' && (<Button onClick={() => { setSelectedExpense(expense); setCreateModalOpen(true); }}>)}`. |
| 11 | New Expense button opens CreateExpenseModal | crud-complete | VERIFIED | ExpensesTab.tsx:187-189 — `onClick={() => setCreateModalOpen(true)}`. Modal at lines 347-354. |
| 12 | Pagination with [10, 20, 50, 100] options | pagination-works | VERIFIED | ExpensesTab.tsx:378-397 — PaginationControls with `pageSizeOptions={[10, 20, 50, 100]}`. |
| 13 | ExpensesPage is thin wrapper | scaffolding-free | VERIFIED | ExpensesPage.tsx:1-25 — Renders DashboardLayout + heading + `<ExpensesTab />`. |
| 14 | Employee column from expense data (no join in hook) | data-access | PARTIAL | ExpensesTab.tsx:288-295 — References `expense.employees.first_name` / `last_name`. But useExpensesPaginated.tsx:48 uses `select('*')` — no join on employees. Unless the Supabase type includes a virtual join via FK or the `*` selector auto-includes FK relations (it doesn't), this will show "Unknown" for all rows. |
| 15 | Navigation between expenses in detail modal | crud-complete | VERIFIED | ExpensesTab.tsx:78-84 — `handleNavigateExpense` updates `currentExpenseIndex` and `selectedExpense`. Passed to modal at lines 362-363. |

### PARTIAL Claims
- **Claim 2 (Stats):** Stats are computed from paginated `expenses` array (current page only). When total expenses exceed one page, the displayed totals will be wrong — they'll reflect only the current page's data.
- **Claim 14 (Employee data):** The hook query `select('*')` does not join the employees table. The component expects `expense.employees.first_name` which will be undefined unless Supabase auto-resolves FK relations (it does not with `select('*')`). All employee columns will show "Unknown".

### FALSIFIED Claims
None.

### Additional Observations
- **No delete functionality:** Unlike invoices and bills, the expenses list has no delete button or handler. Expenses can only be edited (draft only) or viewed.
- **Server-side vs client-side inconsistency:** Search is applied server-side (via ilike in hook), but the component passes search as a filter option differently than status — ExpensesTab uses `statusFilter` for status but doesn't expose a search input to the user in this component. The hook supports search but it's not wired up in the UI.

### Summary
- Total claims: 15
- VERIFIED: 12
- PARTIAL: 2
- FALSIFIED: 0
- UNVERIFIABLE: 0
