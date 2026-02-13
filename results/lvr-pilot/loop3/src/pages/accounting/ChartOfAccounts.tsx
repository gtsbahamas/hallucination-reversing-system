/**
 * ChartOfAccounts — ACC-014
 *
 * Chart of accounts list page with tree structure, edit/delete functionality.
 *
 * Bug fixes:
 *   BUG-M08: Edit button opens FormModal with pre-filled account data
 *   BUG-M09: Delete button shows confirmation dialog, then soft-deletes via useDeleteAccountMutation
 *
 * Architecture:
 *   - DashboardLayout wrapper with header
 *   - DataTable with tree-like visual structure (indented child accounts)
 *   - FormModal for create/edit operations
 *   - ConfirmAction dialog for delete operations
 *   - Uses useAccountsQuery, useCreateAccountMutation, useUpdateAccountMutation,
 *     useDeleteAccountMutation from useChartOfAccounts hook
 *   - Permission-gated actions (create, edit, delete)
 */

import React, { useState, useMemo, useCallback } from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { DataTable, type ColumnDef } from '@/components/accounting/shared/DataTable';
import { StatCards } from '@/components/accounting/shared/StatCards';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  BookOpen,
  Plus,
  Search,
  Edit,
  Trash2,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Scale,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import {
  useAccountsQuery,
  useCreateAccountMutation,
  useUpdateAccountMutation,
  useDeleteAccountMutation,
} from '@/hooks/useChartOfAccounts';
import { useAccountingPermission } from '@/config/accountingPermissions';
import type {
  ChartOfAccountsWithParent,
  ChartOfAccountsInsert,
  ChartOfAccountsUpdate,
  AccountType,
} from '@/types/accounting';

// ---------------------------------------------------------------------------
// Account type styling
// ---------------------------------------------------------------------------

const ACCOUNT_TYPE_CONFIG: Record<AccountType, { label: string; className: string }> = {
  asset: { label: 'Asset', className: 'bg-blue-100 text-blue-800' },
  liability: { label: 'Liability', className: 'bg-red-100 text-red-800' },
  equity: { label: 'Equity', className: 'bg-purple-100 text-purple-800' },
  revenue: { label: 'Revenue', className: 'bg-green-100 text-green-800' },
  expense: { label: 'Expense', className: 'bg-orange-100 text-orange-800' },
};

// ---------------------------------------------------------------------------
// Form Modal Component (for create and edit)
// ---------------------------------------------------------------------------

interface AccountFormData {
  account_code: string;
  account_name: string;
  account_type: AccountType;
  parent_account_id: string | null;
  description: string;
  is_active: boolean;
}

