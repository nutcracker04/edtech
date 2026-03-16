/**
 * Pagination Component
 * Reusable pagination with page controls
 * Supports keyboard navigation and accessibility
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  onPageSizeChange?: (size: number) => void;
  pageSizeOptions?: number[];
  showPageSizeSelector?: boolean;
  className?: string;
}

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  (
    {
      currentPage,
      totalPages,
      onPageChange,
      pageSize = 50,
      onPageSizeChange,
      pageSizeOptions = [25, 50, 100],
      showPageSizeSelector = true,
      className,
    },
    ref,
  ) => {
    const handlePrevious = () => {
      if (currentPage > 1) {
        onPageChange(currentPage - 1);
      }
    };

    const handleNext = () => {
      if (currentPage < totalPages) {
        onPageChange(currentPage + 1);
      }
    };

    const handlePageInput = (e: React.ChangeEvent<HTMLInputElement>) => {
      const page = parseInt(e.target.value, 10);
      if (!isNaN(page) && page >= 1 && page <= totalPages) {
        onPageChange(page);
      }
    };

    return (
      <div
        ref={ref}
        className={cn('flex items-center justify-between gap-4 py-4', className)}
        role="navigation"
        aria-label="Pagination"
      >
        <div className="flex items-center gap-2">
          {showPageSizeSelector && onPageSizeChange && (
            <div className="flex items-center gap-2">
              <label htmlFor="page-size" className="text-sm text-muted-foreground">
                Items per page:
              </label>
              <select
                id="page-size"
                value={pageSize}
                onChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
                className="px-2 py-1 border rounded text-sm"
                aria-label="Items per page"
              >
                {pageSizeOptions.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevious}
            disabled={currentPage === 1}
            aria-label="Previous page"
          >
            Previous
          </Button>

          <div className="flex items-center gap-1">
            <label htmlFor="page-input" className="text-sm text-muted-foreground">
              Page
            </label>
            <input
              id="page-input"
              type="number"
              min="1"
              max={totalPages}
              value={currentPage}
              onChange={handlePageInput}
              className="w-12 px-2 py-1 border rounded text-sm text-center"
              aria-label="Current page"
            />
            <span className="text-sm text-muted-foreground">of {totalPages}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleNext}
            disabled={currentPage >= totalPages}
            aria-label="Next page"
          >
            Next
          </Button>
        </div>
      </div>
    );
  },
);

Pagination.displayName = 'Pagination';

export { Pagination };
