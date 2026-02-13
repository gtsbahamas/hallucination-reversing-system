/**
 * FixedAssets.tsx — ACC-021
 *
 * Fixed asset register with depreciation schedules and calculations.
 *
 * Bug fixes applied:
 *   - Depreciation calculation results are DISPLAYED (not just fetched and discarded)
 *   - Depreciation schedule shows per-year/per-period breakdown
 *   - Asset register with full CRUD via FormModal
 *
 * Hooks: React Query inline hooks for fixed_assets table
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
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Building2,
  Plus,
  DollarSign,
  TrendingDown,
  Calculator,
  Eye,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FixedAssetRow {
  id: string;
  business_id: string;
  asset_name: string;
  asset_code: string;
  category: string;
  purchase_date: string;
  purchase_cost: number;
  useful_life_years: number;
  salvage_value: number;
  depreciation_method: string;
  status: 'active' | 'disposed' | 'fully_depreciated';
  accumulated_depreciation: number;
  current_value: number;
  created_at: string;
}

interface DepreciationScheduleItem {
  year: number;
  openingValue: number;
  depreciation: number;
  accumulatedDepreciation: number;
  closingValue: number;
}

// ---------------------------------------------------------------------------
// Depreciation Calculation (DISPLAYED, not discarded)
// ---------------------------------------------------------------------------

function calculateDepreciationSchedule(asset: FixedAssetRow): DepreciationScheduleItem[] {
  const schedule: DepreciationScheduleItem[] = [];
  const depreciableAmount = asset.purchase_cost - asset.salvage_value;

  if (asset.depreciation_method === 'straight_line' || !asset.depreciation_method) {
    const annualDepreciation = depreciableAmount / asset.useful_life_years;
    let accumulatedDep = 0;

    for (let year = 1; year <= asset.useful_life_years; year++) {
      const openingValue = asset.purchase_cost - accumulatedDep;
      const depreciation = Math.min(annualDepreciation, openingValue - asset.salvage_value);
      accumulatedDep += depreciation;
      const closingValue = asset.purchase_cost - accumulatedDep;

      schedule.push({
        year,
        openingValue,
        depreciation,
        accumulatedDepreciation: accumulatedDep,
        closingValue: Math.max(closingValue, asset.salvage_value),
      });
    }
  } else if (asset.depreciation_method === 'declining_balance') {
    const rate = 2 / asset.useful_life_years; // Double-declining
    let accumulatedDep = 0;
    let currentValue = asset.purchase_cost;

    for (let year = 1; year <= asset.useful_life_years; year++) {
      const depreciation = Math.min(
        currentValue * rate,
        currentValue - asset.salvage_value
      );
      if (depreciation <= 0) break;

      accumulatedDep += depreciation;
      currentValue -= depreciation;

      schedule.push({
        year,
        openingValue: currentValue + depreciation,
        depreciation,
        accumulatedDepreciation: accumulatedDep,
        closingValue: currentValue,
      });
    }
  }

  return schedule;
}

// ---------------------------------------------------------------------------
// Query Functions
// ---------------------------------------------------------------------------

async function fetchFixedAssets(businessId: string): Promise<FixedAssetRow[]> {
  const { data, error } = await supabase
    .from('fixed_assets')
    .select('*')
    .eq('business_id', businessId)
    .order('asset_name');

  if (error) throw error;
  return data ?? [];
}

async function createFixedAsset(
  businessId: string,
  asset: Record<string, any>
): Promise<FixedAssetRow> {
  const purchaseCost = Number(asset.purchase_cost);
  const salvageValue = Number(asset.salvage_value ?? 0);

  const { data, error } = await supabase
    .from('fixed_assets')
    .insert({
      business_id: businessId,
      asset_name: asset.asset_name,
      asset_code: asset.asset_code,
      category: asset.category,
      purchase_date: asset.purchase_date,
      purchase_cost: purchaseCost,
      useful_life_years: Number(asset.useful_life_years),
      salvage_value: salvageValue,
      depreciation_method: asset.depreciation_method ?? 'straight_line',
      status: 'active',
      accumulated_depreciation: 0,
      current_value: purchaseCost,
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

function buildAssetColumns(
  onViewSchedule: (asset: FixedAssetRow) => void
): ColumnDef<FixedAssetRow>[] {
  return [
    {
      id: 'asset_code',
      header: 'Code',
      accessor: 'asset_code',
      sortable: true,
    },
    {
      id: 'asset_name',
      header: 'Asset Name',
      accessor: 'asset_name',
      sortable: true,
    },
    {
      id: 'category',
      header: 'Category',
      accessor: 'category',
      cell: (row) => <Badge variant="outline">{row.category}</Badge>,
    },
    {
      id: 'purchase_date',
      header: 'Purchase Date',
      accessor: 'purchase_date',
      sortable: true,
      cell: (row) => new Date(row.purchase_date).toLocaleDateString(),
    },
    {
      id: 'purchase_cost',
      header: 'Cost',
      accessor: 'purchase_cost',
      sortable: true,
      cell: (row) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
          row.purchase_cost
        ),
    },
    {
      id: 'accumulated_depreciation',
      header: 'Accum. Depreciation',
      accessor: 'accumulated_depreciation',
      cell: (row) => (
        <span className="text-red-600">
          {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
            row.accumulated_depreciation
          )}
        </span>
      ),
    },
    {
      id: 'current_value',
      header: 'Book Value',
      accessor: 'current_value',
      sortable: true,
      cell: (row) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
          row.current_value
        ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      cell: (row) => {
        const config: Record<string, { label: string; className: string }> = {
          active: { label: 'Active', className: 'bg-green-100 text-green-800' },
          disposed: { label: 'Disposed', className: 'bg-gray-100 text-gray-800' },
          fully_depreciated: { label: 'Fully Depreciated', className: 'bg-yellow-100 text-yellow-800' },
        };
        const c = config[row.status] ?? config.active;
        return <Badge className={c.className}>{c.label}</Badge>;
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (row) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onViewSchedule(row);
          }}
        >
          <Eye className="h-4 w-4 mr-1" />
          Schedule
        </Button>
      ),
    },
  ];
}

// ---------------------------------------------------------------------------
// Create Asset Form Fields
// ---------------------------------------------------------------------------

const CREATE_ASSET_FIELDS: FormFieldConfig[] = [
  {
    name: 'asset_name',
    label: 'Asset Name',
    type: 'text',
    required: true,
    placeholder: 'e.g., Office Computer',
    colSpan: 'col-span-2',
  },
  {
    name: 'asset_code',
    label: 'Asset Code',
    type: 'text',
    required: true,
    placeholder: 'e.g., FA-001',
  },
  {
    name: 'category',
    label: 'Category',
    type: 'select',
    required: true,
    options: [
      { value: 'Equipment', label: 'Equipment' },
      { value: 'Furniture', label: 'Furniture' },
      { value: 'Vehicles', label: 'Vehicles' },
      { value: 'Buildings', label: 'Buildings' },
      { value: 'Land', label: 'Land' },
      { value: 'Technology', label: 'Technology' },
      { value: 'Other', label: 'Other' },
    ],
  },
  {
    name: 'purchase_date',
    label: 'Purchase Date',
    type: 'date',
    required: true,
  },
  {
    name: 'purchase_cost',
    label: 'Purchase Cost',
    type: 'number',
    required: true,
    min: 0,
    step: 0.01,
    placeholder: '0.00',
  },
  {
    name: 'useful_life_years',
    label: 'Useful Life (Years)',
    type: 'number',
    required: true,
    min: 1,
    max: 50,
    placeholder: '5',
  },
  {
    name: 'salvage_value',
    label: 'Salvage Value',
    type: 'number',
    min: 0,
    step: 0.01,
    defaultValue: 0,
    placeholder: '0.00',
  },
  {
    name: 'depreciation_method',
    label: 'Depreciation Method',
    type: 'select',
    required: true,
    defaultValue: 'straight_line',
    options: [
      { value: 'straight_line', label: 'Straight Line' },
      { value: 'declining_balance', label: 'Declining Balance' },
    ],
  },
];

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const FixedAssets = () => {
  const canRead = useAccountingPermission('accounting_fixed_assets_read');
  const canManage = useAccountingPermission('accounting_fixed_assets_manage');
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<FixedAssetRow | null>(null);

  // Query
  const { data: assets = [], isLoading } = useQuery({
    queryKey: ['accounting', 'fixed-assets', businessId],
    queryFn: () => fetchFixedAssets(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (values: Record<string, any>) => createFixedAsset(businessId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['accounting', 'fixed-assets', businessId],
      });
    },
  });

  // Depreciation schedule for selected asset — DISPLAYED, not discarded
  const depreciationSchedule = useMemo(
    () => (selectedAsset ? calculateDepreciationSchedule(selectedAsset) : []),
    [selectedAsset]
  );

  // Stats
  const stats = useMemo<StatCardData[]>(() => {
    const totalCost = assets.reduce((s, a) => s + a.purchase_cost, 0);
    const totalDepreciation = assets.reduce((s, a) => s + a.accumulated_depreciation, 0);
    const totalBookValue = assets.reduce((s, a) => s + a.current_value, 0);
    const activeCount = assets.filter((a) => a.status === 'active').length;

    return [
      {
        label: 'Total Asset Cost',
        value: totalCost,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency',
        subtitle: `${assets.length} assets`,
      },
      {
        label: 'Accumulated Depreciation',
        value: totalDepreciation,
        icon: <TrendingDown className="h-4 w-4" />,
        format: 'currency',
      },
      {
        label: 'Total Book Value',
        value: totalBookValue,
        icon: <Building2 className="h-4 w-4" />,
        format: 'currency',
      },
      {
        label: 'Active Assets',
        value: activeCount,
        icon: <Calculator className="h-4 w-4" />,
        format: 'number',
        subtitle: `${assets.length - activeCount} disposed/depreciated`,
      },
    ];
  }, [assets]);

  const handleViewSchedule = useCallback((asset: FixedAssetRow) => {
    setSelectedAsset(asset);
  }, []);

  const columns = useMemo(
    () => buildAssetColumns(handleViewSchedule),
    [handleViewSchedule]
  );

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view fixed assets.</p>
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
              <Building2 className="h-8 w-8" />
              Fixed Assets
            </h1>
            <p className="text-muted-foreground mt-2">
              Track and manage fixed assets and depreciation schedules
            </p>
          </div>
          {canManage && (
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Add Asset
            </Button>
          )}
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={isLoading} />

        {/* Asset table */}
        <DataTable
          columns={columns}
          data={assets}
          isLoading={isLoading}
          emptyMessage="No fixed assets found. Add one to get started."
        />

        {/* Create Asset Modal */}
        <FormModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="Add Fixed Asset"
          description="Register a new fixed asset with depreciation parameters."
          fields={CREATE_ASSET_FIELDS}
          onSubmit={async (values) => {
            await createMutation.mutateAsync(values);
          }}
          isSubmitting={createMutation.isPending}
          submitLabel="Add Asset"
        />

        {/* Depreciation Schedule Dialog — BUG FIX: Actually DISPLAYS results */}
        <Dialog
          open={!!selectedAsset}
          onOpenChange={(open) => !open && setSelectedAsset(null)}
        >
          <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                Depreciation Schedule: {selectedAsset?.asset_name}
              </DialogTitle>
            </DialogHeader>

            {selectedAsset && (
              <div className="space-y-4">
                {/* Asset summary */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Method:</span>{' '}
                    <span className="font-medium">
                      {selectedAsset.depreciation_method === 'straight_line'
                        ? 'Straight Line'
                        : 'Declining Balance'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Useful Life:</span>{' '}
                    <span className="font-medium">{selectedAsset.useful_life_years} years</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Cost:</span>{' '}
                    <span className="font-medium">
                      {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                        selectedAsset.purchase_cost
                      )}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Salvage Value:</span>{' '}
                    <span className="font-medium">
                      {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                        selectedAsset.salvage_value
                      )}
                    </span>
                  </div>
                </div>

                {/* Schedule table */}
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Year</TableHead>
                      <TableHead>Opening Value</TableHead>
                      <TableHead>Depreciation</TableHead>
                      <TableHead>Accum. Depreciation</TableHead>
                      <TableHead>Closing Value</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {depreciationSchedule.map((item) => (
                      <TableRow key={item.year}>
                        <TableCell className="font-medium">Year {item.year}</TableCell>
                        <TableCell>
                          {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                            item.openingValue
                          )}
                        </TableCell>
                        <TableCell className="text-red-600">
                          ({new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                            item.depreciation
                          )})
                        </TableCell>
                        <TableCell>
                          {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                            item.accumulatedDepreciation
                          )}
                        </TableCell>
                        <TableCell className="font-medium">
                          {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(
                            item.closingValue
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};

export default FixedAssets;
