/**
 * JournalEntryDetail — ACC-013
 *
 * Detail page for a single journal entry with tabs (Details, Journal Lines, Activity)
 * and a sidebar (Quick Actions, Entry Summary).
 *
 * Bug fixes:
 *   BUG-H04: Post button uses usePostJournalEntryMutation (routes through GeneralLedgerService)
 *   BUG-H05: Reverse button uses useReverseJournalEntryMutation (creates reversing entry through service)
 *
 * Architecture:
 *   - Uses DetailLayout shared component for consistent structure
 *   - React Query hooks for data fetching and mutations (no raw useState+useEffect)
 *   - Post and Reverse route through GeneralLedgerService (not direct status updates)
 *   - Transaction lines displayed in a real Table with debit/credit columns
 */

import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  CheckCircle,
  AlertCircle,
  FileText,
  Edit,
  Trash2,
} from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { format } from 'date-fns';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import {
  DetailLayout,
  type StatusBadgeConfig,
} from '@/components/accounting/shared/DetailLayout';
import {
  useJournalEntryQuery,
  usePostJournalEntryMutation,
  useReverseJournalEntryMutation,
  useDeleteJournalEntryMutation,
} from '@/hooks/useJournalEntries';
import { useAccountingPermission } from '@/config/accountingPermissions';
import type { JournalEntryWithTransactions } from '@/types/accounting';

// ---------------------------------------------------------------------------
// Status → badge variant mapping
// ---------------------------------------------------------------------------

function getStatusBadgeConfig(status: string): StatusBadgeConfig {
  switch (status) {
    case 'draft':
      return { status: 'Draft', variant: 'default' };
    case 'posted':
      return { status: 'Posted', variant: 'success' };
    case 'reversed':
      return { status: 'Reversed', variant: 'destructive' };
    default:
      return { status, variant: 'default' };
  }
}

// ---------------------------------------------------------------------------
// Details Tab
// ---------------------------------------------------------------------------

