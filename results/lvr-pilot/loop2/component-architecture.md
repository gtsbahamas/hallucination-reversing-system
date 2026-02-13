# Loop 2 -- Component & UI Architecture

*Generated: 2026-02-13*
*Source: 25 accounting page components from Island Biz ERP*
*Agent: A (Architecture Extraction)*

---

## Current Architecture Analysis

### Page Classification

After reading all 25 accounting pages, they fall into four distinct structural categories:

| Category | Count | Pages |
|----------|-------|-------|
| **Thin Wrapper** | 13 | ACC-003, ACC-005, ACC-010, ACC-011, ACC-012, ACC-014, ACC-015, ACC-016, ACC-017, ACC-018, ACC-019, ACC-021, ACC-022 |
| **Tabbed Container** | 5 | ACC-009, ACC-023, ACC-024, ACC-025, ACC-026 |
| **Full List Page** | 1 | ACC-001 |
| **Detail Page** | 5 | ACC-002, ACC-004, ACC-006, ACC-007, ACC-013 |
| **Delegating Page (no wrapper)** | 1 | ACC-020 |

### Thin Wrappers (13 pages)

These pages follow a nearly identical pattern:

```tsx
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import SomeTab from '@/components/accounting/SomeTab';
import { SomeIcon } from 'lucide-react';

const SomePage = () => (
  <DashboardLayout>
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <SomeIcon className="h-8 w-8" />
          Page Title
        </h1>
        <p className="text-neutral-600 mt-2">Description text</p>
      </div>
      <SomeTab />
    </div>
  </DashboardLayout>
);
```

**Specific pages and their delegated Tab components:**

| Page | Tab Component | Notes |
|------|--------------|-------|
| BillsPage (ACC-003) | `BillsDashboard` | Header is separate from Tab |
| ExpensesPage (ACC-005) | `ExpensesTab` | Standard thin wrapper |
| AccountsReceivablePage (ACC-010) | `ARManagementTab` | Uses `p-6` not `container mx-auto py-6` |
| AccountsPayablePage (ACC-011) | `AccountsPayableTab` | Has icon in header |
| JournalEntriesPage (ACC-012) | `JournalEntriesTab` | Uses `PageHeader` component |
| ChartOfAccountsPage (ACC-014) | `ChartOfAccountsTab` | Standard thin wrapper |
| FinancialReportsPage (ACC-015) | `FinancialReportsTab` | Standard thin wrapper |
| BankReconciliationPage (ACC-016) | `BankReconciliationTab` | Standard thin wrapper |
| TaxReportingPage (ACC-017) | `TaxReportingTab` | Standard thin wrapper |
| BudgetAnalysisPage (ACC-018) | `BudgetAnalysisTab` | Standard thin wrapper |
| CashFlowPage (ACC-019) | `CashFlowTab` | Standard thin wrapper |
| FixedAssetsPage (ACC-021) | `FixedAssetsTab` | Standard thin wrapper |
| MultiCurrencyPage (ACC-022) | `MultiCurrencyTab` | Standard thin wrapper |

**Key observation:** Only `JournalEntriesPage` uses the shared `PageHeader` component. The other 12 all manually inline the same header pattern with slight variations in CSS class names (`text-muted-foreground` vs `text-neutral-600`, `text-fg-muted`).

### Tabbed Container Pages (5 pages)

These pages host multiple tab components inside a DashboardLayout:

| Page | Tabs | Sub-Tab Components |
|------|------|--------------------|
| FinancialManagement (ACC-009) | 6 top-level tabs, each with 3-4 sub-tabs | 16 lazy-loaded components total |
| AgingReportsPage (ACC-023) | `AgingReportsTab` has internal AR/AP tabs | Uses hook `useAgingReports` |
| CompliancePlanningPage (ACC-024) | 3 tabs: Tax, Budget, Assets | Re-uses same Tab components as standalone pages |
| BankingAndCashPage (ACC-025) | 4 tabs: Reconciliation, Cash Flow, Multi-Currency, POS EOD | Re-uses same Tab components as standalone pages |
| CreditManagement (ACC-026) | 3 tabs: Overview, Customer Credit, Alerts | 3 sub-panels: `CreditManagementPanel`, `CustomerCreditManagementTab`, `CreditAlertsPanel` |

**Key observation:** ACC-024 and ACC-025 are composite wrappers that embed the same Tab components that already have standalone pages. This means the same content is reachable via two different routes (e.g., `/accounting/tax-reporting` and `/accounting/compliance-planning` -> Tax tab). FinancialManagement (ACC-009) is the "mega-page" that tries to contain everything in one tabbed interface.

### Full List Page (1 page)

**InvoicesPage (ACC-001)** is the only page that directly manages its own list display (no delegation to a Tab component):
- Uses `useInvoicesPaginated` hook
- Has search input, view mode toggle (list/kanban), stat cards
- Manages 3 modals: CreateInvoiceModal, InvoiceViewModal, EditInvoiceModal
- Includes PaginationControls
- Renders list as Card-based layout (not Table)

### Detail Pages (5 pages)

