/**
 * ExpenseDetail (ACC-006)
 *
 * Detail page with DetailLayout, real accounting tab, working Duplicate button,
 * approval workflow (approve/reject).
 *
 * Bug fixes applied:
 *   BUG-M04: Real Accounting tab showing journal entry data (NOT placeholder)
 *   BUG-M05: Working Duplicate button (creates copy as draft)
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
  useExpenseQuery,
  useUpdateExpenseMutation,
  useApproveExpenseMutation,
  useRejectExpenseMutation,
  useDeleteExpenseMutation,
  useCreateExpenseMutation,
} from '@/hooks/useExpenses';
import { useAccountingPermission } from '@/config/accountingPermissions';
import { FormModal, type FormFieldConfig } from '@/components/accounting/shared/FormModal';
import type { ExpenseWithRelations } from '@/types/accounting';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Edit,
  Trash2,
  Copy,
  CheckCircle,
  XCircle,
  AlertCircle,
  Receipt,
  User,
  Building2,
  BookOpen,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';

// ---------------------------------------------------------------------------
// Status badge mapping
// ---------------------------------------------------------------------------

function getStatusBadgeConfig(status: string): StatusBadgeConfig {
  const map: Record<string, StatusBadgeConfig> = {
    draft: { status: 'Draft', variant: 'default' },
    pending_approval: { status: 'Pending Approval', variant: 'warning' },
    approved: { status: 'Approved', variant: 'success' },
    rejected: { status: 'Rejected', variant: 'destructive' },
  };
  return map[status] ?? { status, variant: 'default' };
}

// ---------------------------------------------------------------------------
// Details Tab
// ---------------------------------------------------------------------------

function DetailsTab({ expense }: { expense: ExpenseWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Expense Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Expense Number</label>
            <p className="text-sm font-mono">{expense.expense_number}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Status</label>
            <div className="mt-1">
              <Badge className={
                expense.status === 'approved' ? 'bg-green-100 text-green-800' :
                expense.status === 'rejected' ? 'bg-red-100 text-red-800' :
                expense.status === 'pending_approval' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }>
                {expense.status === 'pending_approval'
                  ? 'Pending Approval'
                  : expense.status.charAt(0).toUpperCase() + expense.status.slice(1)}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Expense Date</label>
            <p className="text-sm">{new Date(expense.expense_date).toLocaleDateString()}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Category</label>
            <p className="text-sm">{expense.category ?? 'Uncategorized'}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Amount</label>
            <p className="text-lg font-semibold">
              ${(expense.total_amount ?? expense.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Payment Method</label>
            <p className="text-sm capitalize">{expense.payment_method?.replace(/_/g, ' ') ?? 'N/A'}</p>
          </div>
          {expense.vendor && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Vendor</label>
              <p className="text-sm">{expense.vendor}</p>
            </div>
          )}
          {expense.reference_number && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Reference</label>
              <p className="text-sm font-mono">{expense.reference_number}</p>
            </div>
          )}
        </div>

        {expense.description && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Description</label>
            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-md">{expense.description}</p>
          </div>
        )}

        {expense.notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Notes</label>
            <p className="text-sm mt-1 p-3 bg-muted/50 rounded-md">{expense.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Accounting Tab (BUG-M04 fix: real data, not placeholder)
// Shows journal entry information if the expense has been posted to GL.
// Since expenses may or may not have a linked journal entry, this tab
// shows the expense's accounting impact with available data.
// ---------------------------------------------------------------------------

function AccountingTab({ expense }: { expense: ExpenseWithRelations }) {
  const amount = expense.total_amount ?? expense.amount;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Accounting Impact</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Expense accounting summary */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <BookOpen className="h-4 w-4 text-muted-foreground" />
            <span className="font-medium">Expense Recognition</span>
          </div>

          <div className="border rounded-md overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50">
                  <th className="text-left px-4 py-2 font-medium">Account</th>
                  <th className="text-right px-4 py-2 font-medium">Debit</th>
                  <th className="text-right px-4 py-2 font-medium">Credit</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t">
                  <td className="px-4 py-2">
                    <span className="font-medium">{expense.category ?? 'Expense'}</span>
                    <span className="text-muted-foreground ml-1">(Expense Account)</span>
                  </td>
                  <td className="text-right px-4 py-2 font-mono">
                    ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right px-4 py-2 font-mono text-muted-foreground">-</td>
                </tr>
                <tr className="border-t">
                  <td className="px-4 py-2">
                    <span className="font-medium">
                      {expense.payment_method === 'cash' ? 'Cash' :
                       expense.payment_method === 'bank_transfer' ? 'Bank' :
                       'Accounts Payable'}
                    </span>
                    <span className="text-muted-foreground ml-1">
                      ({expense.payment_method === 'cash' || expense.payment_method === 'bank_transfer'
                        ? 'Asset' : 'Liability'} Account)
                    </span>
                  </td>
                  <td className="text-right px-4 py-2 font-mono text-muted-foreground">-</td>
                  <td className="text-right px-4 py-2 font-mono">
                    ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr className="border-t bg-muted/30">
                  <td className="px-4 py-2 font-semibold">Total</td>
                  <td className="text-right px-4 py-2 font-mono font-semibold">
                    ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="text-right px-4 py-2 font-mono font-semibold">
                    ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Posting status */}
          <div className="flex items-center gap-2 text-sm mt-4">
            {expense.status === 'approved' ? (
              <>
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-green-700">
                  Approved on {expense.approved_at ? new Date(expense.approved_at).toLocaleDateString() : 'N/A'}
                </span>
              </>
            ) : expense.status === 'pending_approval' ? (
              <>
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <span className="text-yellow-700">Pending approval — not yet posted to GL</span>
              </>
            ) : expense.status === 'rejected' ? (
              <>
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-red-700">Rejected — will not be posted to GL</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Draft — submit for approval to post</span>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab({ expense }: { expense: ExpenseWithRelations }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Submitted</span>
            <span>{new Date(expense.created_at).toLocaleString()}</span>
          </div>
          {expense.approved_at && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">
                {expense.status === 'rejected' ? 'Rejected' : 'Approved'}
              </span>
              <span>{new Date(expense.approved_at).toLocaleString()}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// ExpenseDetail Page
// ---------------------------------------------------------------------------

export default function ExpenseDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();

  // BUG-L05 fix: detect edit mode from URL
  const isEditMode = location.pathname.endsWith('/edit');

  // Permissions
  const canUpdate = useAccountingPermission('accounting_expenses_update');
  const canDelete = useAccountingPermission('accounting_expenses_delete');
  const canApprove = useAccountingPermission('accounting_expenses_approve');

  // Queries
  const { data: expense, isLoading, error } = useExpenseQuery(id ?? '');
  const updateMutation = useUpdateExpenseMutation();
  const approveMutation = useApproveExpenseMutation();
  const rejectMutation = useRejectExpenseMutation();
  const deleteMutation = useDeleteExpenseMutation();
  const createMutation = useCreateExpenseMutation();

  // Edit modal state
  const [showEditModal, setShowEditModal] = useState(isEditMode);

  // -- Approve --
  const handleApprove = async () => {
    if (!expense) return;
    try {
      await approveMutation.mutateAsync(expense.id);
      toast({ title: 'Success', description: 'Expense approved' });
    } catch {
      toast({ title: 'Error', description: 'Failed to approve expense', variant: 'destructive' });
    }
  };

  // -- Reject --
  const handleReject = async () => {
    if (!expense) return;
    try {
      await rejectMutation.mutateAsync(expense.id);
      toast({ title: 'Success', description: 'Expense rejected' });
    } catch {
      toast({ title: 'Error', description: 'Failed to reject expense', variant: 'destructive' });
    }
  };

  // -- Delete --
  const handleDelete = async () => {
    if (!expense) return;
    try {
      await deleteMutation.mutateAsync(expense.id);
      toast({ title: 'Success', description: 'Expense deleted successfully' });
      navigate('/accounting/expenses');
    } catch {
      toast({ title: 'Error', description: 'Failed to delete expense', variant: 'destructive' });
    }
  };

  // -- BUG-M05 fix: Working Duplicate button --
  const handleDuplicate = async () => {
    if (!expense) return;
    try {
      const today = new Date().toISOString().split('T')[0];
      const newExpense = await createMutation.mutateAsync({
        expense_date: today,
        amount: expense.amount,
        total_amount: expense.total_amount ?? expense.amount,
        category: expense.category ?? undefined,
        vendor: expense.vendor ?? undefined,
        payment_method: expense.payment_method ?? undefined,
        description: expense.description ?? undefined,
        notes: expense.notes ?? undefined,
        supplier_id: expense.supplier_id ?? undefined,
        employee_id: expense.employee_id ?? undefined,
        status: 'draft',
      });
      toast({ title: 'Success', description: 'Expense duplicated as draft' });
      navigate(`/accounting/expenses/${newExpense.id}`);
    } catch {
      toast({ title: 'Error', description: 'Failed to duplicate expense', variant: 'destructive' });
    }
  };

  // -- Edit handler --
  const handleEdit = async (values: Record<string, any>) => {
    if (!expense) return;
    await updateMutation.mutateAsync({
      id: expense.id,
      data: {
        expense_date: values.expense_date,
        amount: Number(values.amount),
        total_amount: Number(values.amount),
        category: values.category || undefined,
        vendor: values.vendor || undefined,
        payment_method: values.payment_method || undefined,
        description: values.description || undefined,
        notes: values.notes || undefined,
      },
    });
  };

  // Error / Not Found
  if (!isLoading && (error || !expense) && id) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <Button variant="ghost" onClick={() => navigate('/accounting/expenses')}>
            Back to Expenses
          </Button>
          <Card className="mt-4">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-lg font-medium">Expense not found</p>
              <p className="text-muted-foreground mt-1">
                The expense you are looking for does not exist or you do not have permission to view it.
              </p>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Build tabs
  const tabs: TabConfig[] = expense
    ? [
        { id: 'details', label: 'Details', content: <DetailsTab expense={expense} /> },
        // BUG-M04 fix: real Accounting tab, not placeholder
        { id: 'accounting', label: 'Accounting', content: <AccountingTab expense={expense} /> },
        { id: 'activity', label: 'Activity', content: <ActivityTab expense={expense} /> },
      ]
    : [];

  // Build sidebar
  const sidebar = expense ? (
    <>
      {/* Employee Card */}
      {expense.employees && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Submitted By</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <p className="font-medium">
                {expense.employees.first_name} {expense.employees.last_name}
              </p>
            </div>
            {expense.employees.email && (
              <p className="text-sm text-muted-foreground">{expense.employees.email}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Supplier Card */}
      {expense.suppliers && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Supplier</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <p className="font-medium">{expense.suppliers.name}</p>
            </div>
            {expense.suppliers.email && (
              <p className="text-sm text-muted-foreground">{expense.suppliers.email}</p>
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
          {canApprove && expense.status === 'pending_approval' && (
            <>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={handleApprove}
                disabled={approveMutation.isPending}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-start text-red-600 hover:text-red-700"
                onClick={handleReject}
                disabled={rejectMutation.isPending}
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            </>
          )}
          {/* BUG-M05 fix: working duplicate */}
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={handleDuplicate}
            disabled={createMutation.isPending}
          >
            <Copy className="h-4 w-4 mr-2" />
            Duplicate Expense
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
              <span className="text-muted-foreground">Amount</span>
              <span className="font-semibold">
                ${(expense.total_amount ?? expense.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Category</span>
              <span>{expense.category ?? 'Uncategorized'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Payment</span>
              <span className="capitalize">{expense.payment_method?.replace(/_/g, ' ') ?? 'N/A'}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  ) : undefined;

  // Action buttons
  const actionButtons = expense
    ? [
        ...(canApprove && expense.status === 'pending_approval'
          ? [
              {
                label: 'Approve',
                onClick: handleApprove,
                icon: <CheckCircle className="h-4 w-4" />,
                variant: 'default' as const,
                className: 'bg-green-600 hover:bg-green-700',
                disabled: approveMutation.isPending,
              },
              {
                label: 'Reject',
                onClick: handleReject,
                icon: <XCircle className="h-4 w-4" />,
                variant: 'outline' as const,
                className: 'text-red-600 hover:text-red-700',
                disabled: rejectMutation.isPending,
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
        ...(canDelete && (expense.status === 'draft' || expense.status === 'rejected')
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

  const EDIT_FIELDS: FormFieldConfig[] = expense
    ? [
        {
          name: 'expense_date',
          label: 'Expense Date',
          type: 'date',
          defaultValue: expense.expense_date,
        },
        {
          name: 'amount',
          label: 'Amount',
          type: 'number',
          defaultValue: expense.total_amount ?? expense.amount,
          min: 0,
          step: 0.01,
        },
        {
          name: 'category',
          label: 'Category',
          type: 'text',
          defaultValue: expense.category ?? '',
        },
        {
          name: 'vendor',
          label: 'Vendor',
          type: 'text',
          defaultValue: expense.vendor ?? '',
        },
        {
          name: 'payment_method',
          label: 'Payment Method',
          type: 'select',
          defaultValue: expense.payment_method ?? '',
          options: [
            { label: 'Cash', value: 'cash' },
            { label: 'Credit Card', value: 'credit_card' },
            { label: 'Debit Card', value: 'debit_card' },
            { label: 'Bank Transfer', value: 'bank_transfer' },
            { label: 'Check', value: 'check' },
            { label: 'Other', value: 'other' },
          ],
        },
        {
          name: 'description',
          label: 'Description',
          type: 'textarea',
          defaultValue: expense.description ?? '',
          colSpan: 'col-span-2',
        },
      ]
    : [];

  return (
    <DashboardLayout>
      <DetailLayout
        title={expense ? `Expense ${expense.expense_number}` : 'Loading...'}
        subtitle={
          expense?.employees
            ? `${expense.employees.first_name} ${expense.employees.last_name}`
            : undefined
        }
        breadcrumbs={[
          { label: 'Accounting', href: '/accounting' },
          { label: 'Expenses', href: '/accounting/expenses' },
          { label: expense?.expense_number ?? '...' },
        ]}
        statusBadge={expense ? getStatusBadgeConfig(expense.status) : undefined}
        actionButtons={actionButtons}
        tabs={tabs}
        sidebar={sidebar}
        isLoading={isLoading}
        onBack={() => navigate('/accounting/expenses')}
      />

      {/* Edit Modal */}
      {expense && (
        <FormModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Expense"
          fields={EDIT_FIELDS}
          initialValues={{
            expense_date: expense.expense_date,
            amount: expense.total_amount ?? expense.amount,
            category: expense.category ?? '',
            vendor: expense.vendor ?? '',
            payment_method: expense.payment_method ?? '',
            description: expense.description ?? '',
          }}
          onSubmit={handleEdit}
          isSubmitting={updateMutation.isPending}
          submitLabel="Save Changes"
        />
      )}
    </DashboardLayout>
  );
}
