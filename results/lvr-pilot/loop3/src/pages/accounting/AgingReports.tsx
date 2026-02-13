/**
 * AgingReports.tsx — ACC-023
 *
 * Accounts receivable and payable aging reports with correct bucket keys.
 *
 * Bug fixes applied (BUG-H06):
 *   - Uses CORRECT bucket keys from useAgingReport hook: 'current', '30', '60', '90', '90+'
 *   - NOT '0-30', 'days_30', 'thirtyDays' or any other incorrect variant
 *   - Includes ALL 5 buckets including the previously missing 61-90 day bucket
 *   - Summary cards display real totals from the aging query
 *
 * Hooks: useARAgingQuery, useAPAgingQuery
 */

import React, { useState, useMemo, useCallback } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { StatCards, type StatCardData } from '../components/accounting/shared/StatCards';
import { useAccountingPermission } from '../config/accountingPermissions';
import { useARAgingQuery, useAPAgingQuery } from '../hooks/useAgingReport';
import type { AgingBucket } from '../types/accounting';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Clock,
  DollarSign,
  AlertTriangle,
  Download,
  TrendingUp,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------

const fmt = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

const pct = (value: number, total: number) =>
  total > 0 ? `${((value / total) * 100).toFixed(1)}%` : '0.0%';

// ---------------------------------------------------------------------------
// Aging Table Component — uses CORRECT bucket keys
// ---------------------------------------------------------------------------

