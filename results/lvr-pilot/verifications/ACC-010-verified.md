## ACC-010 Verification: Accounts Receivable

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page is a thin wrapper around ARManagementTab | route-exists | VERIFIED | AccountsReceivablePage.tsx:6-22 — renders DashboardLayout > div > ARManagementTab, no other logic |
| 2 | Route /accounting/accounts-receivable exists | route-exists | VERIFIED | App.tsx:335 — `<Route path="/accounting/accounts-receivable" element={<GuardedRoute ... element={<AccountsReceivablePage />} />} />` |
| 3 | ARManagementTab uses useAccountsReceivable and useARAnalytics hooks | data-access | VERIFIED | ARManagementTab.tsx:20-21 — imports both hooks, line 46-47 calls both |
| 4 | arTransactions is destructured but does not exist in hook return | data-access | FALSIFIED | ARManagementTab.tsx:46 destructures `{ arTransactions, loading }` from useAccountsReceivable. Hook (useAccountsReceivable.tsx:188-222) returns `{ invoices, ... }` — no `arTransactions` property. `arTransactions` is undefined at runtime. |
| 5 | Summary metrics Total AR and Overdue Amount always show $0 | data-access | VERIFIED | ARManagementTab.tsx:50-51 — `arTransactions?.reduce(...)` — when arTransactions is undefined, the optional chaining returns undefined, the `|| 0` fallback makes totalAR = 0, overdueAR = 0 |
| 6 | Collection Rate comes from ar_snapshots via useARAnalytics | data-access | VERIFIED | ARManagementTab.tsx:55 — `latestSnapshot?.collection_effectiveness` — useARAnalytics.tsx:314-321 queries ar_snapshots table ordered by snapshot_date desc |
| 7 | Avg Days to Pay comes from ar_snapshots | data-access | VERIFIED | ARManagementTab.tsx:128 — `latestSnapshot?.average_days_to_pay` |
| 8 | 12 sub-tabs across 2 rows | tab-navigation | VERIFIED | ARManagementTab.tsx:141-194 — First row: customer-dashboard, payment-dashboard, credit-applications, follow-up, analytics, statements. Second row: credit, collections, payment-plans, online-payments, invoices, subscriptions. Total = 12 tabs. |
| 9 | All sub-tab components are lazy-loaded | scaffolding-free | VERIFIED | ARManagementTab.tsx:24-35 — 12 React.lazy() imports with Suspense wrappers (lines 197-267) |
| 10 | useAccountsReceivable queries invoices table via AccountsReceivableService | data-access | VERIFIED | useAccountsReceivable.tsx:27-31 — queryFn calls `AccountsReceivableService.getInvoices(currentBusiness.id)` |
| 11 | useARAnalytics queries ar_snapshots, invoices, customers tables | data-access | VERIFIED | useARAnalytics.tsx:314-319 (ar_snapshots), 71-77 (invoices for aging), 194-211 (customers with invoices join) |
| 12 | useAccountsReceivable provides CRUD mutations (create, send, void, postToGL) | crud-complete | VERIFIED | useAccountsReceivable.tsx:63-155 — createInvoice, sendInvoice, voidInvoice, postToGL mutations defined |
| 13 | Permission guard: only FULL_ACCESS_ROLES can access | permission-guard | VERIFIED | Route guard uses ROUTE_PERMISSION_MAP['accounting'] = 'accounting.invoices.read'. permissionMappings.ts has no mapping for this permission, so only super_admin, owner, operations_manager pass. |

### FALSIFIED Claims (Bugs)
1. **arTransactions property mismatch** (Claim 4): ARManagementTab.tsx:46 destructures `{ arTransactions, loading }` from `useAccountsReceivable()`. However, the hook's return object (useAccountsReceivable.tsx:188-222) exports `invoices`, not `arTransactions`. This means `arTransactions` is always `undefined`, causing the summary metrics (Total AR, Overdue Amount) to display $0 regardless of actual data. The fix would be to either rename the destructured variable to `invoices` or add `arTransactions` as an alias in the hook's return.

### Summary
- Total claims: 13
- VERIFIED: 11
- PARTIAL: 0
- FALSIFIED: 1 (arTransactions property mismatch — summary metrics broken)
- UNVERIFIABLE: 0