All 5 detail pages follow a consistent (but not componentized) pattern:

```
Header: [Back button] [Entity title + subtitle] [Status badge(s)] [Action buttons]
Body: 2-column or 3-column grid
  Left (2/3): Tabs with Details/[entity-specific]/Activity tabs
  Right (1/3): Sidebar cards (related entity, quick actions, summary)
```

| Page | Tabs | Sidebar Cards | Action Buttons |
|------|------|---------------|----------------|
| InvoiceDetailPage (ACC-002) | Details, Line Items, Payments, Activity | Customer, Quick Actions, Summary | Send, Mark Paid, Download PDF, Edit, Delete |
| BillDetailPage (ACC-004) | (no tabs, single card) | Supplier Info, Activity | Approve, Reject, Edit, Delete |
| ExpenseDetailPage (ACC-006) | Details, Receipt, Accounting, Activity | Employee, Quick Actions, Summary | Approve, Reject, Reimburse, Edit, Delete |
| PaymentDetailPage (ACC-007) | Details, Allocation, Activity | Related Records, Quick Actions, Summary | Edit |
| JournalEntryDetailPage (ACC-013) | Details, Journal Lines, Activity | Quick Actions, Entry Summary | Post, Reverse, Edit, Discard Draft |

### Delegating Page (1 page)

**VarianceAnalysisPage (ACC-020)** has no header at all -- it just wraps `VarianceAnalysisDashboard` in `DashboardLayout`:

```tsx
<DashboardLayout>
  <VarianceAnalysisDashboard />
</DashboardLayout>
```

---

## Shared Component Patterns Identified

### Pattern 1: DashboardLayout Wrapper

**Used by:** ALL 25 pages
**Source:** `@/components/dashboard/DashboardLayout`
**Pattern:** Every page is wrapped in `<DashboardLayout>`. This provides the main app shell (sidebar, topbar, etc.).

### Pattern 2: Inline Page Header

**Used by:** 23 of 25 pages (all except ACC-020 which has no header, and ACC-012 which uses PageHeader)
**Current state:** Each page manually creates its header with slight CSS variations.

Three variations observed:

| Variation | Pages | CSS Classes |
|-----------|-------|-------------|
| `text-muted-foreground` | ACC-009, ACC-015, ACC-017, ACC-021, ACC-022, ACC-024, ACC-025, ACC-026 | Standard shadcn theming |
| `text-neutral-600` | ACC-003, ACC-011, ACC-014, ACC-016, ACC-018, ACC-019 | Hardcoded neutral |
| `text-fg-muted` | ACC-001, ACC-005 | Custom token |

### Pattern 3: Stat Cards (Summary Metrics)

**Used by:** 10+ pages (ACC-001, ACC-003, ACC-005, ACC-009, ACC-010, ACC-011, ACC-019, ACC-026)
**Current state:** Each page manually builds its own stat cards using raw Card/CardHeader/CardContent.

Consistent sub-pattern observed:

```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
    <CardTitle className="text-sm font-medium">Metric Name</CardTitle>
    <Icon className="h-4 w-4 text-muted-foreground" />
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">{value}</div>
    <p className="text-xs text-muted-foreground">Subtitle</p>
  </CardContent>
</Card>
```

Grid layout: `grid grid-cols-1 md:grid-cols-4 gap-6` (most common) or `md:grid-cols-3`.

### Pattern 4: Sortable/Configurable Data Table

**Used by:** BillsDashboard, ExpensesTab, InvoicesTab, ChartOfAccountsTab, BankReconciliationTab
**Components involved:**
- `Table` / `TableBody` / `TableCell` / `TableHeader` / `TableRow` (shadcn)
- `SortableTableHead` (custom -- adds sort arrows)
- `DraggableTableHead` (custom -- allows column reorder)
- `ColumnSettingsModal` / `ColumnDefinition` (custom -- show/hide/reorder columns)
- `useColumnPreferences` hook (custom -- persists column config)
- `useSortableData` hook (custom -- client-side multi-column sort)
- `BulkActionToolbar` (custom -- appears when rows are selected)
- `PaginationControls` (custom -- full pagination UI)

Each table defines a `COLUMNS` array:
```tsx
const BILL_COLUMNS: ColumnDefinition[] = [
  { id: 'select', label: 'Select', locked: true },
  { id: 'bill_number', label: 'Bill #' },
  { id: 'supplier', label: 'Supplier' },
  // ...
  { id: 'actions', label: 'Actions', locked: true },
];
```

### Pattern 5: Status Badge System

**Used by:** ALL detail pages, ALL list/tab components
**Current state:** Every component reimplements its own `getStatusBadge(status: string)` function with a status-to-color map.

Common structure:
```tsx
const statusConfig = {
  draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
  sent: { label: 'Sent', className: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
  // ...
};
```

Each entity type has its own status set (invoices: draft/sent/paid/overdue/cancelled; bills: draft/pending_approval/approved/paid/overdue/cancelled; expenses: draft/submitted/approved/rejected/paid/reimbursed; etc.).

### Pattern 6: Detail Page Sidebar