function AgingTable({
  data,
  isLoading,
  title,
  type,
}: {
  data: AgingBucket | undefined;
  isLoading: boolean;
  title: string;
  type: 'ar' | 'ap';
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-4">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // BUG-H06 FIX: Use CORRECT bucket keys matching the useAgingReport hook output.
  // Keys are: 'current', '30', '60', '90', '90+'
  // NOT '0-30', 'days_30', 'thirtyDays', etc.
  const buckets = [
    { key: 'current' as const, label: 'Current (0-30 days)', value: data.current },
    { key: '30' as const, label: '31-60 days', value: data['30'] },
    { key: '60' as const, label: '61-90 days', value: data['60'] },  // Previously MISSING bucket
    { key: '90' as const, label: '91-120 days', value: data['90'] },
    { key: '90+' as const, label: '120+ days', value: data['90+'] },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{title}</span>
          <span className="text-lg font-bold">Total: {fmt(data.total)}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Summary bar chart */}
        <div className="mb-6">
          <div className="flex gap-1 h-8 rounded-lg overflow-hidden">
            {buckets.map((bucket, i) => {
              const widthPct = data.total > 0 ? (bucket.value / data.total) * 100 : 0;
              const colors = [
                'bg-green-500',
                'bg-yellow-400',
                'bg-orange-400',
                'bg-red-400',
                'bg-red-600',
              ];
              if (widthPct === 0) return null;
              return (
                <div
                  key={bucket.key}
                  className={`${colors[i]} transition-all`}
                  style={{ width: `${widthPct}%` }}
                  title={`${bucket.label}: ${fmt(bucket.value)}`}
                />
              );
            })}
          </div>
        </div>

        {/* Detail table */}
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Aging Bucket</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">% of Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {buckets.map((bucket, i) => {
              const textColors = [
                'text-green-600',
                'text-yellow-600',
                'text-orange-600',
                'text-red-500',
                'text-red-700',
              ];
              return (
                <TableRow key={bucket.key}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${['bg-green-500', 'bg-yellow-400', 'bg-orange-400', 'bg-red-400', 'bg-red-600'][i]}`} />
                      {bucket.label}
                    </div>
                  </TableCell>
                  <TableCell className={`text-right font-medium ${textColors[i]}`}>
                    {fmt(bucket.value)}
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {pct(bucket.value, data.total)}
                  </TableCell>
                </TableRow>
              );
            })}
            <TableRow className="font-bold border-t-2">
              <TableCell>Total</TableCell>
              <TableCell className="text-right">{fmt(data.total)}</TableCell>
              <TableCell className="text-right">100%</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// CSV Export
// ---------------------------------------------------------------------------

function exportAgingCSV(data: AgingBucket, type: 'ar' | 'ap') {
  const label = type === 'ar' ? 'Accounts Receivable' : 'Accounts Payable';
  const headers = ['Bucket', 'Amount', '% of Total'];
  const rows = [
    ['Current (0-30 days)', data.current.toFixed(2), pct(data.current, data.total)],
    ['31-60 days', data['30'].toFixed(2), pct(data['30'], data.total)],
    ['61-90 days', data['60'].toFixed(2), pct(data['60'], data.total)],
    ['91-120 days', data['90'].toFixed(2), pct(data['90'], data.total)],
    ['120+ days', data['90+'].toFixed(2), pct(data['90+'], data.total)],
    ['Total', data.total.toFixed(2), '100%'],
  ];

  const csvContent =
    `data:text/csv;charset=utf-8,${label} Aging Report\n` +
    headers.join(',') +
    '\n' +
    rows.map((r) => r.join(',')).join('\n');

  const link = document.createElement('a');
  link.setAttribute('href', encodeURI(csvContent));
  link.setAttribute(
    'download',
    `${type}-aging-report-${new Date().toISOString().split('T')[0]}.csv`
  );
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const AgingReports = () => {
  const canRead = useAccountingPermission('accounting_aging_read');
  const [activeTab, setActiveTab] = useState('ar');

  const { data: arAging, isLoading: arLoading } = useARAgingQuery();
  const { data: apAging, isLoading: apLoading } = useAPAgingQuery();

  // Stats
  const stats = useMemo<StatCardData[]>(() => {
    const arTotal = arAging?.total ?? 0;
    const apTotal = apAging?.total ?? 0;
    const arOverdue = arAging
      ? arAging['30'] + arAging['60'] + arAging['90'] + arAging['90+']
      : 0;
    const apOverdue = apAging
      ? apAging['30'] + apAging['60'] + apAging['90'] + apAging['90+']
      : 0;

    return [
      {
        label: 'AR Outstanding',
        value: arTotal,
        icon: <TrendingUp className="h-4 w-4" />,
        format: 'currency',
        subtitle: 'Total receivables',
      },
      {
        label: 'AR Overdue (30+)',
        value: arOverdue,
        icon: <AlertTriangle className="h-4 w-4" />,
        format: 'currency',
        alert: arOverdue > 0,
        subtitle: arTotal > 0 ? `${((arOverdue / arTotal) * 100).toFixed(0)}% of AR` : '0%',
      },
      {
        label: 'AP Outstanding',
        value: apTotal,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency',
        subtitle: 'Total payables',
      },
      {
        label: 'AP Overdue (30+)',
        value: apOverdue,
        icon: <AlertTriangle className="h-4 w-4" />,
        format: 'currency',
        alert: apOverdue > 0,
        subtitle: apTotal > 0 ? `${((apOverdue / apTotal) * 100).toFixed(0)}% of AP` : '0%',
      },
    ];
  }, [arAging, apAging]);

  const handleExport = useCallback(() => {
    if (activeTab === 'ar' && arAging) {
      exportAgingCSV(arAging, 'ar');
    } else if (activeTab === 'ap' && apAging) {
      exportAgingCSV(apAging, 'ap');
    }
  }, [activeTab, arAging, apAging]);

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view aging reports.</p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Clock className="h-8 w-8" />
              Aging Reports
            </h1>
            <p className="text-muted-foreground mt-2">
              Analyze accounts receivable and payable aging
            </p>
          </div>
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-1" />
            Export CSV
          </Button>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={arLoading || apLoading} />

        {/* Tabs: AR | AP */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList>
            <TabsTrigger value="ar">Accounts Receivable</TabsTrigger>
            <TabsTrigger value="ap">Accounts Payable</TabsTrigger>
          </TabsList>

          <TabsContent value="ar">
            <AgingTable
              data={arAging}
              isLoading={arLoading}
              title="Accounts Receivable Aging"
              type="ar"
            />
          </TabsContent>

          <TabsContent value="ap">
            <AgingTable
              data={apAging}
              isLoading={apLoading}
              title="Accounts Payable Aging"
              type="ap"
            />
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default AgingReports;