function AccountFormModal({
  open,
  onOpenChange,
  editingAccount,
  accounts,
  onSubmit,
  isSubmitting,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingAccount: ChartOfAccountsWithParent | null;
  accounts: ChartOfAccountsWithParent[];
  onSubmit: (data: AccountFormData) => void;
  isSubmitting: boolean;
}) {
  const isEditing = !!editingAccount;
  const [formData, setFormData] = useState<AccountFormData>({
    account_code: editingAccount?.account_code ?? '',
    account_name: editingAccount?.account_name ?? '',
    account_type: editingAccount?.account_type ?? 'asset',
    parent_account_id: editingAccount?.parent_account_id ?? null,
    description: editingAccount?.description ?? '',
    is_active: editingAccount?.is_active ?? true,
  });

  // Reset form when the modal opens with different data
  React.useEffect(() => {
    if (open) {
      setFormData({
        account_code: editingAccount?.account_code ?? '',
        account_name: editingAccount?.account_name ?? '',
        account_type: editingAccount?.account_type ?? 'asset',
        parent_account_id: editingAccount?.parent_account_id ?? null,
        description: editingAccount?.description ?? '',
        is_active: editingAccount?.is_active ?? true,
      });
    }
  }, [open, editingAccount]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  // Filter out the current account from parent options (can't be parent of itself)
  const parentOptions = accounts.filter(
    (a) => a.id !== editingAccount?.id && a.is_active
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{isEditing ? 'Edit Account' : 'Create Account'}</DialogTitle>
            <DialogDescription>
              {isEditing
                ? 'Update the account details below.'
                : 'Add a new account to the chart of accounts.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="account_code">Account Code</Label>
                <Input
                  id="account_code"
                  value={formData.account_code}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, account_code: e.target.value }))
                  }
                  placeholder="e.g., 1000"
                  required
                  disabled={isEditing} // Account codes are typically immutable
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="account_type">Account Type</Label>
                <Select
                  value={formData.account_type}
                  onValueChange={(val) =>
                    setFormData((prev) => ({
                      ...prev,
                      account_type: val as AccountType,
                    }))
                  }
                >
                  <SelectTrigger id="account_type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="asset">Asset</SelectItem>
                    <SelectItem value="liability">Liability</SelectItem>
                    <SelectItem value="equity">Equity</SelectItem>
                    <SelectItem value="revenue">Revenue</SelectItem>
                    <SelectItem value="expense">Expense</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="account_name">Account Name</Label>
              <Input
                id="account_name"
                value={formData.account_name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, account_name: e.target.value }))
                }
                placeholder="e.g., Cash on Hand"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="parent_account">Parent Account (optional)</Label>
              <Select
                value={formData.parent_account_id ?? 'none'}
                onValueChange={(val) =>
                  setFormData((prev) => ({
                    ...prev,
                    parent_account_id: val === 'none' ? null : val,
                  }))
                }
              >
                <SelectTrigger id="parent_account">
                  <SelectValue placeholder="No parent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No parent (top-level)</SelectItem>
                  {parentOptions.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.account_code} - {account.account_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, description: e.target.value }))
                }
                placeholder="Brief description of this account"
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? isEditing
                  ? 'Updating...'
                  : 'Creating...'
                : isEditing
                ? 'Update Account'
                : 'Create Account'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

