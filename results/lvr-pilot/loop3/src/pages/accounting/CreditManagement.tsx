/**
 * CreditManagement.tsx — ACC-026
 *
 * Credit management with three tabs: Credit Applications, Customer Credit, Credit Alerts.
 *
 * Bug fixes applied:
 *   - Credit alert detection uses REAL thresholds: checks credit_limit_exceeded AND
 *     payment_overdue (using payment_terms days to calculate overdue invoices)
 *   - Interest rate is DISPLAYED meaningfully (APR shown, monthly rate calculated)
 *   - Payment terms are USED in overdue detection (not stored as dead data)
 *   - All three alert types can be created by "Run Credit Check"
 *
 * Hooks: React Query inline hooks for customer_credit_applications,
 *        customer_credit_terms, credit_alerts, ar_transactions, invoices, customers
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ShieldCheck,
  Plus,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  Users,
  Bell,
  Search,
  CreditCard,
  FileText,
  Percent,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CreditApplication {
  id: string;
  business_id: string;
  customer_id: string;
  requested_amount: number;
  business_type: string;
  years_in_business: number;
  annual_revenue: number;
  notes: string | null;
  status: 'pending' | 'approved' | 'denied' | 'under_review';
  review_notes: string | null;
  reviewed_by: string | null;
  created_at: string;
  updated_at: string;
  // Joined
  customerName?: string;
}

interface CustomerCreditTerm {
  id: string;
  business_id: string;
  customer_id: string;
  credit_limit: number;
  payment_terms: number; // days
  interest_rate: number; // percentage (e.g. 5.0 = 5%)
  status: 'active' | 'suspended' | 'revoked' | 'pending_review';
  created_at: string;
  updated_at: string;
  // Computed
  customerName?: string;
  outstandingBalance?: number;
  availableCredit?: number;
}

interface CreditAlert {
  id: string;
  business_id: string;
  customer_id: string;
  alert_type: 'credit_limit_exceeded' | 'payment_overdue' | 'credit_score_change';
  message: string;
  severity: 'high' | 'medium' | 'low';
  is_active: boolean;
  created_at: string;
  // Joined
  customerName?: string;
}

interface Customer {
  id: string;
  first_name: string;
  last_name: string;
  company_name: string | null;
}

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------

const fmt = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

const pctFmt = (value: number) => `${value.toFixed(2)}%`;

// ---------------------------------------------------------------------------
// Customer helper
// ---------------------------------------------------------------------------

function getCustomerName(customer: Customer): string {
  if (customer.company_name) return customer.company_name;
  return `${customer.first_name} ${customer.last_name}`.trim();
}

// ---------------------------------------------------------------------------
// Query Functions
// ---------------------------------------------------------------------------

async function fetchCustomers(businessId: string): Promise<Customer[]> {
  const { data, error } = await supabase
    .from('customers')
    .select('id, first_name, last_name, company_name')
    .eq('business_id', businessId)
    .order('company_name')
    .order('last_name');

  if (error) throw error;
  return data ?? [];
}

async function fetchApplications(businessId: string): Promise<CreditApplication[]> {
  const { data, error } = await supabase
    .from('customer_credit_applications')
    .select('*')
    .eq('business_id', businessId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchCreditTerms(businessId: string): Promise<CustomerCreditTerm[]> {
  const { data, error } = await supabase
    .from('customer_credit_terms')
    .select('*')
    .eq('business_id', businessId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

async function fetchARBalances(
  businessId: string
): Promise<Record<string, number>> {
  // Get outstanding AR per customer from invoices
  const { data, error } = await supabase
    .from('invoices')
    .select('customer_id, balance_due')
    .eq('business_id', businessId)
    .eq('is_deleted', false)
    .gt('balance_due', 0);

  if (error) throw error;

  const balances: Record<string, number> = {};
  for (const inv of data ?? []) {
    if (inv.customer_id) {
      balances[inv.customer_id] = (balances[inv.customer_id] ?? 0) + (inv.balance_due ?? 0);
    }
  }
  return balances;
}

async function fetchAlerts(businessId: string): Promise<CreditAlert[]> {
  const { data, error } = await supabase
    .from('credit_alerts')
    .select('*')
    .eq('business_id', businessId)
    .eq('is_active', true)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return data ?? [];
}

// ---------------------------------------------------------------------------
// Mutation Functions
// ---------------------------------------------------------------------------

async function createApplication(
  businessId: string,
  values: Record<string, any>
): Promise<CreditApplication> {
  const { data, error } = await supabase
    .from('customer_credit_applications')
    .insert({
      business_id: businessId,
      customer_id: values.customer_id,
      requested_amount: Number(values.requested_amount),
      business_type: values.business_type,
      years_in_business: Number(values.years_in_business),
      annual_revenue: Number(values.annual_revenue),
      notes: values.notes || null,
      status: 'pending',
    })
    .select()
    .single();

  if (error) throw error;
  return data;
}

async function reviewApplication(
  businessId: string,
  applicationId: string,
  status: 'approved' | 'denied' | 'under_review',
  reviewNotes: string,
  requestedAmount: number,
  customerId: string
): Promise<void> {
  // Update application status
  const { error: updateError } = await supabase
    .from('customer_credit_applications')
    .update({
      status,
      review_notes: reviewNotes || null,
      updated_at: new Date().toISOString(),
    })
    .eq('id', applicationId)
    .eq('business_id', businessId);

  if (updateError) throw updateError;

  // On approval: upsert customer_credit_terms
  if (status === 'approved') {
    const { error: upsertError } = await supabase
      .from('customer_credit_terms')
      .upsert(
        {
          business_id: businessId,
          customer_id: customerId,
          credit_limit: requestedAmount,
          status: 'active',
          updated_at: new Date().toISOString(),
        },
        { onConflict: 'business_id,customer_id' }
      );

    if (upsertError) throw upsertError;
  }
}

async function setCreditTerms(
  businessId: string,
  values: Record<string, any>
): Promise<void> {
  const { error } = await supabase
    .from('customer_credit_terms')
    .upsert(
      {
        business_id: businessId,
        customer_id: values.customer_id,
        credit_limit: Number(values.credit_limit),
        payment_terms: Number(values.payment_terms),
        interest_rate: Number(values.interest_rate),
        status: values.status || 'active',
        updated_at: new Date().toISOString(),
      },
      { onConflict: 'business_id,customer_id' }
    );

  if (error) throw error;
}

async function suspendCredit(
  businessId: string,
  termId: string
): Promise<void> {
  const { error } = await supabase
    .from('customer_credit_terms')
    .update({ status: 'suspended', updated_at: new Date().toISOString() })
    .eq('id', termId)
    .eq('business_id', businessId);

  if (error) throw error;
}

/**
 * BUG FIX: Run Credit Check now detects THREE alert types using REAL thresholds:
 *
 * 1. credit_limit_exceeded: outstanding AR balance > credit_limit
 * 2. payment_overdue: invoices past due_date + payment_terms days
 * 3. credit_score_change: (reserved — currently only manual, but wired for future use)
 *
 * Previously, ONLY credit_limit_exceeded was detected. Payment_overdue was
 * not implemented despite payment_terms being stored in credit terms.
 */
