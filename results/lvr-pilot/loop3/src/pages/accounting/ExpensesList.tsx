/**
 * ExpensesList (ACC-005)
 *
 * List page with DataTable, StatCards, filters, create modal, CSV export.
 *
 * Bug fixes applied:
 *   BUG-L02: Stats from separate aggregation query (useExpenseAggregationsQuery)
 *   BUG-L03: Employee name displayed via employees join in ExpenseWithRelations
 *
 * Uses React Query hooks from foundation (NOT useState+useEffect).
 * Uses shared components (DataTable, StatCards, FormModal).
 * Uses permission guards from accountingPermissions.ts.
 */

import React, { useState, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DataTable, type ColumnDef, type SortingConfig } from '@/components/accounting/shared/DataTable';
import { StatCards, type StatCardData } from '@/components/accounting/shared/StatCards';
import { FormModal, type FormFieldConfig } from '@/components/accounting/shared/FormModal';
import {
  useExpensesQuery,
  useExpenseAggregationsQuery,
  useCreateExpenseMutation,
} from '@/hooks/useExpenses';
import {
  useAccountingPermission,
} from '@/config/accountingPermissions';
import type {
  ExpenseWithRelations,
  ExpenseFilters,
  ExpenseStatus,
  PaginationParams,
} from '@/types/accounting';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Receipt,
  Plus,
  DollarSign,
  CheckCircle,
  Clock,
  AlertTriangle,
  Search,
  Download,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
  pending_approval: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800' },
  approved: { label: 'Approved', className: 'bg-green-100 text-green-800' },
  rejected: { label: 'Rejected', className: 'bg-red-100 text-red-800' },
};

function getStatusBadge(status: string) {
  const config = STATUS_CONFIG[status] ?? { label: status, className: 'bg-gray-100 text-gray-800' };
  return <Badge className={config.className}>{config.label}</Badge>;
}

// ---------------------------------------------------------------------------
// CSV export
// ---------------------------------------------------------------------------

