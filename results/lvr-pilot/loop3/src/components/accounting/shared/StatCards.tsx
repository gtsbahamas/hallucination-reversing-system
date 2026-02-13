/**
 * StatCards — Reusable grid of metric cards for dashboards and overview pages.
 *
 * Used by 10+ accounting pages to display summary statistics
 * (total invoices, outstanding balance, overdue count, etc.).
 *
 * Matches the existing Island Biz Card/CardHeader/CardContent pattern
 * with consistent styling across all pages (eliminates 3 CSS variants).
 *
 * Features:
 *   - Currency, number, and percentage formatting
 *   - Trend indicators (up/down with color)
 *   - Loading skeleton state
 *   - Configurable column count (2, 3, or 4)
 *   - Optional icon per stat
 */

import React, { type ReactNode } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface StatCardData {
  /** Metric label (e.g., "Total Revenue") */
  label: string;
  /** Metric value (raw — will be formatted if format is specified) */
  value: string | number;
  /** Optional icon element (typically a Lucide icon) */
  icon?: ReactNode;
  /** Trend indicator */
  trend?: {
    /** Percentage change value (e.g., 12.5 for +12.5%) */
    value: number;
    /** Whether the trend direction is positive for this metric */
    isPositive: boolean;
  };
  /** Value format. Default: none (raw display) */
  format?: 'currency' | 'number' | 'percent';
  /** Optional subtitle text below the value */
  subtitle?: string;
  /** Render value in alert style (red text). Useful for overdue counts. */
  alert?: boolean;
  /** Optional CSS class for the card */
  className?: string;
}

export interface StatCardsProps {
  /** Array of stat card data */
  stats: StatCardData[];
  /** Whether data is loading (shows skeleton) */
  isLoading?: boolean;
  /** Number of columns in the grid. Default: 4 */
  columns?: 2 | 3 | 4;
  /** Optional CSS class for the grid container */
  className?: string;
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

function formatValue(value: string | number, format?: 'currency' | 'number' | 'percent'): string {
  if (typeof value === 'string' && !format) {
    return value;
  }

  const numValue = typeof value === 'string' ? parseFloat(value) : value;

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(numValue);

    case 'number':
      return new Intl.NumberFormat('en-US').format(numValue);

    case 'percent':
      return `${numValue.toFixed(1)}%`;

    default:
      if (typeof value === 'number') {
        // Auto-format large numbers
        if (Number.isInteger(value)) {
          return new Intl.NumberFormat('en-US').format(value);
        }
        return new Intl.NumberFormat('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        }).format(value);
      }
      return String(value);
  }
}

// ---------------------------------------------------------------------------
// Grid Column Classes
// ---------------------------------------------------------------------------

const GRID_COLUMNS: Record<number, string> = {
  2: 'grid-cols-1 md:grid-cols-2',
  3: 'grid-cols-1 md:grid-cols-3',
  4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
};

// ---------------------------------------------------------------------------
// Trend Indicator
// ---------------------------------------------------------------------------

function TrendIndicator({ trend }: { trend: StatCardData['trend'] }) {
  if (!trend) return null;

  const isUp = trend.value > 0;
  const isFlat = trend.value === 0;
  const colorClass = (() => {
    if (isFlat) return 'text-muted-foreground';
    if (trend.isPositive) return 'text-green-600';
    return 'text-red-600';
  })();

  const Icon = isFlat ? Minus : isUp ? ArrowUp : ArrowDown;

  return (
    <span className={`inline-flex items-center text-xs font-medium ${colorClass}`}>
      <Icon className="h-3 w-3 mr-0.5" />
      {Math.abs(trend.value).toFixed(1)}%
    </span>
  );
}

// ---------------------------------------------------------------------------
// Skeleton Card
// ---------------------------------------------------------------------------

function SkeletonCard() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="h-4 w-24 bg-muted animate-pulse rounded" />
        <div className="h-4 w-4 bg-muted animate-pulse rounded" />
      </CardHeader>
      <CardContent>
        <div className="h-7 w-20 bg-muted animate-pulse rounded mb-1" />
        <div className="h-3 w-16 bg-muted animate-pulse rounded" />
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Single Stat Card
// ---------------------------------------------------------------------------

function StatCard({ stat }: { stat: StatCardData }) {
  const formattedValue = formatValue(stat.value, stat.format);

  return (
    <Card className={stat.className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{stat.label}</CardTitle>
        {stat.icon && (
          <div className="h-4 w-4 text-muted-foreground">{stat.icon}</div>
        )}
      </CardHeader>
      <CardContent>
        <div
          className={`text-2xl font-bold ${
            stat.alert ? 'text-red-600' : ''
          }`}
        >
          {formattedValue}
        </div>
        <div className="flex items-center gap-2 mt-1">
          {stat.trend && <TrendIndicator trend={stat.trend} />}
          {stat.subtitle && (
            <p className="text-xs text-muted-foreground">{stat.subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// StatCards Grid Component
// ---------------------------------------------------------------------------

export function StatCards({
  stats,
  isLoading = false,
  columns = 4,
  className,
}: StatCardsProps) {
  const gridClass = GRID_COLUMNS[columns] ?? GRID_COLUMNS[4];

  if (isLoading) {
    return (
      <div className={`grid ${gridClass} gap-6 ${className ?? ''}`}>
        {Array.from({ length: columns }).map((_, i) => (
          <SkeletonCard key={`stat-skeleton-${i}`} />
        ))}
      </div>
    );
  }

  return (
    <div className={`grid ${gridClass} gap-6 ${className ?? ''}`}>
      {stats.map((stat, index) => (
        <StatCard key={`${stat.label}-${index}`} stat={stat} />
      ))}
    </div>
  );
}

export default StatCards;