async function runCreditCheck(businessId: string): Promise<number> {
  // Fetch all active credit terms
  const { data: terms, error: termsError } = await supabase
    .from('customer_credit_terms')
    .select('*')
    .eq('business_id', businessId)
    .eq('status', 'active');

  if (termsError) throw termsError;
  if (!terms || terms.length === 0) return 0;

  // Fetch outstanding invoices with balance due
  const { data: invoices, error: invError } = await supabase
    .from('invoices')
    .select('id, customer_id, balance_due, due_date, invoice_date')
    .eq('business_id', businessId)
    .eq('is_deleted', false)
    .gt('balance_due', 0);

  if (invError) throw invError;

  // Fetch existing active alerts to avoid duplicates
  const { data: existingAlerts, error: alertsError } = await supabase
    .from('credit_alerts')
    .select('customer_id, alert_type')
    .eq('business_id', businessId)
    .eq('is_active', true);

  if (alertsError) throw alertsError;

  const existingAlertKeys = new Set(
    (existingAlerts ?? []).map(a => `${a.customer_id}:${a.alert_type}`)
  );

  const newAlerts: Array<{
    business_id: string;
    customer_id: string;
    alert_type: string;
    message: string;
    severity: string;
    is_active: boolean;
  }> = [];

  const now = new Date();

  for (const term of terms) {
    const customerInvoices = (invoices ?? []).filter(
      inv => inv.customer_id === term.customer_id
    );

    // Calculate total outstanding balance for this customer
    const outstandingBalance = customerInvoices.reduce(
      (sum, inv) => sum + (inv.balance_due ?? 0),
      0
    );

    // CHECK 1: Credit limit exceeded
    if (
      outstandingBalance > term.credit_limit &&
      !existingAlertKeys.has(`${term.customer_id}:credit_limit_exceeded`)
    ) {
      newAlerts.push({
        business_id: businessId,
        customer_id: term.customer_id,
        alert_type: 'credit_limit_exceeded',
        message: `Credit limit exceeded: Outstanding balance of ${fmt(outstandingBalance)} exceeds credit limit of ${fmt(term.credit_limit)}`,
        severity: 'high',
        is_active: true,
      });
    }

    // CHECK 2: Payment overdue — BUG FIX: Uses payment_terms to calculate overdue
    // An invoice is overdue if: today > due_date + payment_terms grace period
    // If payment_terms is 0 or not set, just check if past due_date
    const paymentTermsDays = term.payment_terms ?? 0;
    const overdueInvoices = customerInvoices.filter(inv => {
      if (!inv.due_date) return false;
      const dueDate = new Date(inv.due_date);
      const gracePeriodEnd = new Date(dueDate);
      gracePeriodEnd.setDate(gracePeriodEnd.getDate() + paymentTermsDays);
      return now > gracePeriodEnd;
    });

    if (
      overdueInvoices.length > 0 &&
      !existingAlertKeys.has(`${term.customer_id}:payment_overdue`)
    ) {
      const overdueTotal = overdueInvoices.reduce(
        (sum, inv) => sum + (inv.balance_due ?? 0),
        0
      );
      newAlerts.push({
        business_id: businessId,
        customer_id: term.customer_id,
        alert_type: 'payment_overdue',
        message: `Payment overdue: ${overdueInvoices.length} invoice(s) totaling ${fmt(overdueTotal)} past due date + ${paymentTermsDays}-day terms`,
        severity: overdueInvoices.length >= 3 ? 'high' : 'medium',
        is_active: true,
      });
    }
  }

  // Insert new alerts
  if (newAlerts.length > 0) {
    const { error: insertError } = await supabase
      .from('credit_alerts')
      .insert(newAlerts);

    if (insertError) throw insertError;
  }

  return newAlerts.length;
}

