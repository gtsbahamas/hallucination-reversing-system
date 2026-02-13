/**
 * InvoiceDetail (ACC-002)
 *
 * Detail page with DetailLayout, REAL line items tab, REAL payments tab,
 * working Duplicate button.
 *
 * Bug fixes applied:
 *   BUG-M01: Real LineItems tab with invoice_line_items data
 *   BUG-M02: Real Payments tab with invoice_payments data
 *   BUG-M03: Working Duplicate button (creates copy as draft)
 *   BUG-L05: Detect /edit URL param and enable edit mode
 */

import React, { useState, useMemo } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DetailLayout, type TabConfig, type StatusBadgeConfig } from '@/components/accounting/shared/DetailLayout';
import {
  useInvoiceQuery,
  useUpdateInvoiceMutation,
  useSoftDeleteInvoiceMutation,
  useCreateInvoiceMutation,
} from '@/hooks/useInvoices';
import { useAccountingPermission } from '@/config/accountingPermissions';
import { FormModal, type FormFieldConfig } from '@/components/accounting/shared/FormModal';
import type { InvoiceWithRelations, InvoiceLineItemRow } from '@/types/accounting';

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
  Send,
  DollarSign,
  Download,
  Edit,
  Trash2,
  Copy,
  User,
  Calendar,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { accountingKeys, useBusinessId } from '@/hooks/useAccountingQueries';

// ---------------------------------------------------------------------------
// Status badge mapping
// ---------------------------------------------------------------------------

function getStatusBadgeConfig(status: string): StatusBadgeConfig {
  const map: Record<string, StatusBadgeConfig> = {
    draft: { status: 'Draft', variant: 'default' },
    sent: { status: 'Sent', variant: 'warning' },
    paid: { status: 'Paid', variant: 'success' },
    overdue: { status: 'Overdue', variant: 'destructive' },
    cancelled: { status: 'Cancelled', variant: 'default' },
  };
  return map[status] ?? { status, variant: 'default' };
}

// ---------------------------------------------------------------------------
// Invoice Payments hook (BUG-M02 fix: real data)
// ---------------------------------------------------------------------------

function useInvoicePaymentsQuery(invoiceId: string) {
  const businessId = useBusinessId();
  return useQuery({
    queryKey: accountingKeys.invoicePayments.byInvoice(businessId, invoiceId),
    queryFn: async () => {
      const { data, error } = await supabase
        .from('invoice_payments')
        .select('*')
        .eq('invoice_id', invoiceId)
        .eq('business_id', businessId)
        .order('payment_date', { ascending: false });
      if (error) throw error;
      return data ?? [];
    },
    enabled: !!businessId && !!invoiceId,
  });
}

// ---------------------------------------------------------------------------
// Line Items Tab (BUG-M01 fix: real data from invoice_line_items)
// ---------------------------------------------------------------------------

