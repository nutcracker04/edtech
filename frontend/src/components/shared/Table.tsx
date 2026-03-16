/**
 * Table Component
 * Reusable table with sortable columns
 * Supports responsive design with proper accessibility
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  className?: string;
}

export interface TableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  onSort?: (key: keyof T, direction: 'asc' | 'desc') => void;
  sortKey?: keyof T;
  sortDirection?: 'asc' | 'desc';
  rowKey: keyof T;
  onRowClick?: (row: T) => void;
  className?: string;
  striped?: boolean;
  hoverable?: boolean;
}

const Table = React.forwardRef<HTMLTableElement, TableProps<any>>(
  (
    {
      columns,
      data,
      onSort,
      sortKey,
      sortDirection = 'asc',
      rowKey,
      onRowClick,
      className,
      striped = true,
      hoverable = true,
    },
    ref,
  ) => {
    const handleSort = (key: string) => {
      if (!onSort) return;
      const newDirection = sortKey === key && sortDirection === 'asc' ? 'desc' : 'asc';
      onSort(key as any, newDirection);
    };

    return (
      <div className="overflow-x-auto">
        <table
          ref={ref}
          className={cn(
            'w-full border-collapse text-sm',
            className,
          )}
          role="table"
        >
          <thead>
            <tr className="border-b bg-muted/50">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    'px-4 py-3 text-left font-semibold text-muted-foreground',
                    column.className,
                  )}
                  role="columnheader"
                  scope="col"
                >
                  {column.sortable ? (
                    <button
                      onClick={() => handleSort(String(column.key))}
                      className="flex items-center gap-2 hover:text-foreground transition-colors cursor-pointer"
                      aria-sort={
                        sortKey === column.key
                          ? sortDirection === 'asc'
                            ? 'ascending'
                            : 'descending'
                          : 'none'
                      }
                    >
                      {column.label}
                      {sortKey === column.key && (
                        <span className="text-xs">
                          {sortDirection === 'asc' ? '↑' : '↓'}
                        </span>
                      )}
                    </button>
                  ) : (
                    column.label
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, index) => (
              <tr
                key={String(row[rowKey])}
                className={cn(
                  'border-b transition-colors',
                  striped && index % 2 === 0 && 'bg-muted/30',
                  hoverable && 'hover:bg-muted/50',
                  onRowClick && 'cursor-pointer',
                )}
                onClick={() => onRowClick?.(row)}
                role="row"
              >
                {columns.map((column) => (
                  <td
                    key={String(column.key)}
                    className={cn('px-4 py-3', column.className)}
                    role="cell"
                  >
                    {column.render
                      ? column.render(row[column.key], row)
                      : String(row[column.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {data.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            No data available
          </div>
        )}
      </div>
    );
  },
);

Table.displayName = 'Table';

export { Table };
