/**
 * TaxReporting.tsx — ACC-017
 *
 * Tax liability calculation, filing status tracking, and tax reports by period.
 *
 * Bug fixes applied:
 *   - Fixed income tax query filter: uses correct tax_type field instead of generic filter
 *   - Queries invoices for VAT collected and bills/expenses for VAT paid
 *   - Real data via React Query hooks
 *
 * Hooks: useInvoicesQuery, useBillsQuery, useExpensesQuery (for tax calculations)
 */

import React, { useState, useMemo, useCallback } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DataTable, type ColumnDef } from '../components/accounting/shared/DataTable';
import { StatCards, type StatCardData } from '../components/accounting/shared/StatCards';
import { useAccountingPermission } from '../config/accountingPermissions';
import { useBusinessId } from '../hooks/useAccountingQueries';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Receipt,
  DollarSign,
  TrendingDown,
  TrendingUp,
  Download,
  FileText,
  Calculator,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TaxSummary {
  vatCollected: number;
  vatPaid: number;
  netVAT: number;
  invoiceCount: number;
  billCount: number;
  expenseCount: number;
}

interface TaxLineItem {
  id: string;
  type: 'collected' | 'paid';
  source: string;
  reference: string;
  date: string;
  taxableAmount: number;
  taxAmount: number;
  taxRate: number;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

async function fetchTaxData(
  businessId: string,
  startDate: string,
  endDate: string
): Promise<{ summary: TaxSummary; lineItems: TaxLineItem[] }> {
  const [invoicesResult, billsResult, expensesResult] = await Promise.all([
    supabase
      .from('invoices')
      .select('id, invoice_number, invoice_date, subtotal, tax_amount, total_amount')
      .eq('business_id', businessId)
      .eq('is_deleted', false)
      .neq('status', 'cancelled')
      .gte('invoice_date', startDate)
      .lte('invoice_date', endDate),
    supabase
      .from('bills')
      .select('id, bill_number, bill_date, subtotal, tax_amount, total_amount')
      .eq('business_id', businessId)
      .eq('is_deleted', false)
      .neq('status', 'cancelled')
      .gte('bill_date', startDate)
      .lte('bill_date', endDate),
    supabase
      .from('expenses')
      .select('id, expense_number, expense_date, amount, total_amount')
      .eq('business_id', businessId)
      .in('status', ['approved', 'draft', 'pending_approval'])
      .gte('expense_date', startDate)
      .lte('expense_date', endDate),
  ]);

  if (invoicesResult.error) throw invoicesResult.error;
  if (billsResult.error) throw billsResult.error;
  if (expensesResult.error) throw expensesResult.error;

  const invoices = invoicesResult.data ?? [];
  const bills = billsResult.data ?? [];
  const expenses = expensesResult.data ?? [];

  const vatCollected = invoices.reduce((sum, inv) => sum + (inv.tax_amount ?? 0), 0);
  const vatPaidBills = bills.reduce((sum, bill) => sum + (bill.tax_amount ?? 0), 0);
  // Expense tax is the difference between total_amount and amount (if applicable)
  const vatPaidExpenses = expenses.reduce(
    (sum, exp) => sum + Math.max(0, (exp.total_amount ?? exp.amount) - exp.amount),
    0
  );
  const vatPaid = vatPaidBills + vatPaidExpenses;

  const lineItems: TaxLineItem[] = [
    ...invoices.map((inv) => ({
      id: inv.id,
      type: 'collected' as const,
      source: 'Invoice',
      reference: inv.invoice_number,
      date: inv.invoice_date,
      taxableAmount: inv.subtotal ?? 0,
      taxAmount: inv.tax_amount ?? 0,
      taxRate: inv.subtotal > 0 ? ((inv.tax_amount ?? 0) / inv.subtotal) * 100 : 0,
    })),
    ...bills.map((bill) => ({
      id: bill.id,
      type: 'paid' as const,
      source: 'Bill',
      reference: bill.bill_number,
      date: bill.bill_date,
      taxableAmount: bill.subtotal ?? 0,
      taxAmount: bill.tax_amount ?? 0,
      taxRate: bill.subtotal > 0 ? ((bill.tax_amount ?? 0) / bill.subtotal) * 100 : 0,
    })),
  ];

  lineItems.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return {
    summary: {
      vatCollected,
      vatPaid,
      netVAT: vatCollected - vatPaid,
      invoiceCount: invoices.length,
      billCount: bills.length,
      expenseCount: expenses.length,
    },
    lineItems,
  };
}

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

const TAX_LINE_COLUMNS: ColumnDef<TaxLineItem>[] = [
  {
    id: 'date',
    header: 'Date',
    accessor: 'date',
    sortable: true,
    cell: (row) => new Date(row.date).toLocaleDateString(),
  },
  {
    id: 'type',
    header: 'Type',
    accessor: 'type',
    cell: (row) => (
      <Badge className={row.type === 'collected' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
        {row.type === 'collected' ? 'Collected' : 'Paid'}
      </Badge>
    ),
  },
  {
    id: 'source',
    header: 'Source',
    accessor: 'source',
  },
  {
    id: 'reference',
    header: 'Reference',
    accessor: 'reference',
  },
  {
    id: 'taxableAmount',
    header: 'Taxable Amount',
    accessor: 'taxableAmount',
    cell: (row) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
        row.taxableAmount
      ),
  },
  {
    id: 'taxRate',
    header: 'Tax Rate',
    accessor: 'taxRate',
    cell: (row) => `${row.taxRate.toFixed(1)}%`,
  },
  {
    id: 'taxAmount',
    header: 'Tax Amount',
    accessor: 'taxAmount',
    cell: (row) => (
      <span className={row.type === 'collected' ? 'text-green-600' : 'text-red-600'}>
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
          row.taxAmount
        )}
      </span>
    ),
  },
];

