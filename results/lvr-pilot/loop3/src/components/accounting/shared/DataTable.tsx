/**
 * DataTable — Reusable sortable, filterable, paginated table with bulk actions.
 *
 * Used by 15+ accounting list pages (invoices, bills, expenses, chart of accounts, etc.).
 * Uses shadcn/ui Table primitives and TailwindCSS for styling.
 *
 * Features:
 *   - Column definitions with custom cell renderers
 *   - Sortable column headers (click to toggle asc/desc/none)
 *   - Row selection with checkboxes for bulk actions
 *   - Pagination controls
 *   - Loading skeleton state
 *   - Empty state with custom message
 *   - Filter controls slot
 */

import React, { useCallback, type ReactNode } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Inbox,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ColumnDef<T = any> {
  /** Unique column identifier */
  id: string;
  /** Column header label */
  header: string;
  /**
   * Property key on the row object to extract the value.
   * Supports dot notation for nested access (e.g., 'customer.name').
   */
  accessor?: string;
  /**
   * Custom cell renderer. Receives the row data and the extracted cell value.
   * If not provided, the raw accessor value is rendered as a string.
   */
  cell?: (row: T, value: any) => ReactNode;
  /** Whether this column is sortable. Default: false */
  sortable?: boolean;
  /** Optional CSS class applied to every cell in this column */
  className?: string;
  /** Minimum width (TailwindCSS class like 'min-w-[120px]') */
  minWidth?: string;
}

export interface PaginationConfig {
  /** Current page number (1-indexed) */
  page: number;
  /** Rows per page */
  pageSize: number;
  /** Total number of rows across all pages */
  totalCount: number;
  /** Callback when user navigates to a different page */
  onPageChange: (page: number) => void;
}

export interface SortingConfig {
  /** Currently sorted column id */
  column: string | null;
  /** Sort direction */
  direction: 'asc' | 'desc' | null;
  /** Callback when user clicks a sortable header */
  onSort: (column: string) => void;
}

export interface BulkAction {
  /** Button label */
  label: string;
  /** Click handler, receives the selected row IDs */
  onClick: (selectedIds: string[]) => void;
  /** Optional Lucide icon */
  icon?: ReactNode;
  /** Button variant */
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
}

export interface DataTableProps<T> {
  /** Column definitions */
  columns: ColumnDef<T>[];
  /** Row data */
  data: T[];
  /** Whether data is loading */
  isLoading: boolean;
  /** Pagination configuration */
  pagination?: PaginationConfig;
  /** Sorting configuration */
  sorting?: SortingConfig;
  /** Filter controls to render above the table */
  filters?: ReactNode;
  /** Bulk action buttons shown when rows are selected */
  bulkActions?: BulkAction[];
  /** Callback when a row is clicked */
  onRowClick?: (row: T) => void;
  /** Message shown when data is empty */
  emptyMessage?: string;
  /** Array of selected row IDs (uses the 'id' property of each row) */
  selectedRows?: string[];
  /** Callback when selection changes */
  onSelectionChange?: (ids: string[]) => void;
  /** Unique key property on each row. Default: 'id' */
  rowKey?: string;
  /** Optional CSS class for the table container */
  className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

function getRowId<T>(row: T, rowKey: string): string {
  return String(getNestedValue(row, rowKey) ?? '');
}

// ---------------------------------------------------------------------------
// Skeleton Rows
// ---------------------------------------------------------------------------

function SkeletonRow({ columnCount }: { columnCount: number }) {
  return (
    <TableRow>
      {Array.from({ length: columnCount }).map((_, i) => (
        <TableCell key={i}>
          <div className="h-4 bg-muted animate-pulse rounded w-3/4" />
        </TableCell>
      ))}
    </TableRow>
  );
}

// ---------------------------------------------------------------------------
// Sort Header
// ---------------------------------------------------------------------------

function SortIcon({ column, sorting }: { column: string; sorting?: SortingConfig }) {
  if (!sorting || sorting.column !== column) {
    return <ArrowUpDown className="ml-1 h-3 w-3 text-muted-foreground/50" />;
  }
  if (sorting.direction === 'asc') {
    return <ArrowUp className="ml-1 h-3 w-3" />;
  }
  return <ArrowDown className="ml-1 h-3 w-3" />;
}

// ---------------------------------------------------------------------------
// Pagination Controls
// ---------------------------------------------------------------------------

function PaginationControls({ config }: { config: PaginationConfig }) {
  const totalPages = Math.max(1, Math.ceil(config.totalCount / config.pageSize));
  const canPrev = config.page > 1;
  const canNext = config.page < totalPages;
  const startRow = (config.page - 1) * config.pageSize + 1;
  const endRow = Math.min(config.page * config.pageSize, config.totalCount);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t">
      <p className="text-sm text-muted-foreground">
        {config.totalCount === 0
          ? 'No results'
          : `Showing ${startRow}-${endRow} of ${config.totalCount}`}
      </p>
      <div className="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => config.onPageChange(1)}
          disabled={!canPrev}
          aria-label="First page"
        >
          <ChevronsLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => config.onPageChange(config.page - 1)}
          disabled={!canPrev}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm text-muted-foreground px-2">
          Page {config.page} of {totalPages}
        </span>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => config.onPageChange(config.page + 1)}
          disabled={!canNext}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          className="h-8 w-8"
          onClick={() => config.onPageChange(totalPages)}
          disabled={!canNext}
          aria-label="Last page"
        >
          <ChevronsRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bulk Action Toolbar
// ---------------------------------------------------------------------------

