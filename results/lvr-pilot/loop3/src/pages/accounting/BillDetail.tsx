/**
 * BillDetail (ACC-004)
 *
 * Detail page with DetailLayout, line items tab, activity tab,
 * supplier sidebar, edit modal.
 *
 * Bug fixes applied:
 *   BUG-H03: SOFT DELETE only (useSoftDeleteBillMutation, not hard .delete())
 *   BUG-L05: Detect /edit URL param and enable edit mode
 *
 * Uses React Query hooks from foundation (NOT useState+useEffect).
 * Uses shared components (DetailLayout, FormModal).
 * Uses permission guards from accountingPermissions.ts.
 */

import React, { useState, useMemo } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DetailLayout, type TabConfig, type StatusBadgeConfig } from '@/components/accounting/shared/DetailLayout';
import {
  useBillQuery,
  useUpdateBillMutation,
  useSoftDeleteBillMutation,
} from '@/hooks/useBills';
import { useAccountingPermission } from '@/config/accountingPermissions';
import { FormModal, type FormFieldConfig } from '@/components/accounting/shared/FormModal';
import type { BillWithRelations, BillItemRow } from '@/types/accounting';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DollarSign,
  Edit,
  Trash2,
  FileText,
  AlertCircle,
  CheckCircle,
  Building2,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// ---------------------------------------------------------------------------
// Status badge mapping
// ---------------------------------------------------------------------------

function getStatusBadgeConfig(status: string): StatusBadgeConfig {
  const map: Record<string, StatusBadgeConfig> = {
    pending: { status: 'Pending', variant: 'warning' },
    approved: { status: 'Approved', variant: 'default' },
    paid: { status: 'Paid', variant: 'success' },
    overdue: { status: 'Overdue', variant: 'destructive' },
    cancelled: { status: 'Cancelled', variant: 'default' },
  };
  return map[status] ?? { status, variant: 'default' };
}

// ---------------------------------------------------------------------------
// Line Items Tab (real data from bill_items)
// ---------------------------------------------------------------------------

