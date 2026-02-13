/**
 * BillsList (ACC-003)
 *
 * List page similar to InvoicesList with DataTable, StatCards, filters,
 * create modal, CSV export.
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
  useBillsQuery,
  useCreateBillMutation,
} from '@/hooks/useBills';
import {
  useAccountingPermission,
} from '@/config/accountingPermissions';
import type {
  BillWithRelations,
  BillFilters,
  BillStatus,
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
  FileText,
  Plus,
  DollarSign,
  CheckCircle,
  AlertTriangle,
  Search,
  Download,
  Clock,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800' },
  approved: { label: 'Approved', className: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
  overdue: { label: 'Overdue', className: 'bg-red-100 text-red-800' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
};

function getStatusBadge(status: string) {
  const config = STATUS_CONFIG[status] ?? { label: status, className: 'bg-gray-100 text-gray-800' };
  return <Badge className={config.className}>{config.label}</Badge>;
}

// ---------------------------------------------------------------------------
// CSV export
// ---------------------------------------------------------------------------

function exportBillsCSV(bills: BillWithRelations[]) {
  const headers = ['Bill #', 'Supplier', 'Date', 'Due Date', 'Status', 'Total', 'Balance Due'];
  const rows = bills.map((bill) => [
    bill.bill_number,
    bill.suppliers?.name ?? 'N/A',
    bill.bill_date,
    bill.due_date,
    bill.status,
    bill.total_amount.toFixed(2),
    bill.balance_due.toFixed(2),
  ]);

  const csvContent =
    'data:text/csv;charset=utf-8,' +
    headers.join(',') +
    '\n' +
    rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `bills-${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Create Bill form fields
// ---------------------------------------------------------------------------

const CREATE_BILL_FIELDS: FormFieldConfig[] = [
  {
    name: 'supplier_id',
    label: 'Supplier',
    type: 'text',
    placeholder: 'Supplier ID',
    required: true,
  },
  {
    name: 'bill_number',
    label: 'Bill Number',
    type: 'text',
    required: true,
    placeholder: 'BILL-00001',
  },
  {
    name: 'bill_date',
    label: 'Bill Date',
    type: 'date',
    required: true,
    defaultValue: new Date().toISOString().split('T')[0],
  },
  {
    name: 'due_date',
    label: 'Due Date',
    type: 'date',
    required: true,
  },
  {
    name: 'subtotal',
    label: 'Subtotal',
    type: 'number',
    required: true,
    min: 0,
    step: 0.01,
  },
  {
    name: 'tax_amount',
    label: 'Tax Amount',
    type: 'number',
    min: 0,
    step: 0.01,
    defaultValue: 0,
  },
  {
    name: 'notes',
    label: 'Notes',
    type: 'textarea',
    colSpan: 'col-span-2',
  },
];

// ---------------------------------------------------------------------------
// Column definitions
// ---------------------------------------------------------------------------

const COLUMNS: ColumnDef<BillWithRelations>[] = [
  {
    id: 'bill_number',
    header: 'Bill #',
    accessor: 'bill_number',
    sortable: true,
    cell: (row) => <span className="font-mono font-medium text-sm">{row.bill_number}</span>,
  },
  {
    id: 'supplier',
    header: 'Supplier',
    cell: (row) => (
      <span className="font-medium text-sm">{row.suppliers?.name ?? 'N/A'}</span>
    ),
  },
  {
    id: 'bill_date',
    header: 'Bill Date',
    accessor: 'bill_date',
    sortable: true,
    cell: (row) => <span className="text-sm">{new Date(row.bill_date).toLocaleDateString()}</span>,
  },
  {
    id: 'due_date',
    header: 'Due Date',
    accessor: 'due_date',
    sortable: true,
    cell: (row) => {
      const isOverdue = row.status !== 'paid' && row.status !== 'cancelled' && new Date(row.due_date) < new Date();
      return (
        <span className={`text-sm ${isOverdue ? 'text-red-600 font-medium' : ''}`}>
          {new Date(row.due_date).toLocaleDateString()}
        </span>
      );
    },
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
    header: 'Total',
    accessor: 'total_amount',
    sortable: true,
    className: 'text-right',
    cell: (row) => (
      <span className="font-medium text-sm">
        ${row.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
    ),
  },
  {
    id: 'balance_due',
    header: 'Balance',
    accessor: 'balance_due',
    sortable: true,
    className: 'text-right',
    cell: (row) => (
      <span className={`text-sm ${row.balance_due > 0 ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
        ${row.balance_due.toLocaleString('en-US', { minimumFractionDigits: 2 })}
      </span>
    ),
  },
];

// ---------------------------------------------------------------------------
// BillsList Page
// ---------------------------------------------------------------------------

export default function BillsList() {
  const navigate = useNavigate();
  const canCreate = useAccountingPermission('accounting_bills_create');
  const canExport = useAccountingPermission('accounting_reports_export');

  // Filter state
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<BillStatus | 'all'>('all');
  const [page, setPage] = useState(1);
  const [selectedRows, setSelectedRows] = useState<string[]>([]);

  // Sorting
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc' | null>(null);

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
  const filters: BillFilters = useMemo(() => ({
    search: search || undefined,
    status: statusFilter === 'all' ? undefined : statusFilter,
  }), [search, statusFilter]);

  const pagination: PaginationParams = { page, pageSize: 20 };

  // Queries
  const { data: billsData, isLoading } = useBillsQuery(filters, pagination);

  // Mutations
  const createMutation = useCreateBillMutation();

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreate = async (values: Record<string, any>) => {
    const subtotal = Number(values.subtotal);
    const taxAmount = Number(values.tax_amount ?? 0);
    await createMutation.mutateAsync({
      supplier_id: values.supplier_id,
      bill_number: values.bill_number,
      bill_date: values.bill_date,
      due_date: values.due_date,
      subtotal,
      tax_amount: taxAmount,
      total_amount: subtotal + taxAmount,
      notes: values.notes || undefined,
    });
  };

  const bills = billsData?.data ?? [];

  // Compute stats from full query data (since bills hook doesn't have separate aggregation)
  const stats: StatCardData[] = useMemo(() => {
    const totalCount = billsData?.totalCount ?? 0;
    const totalAmount = bills.reduce((s, b) => s + b.total_amount, 0);
    const paidCount = bills.filter((b) => b.status === 'paid').length;
    const overdueCount = bills.filter((b) => b.status === 'overdue').length;
    const outstandingAmount = bills.filter((b) => b.status !== 'paid' && b.status !== 'cancelled')
      .reduce((s, b) => s + b.balance_due, 0);

    return [
      {
        label: 'Total Bills',
        value: totalCount,
        icon: <FileText className="h-4 w-4" />,
        format: 'number' as const,
      },
      {
        label: 'Paid',
        value: paidCount,
        icon: <CheckCircle className="h-4 w-4" />,
        format: 'number' as const,
      },
      {
        label: 'Overdue',
        value: overdueCount,
        icon: <AlertTriangle className="h-4 w-4" />,
        format: 'number' as const,
        alert: overdueCount > 0,
      },
      {
        label: 'Outstanding',
        value: outstandingAmount,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency' as const,
      },
    ];
  }, [bills, billsData?.totalCount]);

  // Filter controls
  const filterControls = (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search bills..."
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
          setStatusFilter(v as BillStatus | 'all');
          setPage(1);
        }}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
          <SelectItem value="approved">Approved</SelectItem>
          <SelectItem value="paid">Paid</SelectItem>
          <SelectItem value="overdue">Overdue</SelectItem>
          <SelectItem value="cancelled">Cancelled</SelectItem>
        </SelectContent>
      </Select>
      {canExport && bills.length > 0 && (
        <Button variant="outline" size="sm" onClick={() => exportBillsCSV(bills)}>
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
              <FileText className="h-8 w-8" />
              Bills
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage vendor bills and payments
            </p>
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Bill
            </Button>
          )}
        </div>

        {/* Stat Cards */}
        <StatCards stats={stats} isLoading={isLoading} columns={4} className="mb-6" />

        {/* Data Table */}
        <DataTable<BillWithRelations>
          columns={COLUMNS}
          data={bills}
          isLoading={isLoading}
          filters={filterControls}
          sorting={sorting}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
          pagination={
            billsData
              ? {
                  page: billsData.currentPage,
                  pageSize: billsData.pageSize,
                  totalCount: billsData.totalCount,
                  onPageChange: setPage,
                }
              : undefined
          }
          onRowClick={(row) => navigate(`/accounting/bills/${row.id}`)}
          emptyMessage="No bills found. Create your first bill to start tracking vendor expenses."
        />

        {/* Create Modal */}
        <FormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Bill"
          description="Enter vendor bill details."
          fields={CREATE_BILL_FIELDS}
          onSubmit={handleCreate}
          isSubmitting={createMutation.isPending}
          submitLabel="Create Bill"
        />
      </div>
    </DashboardLayout>
  );
}
