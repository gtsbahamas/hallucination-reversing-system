/**
 * BudgetAnalysis.tsx — ACC-018
 *
 * Budget vs actual comparison with variance display and Create Budget modal.
 *
 * Bug fixes applied:
 *   - WORKING Create Budget button with FormModal (was non-functional)
 *   - business_id filter applied to all budget queries
 *   - Real budget data from Supabase via React Query
 *
 * Hooks: React Query inline hooks for budgets table, useBusinessId
 */

import React, { useState, useMemo, useCallback } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DataTable, type ColumnDef } from '../components/accounting/shared/DataTable';
import { StatCards, type StatCardData } from '../components/accounting/shared/StatCards';
import { FormModal, type FormFieldConfig } from '../components/accounting/shared/FormModal';
import { useAccountingPermission } from '../config/accountingPermissions';
import { useBusinessId, AGGREGATION_STALE_TIME } from '../hooks/useAccountingQueries';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  PieChart,
  Plus,
  DollarSign,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Download,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface BudgetRow {
  id: string;
  business_id: string;
  name: string;
  category: string;
  fiscal_year: number;
  period: string;
  budget_amount: number;
  actual_amount: number;
  notes: string | null;
  created_at: string;
}

interface BudgetInsert {
  name: string;
  category: string;
  fiscal_year: number;
  period: string;
  budget_amount: number;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Query Functions
// ---------------------------------------------------------------------------

async function fetchBudgets(
  businessId: string,
  fiscalYear?: number
): Promise<BudgetRow[]> {
  let query = supabase
    .from('budgets')
    .select('*')
    .eq('business_id', businessId);

  if (fiscalYear) {
    query = query.eq('fiscal_year', fiscalYear);
  }

  const { data, error } = await query.order('category').order('period');
  if (error) throw error;
  return data ?? [];
}

async function createBudget(
  businessId: string,
  budget: BudgetInsert
): Promise<BudgetRow> {
  const { data, error } = await supabase
    .from('budgets')
    .insert({
      ...budget,
      business_id: businessId,
      actual_amount: 0,
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

const BUDGET_COLUMNS: ColumnDef<BudgetRow>[] = [
  {
    id: 'name',
    header: 'Budget Name',
    accessor: 'name',
    sortable: true,
  },
  {
    id: 'category',
    header: 'Category',
    accessor: 'category',
    sortable: true,
    cell: (row) => (
      <Badge variant="outline">{row.category}</Badge>
    ),
  },
  {
    id: 'period',
    header: 'Period',
    accessor: 'period',
  },
  {
    id: 'budget_amount',
    header: 'Budget',
    accessor: 'budget_amount',
    sortable: true,
    cell: (row) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
        row.budget_amount
      ),
  },
  {
    id: 'actual_amount',
    header: 'Actual',
    accessor: 'actual_amount',
    sortable: true,
    cell: (row) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
        row.actual_amount
      ),
  },
  {
    id: 'variance',
    header: 'Variance',
    cell: (row) => {
      const variance = row.budget_amount - row.actual_amount;
      const pct =
        row.budget_amount > 0 ? (variance / row.budget_amount) * 100 : 0;
      const isFavorable = variance >= 0;

      return (
        <div className="flex items-center gap-1">
          <span className={isFavorable ? 'text-green-600' : 'text-red-600'}>
            {new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
            }).format(variance)}
          </span>
          <span className={`text-xs ${isFavorable ? 'text-green-500' : 'text-red-500'}`}>
            ({isFavorable ? '+' : ''}{pct.toFixed(1)}%)
          </span>
        </div>
      );
    },
  },
  {
    id: 'utilization',
    header: 'Utilization',
    cell: (row) => {
      const pct =
        row.budget_amount > 0
          ? Math.min((row.actual_amount / row.budget_amount) * 100, 150)
          : 0;
      const isOver = pct > 100;
      return (
        <div className="flex items-center gap-2 min-w-[120px]">
          <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${isOver ? 'bg-red-500' : 'bg-blue-500'}`}
              style={{ width: `${Math.min(pct, 100)}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground w-[40px] text-right">
            {pct.toFixed(0)}%
          </span>
        </div>
      );
    },
  },
];

// ---------------------------------------------------------------------------
// Create Budget Form Fields
// ---------------------------------------------------------------------------

const CREATE_BUDGET_FIELDS: FormFieldConfig[] = [
  {
    name: 'name',
    label: 'Budget Name',
    type: 'text',
    required: true,
    placeholder: 'e.g., Marketing Q1 2026',
    colSpan: 'col-span-2',
  },
  {
    name: 'category',
    label: 'Category',
    type: 'select',
    required: true,
    options: [
      { value: 'Revenue', label: 'Revenue' },
      { value: 'COGS', label: 'Cost of Goods Sold' },
      { value: 'Payroll', label: 'Payroll' },
      { value: 'Marketing', label: 'Marketing' },
      { value: 'Operations', label: 'Operations' },
      { value: 'Technology', label: 'Technology' },
      { value: 'Rent', label: 'Rent' },
      { value: 'Utilities', label: 'Utilities' },
      { value: 'Other', label: 'Other' },
    ],
  },
  {
    name: 'fiscal_year',
    label: 'Fiscal Year',
    type: 'number',
    required: true,
    defaultValue: new Date().getFullYear(),
    min: 2020,
    max: 2030,
  },
  {
    name: 'period',
    label: 'Period',
    type: 'select',
    required: true,
    options: [
      { value: 'Q1', label: 'Q1 (Jan-Mar)' },
      { value: 'Q2', label: 'Q2 (Apr-Jun)' },
      { value: 'Q3', label: 'Q3 (Jul-Sep)' },
      { value: 'Q4', label: 'Q4 (Oct-Dec)' },
      { value: 'Annual', label: 'Annual' },
    ],
  },
  {
    name: 'budget_amount',
    label: 'Budget Amount',
    type: 'number',
    required: true,
    placeholder: '0.00',
    min: 0,
    step: 0.01,
  },
  {
    name: 'notes',
    label: 'Notes',
    type: 'textarea',
    placeholder: 'Optional notes...',
    colSpan: 'col-span-2',
  },
];

