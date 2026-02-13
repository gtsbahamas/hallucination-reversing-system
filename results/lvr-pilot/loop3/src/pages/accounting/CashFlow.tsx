/**
 * CashFlow.tsx — ACC-019
 *
 * Cash flow statement with date range filters. Displays inflows (invoices),
 * outflows (bills, expenses), and net cash position.
 *
 * This page was CLEAN in Loop 1 (no bugs). Preserved behavior with upgraded
 * architecture (React Query, shared components, permission guards).
 *
 * Hooks: useFinancialSummaryQuery (for cash balance), inline queries for cash flow data
 */

import React, { useState, useMemo } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DataTable, type ColumnDef } from '../components/accounting/shared/DataTable';
import { StatCards, type StatCardData } from '../components/accounting/shared/StatCards';
import { useAccountingPermission } from '../config/accountingPermissions';
import { useBusinessId, AGGREGATION_STALE_TIME } from '../hooks/useAccountingQueries';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CashFlowItem {
  id: string;
  date: string;
  description: string;
  category: 'inflow' | 'outflow';
  source: string;
  reference: string;
  amount: number;
}

interface CashFlowSummary {
  totalInflows: number;
  totalOutflows: number;
  netCashFlow: number;
  inflowCount: number;
  outflowCount: number;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

async function fetchCashFlowData(
  businessId: string,
  startDate: string,
  endDate: string
): Promise<{ summary: CashFlowSummary; items: CashFlowItem[] }> {
  const [invoicesResult, billsResult, expensesResult] = await Promise.all([
    // Inflows: paid invoices (payments received)
    supabase
      .from('invoices')
      .select('id, invoice_number, invoice_date, amount_paid')
      .eq('business_id', businessId)
      .eq('is_deleted', false)
      .gt('amount_paid', 0)
      .gte('invoice_date', startDate)
      .lte('invoice_date', endDate),
    // Outflows: paid bills
    supabase
      .from('bills')
      .select('id, bill_number, bill_date, amount_paid, suppliers(name)')
      .eq('business_id', businessId)
      .eq('is_deleted', false)
      .gt('amount_paid', 0)
      .gte('bill_date', startDate)
      .lte('bill_date', endDate),
    // Outflows: approved expenses
    supabase
      .from('expenses')
      .select('id, expense_number, expense_date, amount, category')
      .eq('business_id', businessId)
      .eq('status', 'approved')
      .gte('expense_date', startDate)
      .lte('expense_date', endDate),
  ]);

  if (invoicesResult.error) throw invoicesResult.error;
  if (billsResult.error) throw billsResult.error;
  if (expensesResult.error) throw expensesResult.error;

  const invoices = invoicesResult.data ?? [];
  const bills = billsResult.data ?? [];
  const expenses = expensesResult.data ?? [];

  const items: CashFlowItem[] = [
    ...invoices.map((inv) => ({
      id: inv.id,
      date: inv.invoice_date,
      description: `Payment received - ${inv.invoice_number}`,
      category: 'inflow' as const,
      source: 'Invoice Payment',
      reference: inv.invoice_number,
      amount: inv.amount_paid ?? 0,
    })),
    ...bills.map((bill: any) => ({
      id: bill.id,
      date: bill.bill_date,
      description: `Bill payment - ${bill.bill_number}${bill.suppliers?.name ? ` (${bill.suppliers.name})` : ''}`,
      category: 'outflow' as const,
      source: 'Bill Payment',
      reference: bill.bill_number,
      amount: bill.amount_paid ?? 0,
    })),
    ...expenses.map((exp) => ({
      id: exp.id,
      date: exp.expense_date,
      description: `Expense - ${exp.category ?? 'General'}`,
      category: 'outflow' as const,
      source: 'Expense',
      reference: exp.expense_number,
      amount: exp.amount ?? 0,
    })),
  ];

  items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  const totalInflows = items
    .filter((i) => i.category === 'inflow')
    .reduce((s, i) => s + i.amount, 0);
  const totalOutflows = items
    .filter((i) => i.category === 'outflow')
    .reduce((s, i) => s + i.amount, 0);

  return {
    summary: {
      totalInflows,
      totalOutflows,
      netCashFlow: totalInflows - totalOutflows,
      inflowCount: items.filter((i) => i.category === 'inflow').length,
      outflowCount: items.filter((i) => i.category === 'outflow').length,
    },
    items,
  };
}

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

const CASH_FLOW_COLUMNS: ColumnDef<CashFlowItem>[] = [
  {
    id: 'date',
    header: 'Date',
    accessor: 'date',
    sortable: true,
    cell: (row) => new Date(row.date).toLocaleDateString(),
  },
  {
    id: 'category',
    header: 'Type',
    accessor: 'category',
    cell: (row) =>
      row.category === 'inflow' ? (
        <Badge className="bg-green-100 text-green-800">
          <ArrowUpRight className="h-3 w-3 mr-1" />
          Inflow
        </Badge>
      ) : (
        <Badge className="bg-red-100 text-red-800">
          <ArrowDownRight className="h-3 w-3 mr-1" />
          Outflow
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
    id: 'description',
    header: 'Description',
    accessor: 'description',
  },
  {
    id: 'amount',
    header: 'Amount',
    accessor: 'amount',
    sortable: true,
    cell: (row) => (
      <span className={row.category === 'inflow' ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
        {row.category === 'inflow' ? '+' : '-'}
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(row.amount)}
      </span>
    ),
  },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const CashFlow = () => {
  const canRead = useAccountingPermission('accounting_cash_flow_read');
  const businessId = useBusinessId();

  // Default to last 30 days
  const today = new Date();
  const thirtyDaysAgo = new Date(today);
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  const [startDate, setStartDate] = useState(thirtyDaysAgo.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(today.toISOString().split('T')[0]);

  const { data: cashFlowData, isLoading } = useQuery({
    queryKey: ['accounting', 'cash-flow', businessId, startDate, endDate],
    queryFn: () => fetchCashFlowData(businessId, startDate, endDate),
    enabled: !!businessId && !!startDate && !!endDate,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const summary = cashFlowData?.summary;
  const items = cashFlowData?.items ?? [];

  const stats = useMemo<StatCardData[]>(() => {
    if (!summary) return [];
    return [
      {
        label: 'Total Inflows',
        value: summary.totalInflows,
        icon: <ArrowUpRight className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${summary.inflowCount} transactions`,
      },
      {
        label: 'Total Outflows',
        value: summary.totalOutflows,
        icon: <ArrowDownRight className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${summary.outflowCount} transactions`,
      },
      {
        label: 'Net Cash Flow',
        value: summary.netCashFlow,
        icon: summary.netCashFlow >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />,
        format: 'currency',
        alert: summary.netCashFlow < 0,
        subtitle: summary.netCashFlow >= 0 ? 'Positive flow' : 'Negative flow',
      },
      {
        label: 'Total Transactions',
        value: summary.inflowCount + summary.outflowCount,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'number',
      },
    ];
  }, [summary]);

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view cash flow.</p>
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
    </div>
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8" />
            Cash Flow Management
          </h1>
          <p className="text-muted-foreground mt-2">
            Monitor cash flow, track inflows and outflows, and analyze cash position
          </p>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} />

        {/* Cash flow table */}
        <DataTable
          columns={CASH_FLOW_COLUMNS}
          data={items}
          isLoading={isLoading}
          filters={filterControls}
          emptyMessage="No cash flow activity found for the selected period."
        />
      </div>
    </DashboardLayout>
  );
};

export default CashFlow;
