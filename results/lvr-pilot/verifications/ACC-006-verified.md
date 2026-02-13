## ACC-006 Verification: Expense Detail

### Claims Verified

| # | Claim | Type | Verdict | Evidence |
|---|-------|------|---------|----------|
| 1 | Fetches single expense by id + business_id with employees join | data-access | VERIFIED | ExpenseDetailPage.tsx:62-75 — `.from('expenses').select('*, employees(id, first_name, last_name, email)').eq('id', id).eq('business_id', currentBusiness.id).single()` |
| 2 | Tabbed layout: Details, Receipt, Accounting, Activity | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:341-347 — TabsList with four TabsTrigger elements. |
| 3 | Details tab shows all fields | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:349-431 — Grid layout with description, amount, category, expense_date, vendor, payment_method, status, employee, billable/reimbursable checkboxes (disabled), notes. |
| 4 | Receipt tab shows image or placeholder | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:434-471 — Conditional: if `receipt_url` exists, renders `<img>` with onError fallback + download button. Else shows Receipt icon + "No receipt attached". |
| 5 | Accounting tab has hardcoded values and placeholder | scaffolding-free | FALSIFIED (scaffolding) | ExpenseDetailPage.tsx:479-495 — Account shows `"Expenses : {category || 'General'}"` (hardcoded, not from database). "Tax Deductible: Yes" is hardcoded (line 487). Placeholder text at line 491: "Accounting integration details will be displayed here when chart of accounts is linked". |
| 6 | Activity tab shows timestamps | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:498-517 — Shows created_at and updated_at. Comment at line 514. |
| 7 | Status badges for 6 statuses | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:97-108 — `getStatusBadge` handles draft, submitted, approved, rejected, paid, reimbursed. |
| 8 | Approve/Reject for submitted status | crud-complete | VERIFIED | ExpenseDetailPage.tsx:283-303 — Buttons visible when `expense.status === 'submitted'`. Approve calls `handleStatusUpdate('approved')`, Reject calls `handleStatusUpdate('rejected')`. `handleStatusUpdate` at lines 154-187 does `.update({ status: newStatus })`. |
| 9 | Mark Reimbursed for approved + reimbursable | crud-complete | VERIFIED | ExpenseDetailPage.tsx:305-314 — `{expense.status === 'approved' && expense.reimbursable && (<Button onClick={() => handleStatusUpdate('reimbursed')}>)}`. |
| 10 | Edit navigates to /accounting/expenses/:id/edit | route-exists | PARTIAL | ExpenseDetailPage.tsx:110-112 — `navigate(/accounting/expenses/${id}/edit)`. Route existence not verified — no edit page in assigned pages. Likely does not exist. |
| 11 | Delete with confirm + hard delete | crud-complete | VERIFIED | ExpenseDetailPage.tsx:114-152 — `window.confirm()` then `.from('expenses').delete().eq('id', expense.id).eq('business_id', currentBusiness.id)`. Navigates to /accounting/expenses. |
| 12 | Duplicate Expense button has no handler | scaffolding-free | FALSIFIED (scaffolding) | ExpenseDetailPage.tsx:604-611 — `<Button variant="outline" size="sm">` with FileText icon and "Duplicate Expense" text but NO onClick handler. |
| 13 | Employee sidebar with View Employee link | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:524-548 — Shows `first_name last_name`, email. Button navigates to `/employees/${expense.employees?.id}`. |
| 14 | Summary sidebar | scaffolding-free | VERIFIED | ExpenseDetailPage.tsx:615-654 — Shows amount, category, status badge, date, billable/reimbursable flags. |
| 15 | Download Receipt opens URL in new tab | crud-complete | VERIFIED | ExpenseDetailPage.tsx:189-199 — `window.open(expense.receipt_url, '_blank')`. Falls back to toast if no receipt_url. |

### FALSIFIED Claims (Scaffolding)
1. **Accounting tab (Claim 5):** Account mapping is hardcoded (`"Expenses : {category}"`), not from actual chart of accounts. "Tax Deductible: Yes" is always shown regardless of actual tax status. Placeholder text explicitly states this feature is not implemented.
2. **Duplicate Expense button (Claim 12):** Button exists in UI but has no onClick handler. Clicking it does nothing.

### PARTIAL Claims
- **Edit route (Claim 10):** Navigation call works but target route `/accounting/expenses/:id/edit` is not in the assigned pages. If no edit page exists in the router, user will see a 404 or blank page.

### Summary
- Total claims: 15
- VERIFIED: 11
- PARTIAL: 1
- FALSIFIED: 2 (scaffolding)
- UNVERIFIABLE: 0