// ---------------------------------------------------------------------------
// CSV Export
// ---------------------------------------------------------------------------

function exportBudgetCSV(budgets: BudgetRow[]) {
  const headers = [
    'Name',
    'Category',
    'Period',
    'Budget',
    'Actual',
    'Variance',
    'Utilization %',
  ];
  const rows = budgets.map((b) => {
    const variance = b.budget_amount - b.actual_amount;
    const pct = b.budget_amount > 0 ? (b.actual_amount / b.budget_amount) * 100 : 0;
    return [
      b.name,
      b.category,
      b.period,
      b.budget_amount.toFixed(2),
      b.actual_amount.toFixed(2),
      variance.toFixed(2),
      pct.toFixed(1),
    ];
  });

  const csvContent =
    'data:text/csv;charset=utf-8,' +
    headers.join(',') +
    '\n' +
    rows.map((r) => r.join(',')).join('\n');

  const link = document.createElement('a');
  link.setAttribute('href', encodeURI(csvContent));
  link.setAttribute('download', `budget-analysis-${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const BudgetAnalysis = () => {
  const canRead = useAccountingPermission('accounting_budgets_read');
  const canCreate = useAccountingPermission('accounting_budgets_create');
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Query budgets with business_id filter
  const { data: budgets = [], isLoading } = useQuery({
    queryKey: ['accounting', 'budgets', businessId, fiscalYear],
    queryFn: () => fetchBudgets(businessId, fiscalYear),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: Record<string, any>) =>
      createBudget(businessId, {
        name: values.name,
        category: values.category,
        fiscal_year: Number(values.fiscal_year),
        period: values.period,
        budget_amount: Number(values.budget_amount),
        notes: values.notes || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['accounting', 'budgets', businessId],
      });
    },
  });

  // Stats
  const stats = useMemo<StatCardData[]>(() => {
    const totalBudget = budgets.reduce((s, b) => s + b.budget_amount, 0);
    const totalActual = budgets.reduce((s, b) => s + b.actual_amount, 0);
    const totalVariance = totalBudget - totalActual;
    const overBudgetCount = budgets.filter(
      (b) => b.actual_amount > b.budget_amount
    ).length;

    return [
      {
        label: 'Total Budget',
        value: totalBudget,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${budgets.length} budget lines`,
      },
      {
        label: 'Total Actual',
        value: totalActual,
        icon: <BarChart3 className="h-4 w-4" />,
        format: 'currency',
      },
      {
        label: 'Total Variance',
        value: totalVariance,
        icon: totalVariance >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />,
        format: 'currency',
        subtitle: totalVariance >= 0 ? 'Under budget' : 'Over budget',
        alert: totalVariance < 0,
      },
      {
        label: 'Over Budget',
        value: overBudgetCount,
        icon: <TrendingDown className="h-4 w-4" />,
        format: 'number',
        alert: overBudgetCount > 0,
        subtitle: `of ${budgets.length} budgets`,
      },
    ];
  }, [budgets]);

  const handleCreateSubmit = useCallback(
    async (values: Record<string, any>) => {
      await createMutation.mutateAsync(values);
    },
    [createMutation]
  );

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view budgets.</p>
        </div>
      </DashboardLayout>
    );
  }

  const filterControls = (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        <label className="text-sm font-medium">Fiscal Year:</label>
        <Input
          type="number"
          value={fiscalYear}
          onChange={(e) => setFiscalYear(Number(e.target.value))}
          className="w-[100px]"
          min={2020}
          max={2030}
        />
      </div>
      {budgets.length > 0 && (
        <Button variant="outline" size="sm" onClick={() => exportBudgetCSV(budgets)}>
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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <PieChart className="h-8 w-8" />
              Budget Analysis
            </h1>
            <p className="text-muted-foreground mt-2">
              Create budgets and analyze budget vs actual performance
            </p>
          </div>
          {canCreate && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Create Budget
            </Button>
          )}
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} />

        {/* Budget table */}
        <DataTable
          columns={BUDGET_COLUMNS}
          data={budgets}
          isLoading={isLoading}
          filters={filterControls}
          emptyMessage="No budgets found. Create one to get started."
        />

        {/* Create Budget Modal */}
        <FormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Create Budget"
          description="Define a new budget line with target amount."
          fields={CREATE_BUDGET_FIELDS}
          onSubmit={handleCreateSubmit}
          isSubmitting={createMutation.isPending}
          submitLabel="Create Budget"
        />
      </div>
    </DashboardLayout>
  );
};

export default BudgetAnalysis;