function LineItemsTab({ invoice }: { invoice: InvoiceWithRelations }) {
  const lineItems = invoice.invoice_line_items ?? [];

  if (lineItems.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No line items on this invoice.</p>
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
            {lineItems.map((item: InvoiceLineItemRow) => (
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
              ${invoice.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex justify-end gap-8">
            <span className="text-muted-foreground">Tax:</span>
            <span>
              ${invoice.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex justify-end gap-8 text-base font-bold">
            <span>Total:</span>
            <span>
              ${invoice.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Payments Tab (BUG-M02 fix: real data from invoice_payments)
// ---------------------------------------------------------------------------

function PaymentsTab({ invoiceId }: { invoiceId: string }) {
  const { data: payments, isLoading } = useInvoicePaymentsQuery(invoiceId);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full mx-auto" />
        </CardContent>
      </Card>
    );
  }

  if (!payments || payments.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          <DollarSign className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No payments recorded for this invoice.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payments ({payments.length})</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Method</TableHead>
              <TableHead>Reference</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((payment: any) => (
              <TableRow key={payment.id}>
                <TableCell>
                  {new Date(payment.payment_date).toLocaleDateString()}
                </TableCell>
                <TableCell className="capitalize">{payment.payment_method?.replace(/_/g, ' ')}</TableCell>
                <TableCell className="font-mono text-sm">
                  {payment.reference_number ?? payment.check_number ?? '-'}
                </TableCell>
                <TableCell className="text-right font-medium text-green-700">
                  ${payment.payment_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <div className="border-t mt-2 pt-4 flex justify-end gap-8 text-sm font-bold">
          <span>Total Payments:</span>
          <span className="text-green-700">
            ${payments.reduce((sum: number, p: any) => sum + (p.payment_amount ?? 0), 0).toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab({ invoice }: { invoice: InvoiceWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{new Date(invoice.created_at).toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Updated</span>
            <span>{new Date(invoice.updated_at).toLocaleString()}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Details Tab
// ---------------------------------------------------------------------------

function DetailsTab({ invoice }: { invoice: InvoiceWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Invoice Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Invoice Number</label>
            <p className="text-sm font-mono">{invoice.invoice_number}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Status</label>
            <div className="mt-1">
              <Badge className={
                invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                invoice.status === 'overdue' ? 'bg-red-100 text-red-800' :
                invoice.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                'bg-gray-100 text-gray-800'
              }>
                {invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1)}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Invoice Date</label>
            <p className="text-sm">{new Date(invoice.invoice_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Due Date</label>
            <p className="text-sm">{new Date(invoice.due_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Subtotal</label>
            <p className="text-sm">
              ${invoice.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Tax Amount</label>
            <p className="text-sm">
              ${invoice.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Total Amount</label>
            <p className="text-lg font-semibold">
              ${invoice.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Balance Due</label>
            <p className={`text-lg font-semibold ${invoice.balance_due > 0 ? 'text-red-600' : ''}`}>
              ${invoice.balance_due.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {invoice.notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Notes</label>
            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-md">{invoice.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// InvoiceDetail Page
// ---------------------------------------------------------------------------

export default function InvoiceDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // BUG-L05 fix: detect edit mode from URL
  const isEditMode = location.pathname.endsWith('/edit');

  // Permissions
  const canUpdate = useAccountingPermission('accounting_invoices_update');
  const canDelete = useAccountingPermission('accounting_invoices_delete');

  // Queries
  const { data: invoice, isLoading, error } = useInvoiceQuery(id ?? '');
  const updateMutation = useUpdateInvoiceMutation();
  const deleteMutation = useSoftDeleteInvoiceMutation();
  const createMutation = useCreateInvoiceMutation();

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(isEditMode);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // -- Status Update --
  const handleStatusUpdate = async (newStatus: string) => {
    if (!invoice) return;
    try {
      await updateMutation.mutateAsync({
        id: invoice.id,
        data: { status: newStatus as any },
      });
      toast({ title: 'Success', description: `Invoice marked as ${newStatus}` });
    } catch {
      toast({ title: 'Error', description: 'Failed to update invoice status', variant: 'destructive' });
    }
  };

  // -- Delete --
  const handleDelete = async () => {
    if (!invoice) return;
    try {
      await deleteMutation.mutateAsync(invoice.id);
      toast({ title: 'Success', description: 'Invoice deleted successfully' });
      navigate('/accounting/invoices');
    } catch {
      toast({ title: 'Error', description: 'Failed to delete invoice', variant: 'destructive' });
    }
  };

  // -- Duplicate (BUG-M03 fix: working duplicate button) --
  const handleDuplicate = async () => {
    if (!invoice) return;
    try {
      const today = new Date().toISOString().split('T')[0];
      const dueDateOffset = Math.max(
        0,
        Math.round((new Date(invoice.due_date).getTime() - new Date(invoice.invoice_date).getTime()) / 86400000)
      );
      const newDueDate = new Date();
      newDueDate.setDate(newDueDate.getDate() + dueDateOffset);

      const newInvoice = await createMutation.mutateAsync({
        customer_id: invoice.customer_id ?? undefined,
        invoice_date: today,
        due_date: newDueDate.toISOString().split('T')[0],
        subtotal: invoice.subtotal,
        tax_amount: invoice.tax_amount,
        total_amount: invoice.total_amount,
        notes: invoice.notes ?? undefined,
        status: 'draft',
        line_items: (invoice.invoice_line_items ?? []).map((li) => ({
          product_id: li.product_id ?? undefined,
          description: li.description,
          quantity: li.quantity,
          unit_price: li.unit_price,
          line_total: li.line_total,
        })),
      });
      toast({ title: 'Success', description: 'Invoice duplicated as draft' });
      navigate(`/accounting/invoices/${newInvoice.id}`);
    } catch {
      toast({ title: 'Error', description: 'Failed to duplicate invoice', variant: 'destructive' });
    }
  };

  // -- Edit handler --
  const handleEdit = async (values: Record<string, any>) => {
    if (!invoice) return;
    await updateMutation.mutateAsync({
      id: invoice.id,
      data: {
        customer_id: values.customer_id || undefined,
        invoice_date: values.invoice_date,
        due_date: values.due_date,
        notes: values.notes || undefined,
      },
    });
  };

  // Error / Not Found
  if (!isLoading && (error || !invoice) && id) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <Button variant="ghost" onClick={() => navigate('/accounting/invoices')}>
            Back to Invoices
          </Button>
          <Card className="mt-4">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-lg font-medium">Invoice not found</p>
              <p className="text-muted-foreground mt-1">
                The invoice you are looking for does not exist or you do not have permission to view it.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Build tabs
  const tabs: TabConfig[] = invoice
    ? [
        { id: 'details', label: 'Details', content: <DetailsTab invoice={invoice} /> },
        { id: 'line-items', label: 'Line Items', content: <LineItemsTab invoice={invoice} /> },
        { id: 'payments', label: 'Payments', content: <PaymentsTab invoiceId={invoice.id} /> },
        { id: 'activity', label: 'Activity', content: <ActivityTab invoice={invoice} /> },
      ]
    : [];

  // Build sidebar
  const sidebar = invoice ? (
    <>
      {/* Customer Card */}
      {invoice.customers && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Customer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="font-medium">
              {invoice.customers.first_name} {invoice.customers.last_name}
            </p>
            {invoice.customers.email && (
              <p className="text-sm text-muted-foreground">{invoice.customers.email}</p>
            )}
            {invoice.customers.company_name && (
              <p className="text-sm text-muted-foreground">{invoice.customers.company_name}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {invoice.status === 'draft' && (
            <Button
              variant="outline"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleStatusUpdate('sent')}
            >
              <Send className="h-4 w-4 mr-2" />
              Send to Customer
            </Button>
          )}
          {(invoice.status === 'sent' || invoice.status === 'overdue') && (
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
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={handleDuplicate}
            disabled={createMutation.isPending}
          >
            <Copy className="h-4 w-4 mr-2" />
            Duplicate Invoice
          </Button>
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
              <span>${invoice.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
            {invoice.tax_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Tax</span>
                <span>${invoice.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="flex justify-between border-t pt-3">
              <span className="font-medium">Total</span>
              <span className="font-semibold">
                ${invoice.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Paid</span>
              <span className="text-green-700">
                ${invoice.amount_paid.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className={invoice.balance_due > 0 ? 'text-red-600 font-medium' : 'text-muted-foreground'}>
                Balance Due
              </span>
              <span className={invoice.balance_due > 0 ? 'text-red-600 font-semibold' : ''}>
                ${invoice.balance_due.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  ) : undefined;

  // Action buttons
  const actionButtons = invoice
    ? [
        ...(invoice.status === 'draft'
          ? [
              {
                label: 'Send Invoice',
                onClick: () => handleStatusUpdate('sent'),
                icon: <Send className="h-4 w-4" />,
                variant: 'default' as const,
              },
            ]
          : []),
        ...(invoice.status === 'sent' || invoice.status === 'overdue'
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

  const EDIT_FIELDS: FormFieldConfig[] = invoice
    ? [
        {
          name: 'customer_id',
          label: 'Customer ID',
          type: 'text',
          defaultValue: invoice.customer_id ?? '',
        },
        {
          name: 'invoice_date',
          label: 'Invoice Date',
          type: 'date',
          defaultValue: invoice.invoice_date,
        },
        {
          name: 'due_date',
          label: 'Due Date',
          type: 'date',
          defaultValue: invoice.due_date,
        },
        {
          name: 'notes',
          label: 'Notes',
          type: 'textarea',
          defaultValue: invoice.notes ?? '',
          colSpan: 'col-span-2',
        },
      ]
    : [];

  return (
    <DashboardLayout>
      <DetailLayout
        title={invoice ? `Invoice ${invoice.invoice_number}` : 'Loading...'}
        subtitle={
          invoice?.customers
            ? `${invoice.customers.first_name} ${invoice.customers.last_name}`
            : undefined
        }
        breadcrumbs={[
          { label: 'Accounting', href: '/accounting' },
          { label: 'Invoices', href: '/accounting/invoices' },
          { label: invoice?.invoice_number ?? '...' },
        ]}
        statusBadge={invoice ? getStatusBadgeConfig(invoice.status) : undefined}
        actionButtons={actionButtons}
        tabs={tabs}
        sidebar={sidebar}
        isLoading={isLoading}
        onBack={() => navigate('/accounting/invoices')}
      />

      {/* Edit Modal */}
      {invoice && (
        <FormModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Invoice"
          fields={EDIT_FIELDS}
          initialValues={{
            customer_id: invoice.customer_id ?? '',
            invoice_date: invoice.invoice_date,
            due_date: invoice.due_date,
            notes: invoice.notes ?? '',
          }}
          onSubmit={handleEdit}
          isSubmitting={updateMutation.isPending}
          submitLabel="Save Changes"
        />
      )}
    </DashboardLayout>
  );
}