**Used by:** ALL 5 detail pages
**Structure:**
1. Related Entity card (Customer, Supplier, Employee)
2. Quick Actions card (context-sensitive buttons)
3. Summary card (key-value pairs for the entity)

All use `<div className="space-y-6">` as the sidebar container.

### Pattern 7: Activity Log Tab

**Used by:** All 5 detail pages (ACC-002, ACC-004, ACC-006, ACC-007, ACC-013)
**Content:** Just created_at and updated_at timestamps, with a comment "Additional activity items would go here."

### Pattern 8: Tab Loader

**Used by:** ACC-009, ACC-024, ACC-025
**Pattern:** A spinner with "Loading..." text, used as Suspense fallback for lazy-loaded tabs.

```tsx
const TabLoader = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    <span className="ml-2">Loading...</span>
  </div>
);
```

### Pattern 9: Create/Edit Modal

**Used by:** InvoicesPage (CreateInvoiceModal, EditInvoiceModal), BillsDashboard (EnhancedCreateBillModal, EditBillModal), ExpensesTab (CreateExpenseModal), JournalEntriesTab (CreateJournalEntryModal), ChartOfAccountsTab (inline Dialog), FixedAssetsTab (inline Dialog), MultiCurrencyTab (inline Dialog)
**Variation:** Some use dedicated modal components, others use inline `<Dialog>`.

### Pattern 10: Export to CSV

**Used by:** AgingReportsTab, BudgetAnalysisTab, TaxReportingTab
**Pattern:** Manual CSV construction via string concatenation and `encodeURI` with a temporary `<a>` element download.

---

## Target Shared Components

### 1. PageHeader

**Already exists at:** `@/components/layout/PageHeader.tsx`
**Currently used by:** Only ACC-012 (JournalEntriesPage)
**Props (current):** `{ title, description?, icon?, className?, children? }`

**Target:** Adopt for ALL 24 remaining pages. The component already handles the icon, title, description, and action slot pattern. Adding it will:
- Eliminate 23 inline header implementations
- Standardize CSS classes (currently 3 variants)
- Add `PageTourButton` consistently to all pages

**No prop changes needed.** The current interface covers all observed variations.

### 2. StatCards

**New shared component**

```tsx
interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  subtitle?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'flat';
  };
  alert?: boolean; // Render value in red (e.g., overdue count)
  className?: string;
}

interface StatCardsGridProps {
  stats: StatCardProps[];
  columns?: 3 | 4; // Default 4
  className?: string;
}
```

**Usage:**
```tsx
<StatCardsGrid stats={[
  { label: 'Total Invoices', value: stats.total, icon: Receipt },
  { label: 'Paid', value: stats.paid, icon: CheckCircle },
  { label: 'Overdue', value: stats.overdue, icon: AlertTriangle, alert: true },
  { label: 'Outstanding', value: `$${stats.unpaidValue.toFixed(2)}`, icon: DollarSign },
]} />
```

**Eliminates:** ~10 manual stat card implementations, each 15-20 lines of JSX.

### 3. StatusBadge

**New shared component**

```tsx
type EntityType = 'invoice' | 'bill' | 'expense' | 'payment' | 'journal_entry' | 'asset';

interface StatusBadgeProps {
  status: string;
  entityType: EntityType;
  className?: string;
}

// Internal: maps entityType to status config
const STATUS_CONFIGS: Record<EntityType, Record<string, { label: string; className: string }>> = {
  invoice: {
    draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
    sent: { label: 'Sent', className: 'bg-blue-100 text-blue-800' },
    paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
    overdue: { label: 'Overdue', className: 'bg-red-100 text-red-800' },
    cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
    partial: { label: 'Partially Paid', className: 'bg-yellow-100 text-yellow-800' },
  },
  bill: {
    draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
    pending_approval: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800' },
    approved: { label: 'Approved', className: 'bg-blue-100 text-blue-800' },
    paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
    overdue: { label: 'Overdue', className: 'bg-red-100 text-red-800' },
    cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
  },
  expense: {
    draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
    submitted: { label: 'Submitted', className: 'bg-blue-100 text-blue-800' },
    approved: { label: 'Approved', className: 'bg-green-100 text-green-800' },
    rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800' },
    paid: { label: 'Paid', className: 'bg-purple-100 text-purple-800' },
    reimbursed: { label: 'Reimbursed', className: 'bg-indigo-100 text-indigo-800' },
  },
  payment: {
    pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800' },
    completed: { label: 'Completed', className: 'bg-green-100 text-green-800' },
    failed: { label: 'Failed', className: 'bg-red-100 text-red-800' },
    cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
    refunded: { label: 'Refunded', className: 'bg-orange-100 text-orange-800' },
  },
  journal_entry: {
    draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
    posted: { label: 'Posted', className: 'bg-green-100 text-green-800' },
    reversed: { label: 'Reversed', className: 'bg-red-100 text-red-800' },
    pending: { label: 'Pending Approval', className: 'bg-yellow-100 text-yellow-800' },
    voided: { label: 'Voided', className: 'bg-gray-100 text-gray-800' },
  },
  asset: {
    active: { label: 'Active', className: 'bg-green-100 text-green-800' },
    disposed: { label: 'Disposed', className: 'bg-gray-100 text-gray-800' },
    fully_depreciated: { label: 'Fully Depreciated', className: 'bg-yellow-100 text-yellow-800' },
  },
};
```