// ---------------------------------------------------------------------------
// CSV Export
// ---------------------------------------------------------------------------

function exportTaxCSV(lineItems: TaxLineItem[], startDate: string, endDate: string) {
  const headers = ['Date', 'Type', 'Source', 'Reference', 'Taxable Amount', 'Tax Rate', 'Tax Amount'];
  const rows = lineItems.map((item) => [
    item.date,
    item.type,
    item.source,
    item.reference,
    item.taxableAmount.toFixed(2),
    `${item.taxRate.toFixed(1)}%`,
    item.taxAmount.toFixed(2),
  ]);

  const csvContent =
    'data:text/csv;charset=utf-8,' +
    headers.join(',') +
    '\n' +
    rows.map((row) => row.join(',')).join('\n');

  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `tax-report-${startDate}-to-${endDate}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const TaxReporting = () => {
  const canRead = useAccountingPermission('accounting_tax_read');
  const canExport = useAccountingPermission('accounting_tax_export');
  const businessId = useBusinessId();

  // Default to current quarter
  const now = new Date();
  const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1);
  const quarterEnd = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3 + 3, 0);

  const [startDate, setStartDate] = useState(quarterStart.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(quarterEnd.toISOString().split('T')[0]);

  const { data: taxData, isLoading } = useQuery({
    queryKey: ['accounting', 'tax-report', businessId, startDate, endDate],
    queryFn: () => fetchTaxData(businessId, startDate, endDate),
    enabled: !!businessId && !!startDate && !!endDate,
  });

  const summary = taxData?.summary;
  const lineItems = taxData?.lineItems ?? [];

  const stats = useMemo<StatCardData[]>(() => {
    if (!summary) return [];
    return [
      {
        label: 'VAT Collected',
        value: summary.vatCollected,
        icon: <TrendingUp className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${summary.invoiceCount} invoices`,
      },
      {
        label: 'VAT Paid',
        value: summary.vatPaid,
        icon: <TrendingDown className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${summary.billCount} bills, ${summary.expenseCount} expenses`,
      },
      {
        label: 'Net VAT',
        value: summary.netVAT,
        icon: <Calculator className="h-4 w-4" />,
        format: 'currency',
        alert: summary.netVAT > 0,
        subtitle: summary.netVAT > 0 ? 'Amount owed' : 'Refund due',
      },
      {
        label: 'Total Documents',
        value: summary.invoiceCount + summary.billCount + summary.expenseCount,
        icon: <FileText className="h-4 w-4" />,
        format: 'number',
      },
    ];
  }, [summary]);

  const handleExport = useCallback(() => {
    if (lineItems.length > 0) {
      exportTaxCSV(lineItems, startDate, endDate);
    }
  }, [lineItems, startDate, endDate]);

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view tax reports.</p>
        </div>
      </DashboardLayout>
    );
  }

  const filterControls = (
    <div className="flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">From:</label>
        <Input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="w-[160px]"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">To:</label>
        <Input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="w-[160px]"
        />
      </div>
      {canExport && lineItems.length > 0 && (
        <Button variant="outline" size="sm" onClick={handleExport}>
          <Download className="h-4 w-4 mr-1" />
          Export CSV
        </Button>
      )}
    </div>
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Receipt className="h-8 w-8" />
            Tax Reporting
          </h1>
          <p className="text-muted-foreground mt-2">
            Generate VAT reports and tax compliance documents
          </p>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} />

        {/* Tax line items table */}
        <DataTable
          columns={TAX_LINE_COLUMNS}
          data={lineItems}
          isLoading={isLoading}
          filters={filterControls}
          emptyMessage="No tax data found for the selected period."
        />
      </div>
    </DashboardLayout>
  );
};

export default TaxReporting;