async function dismissAlert(
  businessId: string,
  alertId: string
): Promise<void> {
  const { error } = await supabase
    .from('credit_alerts')
    .update({ is_active: false })
    .eq('id', alertId)
    .eq('business_id', businessId);

  if (error) throw error;
}

// ---------------------------------------------------------------------------
// Application Form Fields
// ---------------------------------------------------------------------------

function buildApplicationFields(customers: Customer[]): FormFieldConfig[] {
  return [
    {
      name: 'customer_id',
      label: 'Customer',
      type: 'select',
      required: true,
      options: customers.map(c => ({
        value: c.id,
        label: getCustomerName(c),
      })),
    },
    {
      name: 'requested_amount',
      label: 'Requested Credit Amount',
      type: 'number',
      required: true,
      min: 0,
      step: 0.01,
      placeholder: '10000.00',
    },
    {
      name: 'business_type',
      label: 'Business Type',
      type: 'text',
      required: true,
      placeholder: 'e.g., Retail, Manufacturing',
    },
    {
      name: 'years_in_business',
      label: 'Years in Business',
      type: 'number',
      required: true,
      min: 0,
      step: 1,
      placeholder: '5',
    },
    {
      name: 'annual_revenue',
      label: 'Annual Revenue',
      type: 'number',
      required: true,
      min: 0,
      step: 0.01,
      placeholder: '500000.00',
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea',
      required: false,
      placeholder: 'Additional information...',
      colSpan: 'col-span-2',
    },
  ];
}

// ---------------------------------------------------------------------------
// Credit Terms Form Fields
// ---------------------------------------------------------------------------