**Eliminates:** 15+ inline `getStatusBadge` / `getStatusColor` functions across the codebase.

### 4. DetailLayout

**New shared component for all 5 detail pages**

```tsx
interface DetailLayoutProps {
  // Header
  backLabel: string;           // "Back to Invoices"
  backPath: string;            // "/accounting/invoices"
  title: string;               // "Invoice INV-001"
  subtitle?: string;           // "Acme Corp"
  badges?: React.ReactNode;    // Status badges
  actions?: React.ReactNode;   // Action buttons

  // Body
  tabs: DetailTab[];           // Tab definitions
  defaultTab?: string;         // Default active tab
  sidebar?: React.ReactNode;   // Right column content

  // Layout
  sidebarWidth?: '1/3' | '1/4';  // Default '1/3'
}

interface DetailTab {
  value: string;
  label: string;
  content: React.ReactNode;
}
```

**Usage:**
```tsx
<DetailLayout
  backLabel="Back to Invoices"
  backPath="/accounting/invoices"
  title={`Invoice ${invoice.invoice_number}`}
  subtitle={invoice.customers?.name}
  badges={<StatusBadge status={invoice.status} entityType="invoice" />}
  actions={
    <>
      {invoice.status === 'draft' && <Button onClick={handleSend}>Send</Button>}
      <Button variant="outline" onClick={handleEdit}>Edit</Button>
      <Button variant="outline" onClick={handleDelete} className="text-red-600">Delete</Button>
    </>
  }
  tabs={[
    { value: 'details', label: 'Details', content: <InvoiceDetailsCard invoice={invoice} /> },
    { value: 'line-items', label: 'Line Items', content: <LineItemsTable invoiceId={invoice.id} /> },
    { value: 'payments', label: 'Payments', content: <PaymentsTable invoiceId={invoice.id} /> },
    { value: 'activity', label: 'Activity', content: <ActivityLog entity={invoice} /> },
  ]}
  sidebar={
    <>
      <RelatedEntityCard entity={invoice.customers} type="customer" />
      <QuickActionsCard actions={quickActions} />
      <EntitySummaryCard items={summaryItems} />
    </>
  }
/>
```

**Eliminates:** ~200 lines of repeated layout code per detail page (1000+ lines total across 5 pages).

### 5. SidebarCard

**New shared component for detail page sidebars**

```tsx
interface SidebarCardProps {
  title: string;
  children: React.ReactNode;
}

// Already implicitly used by all detail pages, just not extracted
```

### 6. QuickActionsCard

**New shared component for the Quick Actions sidebar pattern**

```tsx
interface QuickAction {
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  variant?: 'default' | 'destructive';
  disabled?: boolean;
  visible?: boolean; // Conditional rendering
}

interface QuickActionsCardProps {
  actions: QuickAction[];
}
```

**Eliminates:** Repeated quick action card JSX in all 5 detail pages.

### 7. EntitySummaryCard

**New shared component for the Summary sidebar card**

```tsx
interface SummaryItem {
  label: string;
  value: string | React.ReactNode;
  className?: string; // For highlighting (e.g., red for overdue)
  isSeparator?: boolean; // Adds border-t pt-3
}

interface EntitySummaryCardProps {
  items: SummaryItem[];
  title?: string; // Default "Summary"
}
```

### 8. ActivityLog

**New shared component for the Activity tab (used by all 5 detail pages)**

```tsx
interface ActivityLogProps {
  createdAt: string;
  updatedAt: string;
  entries?: ActivityEntry[]; // Future: real activity log entries
}

interface ActivityEntry {
  action: string;
  timestamp: string;
  user?: string;
  details?: string;
}
```

Currently all 5 detail pages show the same minimal created/updated timestamps. This component standardizes it and provides a place to add real activity log integration later.

### 9. ListPageLayout

**New shared component for thin wrapper pages**

```tsx
interface ListPageLayoutProps {
  title: string;
  description: string;
  icon: LucideIcon;
  children: React.ReactNode;
}

const ListPageLayout = ({ title, description, icon, children }: ListPageLayoutProps) => (
  <DashboardLayout>
    <div className="container mx-auto py-6">
      <PageHeader title={title} description={description} icon={icon} />
      {children}
    </div>
  </DashboardLayout>
);
```

**Eliminates:** 13 nearly identical thin wrapper pages, each 15-25 lines, reduced to ~5 lines each.

### 10. CSVExport (utility function)

**New shared utility for CSV export**

```tsx
function exportCSV(filename: string, headers: string[], rows: string[][]): void {
  const csvContent = "data:text/csv;charset=utf-8," +
    headers.join(",") + "\n" +
    rows.map(row => row.join(",")).join("\n");

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
```