function DetailsTab({ entry }: { entry: JournalEntryWithTransactions }) {
  const totalDebits = entry.account_transactions?.reduce(
    (sum, tx) => sum + (tx.debit_amount ?? 0),
    0
  ) ?? 0;
  const totalCredits = entry.account_transactions?.reduce(
    (sum, tx) => sum + (tx.credit_amount ?? 0),
    0
  ) ?? 0;
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Journal Entry Information</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">Entry Number</label>
            <p className="text-sm font-mono">{entry.entry_number}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Status</label>
            <div className="mt-1">
              <Badge
                className={
                  entry.status === 'posted'
                    ? 'bg-green-100 text-green-800'
                    : entry.status === 'reversed'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-gray-100 text-gray-800'
                }
              >
                {entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
              </Badge>
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Entry Date</label>
            <p className="text-sm">{format(new Date(entry.entry_date), 'MMM dd, yyyy')}</p>
          </div>
          <div>
            <label className="text-sm font-medium text-muted-foreground">Entry Type</label>
            <p className="text-sm">{entry.entry_type || 'Manual'}</p>
          </div>
          {entry.reference_number && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Reference</label>
              <p className="text-sm">{entry.reference_number}</p>
            </div>
          )}
          <div className="col-span-2">
            <label className="text-sm font-medium text-muted-foreground">Description</label>
            <p className="text-sm">{entry.description || 'No description'}</p>
          </div>
        </div>

        <div className="border-t pt-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">Total Debits</label>
              <p className="text-lg font-semibold">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                }).format(totalDebits)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">Total Credits</label>
              <p className="text-lg font-semibold">
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                }).format(totalCredits)}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">Balance Status</label>
              <div className="mt-1">
                {isBalanced ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Balanced
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Unbalanced
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>

        {entry.notes && (
          <div>
            <label className="text-sm font-medium text-muted-foreground">Notes</label>
            <p className="text-sm mt-1 p-3 bg-muted rounded-md">{entry.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Journal Lines Tab
// ---------------------------------------------------------------------------

function JournalLinesTab({ entry }: { entry: JournalEntryWithTransactions }) {
  const transactions = entry.account_transactions ?? [];
  const totalDebits = transactions.reduce((sum, tx) => sum + (tx.debit_amount ?? 0), 0);
  const totalCredits = transactions.reduce((sum, tx) => sum + (tx.credit_amount ?? 0), 0);

  const formatAmount = (amount: number) =>
    amount > 0
      ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
      : '-';

  return (
    <Card>
      <CardHeader>
        <CardTitle>Journal Entry Lines</CardTitle>
      </CardHeader>
      <CardContent>
        {transactions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Account</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Debit</TableHead>
                <TableHead className="text-right">Credit</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium">
                        {tx.chart_of_accounts?.account_name ?? 'Unknown Account'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {tx.chart_of_accounts?.account_code ?? ''}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>{tx.description || '-'}</TableCell>
                  <TableCell className="text-right">
                    {formatAmount(tx.debit_amount ?? 0)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatAmount(tx.credit_amount ?? 0)}
                  </TableCell>
                </TableRow>
              ))}
              <TableRow className="border-t-2 font-semibold">
                <TableCell colSpan={2}>Total</TableCell>
                <TableCell className="text-right">{formatAmount(totalDebits)}</TableCell>
                <TableCell className="text-right">{formatAmount(totalCredits)}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        ) : (
          <p className="text-muted-foreground text-center py-8">
            No journal entry lines found
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Activity Tab
// ---------------------------------------------------------------------------

function ActivityTab({ entry }: { entry: JournalEntryWithTransactions }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Log</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Created</span>
            <span>{format(new Date(entry.created_at), 'MMM dd, yyyy HH:mm')}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Last Updated</span>
            <span>{format(new Date(entry.updated_at), 'MMM dd, yyyy HH:mm')}</span>
          </div>
          {entry.posted_at && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Posted</span>
              <span>{format(new Date(entry.posted_at), 'MMM dd, yyyy HH:mm')}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Sidebar: Quick Actions
// ---------------------------------------------------------------------------

function QuickActionsSidebar({
  entry,
  isBalanced,
  onPost,
  onReverse,
  onDelete,
  isPosting,
  isReversing,
  isDeleting,
}: {
  entry: JournalEntryWithTransactions;
  isBalanced: boolean;
  onPost: () => void;
  onReverse: () => void;
  onDelete: () => void;
  isPosting: boolean;
  isReversing: boolean;
  isDeleting: boolean;
}) {
  const canPost = useAccountingPermission('accounting_journal_entries_post');
  const canVoid = useAccountingPermission('accounting_journal_entries_void');
  const canDelete = useAccountingPermission('accounting_journal_entries_delete');

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {entry.status === 'draft' && isBalanced && canPost && (
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={onPost}
            disabled={isPosting}
          >
            <CheckCircle className="h-4 w-4 mr-2" />
            {isPosting ? 'Posting...' : 'Post Entry'}
          </Button>
        )}

        {entry.status === 'posted' && canVoid && (
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-red-600 hover:text-red-700"
            onClick={onReverse}
            disabled={isReversing}
          >
            <AlertCircle className="h-4 w-4 mr-2" />
            {isReversing ? 'Reversing...' : 'Reverse Entry'}
          </Button>
        )}

        {entry.status === 'draft' && canDelete && (
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-red-600 hover:text-red-700"
            onClick={onDelete}
            disabled={isDeleting}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            {isDeleting ? 'Discarding...' : 'Discard Draft'}
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Sidebar: Entry Summary
// ---------------------------------------------------------------------------

function EntrySummary({ entry }: { entry: JournalEntryWithTransactions }) {
  const totalDebits = entry.account_transactions?.reduce(
    (sum, tx) => sum + (tx.debit_amount ?? 0),
    0
  ) ?? 0;
  const totalCredits = entry.account_transactions?.reduce(
    (sum, tx) => sum + (tx.credit_amount ?? 0),
    0
  ) ?? 0;
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;
  const difference = Math.abs(totalDebits - totalCredits);

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Entry Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Entry Number</span>
            <span className="font-mono">{entry.entry_number}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status</span>
            <Badge
              className={
                entry.status === 'posted'
                  ? 'bg-green-100 text-green-800'
                  : entry.status === 'reversed'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-gray-100 text-gray-800'
              }
              style={{ fontSize: '0.75rem' }}
            >
              {entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Entry Date</span>
            <span>{format(new Date(entry.entry_date), 'MMM dd, yyyy')}</span>
          </div>
          <div className="flex justify-between border-t pt-3">
            <span className="text-muted-foreground">Total Debits</span>
            <span className="font-semibold">{formatCurrency(totalDebits)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total Credits</span>
            <span className="font-semibold">{formatCurrency(totalCredits)}</span>
          </div>
          <div className="flex justify-between border-t pt-3">
            <span className="text-muted-foreground">Difference</span>
            <span
              className={`font-semibold ${!isBalanced ? 'text-red-600' : 'text-green-600'}`}
            >
              {formatCurrency(difference)}
            </span>
          </div>
          <div className="text-center pt-2">
            {isBalanced ? (
              <Badge className="bg-green-100 text-green-800">
                <CheckCircle className="h-3 w-3 mr-1" />
                Entry Balanced
              </Badge>
            ) : (
              <Badge className="bg-red-100 text-red-800">
                <AlertCircle className="h-3 w-3 mr-1" />
                Entry Unbalanced
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

const JournalEntryDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Data fetching with React Query
  const { data: entry, isLoading, error } = useJournalEntryQuery(id ?? '');

  // BUG-H04 FIX: Post through GeneralLedgerService (not direct status update)
  const postMutation = usePostJournalEntryMutation();

  // BUG-H05 FIX: Reverse through GeneralLedgerService (creates reversing entry)
  const reverseMutation = useReverseJournalEntryMutation();

  // Delete (draft only)
  const deleteMutation = useDeleteJournalEntryMutation();

  // Permission check for edit
  const canEdit = useAccountingPermission('accounting_journal_entries_update');

  // Computed values
  const totalDebits = useMemo(
    () => entry?.account_transactions?.reduce((sum, tx) => sum + (tx.debit_amount ?? 0), 0) ?? 0,
    [entry]
  );
  const totalCredits = useMemo(
    () => entry?.account_transactions?.reduce((sum, tx) => sum + (tx.credit_amount ?? 0), 0) ?? 0,
    [entry]
  );
  const isBalanced = Math.abs(totalDebits - totalCredits) < 0.01;

  // BUG-H04 FIX: Post handler routes through GeneralLedgerService
  const handlePost = () => {
    if (!entry) return;
    postMutation.mutate(entry.id, {
      onSuccess: () => {
        toast({ title: 'Success', description: 'Journal entry posted to general ledger' });
      },
      onError: (err) => {
        toast({
          title: 'Error',
          description: err instanceof Error ? err.message : 'Failed to post journal entry',
          variant: 'destructive',
        });
      },
    });
  };

  // BUG-H05 FIX: Reverse handler routes through GeneralLedgerService
  const handleReverse = () => {
    if (!entry) return;
    if (!confirm('Are you sure you want to reverse this journal entry? This will create a reversing entry with swapped debits and credits.')) {
      return;
    }
    reverseMutation.mutate(entry.id, {
      onSuccess: () => {
        toast({
          title: 'Success',
          description: 'Journal entry reversed. A reversing entry has been created.',
        });
      },
      onError: (err) => {
        toast({
          title: 'Error',
          description: err instanceof Error ? err.message : 'Failed to reverse journal entry',
          variant: 'destructive',
        });
      },
    });
  };

  const handleDelete = () => {
    if (!entry) return;
    if (!confirm('Are you sure you want to discard this draft journal entry?')) return;
    deleteMutation.mutate(entry.id, {
      onSuccess: () => {
        toast({ title: 'Success', description: 'Draft journal entry discarded' });
        navigate('/accounting/journal-entries');
      },
      onError: (err) => {
        toast({
          title: 'Error',
          description: err instanceof Error ? err.message : 'Failed to discard draft',
          variant: 'destructive',
        });
      },
    });
  };

  const handleEdit = () => {
    navigate(`/accounting/journal-entries/${id}/edit`);
  };

  // Error state
  if (error || (!isLoading && !entry)) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <Button
            variant="ghost"
            size="sm"
            className="mb-4"
            onClick={() => navigate('/accounting/journal-entries')}
          >
            Back to Journal Entries
          </Button>
          <Card>
            <CardContent className="p-6 text-center">
              <h3 className="text-lg font-medium mb-2">
                {error instanceof Error ? error.message : 'Journal entry not found'}
              </h3>
              <p className="text-muted-foreground mb-4">
                The journal entry you are looking for does not exist or you do not have
                permission to view it.
              </p>
              <Button onClick={() => navigate('/accounting/journal-entries')}>
                Go to Journal Entries List
              </Button>
            </CardContent>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Build action buttons for the header
  const actionButtons = [];
  if (entry?.status === 'draft' && isBalanced) {
    actionButtons.push({
      label: postMutation.isPending ? 'Posting...' : 'Post Entry',
      onClick: handlePost,
      icon: <CheckCircle className="h-4 w-4" />,
      variant: 'default' as const,
      disabled: postMutation.isPending,
    });
  }
  if (entry?.status === 'posted') {
    actionButtons.push({
      label: reverseMutation.isPending ? 'Reversing...' : 'Reverse Entry',
      onClick: handleReverse,
      icon: <AlertCircle className="h-4 w-4" />,
      variant: 'outline' as const,
      className: 'text-red-600 hover:text-red-700',
      disabled: reverseMutation.isPending,
    });
  }
  if (entry?.status === 'draft' && canEdit) {
    actionButtons.push({
      label: 'Edit',
      onClick: handleEdit,
      icon: <Edit className="h-4 w-4" />,
      variant: 'outline' as const,
    });
  }

  return (
    <DashboardLayout>
      <DetailLayout
        title={entry ? `Journal Entry ${entry.entry_number}` : 'Loading...'}
        subtitle={entry?.description ?? undefined}
        breadcrumbs={[
          { label: 'Accounting', href: '/accounting' },
          { label: 'Journal Entries', href: '/accounting/journal-entries' },
          { label: entry?.entry_number ?? '...' },
        ]}
        statusBadge={entry ? getStatusBadgeConfig(entry.status) : undefined}
        actionButtons={actionButtons}
        isLoading={isLoading}
        onBack={() => navigate('/accounting/journal-entries')}
        tabs={
          entry
            ? [
                {
                  id: 'details',
                  label: 'Details',
                  content: <DetailsTab entry={entry} />,
                },
                {
                  id: 'lines',
                  label: 'Journal Lines',
                  content: <JournalLinesTab entry={entry} />,
                },
                {
                  id: 'activity',
                  label: 'Activity',
                  content: <ActivityTab entry={entry} />,
                },
              ]
            : [{ id: 'loading', label: 'Loading', content: null }]
        }
        sidebar={
          entry ? (
            <>
              <QuickActionsSidebar
                entry={entry}
                isBalanced={isBalanced}
                onPost={handlePost}
                onReverse={handleReverse}
                onDelete={handleDelete}
                isPosting={postMutation.isPending}
                isReversing={reverseMutation.isPending}
                isDeleting={deleteMutation.isPending}
              />
              <EntrySummary entry={entry} />
            </>
          ) : undefined
        }
      />
    </DashboardLayout>
  );
};

export default JournalEntryDetail;