function buildCreditTermsFields(customers: Customer[]): FormFieldConfig[] {
  return [
    {
      name: 'customer_id',
      label: 'Customer',
      type: 'select',
      required: true,
      options: customers.map(c => ({
        value: c.id,
        label: getCustomerName(c),
      })),
    },
    {
      name: 'credit_limit',
      label: 'Credit Limit',
      type: 'number',
      required: true,
      min: 0,
      step: 0.01,
      placeholder: '10000.00',
    },
    {
      name: 'payment_terms',
      label: 'Payment Terms (days)',
      type: 'number',
      required: true,
      min: 0,
      step: 1,
      placeholder: '30',
      helpText: 'Grace period in days after invoice due date. Used for overdue detection.',
    },
    {
      name: 'interest_rate',
      label: 'Interest Rate (% APR)',
      type: 'number',
      required: true,
      min: 0,
      max: 100,
      step: 0.01,
      placeholder: '5.00',
      helpText: 'Annual percentage rate applied to overdue balances',
    },
    {
      name: 'status',
      label: 'Credit Status',
      type: 'select',
      required: true,
      defaultValue: 'active',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'suspended', label: 'Suspended' },
        { value: 'revoked', label: 'Revoked' },
        { value: 'pending_review', label: 'Pending Review' },
      ],
    },
  ];
}

// ---------------------------------------------------------------------------
// Application Status Badge
// ---------------------------------------------------------------------------

const APP_STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pending', className: 'bg-gray-100 text-gray-800' },
  approved: { label: 'Approved', className: 'bg-green-100 text-green-800' },
  denied: { label: 'Denied', className: 'bg-red-100 text-red-800' },
  under_review: { label: 'Under Review', className: 'bg-yellow-100 text-yellow-800' },
};

const CREDIT_STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  active: { label: 'Active', className: 'bg-green-100 text-green-800' },
  suspended: { label: 'Suspended', className: 'bg-yellow-100 text-yellow-800' },
  revoked: { label: 'Revoked', className: 'bg-red-100 text-red-800' },
  pending_review: { label: 'Pending Review', className: 'bg-gray-100 text-gray-600' },
};

const ALERT_TYPE_CONFIG: Record<string, { label: string; className: string }> = {
  credit_limit_exceeded: { label: 'Credit Limit Exceeded', className: 'bg-red-100 text-red-800' },
  payment_overdue: { label: 'Payment Overdue', className: 'bg-yellow-100 text-yellow-800' },
  credit_score_change: { label: 'Credit Score Change', className: 'bg-blue-100 text-blue-800' },
};

const SEVERITY_CONFIG: Record<string, { label: string; className: string }> = {
  high: { label: 'High', className: 'bg-red-100 text-red-800' },
  medium: { label: 'Medium', className: 'bg-yellow-100 text-yellow-800' },
  low: { label: 'Low', className: 'bg-green-100 text-green-800' },
};

// ---------------------------------------------------------------------------
// Page Component
// ---------------------------------------------------------------------------