**Eliminates:** 3 identical CSV export implementations (AgingReportsTab, BudgetAnalysisTab, TaxReportingTab).

### 11. TabLoader

**Exists already but is duplicated in 3 files**

```tsx
const TabLoader = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    <span className="ml-2">Loading...</span>
  </div>
);
```

**Action:** Extract to `@/components/ui/tab-loader.tsx` and import from there.

### 12. ConfirmAction (already partially exists)

`ConfirmDeleteDialog` is already used by InvoiceDetailPage. Other detail pages use raw `confirm()` calls.

**Target:** Use `ConfirmDeleteDialog` (or a more general `ConfirmActionDialog`) consistently across all destructive actions.

---

## Page Component Specifications

### List Pages (Thin Wrappers) -- Target Pattern

```tsx
// Target: Each thin wrapper becomes ~5 lines
const TaxReportingPage = () => (
  <ListPageLayout
    title="Tax Reporting"
    description="Generate VAT reports and tax compliance documents"
    icon={Receipt}
  >
    <TaxReportingTab />
  </ListPageLayout>
);
```

**Pages that become thin wrappers (13):**
ACC-003, ACC-005, ACC-010, ACC-011, ACC-012, ACC-014, ACC-015, ACC-016, ACC-017, ACC-018, ACC-019, ACC-021, ACC-022

**Per-page variations (preserved):**

| Page | Tab Component | Icon |
|------|--------------|------|
| BillsPage | BillsDashboard | FileText |
| ExpensesPage | ExpensesTab | DollarSign |
| AccountsReceivablePage | ARManagementTab | Users |
| AccountsPayablePage | AccountsPayableTab | ShoppingCart |
| JournalEntriesPage | JournalEntriesTab | FileText |
| ChartOfAccountsPage | ChartOfAccountsTab | BookOpen |
| FinancialReportsPage | FinancialReportsTab | TrendingUp |
| BankReconciliationPage | BankReconciliationTab | CreditCard |
| TaxReportingPage | TaxReportingTab | Receipt |
| BudgetAnalysisPage | BudgetAnalysisTab | PieChart |
| CashFlowPage | CashFlowTab | TrendingUp |
| FixedAssetsPage | FixedAssetsTab | Building2 |
| MultiCurrencyPage | MultiCurrencyTab | Globe |

### Full List Page (ACC-001 InvoicesPage) -- Target Pattern

InvoicesPage is the only page with its own list rendering. The target architecture should:

1. Extract stat cards into `<StatCardsGrid>`
2. Keep search + view mode toggle as page-level concerns
3. The kanban view is unique to invoices -- keep as local component
4. List view renders as Cards, not Table (different from other list pages)

This page stays mostly as-is but adopts shared components:
- `PageHeader` for header
- `StatCardsGrid` for stats
- `StatusBadge` for status rendering

### Detail Pages -- Target Pattern

All 5 detail pages should use `DetailLayout`:

**InvoiceDetailPage (ACC-002):**
```
Tabs: Details, Line Items*, Payments*, Activity
Sidebar: Customer card, Quick Actions, Summary
Actions: Send (draft), Mark Paid (sent/overdue), Download PDF, Edit, Delete
* Currently placeholder -- must be implemented
```

**BillDetailPage (ACC-004):**
```
Tabs: (single card, no tabs currently -- target: Details, Line Items, Activity)
Sidebar: Supplier Info, Activity
Actions: Approve (pending), Reject (pending), Edit, Delete
Note: BillDetailPage has NO Tabs component currently -- add one for consistency
```

**ExpenseDetailPage (ACC-006):**
```
Tabs: Details, Receipt, Accounting*, Activity
Sidebar: Employee card, Quick Actions, Summary
Actions: Approve/Reject (submitted), Reimburse (approved+reimbursable), Edit, Delete
* Accounting tab has hardcoded data -- must be wired to real data
```

**PaymentDetailPage (ACC-007):**
```
Tabs: Details, Allocation, Activity
Sidebar: Related Records, Quick Actions, Summary
Actions: Edit
Note: Process Refund and Print Receipt are stubs
```

**JournalEntryDetailPage (ACC-013):**
```
Tabs: Details, Journal Lines (real Table with debit/credit columns), Activity
Sidebar: Quick Actions, Entry Summary (includes balance check)
Actions: Post (draft+balanced), Reverse (posted), Edit (draft), Discard Draft
Note: Post and Reverse must use service layer, not direct status update
```

### Tabbed Container Pages -- Target Pattern

**FinancialManagement (ACC-009):**
- Remains the mega-page
- 6 top-level tabs, each with nested tabs
- All sub-tabs are lazy-loaded
- **Must replace mock data** on Overview tab with real data hooks
- **"Generate Report" button has no handler** -- must wire or remove

**CompliancePlanningPage (ACC-024):**
```
Tabs: Tax Reporting | Budget Analysis | Fixed Assets
Components: TaxReportingTab, BudgetAnalysisTab, FixedAssetsTab (all lazy-loaded)
```