function BulkActionToolbar({
  actions,
  selectedCount,
  selectedIds,
  onClearSelection,
}: {
  actions: BulkAction[];
  selectedCount: number;
  selectedIds: string[];
  onClearSelection: () => void;
}) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center gap-3 bg-muted/50 border rounded-lg px-4 py-2 mb-3">
      <span className="text-sm font-medium">
        {selectedCount} row{selectedCount !== 1 ? 's' : ''} selected
      </span>
      <div className="flex items-center gap-2">
        {actions.map((action) => (
          <Button
            key={action.label}
            variant={action.variant ?? 'outline'}
            size="sm"
            onClick={() => action.onClick(selectedIds)}
          >
            {action.icon && <span className="mr-1.5">{action.icon}</span>}
            {action.label}
          </Button>
        ))}
      </div>
      <Button variant="ghost" size="sm" onClick={onClearSelection} className="ml-auto">
        Clear selection
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DataTable Component
// ---------------------------------------------------------------------------

export function DataTable<T>({
  columns,
  data,
  isLoading,
  pagination,
  sorting,
  filters,
  bulkActions,
  onRowClick,
  emptyMessage = 'No data found.',
  selectedRows = [],
  onSelectionChange,
  rowKey = 'id',
  className,
}: DataTableProps<T>) {
  const hasSelection = !!onSelectionChange;
  const allRowIds = data.map((row) => getRowId(row, rowKey));
  const allSelected = allRowIds.length > 0 && allRowIds.every((id) => selectedRows.includes(id));
  const someSelected = selectedRows.length > 0 && !allSelected;

  // Total column count including checkbox column
  const totalColumnCount = columns.length + (hasSelection ? 1 : 0);

  const handleSelectAll = useCallback(() => {
    if (!onSelectionChange) return;
    if (allSelected) {
      onSelectionChange([]);
    } else {
      onSelectionChange(allRowIds);
    }
  }, [allSelected, allRowIds, onSelectionChange]);

  const handleSelectRow = useCallback(
    (rowId: string) => {
      if (!onSelectionChange) return;
      if (selectedRows.includes(rowId)) {
        onSelectionChange(selectedRows.filter((id) => id !== rowId));
      } else {
        onSelectionChange([...selectedRows, rowId]);
      }
    },
    [selectedRows, onSelectionChange]
  );

  const handleHeaderClick = useCallback(
    (columnId: string) => {
      if (!sorting) return;
      sorting.onSort(columnId);
    },
    [sorting]
  );

  return (
    <div className={className}>
      {/* Filters slot */}
      {filters && <div className="mb-4">{filters}</div>}

      {/* Bulk actions toolbar */}
      {hasSelection && bulkActions && bulkActions.length > 0 && (
        <BulkActionToolbar
          actions={bulkActions}
          selectedCount={selectedRows.length}
          selectedIds={selectedRows}
          onClearSelection={() => onSelectionChange?.([])}
        />
      )}

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              {/* Selection checkbox header */}
              {hasSelection && (
                <TableHead className="w-[40px]">
                  <Checkbox
                    checked={allSelected}
                    ref={(el) => {
                      if (el) {
                        (el as any).indeterminate = someSelected;
                      }
                    }}
                    onCheckedChange={handleSelectAll}
                    aria-label="Select all rows"
                  />
                </TableHead>
              )}

              {/* Data column headers */}
              {columns.map((col) => (
                <TableHead
                  key={col.id}
                  className={[
                    col.minWidth ?? '',
                    col.className ?? '',
                    col.sortable ? 'cursor-pointer select-none hover:bg-muted/50' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={col.sortable ? () => handleHeaderClick(col.id) : undefined}
                >
                  <div className="flex items-center">
                    {col.header}
                    {col.sortable && <SortIcon column={col.id} sorting={sorting} />}
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>

          <TableBody>
            {/* Loading state */}
            {isLoading &&
              Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={`skeleton-${i}`} columnCount={totalColumnCount} />
              ))}

            {/* Empty state */}
            {!isLoading && data.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={totalColumnCount}
                  className="h-32 text-center"
                >
                  <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                    <Inbox className="h-8 w-8" />
                    <p className="text-sm">{emptyMessage}</p>
                  </div>
                </TableCell>
              </TableRow>
            )}

            {/* Data rows */}
            {!isLoading &&
              data.map((row) => {
                const rowId = getRowId(row, rowKey);
                const isSelected = selectedRows.includes(rowId);

                return (
                  <TableRow
                    key={rowId}
                    data-state={isSelected ? 'selected' : undefined}
                    className={[
                      isSelected ? 'bg-muted/50' : '',
                      onRowClick ? 'cursor-pointer hover:bg-muted/30' : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    onClick={
                      onRowClick
                        ? (e) => {
                            // Don't trigger row click when clicking the checkbox
                            if ((e.target as HTMLElement).closest('[role="checkbox"]')) return;
                            onRowClick(row);
                          }
                        : undefined
                    }
                  >
                    {/* Selection checkbox */}
                    {hasSelection && (
                      <TableCell className="w-[40px]">
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => handleSelectRow(rowId)}
                          aria-label={`Select row ${rowId}`}
                        />
                      </TableCell>
                    )}

                    {/* Data cells */}
                    {columns.map((col) => {
                      const value = col.accessor ? getNestedValue(row, col.accessor) : undefined;
                      return (
                        <TableCell key={col.id} className={col.className}>
                          {col.cell ? col.cell(row, value) : (value != null ? String(value) : '')}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
          </TableBody>
        </Table>

        {/* Pagination */}
        {pagination && <PaginationControls config={pagination} />}
      </div>
    </div>
  );
}

export default DataTable;