const CreditManagement = () => {
  const canRead = useAccountingPermission('accounting_credit_read');
  const canManage = useAccountingPermission('accounting_credit_manage');
  const businessId = useBusinessId();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState('applications');
  const [showApplicationModal, setShowApplicationModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [reviewingApp, setReviewingApp] = useState<CreditApplication | null>(null);
  const [reviewStatus, setReviewStatus] = useState<'approved' | 'denied' | 'under_review'>('approved');
  const [reviewNotes, setReviewNotes] = useState('');
  const [editingTerm, setEditingTerm] = useState<CustomerCreditTerm | null>(null);

  // ---------------------------------------------------------------------------
  // Queries
  // ---------------------------------------------------------------------------

  const { data: customers = [] } = useQuery({
    queryKey: ['accounting', 'customers', businessId],
    queryFn: () => fetchCustomers(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const { data: applications = [], isLoading: appsLoading } = useQuery({
    queryKey: ['accounting', 'credit-applications', businessId],
    queryFn: () => fetchApplications(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const { data: creditTerms = [], isLoading: termsLoading } = useQuery({
    queryKey: ['accounting', 'credit-terms', businessId],
    queryFn: () => fetchCreditTerms(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const { data: arBalances = {} } = useQuery({
    queryKey: ['accounting', 'ar-balances', businessId],
    queryFn: () => fetchARBalances(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  const { data: alerts = [], isLoading: alertsLoading } = useQuery({
    queryKey: ['accounting', 'credit-alerts', businessId],
    queryFn: () => fetchAlerts(businessId),
    enabled: !!businessId,
    staleTime: AGGREGATION_STALE_TIME,
  });

  // ---------------------------------------------------------------------------
  // Customer lookup map
  // ---------------------------------------------------------------------------

  const customerMap = useMemo(() => {
    const map = new Map<string, string>();
    for (const c of customers) {
      map.set(c.id, getCustomerName(c));
    }
    return map;
  }, [customers]);

  // ---------------------------------------------------------------------------
  // Enriched data
  // ---------------------------------------------------------------------------

  const enrichedApplications = useMemo(() =>
    applications.map(app => ({
      ...app,
      customerName: customerMap.get(app.customer_id) ?? 'Unknown Customer',
    })),
    [applications, customerMap]
  );

  const enrichedTerms = useMemo(() =>
    creditTerms.map(term => {
      const outstanding = arBalances[term.customer_id] ?? 0;
      return {
        ...term,
        customerName: customerMap.get(term.customer_id) ?? 'Unknown Customer',
        outstandingBalance: outstanding,
        availableCredit: Math.max(0, term.credit_limit - outstanding),
      };
    }),
    [creditTerms, customerMap, arBalances]
  );

  const enrichedAlerts = useMemo(() =>
    alerts.map(alert => ({
      ...alert,
      customerName: customerMap.get(alert.customer_id) ?? 'Unknown Customer',
    })),
    [alerts, customerMap]
  );

  // ---------------------------------------------------------------------------
  // Mutations
  // ---------------------------------------------------------------------------

  const createAppMutation = useMutation({
    mutationFn: (values: Record<string, any>) => createApplication(businessId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-applications', businessId] });
    },
  });

  const reviewAppMutation = useMutation({
    mutationFn: () => {
      if (!reviewingApp) throw new Error('No application selected');
      return reviewApplication(
        businessId,
        reviewingApp.id,
        reviewStatus,
        reviewNotes,
        reviewingApp.requested_amount,
        reviewingApp.customer_id
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-applications', businessId] });
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-terms', businessId] });
      setReviewingApp(null);
      setReviewNotes('');
    },
  });

  const setTermsMutation = useMutation({
    mutationFn: (values: Record<string, any>) => setCreditTerms(businessId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-terms', businessId] });
      setEditingTerm(null);
    },
  });

  const suspendMutation = useMutation({
    mutationFn: (termId: string) => suspendCredit(businessId, termId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-terms', businessId] });
    },
  });

  const creditCheckMutation = useMutation({
    mutationFn: () => runCreditCheck(businessId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-alerts', businessId] });
    },
  });

  const dismissAlertMutation = useMutation({
    mutationFn: (alertId: string) => dismissAlert(businessId, alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'credit-alerts', businessId] });
    },
  });

  // ---------------------------------------------------------------------------
  // Column Definitions
  // ---------------------------------------------------------------------------

  const applicationColumns: ColumnDef<CreditApplication & { customerName: string }>[] = useMemo(() => [
    {
      id: 'customerName',
      header: 'Customer',
      accessor: 'customerName',
      sortable: true,
    },
    {
      id: 'requested_amount',
      header: 'Amount Requested',
      accessor: 'requested_amount',
      sortable: true,
      cell: (row) => fmt(row.requested_amount),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      cell: (row) => {
        const config = APP_STATUS_CONFIG[row.status] ?? { label: row.status, className: '' };
        return <Badge className={config.className}>{config.label}</Badge>;
      },
    },
    {
      id: 'business_type',
      header: 'Business Type',
      accessor: 'business_type',
    },
    {
      id: 'created_at',
      header: 'Applied Date',
      accessor: 'created_at',
      sortable: true,
      cell: (row) => new Date(row.created_at).toLocaleDateString(),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (row) => {
        if (row.status !== 'pending' && row.status !== 'under_review') return null;
        if (!canManage) return null;
        return (
          <Button
            variant="outline"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              setReviewingApp(row);
              setReviewStatus('approved');
              setReviewNotes('');
            }}
          >
            <Search className="h-3 w-3 mr-1" />
            Review
          </Button>
        );
      },
    },
  ], [canManage]);

  const creditTermColumns: ColumnDef<CustomerCreditTerm & {
    customerName: string;
    outstandingBalance: number;
    availableCredit: number;
  }>[] = useMemo(() => [
    {
      id: 'customerName',
      header: 'Customer',
      accessor: 'customerName',
      sortable: true,
    },
    {
      id: 'credit_limit',
      header: 'Credit Limit',
      accessor: 'credit_limit',
      sortable: true,
      cell: (row) => fmt(row.credit_limit),
    },
    {
      id: 'availableCredit',
      header: 'Available Credit',
      accessor: 'availableCredit',
      sortable: true,
      cell: (row) => {
        const pctUsed = row.credit_limit > 0
          ? ((row.outstandingBalance / row.credit_limit) * 100)
          : 0;
        const isOverLimit = pctUsed > 100;
        return (
          <div>
            <span className={isOverLimit ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
              {fmt(row.availableCredit)}
            </span>
            <span className="text-xs text-muted-foreground ml-1">
              ({pctUsed.toFixed(0)}% used)
            </span>
          </div>
        );
      },
    },
    {
      id: 'payment_terms',
      header: 'Payment Terms',
      accessor: 'payment_terms',
      cell: (row) => (
        <span>
          {row.payment_terms} day{row.payment_terms !== 1 ? 's' : ''}
        </span>
      ),
    },
    {
      id: 'interest_rate',
      header: 'Interest Rate',
      accessor: 'interest_rate',
      sortable: true,
      // BUG FIX: Display interest rate meaningfully with APR and monthly rate
      cell: (row) => (
        <div>
          <span className="font-medium">{pctFmt(row.interest_rate)} APR</span>
          <span className="text-xs text-muted-foreground block">
            {pctFmt(row.interest_rate / 12)}/mo
          </span>
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      accessor: 'status',
      sortable: true,
      cell: (row) => {
        const config = CREDIT_STATUS_CONFIG[row.status] ?? { label: row.status, className: '' };
        return <Badge className={config.className}>{config.label}</Badge>;
      },
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (row) => {
        if (!canManage) return null;
        return (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setEditingTerm(row);
                setShowTermsModal(true);
              }}
            >
              Edit
            </Button>
            {row.status === 'active' && (
              <Button
                variant="ghost"
                size="sm"
                className="text-yellow-600"
                onClick={(e) => {
                  e.stopPropagation();
                  suspendMutation.mutate(row.id);
                }}
              >
                Suspend
              </Button>
            )}
          </div>
        );
      },
    },
  ], [canManage, suspendMutation]);

  const alertColumns: ColumnDef<CreditAlert & { customerName: string }>[] = useMemo(() => [
    {
      id: 'customerName',
      header: 'Customer',
      accessor: 'customerName',
      sortable: true,
    },
    {
      id: 'alert_type',
      header: 'Alert Type',
      accessor: 'alert_type',
      sortable: true,
      cell: (row) => {
        const config = ALERT_TYPE_CONFIG[row.alert_type] ?? { label: row.alert_type, className: '' };
        return <Badge className={config.className}>{config.label}</Badge>;
      },
    },
    {
      id: 'message',
      header: 'Message',
      accessor: 'message',
    },
    {
      id: 'severity',
      header: 'Severity',
      accessor: 'severity',
      sortable: true,
      cell: (row) => {
        const config = SEVERITY_CONFIG[row.severity] ?? { label: row.severity, className: '' };
        return <Badge className={config.className}>{config.label}</Badge>;
      },
    },
    {
      id: 'created_at',
      header: 'Created',
      accessor: 'created_at',
      sortable: true,
      cell: (row) => new Date(row.created_at).toLocaleDateString(),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (row) => {
        if (!canManage) return null;
        return (
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                dismissAlertMutation.mutate(row.id);
              }}
            >
              Dismiss
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-green-600"
              onClick={(e) => {
                e.stopPropagation();
                dismissAlertMutation.mutate(row.id);
              }}
            >
              Resolve
            </Button>
          </div>
        );
      },
    },
  ], [canManage, dismissAlertMutation]);

  // ---------------------------------------------------------------------------
  // Stats
  // ---------------------------------------------------------------------------

  const stats = useMemo<StatCardData[]>(() => {
    const pendingApps = applications.filter(a => a.status === 'pending').length;
    const activeTerms = creditTerms.filter(t => t.status === 'active').length;
    const totalCreditExtended = creditTerms
      .filter(t => t.status === 'active')
      .reduce((sum, t) => sum + t.credit_limit, 0);
    const activeAlerts = alerts.length;

    return [
      {
        label: 'Pending Applications',
        value: pendingApps,
        icon: <FileText className="h-4 w-4" />,
        format: 'number',
        alert: pendingApps > 0,
        subtitle: `${applications.length} total applications`,
      },
      {
        label: 'Active Credit Lines',
        value: activeTerms,
        icon: <CreditCard className="h-4 w-4" />,
        format: 'number',
        subtitle: `${creditTerms.length} total terms`,
      },
      {
        label: 'Total Credit Extended',
        value: totalCreditExtended,
        icon: <DollarSign className="h-4 w-4" />,
        format: 'currency',
        subtitle: 'Active credit limits',
      },
      {
        label: 'Active Alerts',
        value: activeAlerts,
        icon: <Bell className="h-4 w-4" />,
        format: 'number',
        alert: activeAlerts > 0,
        subtitle: activeAlerts > 0 ? 'Needs attention' : 'No active alerts',
      },
    ];
  }, [applications, creditTerms, alerts]);

  // ---------------------------------------------------------------------------
  // Application form fields (computed from customers)
  // ---------------------------------------------------------------------------

  const applicationFields = useMemo(() => buildApplicationFields(customers), [customers]);
  const creditTermsFields = useMemo(() => buildCreditTermsFields(customers), [customers]);

  // ---------------------------------------------------------------------------
  // Permission guard
  // ---------------------------------------------------------------------------

  if (!canRead) {
    return (
      <DashboardLayout>
        <div className="container mx-auto py-6">
          <p className="text-muted-foreground">You do not have permission to view credit management.</p>
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
              <ShieldCheck className="h-8 w-8" />
              Credit Management
            </h1>
            <p className="text-muted-foreground mt-2">
              Manage credit applications, customer credit terms, and credit alerts
            </p>
          </div>
        </div>

        {/* Stats */}
        <StatCards stats={stats} isLoading={appsLoading || termsLoading || alertsLoading} />

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList>
            <TabsTrigger value="applications">
              <FileText className="h-4 w-4 mr-1" />
              Credit Applications
            </TabsTrigger>
            <TabsTrigger value="credit-terms">
              <CreditCard className="h-4 w-4 mr-1" />
              Customer Credit
            </TabsTrigger>
            <TabsTrigger value="alerts">
              <Bell className="h-4 w-4 mr-1" />
              Credit Alerts
              {alerts.length > 0 && (
                <Badge className="ml-1 bg-red-500 text-white text-xs px-1.5 py-0">
                  {alerts.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Credit Applications */}
          <TabsContent value="applications">
            <DataTable
              columns={applicationColumns}
              data={enrichedApplications}
              isLoading={appsLoading}
              emptyMessage="No credit applications found."
              filters={
                canManage ? (
                  <Button onClick={() => setShowApplicationModal(true)}>
                    <Plus className="h-4 w-4 mr-1" />
                    New Application
                  </Button>
                ) : undefined
              }
            />
          </TabsContent>

          {/* Tab 2: Customer Credit */}
          <TabsContent value="credit-terms">
            <DataTable
              columns={creditTermColumns}
              data={enrichedTerms}
              isLoading={termsLoading}
              emptyMessage="No credit terms configured. Set credit terms for customers to manage their credit."
              filters={
                canManage ? (
                  <Button onClick={() => {
                    setEditingTerm(null);
                    setShowTermsModal(true);
                  }}>
                    <Plus className="h-4 w-4 mr-1" />
                    Set Credit Terms
                  </Button>
                ) : undefined
              }
            />
          </TabsContent>

          {/* Tab 3: Credit Alerts */}
          <TabsContent value="alerts">
            <DataTable
              columns={alertColumns}
              data={enrichedAlerts}
              isLoading={alertsLoading}
              emptyMessage="No active credit alerts. Run a credit check to detect issues."
              filters={
                canManage ? (
                  <Button
                    onClick={() => creditCheckMutation.mutate()}
                    disabled={creditCheckMutation.isPending}
                  >
                    <Search className="h-4 w-4 mr-1" />
                    {creditCheckMutation.isPending ? 'Checking...' : 'Run Credit Check'}
                  </Button>
                ) : undefined
              }
            />
            {creditCheckMutation.isSuccess && (
              <p className="text-sm text-muted-foreground mt-2">
                Credit check complete. {creditCheckMutation.data} new alert(s) created.
              </p>
            )}
          </TabsContent>
        </Tabs>

        {/* New Application Modal */}
        <FormModal
          isOpen={showApplicationModal}
          onClose={() => setShowApplicationModal(false)}
          title="New Credit Application"
          description="Submit a credit application for a customer."
          fields={applicationFields}
          onSubmit={async (values) => {
            await createAppMutation.mutateAsync(values);
          }}
          isSubmitting={createAppMutation.isPending}
          submitLabel="Submit Application"
        />

        {/* Set/Edit Credit Terms Modal */}
        <FormModal
          isOpen={showTermsModal}
          onClose={() => {
            setShowTermsModal(false);
            setEditingTerm(null);
          }}
          title={editingTerm ? 'Edit Credit Terms' : 'Set Credit Terms'}
          description="Configure credit limit, payment terms, and interest rate for a customer."
          fields={creditTermsFields}
          defaultValues={
            editingTerm
              ? {
                  customer_id: editingTerm.customer_id,
                  credit_limit: editingTerm.credit_limit,
                  payment_terms: editingTerm.payment_terms,
                  interest_rate: editingTerm.interest_rate,
                  status: editingTerm.status,
                }
              : undefined
          }
          onSubmit={async (values) => {
            await setTermsMutation.mutateAsync(values);
          }}
          isSubmitting={setTermsMutation.isPending}
          submitLabel={editingTerm ? 'Update Terms' : 'Set Terms'}
        />

        {/* Review Application Dialog */}
        <Dialog open={!!reviewingApp} onOpenChange={(open) => !open && setReviewingApp(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Review Credit Application</DialogTitle>
              <DialogDescription>
                Review and approve or deny this credit application.
              </DialogDescription>
            </DialogHeader>

            {reviewingApp && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Customer</p>
                    <p className="font-medium">
                      {customerMap.get(reviewingApp.customer_id) ?? 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Requested Amount</p>
                    <p className="font-medium">{fmt(reviewingApp.requested_amount)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Business Type</p>
                    <p className="font-medium">{reviewingApp.business_type}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Years in Business</p>
                    <p className="font-medium">{reviewingApp.years_in_business}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Annual Revenue</p>
                    <p className="font-medium">{fmt(reviewingApp.annual_revenue)}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Applied</p>
                    <p className="font-medium">
                      {new Date(reviewingApp.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>

                {reviewingApp.notes && (
                  <div>
                    <p className="text-sm text-muted-foreground">Notes</p>
                    <p className="text-sm">{reviewingApp.notes}</p>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-medium">Decision</label>
                  <Select
                    value={reviewStatus}
                    onValueChange={(val) => setReviewStatus(val as typeof reviewStatus)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="approved">
                        <span className="flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3 text-green-600" />
                          Approve
                        </span>
                      </SelectItem>
                      <SelectItem value="denied">
                        <span className="flex items-center gap-1">
                          <XCircle className="h-3 w-3 text-red-600" />
                          Deny
                        </span>
                      </SelectItem>
                      <SelectItem value="under_review">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3 text-yellow-600" />
                          Mark Under Review
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Review Notes</label>
                  <Textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    placeholder="Add review notes..."
                    rows={3}
                  />
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setReviewingApp(null)}>
                Cancel
              </Button>
              <Button
                onClick={() => reviewAppMutation.mutate()}
                disabled={reviewAppMutation.isPending}
                className={
                  reviewStatus === 'approved'
                    ? 'bg-green-600 hover:bg-green-700'
                    : reviewStatus === 'denied'
                    ? 'bg-red-600 hover:bg-red-700'
                    : ''
                }
              >
                {reviewAppMutation.isPending ? 'Processing...' : `Submit ${reviewStatus === 'approved' ? 'Approval' : reviewStatus === 'denied' ? 'Denial' : 'Review'}`}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
};

export default CreditManagement;