**BankingAndCashPage (ACC-025):**
```
Tabs: Bank Reconciliation | Cash Flow | Multi-Currency | POS End of Day
Components: BankReconciliationTab, CashFlowTab, MultiCurrencyTab, POSEndOfDayContent (all lazy-loaded)
```

**CreditManagement (ACC-026):**
```
Tabs: Overview | Customer Credit | Alerts
Components: CreditManagementPanel, CustomerCreditManagementTab, CreditAlertsPanel
Note: Has its own auth check (useAuth + redirect) -- other pages don't do this
```

### Report Pages -- Common Pattern

Report-style tabs (TaxReportingTab, AgingReportsTab, BudgetAnalysisTab) share a pattern:
1. Date range selector (start date, end date inputs)
2. "Generate" button to run the report
3. Results table rendered below
4. Export to CSV button

**Target: ReportLayout component**

```tsx
interface ReportLayoutProps {
  title: string;
  icon: LucideIcon;
  dateRange?: {
    startDate: string;
    endDate: string;
    onStartChange: (date: string) => void;
    onEndChange: (date: string) => void;
  };
  onGenerate: () => void;
  onExport?: () => void;
  loading: boolean;
  children: React.ReactNode; // Report results
}
```

---

## Component --> Requirement Mapping

| ACC# | Page | Page Component | Tab/Body Component | Shared Components Used (Target) |
|------|------|----------------|--------------------|---------------------------------|
| ACC-001 | Invoices List | InvoicesPage | (inline) | DashboardLayout, PageHeader, StatCardsGrid, StatusBadge, PaginationControls |
| ACC-002 | Invoice Detail | InvoiceDetailPage | (inline) | DetailLayout, StatusBadge, QuickActionsCard, EntitySummaryCard, ActivityLog, ConfirmDeleteDialog |
| ACC-003 | Bills List | BillsPage | BillsDashboard | ListPageLayout, StatCardsGrid, SortableTable*, StatusBadge, PaginationControls, BulkActionToolbar |
| ACC-004 | Bill Detail | BillDetailPage | (inline) | DetailLayout, StatusBadge, EntitySummaryCard, ActivityLog, ConfirmDeleteDialog |
| ACC-005 | Expenses List | ExpensesPage | ExpensesTab | ListPageLayout, SortableTable*, StatusBadge, PaginationControls |
| ACC-006 | Expense Detail | ExpenseDetailPage | (inline) | DetailLayout, StatusBadge, QuickActionsCard, EntitySummaryCard, ActivityLog |
| ACC-007 | Payment Detail | PaymentDetailPage | (inline) | DetailLayout, StatusBadge, QuickActionsCard, EntitySummaryCard, ActivityLog |
| ACC-009 | Financial Mgmt | FinancialManagement | (tabs) | DashboardLayout, StatCardsGrid, TabLoader, StatusBadge |
| ACC-010 | Accounts Receivable | AccountsReceivablePage | ARManagementTab | ListPageLayout, StatCardsGrid, TabLoader |
| ACC-011 | Accounts Payable | AccountsPayablePage | AccountsPayableTab | ListPageLayout, StatCardsGrid, TabLoader |
| ACC-012 | Journal Entries | JournalEntriesPage | JournalEntriesTab | ListPageLayout (with PageHeader), StatusBadge, PaginationControls |
| ACC-013 | Journal Entry Detail | JournalEntryDetailPage | (inline) | DetailLayout, StatusBadge, QuickActionsCard, EntitySummaryCard, ActivityLog |
| ACC-014 | Chart of Accounts | ChartOfAccountsPage | ChartOfAccountsTab | ListPageLayout, SortableTable*, StatusBadge |
| ACC-015 | Financial Reports | FinancialReportsPage | FinancialReportsTab | ListPageLayout |
| ACC-016 | Bank Reconciliation | BankReconciliationPage | BankReconciliationTab | ListPageLayout, SortableTable*, StatusBadge |
| ACC-017 | Tax Reporting | TaxReportingPage | TaxReportingTab | ListPageLayout, ReportLayout, CSVExport |
| ACC-018 | Budget Analysis | BudgetAnalysisPage | BudgetAnalysisTab | ListPageLayout, ReportLayout, CSVExport |
| ACC-019 | Cash Flow | CashFlowPage | CashFlowTab | ListPageLayout, StatCardsGrid, StatusBadge |
| ACC-020 | Variance Analysis | VarianceAnalysisPage | VarianceAnalysisDashboard | DashboardLayout |
| ACC-021 | Fixed Assets | FixedAssetsPage | FixedAssetsTab | ListPageLayout, StatusBadge |
| ACC-022 | Multi-Currency | MultiCurrencyPage | MultiCurrencyTab | ListPageLayout, StatusBadge |
| ACC-023 | Aging Reports | AgingReportsPage | AgingReportsTab | ListPageLayout, ReportLayout, CSVExport |
| ACC-024 | Compliance Planning | CompliancePlanningPage | (tabs) | DashboardLayout, TabLoader |
| ACC-025 | Banking & Cash | BankingAndCashPage | (tabs) | DashboardLayout, TabLoader |
| ACC-026 | Credit Management | CreditManagement | (tabs) | DashboardLayout, StatCardsGrid |

