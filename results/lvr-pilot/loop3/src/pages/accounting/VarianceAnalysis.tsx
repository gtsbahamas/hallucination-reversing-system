/**
 * VarianceAnalysis.tsx — ACC-020
 *
 * Budget vs actual variance analysis with proper positive/negative display.
 *
 * Bug fixes applied:
 *   - Does NOT use Math.abs to mask negative actuals
 *   - Shows real positive/negative variance with proper color coding
 *   - Positive variance = favorable (green), negative variance = unfavorable (red)
 *
 * Hooks: React Query inline hooks for budgets, chart_of_accounts
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface VarianceItem {
  id: string;
  name: string;
  category: string;
  period: string;
  budgetAmount: number;
  actualAmount: number;
  variance: number;
  variancePercent: number;
  isFavorable: boolean;
}

// ---------------------------------------------------------------------------
// Query
// ---------------------------------------------------------------------------

async function fetchVarianceData(
  businessId: string,
  fiscalYear: number
): Promise<VarianceItem[]> {
  const { data, error } = await supabase
    .from('budgets')
    .select('*')
    .eq('business_id', businessId)
    .eq('fiscal_year', fiscalYear)
    .order('category')
    .order('period');

  if (error) throw error;

  return (data ?? []).map((row: any) => {
    const budgetAmount = row.budget_amount ?? 0;
    const actualAmount = row.actual_amount ?? 0;
    // Variance = budget - actual. Positive = under budget (favorable).
    // NO Math.abs here -- we show the real signed variance.
    const variance = budgetAmount - actualAmount;
    const variancePercent = budgetAmount > 0 ? (variance / budgetAmount) * 100 : 0;

    return {
      id: row.id,
      name: row.name,
      category: row.category,
      period: row.period,
      budgetAmount,
      actualAmount,
      variance,
      variancePercent,
      isFavorable: variance >= 0,
    };
  });
}

// ---------------------------------------------------------------------------
// Columns — Shows real variance with proper sign and color
// ---------------------------------------------------------------------------

const VARIANCE_COLUMNS: ColumnDef<VarianceItem>[] = [
  {
    id: 'name',
    header: 'Budget Line',
    accessor: 'name',
    sortable: true,
  },
  {
    id: 'category',
    header: 'Category',
    accessor: 'category',
    sortable: true,
    cell: (row) => <Badge variant="outline">{row.category}</Badge>,
  },
  {
    id: 'period',
    header: 'Period',
    accessor: 'period',
  },
  {
    id: 'budgetAmount',
    header: 'Budget',
    accessor: 'budgetAmount',
    sortable: true,
    cell: (row) =>
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
        row.budgetAmount
      ),
  },
  {
    id: 'actualAmount',
    header: 'Actual',
    accessor: 'actualAmount',
    sortable: true,
    cell: (row) =>
      // Show REAL actual amount, NOT Math.abs. Negative actuals are valid
      // (e.g., revenue shortfalls, refunds, credits).
      new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
        row.actualAmount
      ),
  },
  {
    id: 'variance',
    header: 'Variance ($)',
    accessor: 'variance',
    sortable: true,
    cell: (row) => (
      <span className={row.isFavorable ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
        {row.isFavorable ? '+' : ''}
        {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(row.variance)}
      </span>
    ),
  },
  {
    id: 'variancePercent',
    header: 'Variance (%)',
    accessor: 'variancePercent',
    sortable: true,
    cell: (row) => (
      <div className="flex items-center gap-1">
        {row.isFavorable ? (
          <TrendingUp className="h-4 w-4 text-green-600" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-600" />
        )}
        <span className={row.isFavorable ? 'text-green-600' : 'text-red-600'}>
          {row.isFavorable ? '+' : ''}
          {row.variancePercent.toFixed(1)}%
        </span>
      </div>
    ),
  },
  {
    id: 'status',
    header: 'Status',
    cell: (row) =>
      row.isFavorable ? (
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          Favorable
        </Badge>
      ) : (
        <Badge className="bg-red-100 text-red-800">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Unfavorable
        </Badge>
      ),
  },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const VarianceAnalysis = () => {
  const canRead = useAccountingPermission('accounting_variance_read');
  const businessId = useBusinessId();

  const [fiscalYear, setFiscalYear] = useState(new Date().getFullYear());
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const { data: allItems = [], isLoading } = useQuery({
    queryKey: ['accounting', 'variance', businessId, fiscalYear],
    queryFn: () => fetchVarianceData(businessId, fiscalYear),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  // Apply category filter
  const items = useMemo(
    () =>
      categoryFilter === 'all'
        ? allItems
        : allItems.filter((i) => i.category === categoryFilter),
    [allItems, categoryFilter]
  );

  // Get unique categories for filter
  const categories = useMemo(
    () => [...new Set(allItems.map((i) => i.category))].sort(),
    [allItems]
  );

  // Stats
  const stats = useMemo<StatCardData[]>(() => {
    const totalBudget = items.reduce((s, i) => s + i.budgetAmount, 0);
    const totalActual = items.reduce((s, i) => s + i.actualAmount, 0);
    const totalVariance = totalBudget - totalActual;
    const favorableCount = items.filter((i) => i.isFavorable).length;
    const unfavorableCount = items.filter((i) => !i.isFavorable).length;

    return [
      {
        label: 'Total Budget',
        value: totalBudget,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency',
      },
      {
        label: 'Total Actual',
        value: totalActual,
        icon: <BarChart3 className="h-4 w-4" />,
        format: 'currency',
      },
      {
        label: 'Net Variance',
        value: totalVariance,
        icon: totalVariance >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />,
        format: 'currency',
        alert: totalVariance < 0,
        subtitle: totalVariance >= 0 ? 'Overall favorable' : 'Overall unfavorable',
      },
      {
        label: 'Favorable / Unfavorable',
        value: `${favorableCount} / ${unfavorableCount}`,
        icon: <CheckCircle2 className="h-4 w-4" />,
        subtitle: `${items.length} total budget lines`,
      },
    ];
  }, [items]);

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view variance analysis.</p>
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
      <Select value={categoryFilter} onValueChange={setCategoryFilter}>
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="All Categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          {categories.map((cat) => (
            <SelectItem key={cat} value={cat}>
              {cat}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="h-8 w-8" />
            Variance Analysis
          </h1>
          <p className="text-muted-foreground mt-2">
            Compare budget vs actual performance with real variance indicators
          </p>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} />

        {/* Variance table */}
        <DataTable
          columns={VARIANCE_COLUMNS}
          data={items}
          isLoading={isLoading}
          filters={filterControls}
          emptyMessage="No budget data found for variance analysis."
        />
      </div>
    </DashboardLayout>
  );
};

export default VarianceAnalysis;
