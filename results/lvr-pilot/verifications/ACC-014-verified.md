## ACC-014 Verification: Chart of Accounts

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Page is a thin wrapper around ChartOfAccountsTab | route-exists | VERIFIED | ChartOfAccountsPage.tsx:6-25 — renders DashboardLayout > container > heading > ChartOfAccountsTab |
| 2 | Route /accounting/chart-of-accounts exists | route-exists | VERIFIED | App.tsx:389 — `<Route path="/accounting/chart-of-accounts" element={<GuardedRoute ... element={<ChartOfAccountsPage />} />} />` |
| 3 | Uses useAccounting hook | data-access | VERIFIED | ChartOfAccountsTab.tsx:29 — `const { accounts, loading, createAccount, getAccountsByType } = useAccounting();` |
| 4 | useAccounting queries chart_of_accounts with business_id + is_active=true | data-access | VERIFIED | useAccounting.tsx:42-47 — `.from('chart_of_accounts').select('*').eq('business_id', businessId).eq('is_active', true).order('account_code')` |
| 5 | useAccounting also loads journal_entries, invoices, expenses (unnecessary for this tab) | data-access | VERIFIED | useAccounting.tsx:52-79 — Loads journal_entries (limit 100), invoices (limit 50), expenses (limit 50) alongside accounts |
| 6 | Accounts grouped by 5 types: asset, liability, equity, revenue, expense | data-access | VERIFIED | ChartOfAccountsTab.tsx:84-90 — `groupedAccounts` object with 5 keys, each calling getAccountsByType() |
| 7 | Each group renders as Card with colored Badge and count | scaffolding-free | VERIFIED | ChartOfAccountsTab.tsx:273-280 — Card with CardTitle containing Badge with getAccountTypeColor(type) + `({accountList.length} accounts)` |
| 8 | Sortable/draggable columns: Code, Account Name, Balance, Actions | data-access | VERIFIED | ChartOfAccountsTab.tsx:21-26 — COLUMNS array with 4 columns. DraggableTableHead used for non-locked columns. |
| 9 | Column preferences via useColumnPreferences('chart-of-accounts') | data-access | VERIFIED | ChartOfAccountsTab.tsx:43-46 — `const { visibleColumns, columnOrder, reorderColumns, toggleColumn } = useColumnPreferences('chart-of-accounts', COLUMNS)` |
| 10 | Edit button has no onClick handler | scaffolding-free | FALSIFIED | ChartOfAccountsTab.tsx:175-176 — `<Button variant="ghost" size="sm"><Edit className="h-4 w-4" /></Button>` — no onClick prop. Button renders but does nothing when clicked. |
| 11 | Delete button has no onClick handler | scaffolding-free | FALSIFIED | ChartOfAccountsTab.tsx:177-179 — `<Button variant="ghost" size="sm" disabled={account.is_system_account}><Trash2 className="h-4 w-4" /></Button>` — no onClick prop. For non-system accounts, button is enabled but does nothing. |
| 12 | "Add Account" button opens Dialog with form | crud-complete | VERIFIED | ChartOfAccountsTab.tsx:206-265 — Dialog with DialogTrigger (Plus button), form with account_code, account_name, account_type Select, description inputs, and "Create Account" button |
| 13 | createAccount inserts to chart_of_accounts | crud-complete | VERIFIED | useAccounting.tsx:102-137 — `.from('chart_of_accounts').insert({ ...accountData, business_id }).select().single()` then appends to local state |
| 14 | "Create Default Accounts" button calls createDefaultAccounts | crud-complete | VERIFIED | ChartOfAccountsTab.tsx:202-204 — `<Button variant="outline" onClick={createDefaultAccounts}>` from usePOSAccounting hook |
| 15 | Account type color coding (5 colors) | scaffolding-free | VERIFIED | ChartOfAccountsTab.tsx:74-81 — colors object: asset=blue, liability=red, equity=green, revenue=violet, expense=orange |
| 16 | ViewAccountModal with prev/next navigation | data-access | VERIFIED | ChartOfAccountsTab.tsx:336-345 — ViewAccountModal with currentIndex, totalCount, onNavigate props. handleNavigateAccount (lines 128-135) updates index and viewingAccount. |
| 17 | System accounts marked with "System" badge | scaffolding-free | VERIFIED | ChartOfAccountsTab.tsx:155-156 — `{account.is_system_account && <Badge variant="outline" className="ml-2">System</Badge>}` |
| 18 | Multi-sort via useSortableData (default: account_code asc) | data-access | VERIFIED | ChartOfAccountsTab.tsx:92-115 — 5 useSortableData instances (one per type), all with defaultSort: [{ key: 'account_code', direction: 'asc' }] |
| 19 | Permission guard: only FULL_ACCESS_ROLES can access | permission-guard | VERIFIED | Same guard as all /accounting routes |

### FALSIFIED Claims (Bugs)
1. **Edit button is non-functional** (Claim 10): ChartOfAccountsTab.tsx:175-176 renders an Edit button with no onClick handler. The button is visible and clickable but does nothing. Users see an edit icon but cannot edit accounts.

2. **Delete button is non-functional for non-system accounts** (Claim 11): ChartOfAccountsTab.tsx:177-179 renders a Delete button with no onClick handler. For system accounts, the button is properly disabled. For non-system accounts, the button appears enabled/clickable but does nothing when clicked.

### Summary
- Total claims: 19
- VERIFIED: 17
- PARTIAL: 0
- FALSIFIED: 2 (Edit and Delete buttons have no handlers)
- UNVERIFIABLE: 0