*SortableTable = the existing combination of Table + SortableTableHead + DraggableTableHead + ColumnSettingsModal + useColumnPreferences + useSortableData. These are already shared components; the naming here is for clarity.

---

## Bug Fix Architecture

### BUG-M01: Invoice Detail Line Items Tab is Placeholder

**Architecture fix:** The `DetailLayout` for InvoiceDetailPage must include a real `LineItemsTab` component:

```tsx
// New component: @/components/invoices/LineItemsTable.tsx
interface LineItemsTableProps {
  invoiceId: string;
}
// Fetches from invoice_line_items table joined with products
// Columns: Item, Description, Quantity, Unit Price, Tax, Total
```

The InvoiceDetailPage query (`fetchInvoice`) must be updated to also select `invoice_line_items(*, products(*))`.

### BUG-M02: Invoice Detail Payments Tab is Placeholder

**Architecture fix:** Add a real `PaymentsTable` component:

```tsx
// New component: @/components/invoices/InvoicePaymentsTable.tsx
interface InvoicePaymentsTableProps {
  invoiceId: string;
}
// Fetches from invoice_payments or payments table where invoice_id = invoiceId
// Columns: Date, Amount, Method, Reference, Status
```

### BUG-M03/M05: Duplicate Buttons Have No Handler

**Architecture fix:** The `QuickActionsCard` should support a `DuplicateAction` pattern:

```tsx
// Shared handler factory for duplication
async function duplicateEntity(
  table: string,
  id: string,
  businessId: string,
  fieldsToReset: Record<string, any> // e.g., { status: 'draft', invoice_number: generateNew() }
): Promise<{ id: string } | null>
```

Each entity type defines which fields to reset on duplication (status becomes 'draft', number is regenerated, dates are updated to today).

The "Duplicate" button in QuickActionsCard gets a real `onClick` that:
1. Calls `duplicateEntity()`
2. Navigates to the new entity's detail page
3. Shows a success toast

### BUG-M04: Expense Accounting Tab is Hardcoded

**Architecture fix:** Replace the hardcoded tab with a real `ExpenseAccountingTab` component:

```tsx
// New component: @/components/accounting/ExpenseAccountingTab.tsx
interface ExpenseAccountingTabProps {
  expenseId: string;
  category: string;
}
// Fetches linked chart_of_accounts entry
// Shows actual account mapping, tax deductibility from config, linked journal entry
```

### BUG-M06/M07: Payment Refund/Print Are Stubs

**Architecture fix:** Two options:

1. **Implement:** Create `ProcessRefundModal` and `PrintReceiptAction` components.
2. **Remove:** Delete the buttons from the QuickActionsCard for now, with a TODO in the component map.

Recommendation: Remove from QuickActionsCard by setting `visible: false` until implemented. This is better than a toast that says "coming in v2.0" -- users should not see buttons that do nothing.

### BUG-M08/M09: Chart of Accounts Edit/Delete Have No Handler

**Architecture fix:** The ChartOfAccountsTab must implement:

```tsx
// Edit: Open a modal with pre-filled account data
const handleEditAccount = (account: Account) => {
  setEditingAccount(account);
  setIsEditDialogOpen(true);
};

// Delete: Use ConfirmDeleteDialog, then call deleteAccount
const handleDeleteAccount = async (account: Account) => {
  if (account.is_system) return; // System accounts cannot be deleted
  setDeletingAccount(account);
  setShowDeleteDialog(true);
};
```

The `useAccounting` hook must expose `updateAccount` and `deleteAccount` methods.

### BUG-M10: Bills Bulk Email is Stub

**Architecture fix:** Same as BUG-M06/M07 -- either implement `BulkEmailModal` or remove the button from the BulkActionToolbar.

### BUG-H01: Financial Management Shows Mock Data

**Architecture fix:** Replace the hardcoded `financialStats` object with real data:

```tsx
// Replace:
const financialStats = { totalAssets: 1250000, ... };

// With:
const { financialStats, loading } = useFinancialOverview();

// New hook: @/hooks/useFinancialOverview.ts
// Aggregates from: chart_of_accounts (balances), invoices (AR), bills (AP), bank_accounts (cash)
```

Similarly, replace `recentTransactions` array with a real query.

### BUG-L05: Edit Routes Have No Effect

**Architecture fix:** Detail pages should accept an `?edit=true` query parameter or a `/edit` route segment and respond by:
1. Opening the edit modal on mount
2. Or switching to an inline edit mode

The `DetailLayout` component should support this:

```tsx
interface DetailLayoutProps {
  // ...existing props
  editMode?: boolean;       // Start in edit mode
  onEditModeChange?: (editing: boolean) => void;
}
```

---

## Data Hook Mapping

Each page type relies on specific data hooks. These are already implemented but should be documented:

| Hook | Used By | Returns |
|------|---------|---------|
| `useInvoicesPaginated` | ACC-001, InvoicesTab | `{ invoices, loading, pagination, refetch, metadata }` |
| `useAccountsPayable` | ACC-003 (BillsDashboard), ACC-011 (AccountsPayableTab) | `{ bills, loading, refetch }` |
| `useExpensesPaginated` | ACC-005 (ExpensesTab) | `{ expenses, loading, refetch, pagination }` |
| `useAccountsReceivable` | ACC-010 (ARManagementTab) | `{ invoices, loading }` (NOT `arTransactions`) |
| `useARAnalytics` | ACC-010 (ARManagementTab) | `{ snapshots }` |
| `useJournalEntriesPaginated` | ACC-012 (JournalEntriesTab) | `{ journalEntries, loading, pagination, refetch }` |
| `useAccounting` | ACC-014 (ChartOfAccountsTab) | `{ accounts, loading, createAccount, getAccountsByType }` |
| `useBankReconciliation` | ACC-016 (BankReconciliationTab) | `{ bankTransactions, loading, refetch }` |
| `useTaxReporting` | ACC-017 (TaxReportingTab) | `{ loading, generateVATReport, generateIncomeStatementForTax }` |
| `useBudgets` | ACC-018 (BudgetAnalysisTab) | `{ budgets, loading, generateBudgetVsActual }` |
| `useCashFlow` | ACC-019 (CashFlowTab) | `{ cashFlowCategories, cashFlowTransactions, loading, getCashFlowStatement }` |
| `useFixedAssets` | ACC-021 (FixedAssetsTab) | `{ assets, loading, addAsset, fetchDepreciationSchedule, calculateCurrentDepreciation }` |
| `useMultiCurrency` | ACC-022 (MultiCurrencyTab) | `{ currencies, baseCurrency, loading, addCurrency, updateExchangeRate }` |
| `useAgingReports` | ACC-023 (AgingReportsTab) | `{ loading, generateAccountsReceivableAging, generateAccountsPayableAging }` |
| `useBusiness` | Many pages | `{ currentBusiness }` |
| `useAuth` | ACC-026, detail pages | `{ user, loading }` |
| `usePermission` | ACC-003 (BillsDashboard) | `{ hasPermission }` |
| `useSortableData` | BillsDashboard, ExpensesTab, InvoicesTab, ChartOfAccountsTab, BankReconciliationTab | `{ sortedData, requestSort, getSortDirection, getSortIndex }` |
| `useColumnPreferences` | BillsDashboard, ExpensesTab, InvoicesTab, ChartOfAccountsTab, BankReconciliationTab | `{ visibleColumns, orderedColumnIds, hiddenColumnIds, savePreferences, resetToDefault }` |

---

## Summary of Architectural Changes

| Change | Files Affected | Lines Saved (est.) | Bugs Fixed |
|--------|---------------|--------------------|----|
| Adopt `PageHeader` everywhere | 23 pages | ~230 | -- |
| Extract `StatCardsGrid` | 10+ pages | ~400 | -- |
| Extract `StatusBadge` | 20+ files | ~300 | -- |
| Create `DetailLayout` | 5 detail pages | ~1000 | BUG-L05 |
| Create `ListPageLayout` | 13 thin wrappers | ~200 | -- |
| Create `QuickActionsCard` | 5 detail pages | ~250 | BUG-M03, M05 |
| Create `EntitySummaryCard` | 5 detail pages | ~200 | -- |
| Create `ActivityLog` | 5 detail pages | ~100 | -- |
| Extract `TabLoader` | 3 files | ~30 | -- |
| Extract `CSVExport` | 3 files | ~60 | -- |
| Implement `LineItemsTable` | ACC-002 | new ~150 | BUG-M01 |
| Implement `InvoicePaymentsTable` | ACC-002 | new ~150 | BUG-M02 |
| Wire ChartOfAccounts Edit/Delete | ACC-014 | ~80 | BUG-M08, M09 |
| Replace mock data in ACC-009 | ACC-009 | ~20 modified | BUG-H01 |
| Wire Expense Accounting tab | ACC-006 | ~60 modified | BUG-M04 |
| Remove/implement stubs | ACC-003, ACC-007 | varies | BUG-M06, M07, M10 |
| Fix JE Post/Reverse to use service | ACC-013 | ~10 modified | BUG-H04, H05 |
| **Total estimated reduction** | | **~2,770 lines** | **14 bugs** |

---

## Implementation Priority

1. **PageHeader adoption** -- Lowest risk, immediate consistency win
2. **ListPageLayout** -- Simplifies 13 files with zero behavioral change
3. **StatusBadge** -- Removes duplication, single source of truth for status colors
4. **StatCardsGrid** -- Standardizes the most common dashboard pattern
5. **DetailLayout** -- Highest impact but most complex; do after 1-4 are stable
6. **QuickActionsCard + EntitySummaryCard** -- Support components for DetailLayout
7. **Bug fixes** (H04/H05 service wiring, M01/M02 tab implementations) -- Can be done in parallel with component extraction
8. **ActivityLog** -- Low priority since current implementation is minimal
9. **ReportLayout + CSVExport** -- Nice-to-have standardization
10. **TabLoader extraction** -- Trivial, do anytime
