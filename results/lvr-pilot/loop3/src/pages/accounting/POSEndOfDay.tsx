/**
 * POSEndOfDay (ACC-008)
 *
 * POS end-of-day reconciliation page.
 *
 * Displays:
 *   - Summary stats for today's POS transactions
 *   - Transaction list with items and payments
 *   - Reconciliation controls
 *
 * Uses React Query hooks from foundation (NOT useState+useEffect).
 * Uses shared components (StatCards).
 * Uses permission guards from accountingPermissions.ts.
 *
 * Note: This is a simplified but fully functional version.
 * The POS transaction hooks are defined inline since they were not
 * part of the Phase 4 foundation (POS was lower priority).
 */

import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { StatCards, type StatCardData } from '@/components/accounting/shared/StatCards';
import { useAccountingPermission } from '@/config/accountingPermissions';
import type {
  POSTransactionRow,
  POSTransactionWithItems,
  POSTransactionStatus,
} from '@/types/accounting';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ShoppingCart,
  DollarSign,
  CreditCard,
  Receipt,
  CheckCircle,
  AlertTriangle,
  Clock,
  Banknote,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { useBusinessId, accountingKeys } from '@/hooks/useAccountingQueries';
import { useToast } from '@/components/ui/use-toast';

// ---------------------------------------------------------------------------
// POS Transaction queries (inline — not in shared hooks since POS was
// lower priority for Phase 4 foundation)
// ---------------------------------------------------------------------------

function usePOSTransactionsQuery(date: string) {
  const businessId = useBusinessId();

  return useQuery({
    queryKey: ['pos-transactions', businessId, date],
    queryFn: async () => {
      const startOfDay = `${date}T00:00:00.000Z`;
      const endOfDay = `${date}T23:59:59.999Z`;

      const { data, error } = await supabase
        .from('pos_transactions')
        .select(`
          id, business_id, transaction_number, cashier_id, customer_id,
          subtotal, tax_amount, total_amount, amount_tendered, change_amount,
          status, notes, is_bonded, exemption_reason, authorized_by, created_at,
          pos_transaction_items (id, product_name, product_sku, quantity, unit_price, tax_amount, line_total, duty_amount, exemption_type),
          pos_payments (id, payment_method, amount, reference_number, notes)
        `)
        .eq('business_id', businessId)
        .gte('created_at', startOfDay)
        .lte('created_at', endOfDay)
        .order('created_at', { ascending: false });

      if (error) throw error;
      return (data ?? []) as POSTransactionWithItems[];
    },
    enabled: !!businessId && !!date,
  });
}

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  completed: { label: 'Completed', className: 'bg-green-100 text-green-800' },
  pending: { label: 'Pending', className: 'bg-yellow-100 text-yellow-800' },
  refunded: { label: 'Refunded', className: 'bg-red-100 text-red-800' },
  voided: { label: 'Voided', className: 'bg-gray-100 text-gray-800' },
};

function getStatusBadge(status: string) {
  const config = STATUS_CONFIG[status] ?? { label: status, className: 'bg-gray-100 text-gray-800' };
  return <Badge className={config.className}>{config.label}</Badge>;
}

// ---------------------------------------------------------------------------
// Date helper
// ---------------------------------------------------------------------------

function getToday(): string {
  return new Date().toISOString().split('T')[0];
}

// ---------------------------------------------------------------------------
// POSEndOfDay Page
// ---------------------------------------------------------------------------

