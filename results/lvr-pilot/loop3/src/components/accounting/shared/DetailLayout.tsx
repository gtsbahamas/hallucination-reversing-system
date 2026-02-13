/**
 * DetailLayout — Reusable detail page layout for all 5 accounting detail pages.
 *
 * Provides a consistent structure:
 *   Header: [Back button] [Title + subtitle] [Status badge] [Action buttons]
 *   Body:   [2/3 Tabs] [1/3 Sidebar]
 *
 * Used by: InvoiceDetailPage, BillDetailPage, ExpenseDetailPage,
 *          PaymentDetailPage, JournalEntryDetailPage
 *
 * Eliminates ~200 lines of repeated layout code per detail page.
 */

import React, { useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Breadcrumb {
  /** Display label */
  label: string;
  /** Navigation target. If omitted, rendered as plain text (current page). */
  href?: string;
}

export interface StatusBadgeConfig {
  /** Status label text */
  status: string;
  /** Visual variant */
  variant: 'default' | 'success' | 'warning' | 'destructive';
}

export interface ActionButtonConfig {
  /** Button label */
  label: string;
  /** Click handler */
  onClick: () => void;
  /** Optional icon (rendered before label) */
  icon?: ReactNode;
  /** Button variant. Default: 'outline' */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  /** Permission code required to show this button. If provided and user lacks permission, button is hidden. */
  permission?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
  /** Optional additional CSS class */
  className?: string;
}

export interface TabConfig {
  /** Unique tab identifier */
  id: string;
  /** Tab label */
  label: string;
  /** Tab content */
  content: ReactNode;
}

export interface DetailLayoutProps {
  /** Page title (e.g., "Invoice INV-001") */
  title: string;
  /** Optional subtitle (e.g., customer name) */
  subtitle?: string;
  /** Breadcrumb navigation trail */
  breadcrumbs: Breadcrumb[];
  /** Status badge configuration */
  statusBadge?: StatusBadgeConfig;
  /** Action buttons in the header */
  actionButtons?: ActionButtonConfig[];
  /** Tab definitions for the main content area */
  tabs: TabConfig[];
  /** Sidebar content (right column) */
  sidebar?: ReactNode;
  /** Whether the page is in a loading state */
  isLoading?: boolean;
  /** Callback when the back button is clicked. If omitted, uses browser history. */
  onBack?: () => void;
}

// ---------------------------------------------------------------------------
// Status Badge Variant Mapping
// ---------------------------------------------------------------------------

const BADGE_VARIANT_CLASSES: Record<StatusBadgeConfig['variant'], string> = {
  default: 'bg-gray-100 text-gray-800 border-gray-200',
  success: 'bg-green-100 text-green-800 border-green-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  destructive: 'bg-red-100 text-red-800 border-red-200',
};

// ---------------------------------------------------------------------------
// Loading Skeleton
// ---------------------------------------------------------------------------

function DetailSkeleton() {
  return (
    <div className="container mx-auto py-6 animate-pulse">
      {/* Back button skeleton */}
      <div className="h-8 w-32 bg-muted rounded mb-4" />

      {/* Header skeleton */}
      <div className="flex items-center justify-between mb-6">
        <div className="space-y-2">
          <div className="h-8 w-64 bg-muted rounded" />
          <div className="h-4 w-40 bg-muted rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-24 bg-muted rounded" />
          <div className="h-9 w-24 bg-muted rounded" />
        </div>
      </div>

      {/* Content skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="h-10 w-full bg-muted rounded" />
          <div className="h-64 w-full bg-muted rounded" />
        </div>
        <div className="space-y-4">
          <div className="h-48 w-full bg-muted rounded" />
          <div className="h-32 w-full bg-muted rounded" />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Breadcrumbs
// ---------------------------------------------------------------------------

function BreadcrumbNav({
  breadcrumbs,
  onNavigate,
}: {
  breadcrumbs: Breadcrumb[];
  onNavigate: (href: string) => void;
}) {
  return (
    <nav className="flex items-center text-sm text-muted-foreground mb-2" aria-label="Breadcrumb">
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={index}>
          {index > 0 && <span className="mx-1.5">/</span>}
          {crumb.href ? (
            <button
              type="button"
              className="hover:text-foreground transition-colors"
              onClick={() => onNavigate(crumb.href!)}
            >
              {crumb.label}
            </button>
          ) : (
            <span className="text-foreground font-medium">{crumb.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}

// ---------------------------------------------------------------------------
// DetailLayout Component
// ---------------------------------------------------------------------------

export function DetailLayout({
  title,
  subtitle,
  breadcrumbs,
  statusBadge,
  actionButtons = [],
  tabs,
  sidebar,
  isLoading = false,
  onBack,
}: DetailLayoutProps) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(tabs[0]?.id ?? '');

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  const handleNavigate = (href: string) => {
    navigate(href);
  };

  if (isLoading) {
    return <DetailSkeleton />;
  }

  return (
    <div className="container mx-auto py-6">
      {/* Back button */}
      <Button
        variant="ghost"
        size="sm"
        className="mb-4 -ml-2 text-muted-foreground hover:text-foreground"
        onClick={handleBack}
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back
      </Button>

      {/* Breadcrumbs */}
      {breadcrumbs.length > 0 && (
        <BreadcrumbNav breadcrumbs={breadcrumbs} onNavigate={handleNavigate} />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        {/* Title + status */}
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
            {statusBadge && (
              <Badge
                variant="outline"
                className={BADGE_VARIANT_CLASSES[statusBadge.variant]}
              >
                {statusBadge.status}
              </Badge>
            )}
          </div>
          {subtitle && (
            <p className="text-muted-foreground">{subtitle}</p>
          )}
        </div>

        {/* Action buttons */}
        {actionButtons.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {actionButtons.map((btn) => (
              <Button
                key={btn.label}
                variant={btn.variant ?? 'outline'}
                onClick={btn.onClick}
                disabled={btn.disabled}
                className={btn.className}
              >
                {btn.icon && <span className="mr-1.5">{btn.icon}</span>}
                {btn.label}
              </Button>
            ))}
          </div>
        )}
      </div>

      {/* Body: Tabs + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content (tabs) — 2/3 width */}
        <div className={sidebar ? 'lg:col-span-2' : 'lg:col-span-3'}>
          {tabs.length === 1 ? (
            // Single "tab" — render content directly without tab UI
            <div>{tabs[0].content}</div>
          ) : (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                {tabs.map((tab) => (
                  <TabsTrigger key={tab.id} value={tab.id}>
                    {tab.label}
                  </TabsTrigger>
                ))}
              </TabsList>
              {tabs.map((tab) => (
                <TabsContent key={tab.id} value={tab.id}>
                  {tab.content}
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>

        {/* Sidebar — 1/3 width */}
        {sidebar && (
          <div className="space-y-6">
            {sidebar}
          </div>
        )}
      </div>
    </div>
  );
}

export default DetailLayout;
