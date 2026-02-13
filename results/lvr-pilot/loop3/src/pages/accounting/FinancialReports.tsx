/**
 * FinancialReports — ACC-015
 *
 * Financial reports page with income statement, balance sheet, cash flow,
 * and trial balance tabs. Delegates to FinancialReportsTab.
 *
 * This was a CLEAN page in Loop 1 — all working features preserved.
 *
 * Architecture:
 *   - DashboardLayout wrapper
 *   - Page header with icon
 *   - Delegates to FinancialReportsTab for all reporting functionality
 */

import React from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import FinancialReportsTab from '@/components/accounting/FinancialReportsTab';
import { TrendingUp } from 'lucide-react';

const FinancialReports = () => {
  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <TrendingUp className="h-8 w-8" />
            Financial Reports
          </h1>
          <p className="text-muted-foreground mt-2">
            Generate comprehensive financial reports including P&L, Balance Sheet, and Cash Flow
          </p>
        </div>
        <FinancialReportsTab />
      </div>
    </DashboardLayout>
  );
};

export default FinancialReports;