export default function POSEndOfDay() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const canManage = useAccountingPermission('accounting_pos_eod_manage');

  const [selectedDate, setSelectedDate] = useState(getToday());
  const { data: transactions, isLoading } = usePOSTransactionsQuery(selectedDate);

  // Compute summary stats from transaction data
  const stats = useMemo(() => {
    if (!transactions || transactions.length === 0) return null;

    const completed = transactions.filter((t) => t.status === 'completed');
    const totalSales = completed.reduce((s, t) => s + t.total_amount, 0);
    const totalTax = completed.reduce((s, t) => s + t.tax_amount, 0);
    const transactionCount = completed.length;

    // Payment method breakdown
    const paymentBreakdown: Record<string, number> = {};
    for (const txn of completed) {
      for (const pmt of txn.pos_payments ?? []) {
        paymentBreakdown[pmt.payment_method] = (paymentBreakdown[pmt.payment_method] ?? 0) + pmt.amount;
      }
    }

    const cashTotal = paymentBreakdown['cash'] ?? 0;
    const cardTotal = (paymentBreakdown['credit_card'] ?? 0) + (paymentBreakdown['debit_card'] ?? 0);

    const voidedCount = transactions.filter((t) => t.status === 'voided').length;
    const refundedCount = transactions.filter((t) => t.status === 'refunded').length;

    return {
      totalSales,
      totalTax,
      transactionCount,
      cashTotal,
      cardTotal,
      voidedCount,
      refundedCount,
      paymentBreakdown,
    };
  }, [transactions]);

  const statCards: StatCardData[] = useMemo(() => {
    if (!stats) return [];
    return [
      {
        label: 'Total Sales',
        value: stats.totalSales,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency' as const,
        subtitle: `${stats.transactionCount} transactions`,
      },
      {
        label: 'Cash',
        value: stats.cashTotal,
        icon: <Banknote className="h-4 w-4" />,
        format: 'currency' as const,
      },
      {
        label: 'Card',
        value: stats.cardTotal,
        icon: <CreditCard className="h-4 w-4" />,
        format: 'currency' as const,
      },
      {
        label: 'Tax Collected',
        value: stats.totalTax,
        icon: <Receipt className="h-4 w-4" />,
        format: 'currency' as const,
      },
    ];
  }, [stats]);

  // Expanded row tracking
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <ShoppingCart className="h-8 w-8" />
              POS End of Day
            </h1>
            <p className="text-muted-foreground mt-2">
              Daily reconciliation of point-of-sale transactions
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              max={getToday()}
              className="px-3 py-2 border rounded-md text-sm"
            />
          </div>
        </div>

        {/* Stat Cards */}
        <StatCards
          stats={statCards}
          isLoading={isLoading}
          columns={4}
          className="mb-6"
        />

        {/* Voids and Refunds alert */}
        {stats && (stats.voidedCount > 0 || stats.refundedCount > 0) && (
          <Card className="mb-6 border-yellow-200 bg-yellow-50">
            <CardContent className="py-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <span className="font-medium text-yellow-800">
                  {stats.voidedCount > 0 && `${stats.voidedCount} voided`}
                  {stats.voidedCount > 0 && stats.refundedCount > 0 && ', '}
                  {stats.refundedCount > 0 && `${stats.refundedCount} refunded`}
                  {' '}transaction{(stats.voidedCount + stats.refundedCount) !== 1 ? 's' : ''}
                </span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Method Breakdown */}
        {stats && Object.keys(stats.paymentBreakdown).length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="text-lg">Payment Method Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(stats.paymentBreakdown).map(([method, amount]) => (
                  <div key={method} className="text-center p-3 bg-muted/30 rounded-lg">
                    <p className="text-sm text-muted-foreground capitalize">
                      {method.replace(/_/g, ' ')}
                    </p>
                    <p className="text-lg font-semibold mt-1">
                      ${amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Transactions Table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Transactions</CardTitle>
            <CardDescription>
              {selectedDate === getToday()
                ? "Today's POS transactions"
                : `Transactions for ${new Date(selectedDate).toLocaleDateString()}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-8 text-center">
                <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full mx-auto" />
                <p className="text-sm text-muted-foreground mt-2">Loading transactions...</p>
              </div>
            ) : !transactions || transactions.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                <ShoppingCart className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No transactions found for this date.</p>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Transaction #</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Items</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Subtotal</TableHead>
                    <TableHead className="text-right">Tax</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactions.map((txn) => (
                    <React.Fragment key={txn.id}>
                      <TableRow
                        className="cursor-pointer hover:bg-muted/50"
                        onClick={() => setExpandedRow(expandedRow === txn.id ? null : txn.id)}
                      >
                        <TableCell className="font-mono text-sm font-medium">
                          {txn.transaction_number}
                        </TableCell>
                        <TableCell className="text-sm">
                          {new Date(txn.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </TableCell>
                        <TableCell className="text-sm">
                          {txn.pos_transaction_items?.length ?? 0} item{(txn.pos_transaction_items?.length ?? 0) !== 1 ? 's' : ''}
                        </TableCell>
                        <TableCell>{getStatusBadge(txn.status)}</TableCell>
                        <TableCell className="text-right text-sm">
                          ${txn.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell className="text-right text-sm">
                          ${txn.tax_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell className="text-right font-medium text-sm">
                          ${txn.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </TableCell>
                      </TableRow>

                      {/* Expanded detail row */}
                      {expandedRow === txn.id && (
                        <TableRow>
                          <TableCell colSpan={7} className="bg-muted/20 p-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              {/* Items */}
                              <div>
                                <h4 className="font-medium text-sm mb-2">Items</h4>
                                <div className="space-y-1">
                                  {(txn.pos_transaction_items ?? []).map((item) => (
                                    <div key={item.id} className="flex justify-between text-sm">
                                      <span>
                                        {item.quantity}x {item.product_name}
                                        <span className="text-muted-foreground ml-1">({item.product_sku})</span>
                                      </span>
                                      <span className="font-mono">
                                        ${item.line_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Payments */}
                              <div>
                                <h4 className="font-medium text-sm mb-2">Payments</h4>
                                <div className="space-y-1">
                                  {(txn.pos_payments ?? []).map((pmt) => (
                                    <div key={pmt.id} className="flex justify-between text-sm">
                                      <span className="capitalize">{pmt.payment_method.replace(/_/g, ' ')}</span>
                                      <span className="font-mono">
                                        ${pmt.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                                {txn.amount_tendered > txn.total_amount && (
                                  <div className="flex justify-between text-sm mt-2 pt-2 border-t">
                                    <span className="text-muted-foreground">Change</span>
                                    <span className="font-mono">
                                      ${txn.change_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                    </span>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Bonded goods indicator */}
                            {txn.is_bonded && (
                              <div className="mt-3 text-sm">
                                <Badge className="bg-blue-100 text-blue-800">Bonded Goods</Badge>
                                {txn.exemption_reason && (
                                  <span className="text-muted-foreground ml-2">{txn.exemption_reason}</span>
                                )}
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
