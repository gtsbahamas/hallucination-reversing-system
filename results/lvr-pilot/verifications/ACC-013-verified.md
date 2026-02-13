## ACC-013 Verification: Journal Entry Detail

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Route /accounting/journal-entries/:id exists | route-exists | VERIFIED | App.tsx:347 — `<Route path="/accounting/journal-entries/:id" element={<GuardedRoute ... element={<JournalEntryDetailPage />} />} />` |
| 2 | Fetches journal entry by id + business_id | data-access | VERIFIED | JournalEntryDetailPage.tsx:62-67 — `.from('journal_entries').select('*').eq('id', id).eq('business_id', currentBusiness.id).single()` |
| 3 | Fetches journal_entry_lines with chart_of_accounts join | data-access | VERIFIED | JournalEntryDetailPage.tsx:83-96 — `.from('journal_entry_lines').select('id, description, debit_amount, credit_amount, chart_of_accounts(name, code)').eq('journal_entry_id', id)` |
| 4 | Status badges: draft=gray, posted=green, reversed=red, pending=yellow | scaffolding-free | VERIFIED | JournalEntryDetailPage.tsx:121-129 — statusConfig object with className mappings |
| 5 | Balance check with 0.01 tolerance | data-access | VERIFIED | JournalEntryDetailPage.tsx:247 — `Math.abs(journalEntry.total_debits - journalEntry.total_credits) < 0.01` |
| 6 | 3 content tabs: Details, Journal Lines, Activity | tab-navigation | VERIFIED | JournalEntryDetailPage.tsx:383-387 — TabsTrigger values: details, lines, activity |
| 7 | Details tab shows entry info fields | scaffolding-free | VERIFIED | JournalEntryDetailPage.tsx:389-462 — Renders entry_number, status, entry_date, reference, description, total_debits, total_credits, balance status, notes |
| 8 | Journal Lines tab shows table with Account, Description, Debit, Credit + totals | data-access | VERIFIED | JournalEntryDetailPage.tsx:465-514 — Table with 4 columns, maps journalLines, totals row at bottom |
| 9 | Activity tab shows only created_at and updated_at | scaffolding-free | VERIFIED | JournalEntryDetailPage.tsx:519-537 — Only 2 items: Created and Last Updated, with comment "Additional activity items would go here" |
| 10 | Draft entries show Post, Edit, Discard Draft buttons | crud-complete | VERIFIED | JournalEntryDetailPage.tsx:331-374 — Post (conditional: draft + balanced), Edit (conditional: draft), Discard Draft (conditional: draft) |
| 11 | Posted entries show Reverse Entry button | crud-complete | VERIFIED | JournalEntryDetailPage.tsx:342-352 — Conditional render when status==='posted' |
| 12 | "Print Entry" shows "coming in v2.0" toast | scaffolding-free | VERIFIED | JournalEntryDetailPage.tsx:233-237 — `toast({ title: "Print Entry", description: "Journal entry printing coming in v2.0" })` |
| 13 | "Export to PDF" shows "coming in v2.0" toast | scaffolding-free | VERIFIED | JournalEntryDetailPage.tsx:240-244 — `toast({ title: "Export to PDF", description: "PDF export coming in v2.0" })` |
| 14 | handlePost does simple status update, NOT using journalEntryService | crud-complete | FALSIFIED | JournalEntryDetailPage.tsx:223-225 — `handleStatusUpdate('posted')` which at line 188-221 does `.from('journal_entries').update({ status: newStatus })`. Does NOT validate balance, does NOT update GL, does NOT validate period, does NOT create audit trail. The list page uses the proper journalEntryService.postJournalEntry which does all of these. |
| 15 | handleReverse does simple status update, NOT creating reversing entry | crud-complete | FALSIFIED | JournalEntryDetailPage.tsx:227-231 — `handleStatusUpdate('reversed')`. Just changes status string. Does NOT create a reversing journal entry, does NOT reverse account balances. Compare with journalEntryService.voidJournalEntry which properly creates VOID-{number} reversing entries. |
| 16 | handleDeleteDraft updates status to 'voided' with guards | crud-complete | VERIFIED | JournalEntryDetailPage.tsx:139-186 — Checks status==='draft', confirms with user, updates status to 'voided' with eq('status', 'draft') guard |
| 17 | Uses useBusiness for business_id context | data-access | VERIFIED | JournalEntryDetailPage.tsx:42 — `const { currentBusiness } = useBusiness();` |
| 18 | Permission guard: only FULL_ACCESS_ROLES can access | permission-guard | VERIFIED | Same guard as all /accounting routes |

### FALSIFIED Claims (Bugs)
1. **handlePost bypasses journal entry service** (Claim 14): JournalEntryDetailPage.tsx:223 calls `handleStatusUpdate('posted')` which is a simple Supabase `.update({ status: newStatus })`. This is WRONG because it bypasses ALL the validation and side effects in `journalEntryService.postJournalEntry()`:
   - Does NOT validate debits = credits
   - Does NOT validate period is not closed (no RPC call)
   - Does NOT update account balances in general_ledger
   - Does NOT create audit trail entry
   - Allows posting an unbalanced entry (the UI hides the button but the function itself has no guard)

   The list page (JournalEntriesTab) correctly uses `postJournalEntry(entryId)` from journalEntryService. This detail page should use the same service.

2. **handleReverse does not create reversing entry** (Claim 15): JournalEntryDetailPage.tsx:227 calls `handleStatusUpdate('reversed')` which just changes the status field. In proper accounting (GAAP), reversal requires creating a new reversing journal entry with swapped debits/credits. The `voidJournalEntry()` in journalEntryService.ts does this correctly. The detail page's reversal is accounting-incorrect.

### Summary
- Total claims: 18
- VERIFIED: 14
- PARTIAL: 0
- FALSIFIED: 2 (Post bypasses service, Reverse doesn't create reversing entry)
- UNVERIFIABLE: 0