const ChartOfAccounts = () => {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<ChartOfAccountsWithParent | null>(null);
  const [deletingAccount, setDeletingAccount] = useState<ChartOfAccountsWithParent | null>(null);

  // Queries and mutations
  const { data: accounts = [], isLoading } = useAccountsQuery({
    search: searchTerm || undefined,
    account_type: typeFilter !== 'all' ? (typeFilter as AccountType) : undefined,
  });

  const createMutation = useCreateAccountMutation();
  const updateMutation = useUpdateAccountMutation();
  const deleteMutation = useDeleteAccountMutation();

  // Permissions
  const canCreate = useAccountingPermission('accounting_coa_create');
  const canUpdate = useAccountingPermission('accounting_coa_update');
  const canDelete = useAccountingPermission('accounting_coa_delete');

  // Compute stats from accounts data
  const stats = useMemo(() => {
    const totalAccounts = accounts.length;
    const activeAccounts = accounts.filter((a) => a.is_active).length;
    const totalAssets = accounts
      .filter((a) => a.account_type === 'asset')
      .reduce((sum, a) => sum + a.current_balance, 0);
    const totalLiabilities = accounts
      .filter((a) => a.account_type === 'liability')
      .reduce((sum, a) => sum + a.current_balance, 0);

    return [
      {
        label: 'Total Accounts',
        value: totalAccounts,
        format: 'number' as const,
        icon: <BookOpen className="h-4 w-4" />,
        subtitle: `${activeAccounts} active`,
      },
      {
        label: 'Total Assets',
        value: totalAssets,
        format: 'currency' as const,
        icon: <TrendingUp className="h-4 w-4" />,
      },
      {
        label: 'Total Liabilities',
        value: totalLiabilities,
        format: 'currency' as const,
        icon: <TrendingDown className="h-4 w-4" />,
      },
      {
        label: 'Net Worth',
        value: totalAssets - totalLiabilities,
        format: 'currency' as const,
        icon: <Scale className="h-4 w-4" />,
      },
    ];
  }, [accounts]);

  // BUG-M08 FIX: Edit handler opens FormModal with pre-filled account data
  const handleEditAccount = useCallback(
    (account: ChartOfAccountsWithParent) => {
      setEditingAccount(account);
      setIsFormOpen(true);
    },
    []
  );

  // BUG-M09 FIX: Delete handler shows confirmation dialog, then soft-deletes
  const handleDeleteClick = useCallback(
    (account: ChartOfAccountsWithParent) => {
      if (account.is_system_account) {
        toast({
          title: 'Cannot Delete',
          description: 'System accounts cannot be deleted.',
          variant: 'destructive',
        });
        return;
      }
      if (account.current_balance !== 0) {
        toast({
          title: 'Cannot Delete',
          description: 'Cannot delete an account with a non-zero balance.',
          variant: 'destructive',
        });
        return;
      }
      setDeletingAccount(account);
    },
    [toast]
  );

  const handleConfirmDelete = () => {
    if (!deletingAccount) return;
    deleteMutation.mutate(deletingAccount.id, {
      onSuccess: () => {
        toast({
          title: 'Account Deleted',
          description: `Account "${deletingAccount.account_name}" has been deactivated.`,
        });
        setDeletingAccount(null);
      },
      onError: (err) => {
        toast({
          title: 'Error',
          description: err instanceof Error ? err.message : 'Failed to delete account',
          variant: 'destructive',
        });
      },
    });
  };

  const handleCreateClick = () => {
    setEditingAccount(null);
    setIsFormOpen(true);
  };

  const handleFormSubmit = (data: {
    account_code: string;
    account_name: string;
    account_type: AccountType;
    parent_account_id: string | null;
    description: string;
    is_active: boolean;
  }) => {
    if (editingAccount) {
      // Update existing account
      const updateData: ChartOfAccountsUpdate = {
        account_name: data.account_name,
        account_type: data.account_type,
        parent_account_id: data.parent_account_id,
        description: data.description || null,
        is_active: data.is_active,
      };
      updateMutation.mutate(
        { id: editingAccount.id, data: updateData },
        {
          onSuccess: () => {
            toast({
              title: 'Account Updated',
              description: `Account "${data.account_name}" has been updated.`,
            });
            setIsFormOpen(false);
            setEditingAccount(null);
          },
          onError: (err) => {
            toast({
              title: 'Error',
              description: err instanceof Error ? err.message : 'Failed to update account',
              variant: 'destructive',
            });
          },
        }
      );
    } else {
      // Create new account
      const insertData: ChartOfAccountsInsert = {
        account_code: data.account_code,
        account_name: data.account_name,
        account_type: data.account_type,
        parent_account_id: data.parent_account_id,
        description: data.description || null,
        is_active: true,
      };
      createMutation.mutate(insertData, {
        onSuccess: () => {
          toast({
            title: 'Account Created',
            description: `Account "${data.account_name}" has been created.`,
          });
          setIsFormOpen(false);
        },
        onError: (err) => {
          toast({
            title: 'Error',
            description: err instanceof Error ? err.message : 'Failed to create account',
            variant: 'destructive',
          });
        },
      });
    }
  };

  // Column definitions with working action buttons
  const columns: ColumnDef<ChartOfAccountsWithParent>[] = useMemo(
    () => [
      {
        id: 'account_code',
        header: 'Code',
        accessor: 'account_code',
        sortable: true,
        minWidth: 'min-w-[100px]',
        cell: (row) => {
          // Indent child accounts for tree-like display
          const isChild = !!row.parent_account_id;
          return (
            <span className={`font-mono font-medium ${isChild ? 'ml-6' : ''}`}>
              {row.account_code}
            </span>
          );
        },
      },
      {
        id: 'account_name',
        header: 'Account Name',
        accessor: 'account_name',
        sortable: true,
        cell: (row) => (
          <div>
            <p className="font-medium">{row.account_name}</p>
            {row.parent && (
              <p className="text-xs text-muted-foreground">
                Parent: {row.parent.account_code} - {row.parent.account_name}
              </p>
            )}
          </div>
        ),
      },
      {
        id: 'account_type',
        header: 'Type',
        accessor: 'account_type',
        sortable: true,
        cell: (_row, value) => {
          const config = ACCOUNT_TYPE_CONFIG[value as AccountType];
          return config ? (
            <Badge className={config.className}>{config.label}</Badge>
          ) : (
            <span>{String(value)}</span>
          );
        },
      },
      {
        id: 'current_balance',
        header: 'Balance',
        accessor: 'current_balance',
        sortable: true,
        className: 'text-right',
        cell: (_row, value) =>
          new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
          }).format((value as number) ?? 0),
      },
      {
        id: 'is_active',
        header: 'Status',
        accessor: 'is_active',
        cell: (_row, value) =>
          value ? (
            <Badge className="bg-green-100 text-green-800">Active</Badge>
          ) : (
            <Badge className="bg-gray-100 text-gray-800">Inactive</Badge>
          ),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: (row) => (
          <div className="flex items-center gap-1">
            {/* BUG-M08 FIX: Working Edit button with onClick handler */}
            {canUpdate && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={(e) => {
                  e.stopPropagation();
                  handleEditAccount(row);
                }}
                aria-label={`Edit account ${row.account_name}`}
              >
                <Edit className="h-4 w-4" />
              </Button>
            )}
            {/* BUG-M09 FIX: Working Delete button with onClick handler */}
            {canDelete && !row.is_system_account && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-red-600 hover:text-red-700"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteClick(row);
                }}
                aria-label={`Delete account ${row.account_name}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        ),
      },
    ],
    [canUpdate, canDelete, handleEditAccount, handleDeleteClick]
  );

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BookOpen className="h-8 w-8" />
              Chart of Accounts
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage your business account structure and organization
            </p>
          </div>
          {canCreate && (
            <Button onClick={handleCreateClick}>
              <Plus className="h-4 w-4 mr-2" />
              New Account
            </Button>
          )}
        </div>

        {/* Summary Stats */}
        <StatCards stats={stats} isLoading={isLoading} columns={4} className="mb-6" />

        {/* Accounts Table */}
        <DataTable
          columns={columns}
          data={accounts}
          isLoading={isLoading}
          emptyMessage="No accounts found. Create your first account to get started."
          filters={
            <div className="flex items-center gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search accounts..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[160px]">
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="asset">Asset</SelectItem>
                  <SelectItem value="liability">Liability</SelectItem>
                  <SelectItem value="equity">Equity</SelectItem>
                  <SelectItem value="revenue">Revenue</SelectItem>
                  <SelectItem value="expense">Expense</SelectItem>
                </SelectContent>
              </Select>
            </div>
          }
        />

        {/* Create/Edit Form Modal (BUG-M08 fix: edit now opens this modal with data) */}
        <AccountFormModal
          open={isFormOpen}
          onOpenChange={(open) => {
            setIsFormOpen(open);
            if (!open) setEditingAccount(null);
          }}
          editingAccount={editingAccount}
          accounts={accounts}
          onSubmit={handleFormSubmit}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />

        {/* Delete Confirmation Dialog (BUG-M09 fix: shows confirmation then soft-deletes) */}
        <AlertDialog
          open={!!deletingAccount}
          onOpenChange={(open) => {
            if (!open) setDeletingAccount(null);
          }}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Account</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete the account &quot;
                {deletingAccount?.account_code} - {deletingAccount?.account_name}&quot;?
                This will deactivate the account. It can be reactivated later.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirmDelete}
                className="bg-red-600 hover:bg-red-700"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete Account'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </DashboardLayout>
  );
};

export default ChartOfAccounts;
