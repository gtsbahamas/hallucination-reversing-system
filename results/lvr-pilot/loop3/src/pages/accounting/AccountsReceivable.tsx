/**
 * AccountsReceivable — ACC-010
 *
 * Accounts receivable management page with outstanding invoices,
 * payment tracking, and aging summary.
 *
 * Bug fixes:
 *   BUG-H02: Uses `invoices` from useAccountsReceivableSummaryQuery, NOT `arTransactions`
 *
 * Architecture:
 *   - Thin wrapper around StatCards + DataTable
 *   - Uses useAccountsReceivableSummaryQuery for real invoice data
 *   - Permission-gated actions (create invoice, record payment)
 *   - DashboardLayout wrapper
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { StatCards } from '@/components/accounting/shared/StatCards';
import { DataTable, type ColumnDef } from '@/components/accounting/shared/DataTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Users,
  DollarSign,
  AlertTriangle,
  Clock,
  Search,
  Plus,
} from 'lucide-react';
import { useAccountsReceivableSummaryQuery } from '@/hooks/useAccountsReceivable';
import { useAccountingPermission } from '@/config/accountingPermissions';
import type { InvoiceWithRelations, InvoiceStatus } from '@/types/accounting';
import { format } from 'date-fns';

// ---------------------------------------------------------------------------
// Status badge colors
// ---------------------------------------------------------------------------

const STATUS_BADGE_CONFIG: Record<string, { label: string; className: string }> = {
  draft: { label: 'Draft', className: 'bg-gray-100 text-gray-800' },
  sent: { label: 'Sent', className: 'bg-blue-100 text-blue-800' },
  paid: { label: 'Paid', className: 'bg-green-100 text-green-800' },
  overdue: { label: 'Overdue', className: 'bg-red-100 text-red-800' },
  cancelled: { label: 'Cancelled', className: 'bg-gray-100 text-gray-800' },
};

function getStatusBadge(status: string) {
  const config = STATUS_BADGE_CONFIG[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-800',
  };
  return <Badge className={config.className}>{config.label}</Badge>;
}

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
      <span className="font-mono font-medium">{row.invoice_number}</span>
    ),
  },
  {
    id: 'customer',
    header: 'Customer',
    sortable: true,
    cell: (row) => {
      const customer = row.customers;
      if (!customer) return <span className="text-muted-foreground">N/A</span>;
      const name = customer.company_name
        ? customer.company_name
        : `${customer.first_name} ${customer.last_name}`;
      return <span>{name}</span>;
    },
  },
  {
    id: 'invoice_date',
    header: 'Date',
    accessor: 'invoice_date',
    sortable: true,
    cell: (_row, value) =>
      value ? format(new Date(value as string), 'MMM dd, yyyy') : '-',
  },
  {
    id: 'due_date',
    header: 'Due Date',
    accessor: 'due_date',
    sortable: true,
    cell: (row, value) => {
      if (!value) return '-';
      const dueDate = new Date(value as string);
      const isOverdue = row.status !== 'paid' && dueDate < new Date();
      return (
        <span className={isOverdue ? 'text-red-600 font-medium' : ''}>
          {format(dueDate, 'MMM dd, yyyy')}
        </span>
      );
    },
  },
  {
    id: 'total_amount',
    header: 'Total',
    accessor: 'total_amount',
    sortable: true,
    className: 'text-right',
    cell: (_row, value) =>
      new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format((value as number) ?? 0),
  },
  {
    id: 'balance_due',
    header: 'Balance Due',
    accessor: 'balance_due',
    sortable: true,
    className: 'text-right',
    cell: (_row, value) => {
      const amount = (value as number) ?? 0;
      return (
        <span className={amount > 0 ? 'text-red-600 font-medium' : ''}>
          {new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
          }).format(amount)}
        </span>
      );
    },
  },
  {
    id: 'status',
    header: 'Status',
    accessor: 'status',
    sortable: true,
    cell: (_row, value) => getStatusBadge(value as string),
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const AccountsReceivable = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // BUG-H02 FIX: Destructure `invoices`, NOT `arTransactions`
  const { data: arSummary, isLoading } = useAccountsReceivableSummaryQuery();

  // Permission checks
  const canCreateInvoice = useAccountingPermission('accounting_invoices_create');

  // Filter invoices based on search and status
  const filteredInvoices = useMemo(() => {
    if (!arSummary?.invoices) return [];

    let filtered = arSummary.invoices;

    if (statusFilter !== 'all') {
      filtered = filtered.filter((inv) => inv.status === statusFilter);
    }

    if (searchTerm) {
      const lower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (inv) =>
          inv.invoice_number.toLowerCase().includes(lower) ||
          inv.customers?.first_name?.toLowerCase().includes(lower) ||
          inv.customers?.last_name?.toLowerCase().includes(lower) ||
          inv.customers?.company_name?.toLowerCase().includes(lower) ||
          inv.customers?.email?.toLowerCase().includes(lower)
      );
    }

    return filtered;
  }, [arSummary?.invoices, searchTerm, statusFilter]);

  const handleRowClick = useCallback(
    (invoice: InvoiceWithRelations) => {
      navigate(`/accounting/invoices/${invoice.id}`);
    },
    [navigate]
  );

  // Build stat cards from real AR summary data
  const stats = [
    {
      label: 'Total Outstanding',
      value: arSummary?.totalOutstanding ?? 0,
      format: 'currency' as const,
      icon: <DollarSign className="h-4 w-4" />,
      subtitle: `${arSummary?.invoices?.length ?? 0} open invoices`,
    },
    {
      label: 'Overdue',
      value: arSummary?.totalOverdue ?? 0,
      format: 'currency' as const,
      icon: <AlertTriangle className="h-4 w-4" />,
      alert: (arSummary?.totalOverdue ?? 0) > 0,
      subtitle: 'Past due date',
    },
    {
      label: 'Current (0-30 days)',
      value: arSummary?.aging?.current ?? 0,
      format: 'currency' as const,
      icon: <Clock className="h-4 w-4" />,
      subtitle: 'Within terms',
    },
    {
      label: '90+ Days',
      value: (arSummary?.aging?.['90'] ?? 0) + (arSummary?.aging?.['90+'] ?? 0),
      format: 'currency' as const,
      icon: <AlertTriangle className="h-4 w-4" />,
      alert: ((arSummary?.aging?.['90'] ?? 0) + (arSummary?.aging?.['90+'] ?? 0)) > 0,
      subtitle: 'Collection risk',
    },
  ];

  // Aging breakdown card
  const agingBuckets = [
    { label: 'Current (0-30)', amount: arSummary?.aging?.current ?? 0 },
    { label: '31-60 Days', amount: arSummary?.aging?.['30'] ?? 0 },
    { label: '61-90 Days', amount: arSummary?.aging?.['60'] ?? 0 },
    { label: '91-120 Days', amount: arSummary?.aging?.['90'] ?? 0 },
    { label: '120+ Days', amount: arSummary?.aging?.['90+'] ?? 0 },
  ];

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Users className="h-8 w-8" />
              Accounts Receivable
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage customer invoices, payments, and collections
            </p>
          </div>
          {canCreateInvoice && (
            <Button onClick={() => navigate('/accounting/invoices')}>
              <Plus className="h-4 w-4 mr-2" />
              New Invoice
            </Button>
          )}
        </div>

        {/* Summary Stats */}
        <StatCards stats={stats} isLoading={isLoading} columns={4} className="mb-6" />

        {/* Aging Breakdown */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Aging Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              {agingBuckets.map((bucket) => (
                <div key={bucket.label} className="text-center">
                  <p className="text-xs text-muted-foreground mb-1">{bucket.label}</p>
                  <p
                    className={`text-lg font-semibold ${
                      bucket.amount > 0 && bucket.label !== 'Current (0-30)'
                        ? 'text-red-600'
                        : ''
                    }`}
                  >
                    {new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }).format(bucket.amount)}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Outstanding Invoices Table */}
        <DataTable
          columns={COLUMNS}
          data={filteredInvoices}
          isLoading={isLoading}
          onRowClick={handleRowClick}
          emptyMessage="No outstanding invoices found."
          filters={
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search invoices..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          }
        />
      </div>
    </DashboardLayout>
  );
};

export default AccountsReceivable;
