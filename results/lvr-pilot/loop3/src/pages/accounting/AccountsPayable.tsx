/**
 * AccountsPayable — ACC-011
 *
 * Accounts payable management page. Thin wrapper around AccountsPayableTab.
 * This was a CLEAN page in Loop 1 — all features preserved.
 *
 * Architecture:
 *   - DashboardLayout wrapper
 *   - Page header with icon
 *   - Delegates to AccountsPayableTab for all AP functionality
 *   - Permission-gated create button
 */

import React from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import AccountsPayableTab from '@/components/accounting/AccountsPayableTab';
import { ShoppingCart } from 'lucide-react';

const AccountsPayable = () => {
  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <ShoppingCart className="h-8 w-8" />
            Accounts Payable
          </h1>
          <p className="text-muted-foreground mt-2">
            Manage purchase orders, bills, and vendor payments
          </p>
        </div>
        <AccountsPayableTab />
      </div>
    </DashboardLayout>
  );
};

export default AccountsPayable;
