## ACC-008 Verification: POS End of Day

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches cash_drawer_sessions by business_id and closeout_status | data-access | VERIFIED | POSEndOfDayPage.tsx:68-82 — `.from('cash_drawer_sessions').select('*').eq('business_id', currentBusiness?.id).in('closeout_status', [...])`. Date filter at lines 76-79 uses `.gte()` / `.lte()` on `closed_at`. Ordered by `closed_at` desc. |
| 2 | Summary cards: Pending Review, Needs Info, Closed Today | data-access | FALSIFIED (bug) | POSEndOfDayPage.tsx:154-156 — `pendingCount`, `needsInfoCount`, `closedCount` are computed from the `closeouts` array. But `closeouts` is filtered by `activeTab` (line 72). When viewing "Pending" tab, `closeouts` only contains pending_review items, so `needsInfoCount` and `closedCount` will be 0. The summary cards don't show global counts — they show counts from the currently filtered dataset. |
| 3 | Tab-based filtering | filter-works | VERIFIED | POSEndOfDayPage.tsx:248-260 — Four TabsTrigger: pending_review, needs_info, closed, all. `activeTab` controls the `.in()` filter in the query. |
| 4 | Client-side search by terminal_id and cashier_name | filter-works | VERIFIED | POSEndOfDayPage.tsx:99-106 — `filteredCloseouts` filters on `closeout.terminal_id.toLowerCase().includes(search)` and `closeout.cashier_name.toLowerCase().includes(search)`. |
| 5 | Date filter server-side | filter-works | VERIFIED | POSEndOfDayPage.tsx:75-79 — If `dateFilter` is set, creates startOfDay/endOfDay and applies `.gte()` / `.lte()` on `closed_at`. |
| 6 | Closeout card shows terminal, status, approval flag, cashier, closed_at, cash, variance | scaffolding-free | VERIFIED | POSEndOfDayPage.tsx:271-327 — Card renders terminal_id (line 277), status badge (line 278), requires_approval badge (lines 279-284), cashier_name (line 291), closed_at (line 300), opening_amount (line 310), difference/variance badge (line 318). |
| 7 | Variance badge: Balanced, Over, Short | scaffolding-free | VERIFIED | POSEndOfDayPage.tsx:134-142 — `getVarianceBadge`: < $0.01 = "Balanced" (green), positive = "Over" (blue), negative = "Short" (red). Uses `formatCurrency()`. |
| 8 | Cashier notes displayed if present | scaffolding-free | VERIFIED | POSEndOfDayPage.tsx:322-327 — Conditional render: `{closeout.cashier_notes && (<div className="bg-blue-50 p-3 rounded-md">...)}`. |
| 9 | View Details opens CloseoutDetailModal | crud-complete | VERIFIED | POSEndOfDayPage.tsx:331-334 — Button `onClick={() => handleViewDetails(closeout)}`. Modal at lines 348-355 with `sessionId`, `closeout`, and `onSuccess` callback that refetches + closes modal. |
| 10 | POSEndOfDayContent exported separately | scaffolding-free | VERIFIED | POSEndOfDayPage.tsx:48 — `export const POSEndOfDayContent = () => {`. No DashboardLayout in this component. |
| 11 | POSEndOfDayPage wraps in DashboardLayout | scaffolding-free | VERIFIED | POSEndOfDayPage.tsx:361-369 — `export const POSEndOfDayPage = () => { return (<DashboardLayout><POSEndOfDayContent /></DashboardLayout>)}`. |
| 12 | useEffect re-fetches on activeTab change | data-access | VERIFIED | POSEndOfDayPage.tsx:59-63 — `useEffect(() => { if (currentBusiness?.id) { loadCloseouts(); } }, [currentBusiness?.id, activeTab])`. |
| 13 | Counts computed from filtered closeouts array | data-access | FALSIFIED (bug) | POSEndOfDayPage.tsx:154-156 — Same as Claim 2. Counts are derived from `closeouts` which is already filtered by tab. This means the summary cards and tab labels show incorrect counts when any tab other than "all" is selected. |

### FALSIFIED Claims (Bugs)
1. **Summary card counts (Claim 2):** The counts `pendingCount`, `needsInfoCount`, `closedCount` are computed from the `closeouts` array at lines 154-156. However, `closeouts` is populated by a query that filters by `activeTab` (line 72: `.in('closeout_status', activeTab === 'all' ? [...] : [activeTab])`). When viewing the "Pending" tab, only pending_review closeouts are fetched, so `needsInfoCount` and `closedCount` will always be 0. The summary cards and tab labels are inaccurate.
2. **"Closed Today" label (Claim 13):** The label says "Closed Today" but `closedCount` counts ALL closed sessions in the filtered dataset, not just today's. Without a date filter, this shows all-time closed count (or 0 if not on the "closed" or "all" tab).

### PARTIAL Claims
None.

### Additional Observations
- **Expected Cash label misleading:** The card shows "Expected Cash" with `opening_amount`, but this is the cash amount at the start of the session, not the expected end-of-shift total. Expected end-of-shift amount would be `opening_amount + cash_sales`.
- **No create/edit/delete on this page:** This is a review-only page. All mutations happen in the CloseoutDetailModal.
- **Well-structured:** The separation of POSEndOfDayContent and POSEndOfDayPage is good practice for reuse in tab contexts.

### Summary
- Total claims: 13
- VERIFIED: 9
- PARTIAL: 0
- FALSIFIED: 2 (bugs: filtered counts, misleading "today" label)
- UNVERIFIABLE: 0
