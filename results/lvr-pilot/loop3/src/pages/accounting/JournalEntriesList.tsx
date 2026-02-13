/**
 * JournalEntriesList — ACC-012
 *
 * Journal entries list page with DataTable, filtering, and create modal.
 * This was a CLEAN page in Loop 1 — all working features preserved.
 *
 * Architecture:
 *   - DashboardLayout wrapper with PageHeader
 *   - Delegates to JournalEntriesTab for list/create functionality
 *   - Uses the existing PageHeader component (this page already used it in the original)
 */

import React from 'react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import JournalEntriesTab from '@/components/accounting/JournalEntriesTab';
import { PageHeader } from '@/components/layout/PageHeader';
import { FileText } from 'lucide-react';

const JournalEntriesList = () => {
  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        <PageHeader
          title="Journal Entries"
          description="Create and manage journal entries for proper double-entry bookkeeping"
          icon={FileText}
        />
        <JournalEntriesTab />
      </div>
    </DashboardLayout>
  );
};

export default JournalEntriesList;