function LineItemsTab({ bill }: { bill: BillWithRelations }) {
  const lineItems = bill.bill_items ?? [];

  if (lineItems.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No line items on this bill.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Line Items ({lineItems.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description</TableHead>
              <TableHead className="text-right">Qty</TableHead>
              <TableHead className="text-right">Unit Price</TableHead>
              <TableHead className="text-right">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lineItems.map((item: BillItemRow) => (
              <TableRow key={item.id}>
                <TableCell className="font-medium">{item.description}</TableCell>
                <TableCell className="text-right">{item.quantity}</TableCell>
                <TableCell className="text-right">
                  ${item.unit_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
                <TableCell className="text-right font-medium">
                  ${item.line_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {/* Totals */}
        <div className="border-t mt-2 pt-4 space-y-1 text-sm text-right">
          <div className="flex justify-end gap-8">
            <span className="text-muted-foreground">Subtotal:</span>
            <span className="font-medium">
              ${bill.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex justify-end gap-8">
            <span className="text-muted-foreground">Tax:</span>
            <span>
              ${bill.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex justify-end gap-8 text-base font-bold">
            <span>Total:</span>
            <span>
              ${bill.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Details Tab
// ---------------------------------------------------------------------------

function DetailsTab({ bill }: { bill: BillWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Bill Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Bill Number</label>
            <p className="text-sm font-mono">{bill.bill_number}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Status</label>
            <div className="mt-1">
              <Badge className={
                bill.status === 'paid' ? 'bg-green-100 text-green-800' :
                bill.status === 'overdue' ? 'bg-red-100 text-red-800' :
                bill.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                bill.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }>
                {bill.status.charAt(0).toUpperCase() + bill.status.slice(1)}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Bill Date</label>
            <p className="text-sm">{new Date(bill.bill_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Due Date</label>
            <p className="text-sm">{new Date(bill.due_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Subtotal</label>
            <p className="text-sm">
              ${bill.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Tax Amount</label>
            <p className="text-sm">
              ${bill.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Total Amount</label>
            <p className="text-lg font-semibold">
              ${bill.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Balance Due</label>
            <p className={`text-lg font-semibold ${bill.balance_due > 0 ? 'text-red-600' : ''}`}>
              ${bill.balance_due.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          {bill.processing_status && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Processing</label>
              <p className="text-sm capitalize">{bill.processing_status}</p>
            </div>
          )}
          {bill.confidence_score != null && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Confidence</label>
              <p className="text-sm">{(bill.confidence_score * 100).toFixed(0)}%</p>
            </div>
          )}
        </div>

        {bill.notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Notes</label>
            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-md">{bill.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab({ bill }: { bill: BillWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{new Date(bill.created_at).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Updated</span>
            <span>{new Date(bill.updated_at).toLocaleString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// BillDetail Page
// ---------------------------------------------------------------------------

export default function BillDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // BUG-L05 fix: detect edit mode from URL
  const isEditMode = location.pathname.endsWith('/edit');

  // Permissions
  const canUpdate = useAccountingPermission('accounting_bills_update');
  const canDelete = useAccountingPermission('accounting_bills_delete');

  // Queries
  const { data: bill, isLoading, error } = useBillQuery(id ?? '');
  const updateMutation = useUpdateBillMutation();

  // BUG-H03 fix: soft delete only
  const deleteMutation = useSoftDeleteBillMutation();

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(isEditMode);

  // -- Status Update --
  const handleStatusUpdate = async (newStatus: string) => {
    if (!bill) return;
    try {
      await updateMutation.mutateAsync({
        id: bill.id,
        data: { status: newStatus as any },
      });
      toast({ title: 'Success', description: `Bill marked as ${newStatus}` });
    } catch {
      toast({ title: 'Error', description: 'Failed to update bill status', variant: 'destructive' });
    }
  };

  // -- BUG-H03 FIX: Soft Delete (sets is_deleted=true, status=cancelled) --
  const handleDelete = async () => {
    if (!bill) return;
    try {
      await deleteMutation.mutateAsync(bill.id);
      toast({ title: 'Success', description: 'Bill deleted successfully' });
      navigate('/accounting/bills');
    } catch {
      toast({ title: 'Error', description: 'Failed to delete bill', variant: 'destructive' });
    }
  };

  // -- Edit handler --
  const handleEdit = async (values: Record<string, any>) => {
    if (!bill) return;
    await updateMutation.mutateAsync({
      id: bill.id,
      data: {
        supplier_id: values.supplier_id || undefined,
        bill_date: values.bill_date,
        due_date: values.due_date,
        notes: values.notes || undefined,
      },
    });
  };

  // Error / Not Found
  if (!isLoading && (error || !bill) && id) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <Button variant="ghost" onClick={() => navigate('/accounting/bills')}>
            Back to Bills
          </Button>
          <Card className="mt-4">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-lg font-medium">Bill not found</p>
              <p className="text-muted-foreground mt-1">
                The bill you are looking for does not exist or you do not have permission to view it.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Build tabs
  const tabs: TabConfig[] = bill
    ? [
        { id: 'details', label: 'Details', content: <DetailsTab bill={bill} /> },
        { id: 'line-items', label: 'Line Items', content: <LineItemsTab bill={bill} /> },
        { id: 'activity', label: 'Activity', content: <ActivityTab bill={bill} /> },
      ]
    : [];

  // Build sidebar
  const sidebar = bill ? (
    <>
      {/* Supplier Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Supplier</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <p className="font-medium">{bill.suppliers?.name ?? 'Unknown Supplier'}</p>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {bill.status === 'pending' && (
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleStatusUpdate('approved')}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Approve Bill
            </Button>
          )}
          {(bill.status === 'approved' || bill.status === 'overdue') && (
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleStatusUpdate('paid')}
            >
              <DollarSign className="h-4 w-4 mr-2" />
              Record Payment
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Subtotal</span>
              <span>${bill.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            {bill.tax_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax</span>
                <span>${bill.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="flex justify-between border-t pt-3">
              <span className="font-medium">Total</span>
              <span className="font-semibold">
                ${bill.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Paid</span>
              <span className="text-green-700">
                ${bill.amount_paid.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={bill.balance_due > 0 ? 'text-red-600 font-medium' : 'text-muted-foreground'}>
                Balance Due
              </span>
              <span className={bill.balance_due > 0 ? 'text-red-600 font-semibold' : ''}>
                ${bill.balance_due.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  ) : undefined;

  // Action buttons
  const actionButtons = bill
    ? [
        ...(bill.status === 'pending'
          ? [
              {
                label: 'Approve',
                onClick: () => handleStatusUpdate('approved'),
                icon: <CheckCircle className="h-4 w-4" />,
                variant: 'default' as const,
              },
            ]
          : []),
        ...(bill.status === 'approved' || bill.status === 'overdue'
          ? [
              {
                label: 'Mark Paid',
                onClick: () => handleStatusUpdate('paid'),
                icon: <DollarSign className="h-4 w-4" />,
                variant: 'default' as const,
                className: 'bg-green-600 hover:bg-green-700',
              },
            ]
          : []),
        ...(canUpdate
          ? [
              {
                label: 'Edit',
                onClick: () => setShowEditModal(true),
                icon: <Edit className="h-4 w-4" />,
                variant: 'outline' as const,
              },
            ]
          : []),
        ...(canDelete
          ? [
              {
                label: 'Delete',
                onClick: handleDelete,
                icon: <Trash2 className="h-4 w-4" />,
                variant: 'outline' as const,
                className: 'text-red-600 hover:text-red-700',
              },
            ]
          : []),
      ]
    : [];

  const EDIT_FIELDS: FormFieldConfig[] = bill
    ? [
        {
          name: 'supplier_id',
          label: 'Supplier ID',
          type: 'text',
          defaultValue: bill.supplier_id,
        },
        {
          name: 'bill_date',
          label: 'Bill Date',
          type: 'date',
          defaultValue: bill.bill_date,
        },
        {
          name: 'due_date',
          label: 'Due Date',
          type: 'date',
          defaultValue: bill.due_date,
        },
        {
          name: 'notes',
          label: 'Notes',
          type: 'textarea',
          defaultValue: bill.notes ?? '',
          colSpan: 'col-span-2',
        },
      ]
    : [];

  return (
    <DashboardLayout>
      <DetailLayout
        title={bill ? `Bill ${bill.bill_number}` : 'Loading...'}
        subtitle={bill?.suppliers?.name ?? undefined}
        breadcrumbs={[
          { label: 'Accounting', href: '/accounting' },
          { label: 'Bills', href: '/accounting/bills' },
          { label: bill?.bill_number ?? '...' },
        ]}
        statusBadge={bill ? getStatusBadgeConfig(bill.status) : undefined}
        actionButtons={actionButtons}
        tabs={tabs}
        sidebar={sidebar}
        isLoading={isLoading}
        onBack={() => navigate('/accounting/bills')}
      />

      {/* Edit Modal */}
      {bill && (
        <FormModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Bill"
          fields={EDIT_FIELDS}
          initialValues={{
            supplier_id: bill.supplier_id,
            bill_date: bill.bill_date,
            due_date: bill.due_date,
            notes: bill.notes ?? '',
          }}
          onSubmit={handleEdit}
          isSubmitting={updateMutation.isPending}
          submitLabel="Save Changes"
        />
      )}
    </DashboardLayout>
  );
}
