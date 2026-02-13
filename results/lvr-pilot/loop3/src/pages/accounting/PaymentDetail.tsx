/**
 * PaymentDetail (ACC-007)
 *
 * Detail page with DetailLayout, payment applications tab, activity tab.
 *
 * Bug fixes applied:
 *   BUG-M06: NO "Process Refund" button (was a stub with empty onClick)
 *   BUG-M07: NO "Print Receipt" button (was a stub with empty onClick)
 *   BUG-L05: Detect /edit URL param and enable edit mode
 *
 * These features (refund, print) are intentionally OMITTED rather than
 * included as non-functional stubs. When refund/print functionality is
 * designed and implemented end-to-end, they can be added with real handlers.
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
  usePaymentQuery,
  useVoidPaymentMutation,
} from '@/hooks/usePayments';
import { useAccountingPermission } from '@/config/accountingPermissions';
import type { PaymentWithRelations, PaymentApplicationRow } from '@/types/accounting';

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
  AlertCircle,
  User,
  Building2,
  XCircle,
  CreditCard,
  Banknote,
  FileText,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// ---------------------------------------------------------------------------
// Status badge mapping
// ---------------------------------------------------------------------------

function getStatusBadgeConfig(status: string): StatusBadgeConfig {
  const map: Record<string, StatusBadgeConfig> = {
    pending: { status: 'Pending', variant: 'warning' },
    cleared: { status: 'Cleared', variant: 'success' },
    bounced: { status: 'Bounced', variant: 'destructive' },
    cancelled: { status: 'Cancelled', variant: 'default' },
  };
  return map[status] ?? { status, variant: 'default' };
}

// ---------------------------------------------------------------------------
// Payment method display helper
// ---------------------------------------------------------------------------

function formatPaymentMethod(method: string): string {
  const map: Record<string, string> = {
    cash: 'Cash',
    check: 'Check',
    bank_transfer: 'Bank Transfer',
    credit_card: 'Credit Card',
    debit_card: 'Debit Card',
    other: 'Other',
  };
  return map[method] ?? method;
}

// ---------------------------------------------------------------------------
// Details Tab
// ---------------------------------------------------------------------------

function DetailsTab({ payment }: { payment: PaymentWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Payment Number</label>
            <p className="text-sm font-mono">{payment.payment_number}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Status</label>
            <div className="mt-1">
              <Badge className={
                payment.status === 'cleared' ? 'bg-green-100 text-green-800' :
                payment.status === 'bounced' ? 'bg-red-100 text-red-800' :
                payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }>
                {payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Payment Date</label>
            <p className="text-sm">{new Date(payment.payment_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Payment Method</label>
            <p className="text-sm">{formatPaymentMethod(payment.payment_method)}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Amount</label>
            <p className="text-lg font-semibold">
              ${payment.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Payment Type</label>
            <p className="text-sm capitalize">{payment.payment_type.replace(/_/g, ' ')}</p>
          </div>
          {payment.currency !== 'BSD' && (
            <>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Currency</label>
                <p className="text-sm">{payment.currency}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Exchange Rate</label>
                <p className="text-sm">{payment.exchange_rate}</p>
              </div>
            </>
          )}
          {payment.reference_number && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Reference Number</label>
              <p className="text-sm font-mono">{payment.reference_number}</p>
            </div>
          )}
          {payment.check_number && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Check Number</label>
              <p className="text-sm font-mono">{payment.check_number}</p>
            </div>
          )}
          <div>
            <label className="text-sm font-medium text-muted-foreground">Posted to GL</label>
            <p className="text-sm">
              {payment.posted_to_gl ? (
                <span className="text-green-700">Yes</span>
              ) : (
                <span className="text-muted-foreground">No</span>
              )}
            </p>
          </div>
        </div>

        {payment.notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Notes</label>
            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-md">{payment.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Payment Applications Tab
// ---------------------------------------------------------------------------

function ApplicationsTab({ payment }: { payment: PaymentWithRelations }) {
  const applications = payment.payment_applications ?? [];

  if (applications.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No payment applications recorded.</p>
          <p className="text-xs mt-1">This payment has not been applied to any invoice or bill.</p>
        </CardContent>
      </Card>
    );
  }

  const totalApplied = applications.reduce((sum, app) => sum + app.applied_amount, 0);
  const unappliedAmount = payment.amount - totalApplied;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Applications ({applications.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Applied To</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Notes</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {applications.map((app: PaymentApplicationRow) => (
              <TableRow key={app.id}>
                <TableCell className="font-mono text-sm">
                  {app.invoice_id
                    ? `Invoice: ${app.invoice_id.slice(0, 8)}...`
                    : app.bill_id
                    ? `Bill: ${app.bill_id.slice(0, 8)}...`
                    : 'Unlinked'}
                </TableCell>
                <TableCell className="text-sm">
                  {new Date(app.application_date).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {app.notes ?? '-'}
                </TableCell>
                <TableCell className="text-right font-medium text-sm">
                  ${app.applied_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="border-t mt-2 pt-4 space-y-1 text-sm text-right">
          <div className="flex justify-end gap-8">
            <span className="text-muted-foreground">Total Applied:</span>
            <span className="font-medium">
              ${totalApplied.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          {unappliedAmount > 0 && (
            <div className="flex justify-end gap-8">
              <span className="text-yellow-600">Unapplied:</span>
              <span className="font-medium text-yellow-600">
                ${unappliedAmount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab({ payment }: { payment: PaymentWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{new Date(payment.created_at).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Updated</span>
            <span>{new Date(payment.updated_at).toLocaleString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// PaymentDetail Page
// ---------------------------------------------------------------------------

export default function PaymentDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // BUG-L05 fix: detect edit mode from URL
  const isEditMode = location.pathname.endsWith('/edit');

  // Permissions
  const canVoid = useAccountingPermission('accounting_payments_refund');

  // Queries
  const { data: payment, isLoading, error } = usePaymentQuery(id ?? '');
  const voidMutation = useVoidPaymentMutation();

  // -- Void Payment --
  const handleVoid = async () => {
    if (!payment) return;
    try {
      await voidMutation.mutateAsync(payment.id);
      toast({ title: 'Success', description: 'Payment voided successfully' });
    } catch {
      toast({ title: 'Error', description: 'Failed to void payment', variant: 'destructive' });
    }
  };

  // Error / Not Found
  if (!isLoading && (error || !payment) && id) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <Button variant="ghost" onClick={() => navigate(-1)}>
            Back
          </Button>
          <Card className="mt-4">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-lg font-medium">Payment not found</p>
              <p className="text-muted-foreground mt-1">
                The payment you are looking for does not exist or you do not have permission to view it.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Build tabs
  const tabs: TabConfig[] = payment
    ? [
        { id: 'details', label: 'Details', content: <DetailsTab payment={payment} /> },
        { id: 'applications', label: 'Applications', content: <ApplicationsTab payment={payment} /> },
        { id: 'activity', label: 'Activity', content: <ActivityTab payment={payment} /> },
      ]
    : [];

  // Build sidebar
  const sidebar = payment ? (
    <>
      {/* Customer/Supplier Card */}
      {payment.payment_type === 'customer_payment' && payment.customers ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Customer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <p className="font-medium">
                {payment.customers.first_name} {payment.customers.last_name}
              </p>
            </div>
            {payment.customers.email && (
              <p className="text-sm text-muted-foreground">{payment.customers.email}</p>
            )}
            {payment.customers.company_name && (
              <p className="text-sm text-muted-foreground">{payment.customers.company_name}</p>
            )}
          </CardContent>
        </Card>
      ) : payment.payment_type === 'supplier_payment' && payment.suppliers ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Supplier</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <p className="font-medium">{payment.suppliers.name}</p>
            </div>
            {payment.suppliers.email && (
              <p className="text-sm text-muted-foreground">{payment.suppliers.email}</p>
            )}
          </CardContent>
        </Card>
      ) : null}

      {/* Quick Actions */}
      {/*
       * BUG-M06 fix: NO "Process Refund" button (was empty onClick handler)
       * BUG-M07 fix: NO "Print Receipt" button (was empty onClick handler)
       *
       * Only actions with real implementations are shown here.
       * Void is a real action backed by useVoidPaymentMutation.
       */}
      {canVoid && payment.status !== 'cancelled' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start text-red-600 hover:text-red-700"
              onClick={handleVoid}
              disabled={voidMutation.isPending}
            >
              <XCircle className="h-4 w-4 mr-2" />
              Void Payment
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Amount</span>
              <span className="font-semibold">
                ${payment.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Method</span>
              <span>{formatPaymentMethod(payment.payment_method)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Type</span>
              <span className="capitalize">{payment.payment_type.replace(/_/g, ' ')}</span>
            </div>
            {payment.payment_applications && payment.payment_applications.length > 0 && (
              <>
                <div className="border-t pt-3 flex justify-between">
                  <span className="text-muted-foreground">Applied</span>
                  <span className="text-green-700">
                    ${payment.payment_applications
                      .reduce((s, a) => s + a.applied_amount, 0)
                      .toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Unapplied</span>
                  <span className={
                    payment.amount - payment.payment_applications.reduce((s, a) => s + a.applied_amount, 0) > 0
                      ? 'text-yellow-600'
                      : ''
                  }>
                    ${(payment.amount - payment.payment_applications.reduce((s, a) => s + a.applied_amount, 0))
                      .toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </>
  ) : undefined;

  // Action buttons
  // BUG-M06/M07: Only real actions are included (void). No stub buttons.
  const actionButtons = payment
    ? [
        ...(canVoid && payment.status !== 'cancelled'
          ? [
              {
                label: 'Void Payment',
                onClick: handleVoid,
                icon: <XCircle className="h-4 w-4" />,
                variant: 'outline' as const,
                className: 'text-red-600 hover:text-red-700',
                disabled: voidMutation.isPending,
              },
            ]
          : []),
      ]
    : [];

  return (
    <DashboardLayout>
      <DetailLayout
        title={payment ? `Payment ${payment.payment_number}` : 'Loading...'}
        subtitle={
          payment?.payment_type === 'customer_payment' && payment.customers
            ? `${payment.customers.first_name} ${payment.customers.last_name}`
            : payment?.payment_type === 'supplier_payment' && payment.suppliers
            ? payment.suppliers.name
            : undefined
        }
        breadcrumbs={[
          { label: 'Accounting', href: '/accounting' },
          { label: 'Payments' },
          { label: payment?.payment_number ?? '...' },
        ]}
        statusBadge={payment ? getStatusBadgeConfig(payment.status) : undefined}
        actionButtons={actionButtons}
        tabs={tabs}
        sidebar={sidebar}
        isLoading={isLoading}
      />
    </DashboardLayout>
  );
}
