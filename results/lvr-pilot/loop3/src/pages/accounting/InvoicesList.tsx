/**
 * InvoicesList (ACC-001)
 *
 * Full list page with DataTable, StatCards, filters, create modal, CSV export.
 *
 * Bug fixes applied:
 *   BUG-L02: Stats from aggregation queries, not paginated subset
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
  useInvoicesQuery,
  useInvoiceAggregationsQuery,
  useCreateInvoiceMutation,
} from '@/hooks/useInvoices';
import {
  useAccountingPermission,
  useAccountingPermissions,
} from '@/config/accountingPermissions';
import type {
  InvoiceWithRelations,
  InvoiceFilters,
  InvoiceStatus,
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
  AlertTriangle,
  Search,
  Download,
  Clock,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
  sent: { label: 'Sent', className: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
  overdue: { label: 'Overdue', className: 'bg-red-100 text-red-800' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
};

function getStatusBadge(status: string) {
  const config = STATUS_CONFIG[status] ?? { label: status, className: 'bg-gray-100 text-gray-800' };
  return <Badge className={config.className}>{config.label}</Badge>;
}

// ---------------------------------------------------------------------------
// CSV export utility
// ---------------------------------------------------------------------------

function exportInvoicesCSV(invoices: InvoiceWithRelations[]) {
  const headers = ['Invoice #', 'Customer', 'Date', 'Due Date', 'Status', 'Total', 'Balance Due'];
  const rows = invoices.map((inv) => [
    inv.invoice_number,
    inv.customers
      ? `${inv.customers.first_name} ${inv.customers.last_name}`
      : 'N/A',
    inv.invoice_date,
    inv.due_date,
    inv.status,
    inv.total_amount.toFixed(2),
    inv.balance_due.toFixed(2),
  ]);

  const csvContent =
    'data:text/csv;charset=utf-8,' +
    headers.join(',') +
    '\n' +
    rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `invoices-${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Create Invoice form fields
// ---------------------------------------------------------------------------

const CREATE_INVOICE_FIELDS: FormFieldConfig[] = [
  {
    name: 'customer_id',
    label: 'Customer',
    type: 'text',
    placeholder: 'Customer ID',
    required: true,
  },
  {
    name: 'invoice_date',
    label: 'Invoice Date',
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
    placeholder: '0.00',
  },
  {
    name: 'tax_amount',
    label: 'Tax Amount',
    type: 'number',
    min: 0,
    step: 0.01,
    defaultValue: 0,
    placeholder: '0.00',
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

const COLUMNS: ColumnDef<InvoiceWithRelations>[] = [
  {
    id: 'invoice_number',
    header: 'Invoice #',
    accessor: 'invoice_number',
    sortable: true,
    cell: (row) => (
      <span className="font-mono font-medium text-sm">{row.invoice_number}</span>
    ),
  },
  {
    id: 'customer',
    header: 'Customer',
    cell: (row) => {
      if (!row.customers) return <span className="text-muted-foreground">N/A</span>;
      return (
        <div>
          <p className="font-medium text-sm">
            {row.customers.first_name} {row.customers.last_name}
          </p>
          {row.customers.company_name && (
            <p className="text-xs text-muted-foreground">{row.customers.company_name}</p>
          )}
        </div>
      );
    },
  },
  {
    id: 'invoice_date',
    header: 'Date',
    accessor: 'invoice_date',
    sortable: true,
    cell: (row) => (
      <span className="text-sm">
        {new Date(row.invoice_date).toLocaleDateString()}
      </span>
    ),
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
// InvoicesList Page
// ---------------------------------------------------------------------------

export default function InvoicesList() {
  const navigate = useNavigate();
  const canCreate = useAccountingPermission('accounting_invoices_create');
  const canExport = useAccountingPermission('accounting_reports_export');

  // Filter state
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<InvoiceStatus | 'all'>('all');
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
  const filters: InvoiceFilters = useMemo(() => ({
    search: search || undefined,
    status: statusFilter === 'all' ? undefined : statusFilter,
  }), [search, statusFilter]);

  const pagination: PaginationParams = { page, pageSize: 20 };

  // Queries
  const { data: invoicesData, isLoading: invoicesLoading } = useInvoicesQuery(filters, pagination);
  const { data: aggregations, isLoading: aggLoading } = useInvoiceAggregationsQuery();

  // Mutations
  const createMutation = useCreateInvoiceMutation();

  // Create modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreate = async (values: Record<string, any>) => {
    const subtotal = Number(values.subtotal);
    const taxAmount = Number(values.tax_amount ?? 0);
    await createMutation.mutateAsync({
      customer_id: values.customer_id,
      invoice_date: values.invoice_date,
      due_date: values.due_date,
      subtotal,
      tax_amount: taxAmount,
      total_amount: subtotal + taxAmount,
      notes: values.notes || undefined,
      line_items: [],
    });
  };

  // Stats from aggregation query (BUG-L02 fix: NOT from paginated data)
  const stats: StatCardData[] = useMemo(() => {
    if (!aggregations) return [];
    return [
      {
        label: 'Total Invoices',
        value: aggregations.totalCount,
        icon: <Receipt className="h-4 w-4" />,
        format: 'number' as const,
      },
      {
        label: 'Paid',
        value: aggregations.paidCount,
        icon: <CheckCircle className="h-4 w-4" />,
        format: 'number' as const,
        subtitle: `$${aggregations.paidAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      },
      {
        label: 'Overdue',
        value: aggregations.overdueCount,
        icon: <AlertTriangle className="h-4 w-4" />,
        format: 'number' as const,
        alert: aggregations.overdueCount > 0,
        subtitle: `$${aggregations.overdueAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}`,
      },
      {
        label: 'Outstanding',
        value: aggregations.outstandingAmount,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency' as const,
        subtitle: `${aggregations.outstandingCount} invoice${aggregations.outstandingCount !== 1 ? 's' : ''}`,
      },
    ];
  }, [aggregations]);

  const invoices = invoicesData?.data ?? [];

  // Filter controls
  const filterControls = (
    <div className="flex flex-col sm:flex-row gap-3">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
        <Input
          placeholder="Search invoices..."
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
          setStatusFilter(v as InvoiceStatus | 'all');
          setPage(1);
        }}
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="All Statuses" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="sent">Sent</SelectItem>
          <SelectItem value="paid">Paid</SelectItem>
          <SelectItem value="overdue">Overdue</SelectItem>
          <SelectItem value="cancelled">Cancelled</SelectItem>
        </SelectContent>
      </Select>
      {canExport && invoices.length > 0 && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => exportInvoicesCSV(invoices)}
        >
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
              Invoices
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage customer invoices and track payments
            </p>
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Invoice
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
        <DataTable<InvoiceWithRelations>
          columns={COLUMNS}
          data={invoices}
          isLoading={invoicesLoading}
          filters={filterControls}
          sorting={sorting}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
          pagination={
            invoicesData
              ? {
                  page: invoicesData.currentPage,
                  pageSize: invoicesData.pageSize,
                  totalCount: invoicesData.totalCount,
                  onPageChange: setPage,
                }
              : undefined
          }
          onRowClick={(row) => navigate(`/accounting/invoices/${row.id}`)}
          emptyMessage="No invoices found. Create your first invoice to start billing customers."
        />

        {/* Create Invoice Modal */}
        <FormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Invoice"
          description="Create a new invoice for a customer."
          fields={CREATE_INVOICE_FIELDS}
          onSubmit={handleCreate}
          isSubmitting={createMutation.isPending}
          submitLabel="Create Invoice"
        />
      </div>
    </DashboardLayout>
  );
}