function exportExpensesCSV(expenses: ExpenseWithRelations[]) {
  const headers = ['Expense #', 'Employee', 'Date', 'Category', 'Status', 'Amount', 'Vendor'];
  const rows = expenses.map((exp) => [
    exp.expense_number,
    exp.employees
      ? `${exp.employees.first_name} ${exp.employees.last_name}`
      : 'N/A',
    exp.expense_date,
    exp.category ?? 'N/A',
    exp.status,
    (exp.total_amount ?? exp.amount).toFixed(2),
    exp.vendor ?? 'N/A',
  ]);

  const csvContent =
    'data:text/csv;charset=utf-8,' +
    headers.join(',') +
    '\n' +
    rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `expenses-${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Create Expense form fields
// ---------------------------------------------------------------------------

const CREATE_EXPENSE_FIELDS: FormFieldConfig[] = [
  {
    name: 'expense_date',
    label: 'Date',
    type: 'date',
    required: true,
    defaultValue: new Date().toISOString().split('T')[0],
  },
  {
    name: 'amount',
    label: 'Amount',
    type: 'number',
    required: true,
    min: 0,
    step: 0.01,
    placeholder: '0.00',
  },
  {
    name: 'category',
    label: 'Category',
    type: 'text',
    placeholder: 'e.g. Travel, Office Supplies',
  },
  {
    name: 'vendor',
    label: 'Vendor',
    type: 'text',
    placeholder: 'Vendor name',
  },
  {
    name: 'payment_method',
    label: 'Payment Method',
    type: 'select',
    options: [
      { label: 'Cash', value: 'cash' },
      { label: 'Credit Card', value: 'credit_card' },
      { label: 'Debit Card', value: 'debit_card' },
      { label: 'Bank Transfer', value: 'bank_transfer' },
      { label: 'Check', value: 'check' },
      { label: 'Other', value: 'other' },
    ],
  },
  {
    name: 'description',
    label: 'Description',
    type: 'textarea',
    colSpan: 'col-span-2',
    placeholder: 'Describe the expense...',
  },
];

// ---------------------------------------------------------------------------
// Column definitions
// ---------------------------------------------------------------------------

const COLUMNS: ColumnDef<ExpenseWithRelations>[] = [
  {
    id: 'expense_number',
    header: 'Expense #',
    accessor: 'expense_number',
    sortable: true,
    cell: (row) => <span className="font-mono font-medium text-sm">{row.expense_number}</span>,
  },
  {
    // BUG-L03 fix: show employee name from employees join
    id: 'employee',
    header: 'Employee',
    cell: (row) => {
      if (!row.employees) return <span className="text-muted-foreground text-sm">N/A</span>;
      return (
        <span className="font-medium text-sm">
          {row.employees.first_name} {row.employees.last_name}
        </span>
      );
    },
  },
  {
    id: 'expense_date',
    header: 'Date',
    accessor: 'expense_date',
    sortable: true,
    cell: (row) => <span className="text-sm">{new Date(row.expense_date).toLocaleDateString()}</span>,
  },
  {
    id: 'category',
    header: 'Category',
    cell: (row) => (
      <span className="text-sm">{row.category ?? 'Uncategorized'}</span>
    ),
  },
  {
    id: 'vendor',
    header: 'Vendor',
    cell: (row) => (
      <span className="text-sm">{row.vendor ?? row.suppliers?.name ?? 'N/A'}</span>
    ),
  },
  {
    id: 'status',
    header: 'Status',
    accessor: 'status',
    sortable: true,
    cell: (row) => getStatusBadge(row.status),
  },
  {
    id: 'total_amount',
    header: 'Amount',
    sortable: true,
    className: 'text-right',
    cell: (row) => (
      <span className="font-medium text-sm">
        ${(row.total_amount ?? row.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
    ),
  },
];

// ---------------------------------------------------------------------------
// ExpensesList Page
// ---------------------------------------------------------------------------

export default function ExpensesList() {
  const navigate = useNavigate();
  const canCreate = useAccountingPermission('accounting_expenses_create');
  const canExport = useAccountingPermission('accounting_reports_export');

  // Filter state
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ExpenseStatus | 'all'>('all');
  const [page, setPage] = useState(1);
  const [selectedRows, setSelectedRows] = useState<string[]>([]);

  // Sorting
  const [sortColumn, setSortColumn] = useState<string | null>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>('desc');

  const handleSort = useCallback((column: string) => {
    if (sortColumn === column) {
      if (sortDirection === 'asc') setSortDirection('desc');
      else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      }
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  }, [sortColumn, sortDirection]);

  const sorting: SortingConfig = {
    column: sortColumn,
    direction: sortDirection,
    onSort: handleSort,
  };

  // Build filters
  const filters: ExpenseFilters = useMemo(() => ({
    search: search || undefined,
    status: statusFilter === 'all' ? undefined : statusFilter,
  }), [search, statusFilter]);

  const pagination: PaginationParams = { page, pageSize: 20 };

  // Queries
  const { data: expensesData, isLoading: expensesLoading } = useExpensesQuery(filters, pagination);
  // BUG-L02 fix: stats from separate aggregation query, NOT paginated subset
  const { data: aggregations, isLoading: aggLoading } = useExpenseAggregationsQuery();

  // Mutations
  const createMutation = useCreateExpenseMutation();

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreate = async (values: Record<string, any>) => {
    const amount = Number(values.amount);
    await createMutation.mutateAsync({
      expense_date: values.expense_date,
      amount,
      total_amount: amount,
      category: values.category || undefined,
      vendor: values.vendor || undefined,
      payment_method: values.payment_method || undefined,
      description: values.description || undefined,
      status: 'pending_approval',
    });
  };

  // Stats from aggregation query (BUG-L02 fix)
  const stats: StatCardData[] = useMemo(() => {
    if (!aggregations) return [];
    return [
      {
        label: 'Total Expenses',
        value: aggregations.totalCount,
        icon: <Receipt className="h-4 w-4" />,
        format: 'number' as const,
      },
      {
        label: 'Approved',
        value: aggregations.approvedCount,
        icon: <CheckCircle className="h-4 w-4" />,
        format: 'number' as const,
        subtitle: `$${aggregations.approvedAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      },
      {
        label: 'Pending',
        value: aggregations.pendingCount,
        icon: <Clock className="h-4 w-4" />,
        format: 'number' as const,
        alert: aggregations.pendingCount > 0,
        subtitle: `$${aggregations.pendingAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      },
      {
        label: 'Total Amount',
        value: aggregations.totalAmount,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency' as const,
      },
    ];
  }, [aggregations]);

  const expenses = expensesData?.data ?? [];

  // Filter controls
  const filterControls = (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search expenses..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="pl-10"
        />
      </div>
      <Select
        value={statusFilter}
        onValueChange={(v) => {
          setStatusFilter(v as ExpenseStatus | 'all');
          setPage(1);
        }}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All Statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="pending_approval">Pending Approval</SelectItem>
          <SelectItem value="approved">Approved</SelectItem>
          <SelectItem value="rejected">Rejected</SelectItem>
        </SelectContent>
      </Select>
      {canExport && expenses.length > 0 && (
        <Button variant="outline" size="sm" onClick={() => exportExpensesCSV(expenses)}>
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      )}
    </div>
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Receipt className="h-8 w-8" />
              Expenses
            </h1>
            <p className="text-muted-foreground mt-2">
              Track and manage business expenses
            </p>
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Expense
            </Button>
          )}
        </div>

        {/* Stat Cards (BUG-L02 fix: from aggregation query) */}
        <StatCards
          stats={stats}
          isLoading={aggLoading}
          columns={4}
          className="mb-6"
        />

        {/* Data Table */}
        <DataTable<ExpenseWithRelations>
          columns={COLUMNS}
          data={expenses}
          isLoading={expensesLoading}
          filters={filterControls}
          sorting={sorting}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
          pagination={
            expensesData
              ? {
                  page: expensesData.currentPage,
                  pageSize: expensesData.pageSize,
                  totalCount: expensesData.totalCount,
                  onPageChange: setPage,
                }
              : undefined
          }
          onRowClick={(row) => navigate(`/accounting/expenses/${row.id}`)}
          emptyMessage="No expenses found. Submit your first expense to start tracking."
        />

        {/* Create Modal */}
        <FormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Submit Expense"
          description="Enter expense details for approval."
          fields={CREATE_EXPENSE_FIELDS}
          onSubmit={handleCreate}
          isSubmitting={createMutation.isPending}
          submitLabel="Submit Expense"
        />
      </div>
    </DashboardLayout>
  );
}
