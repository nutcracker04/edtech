/**
 * LoadingSpinner Component
 * Reusable loading spinner for async operations
 * Supports different sizes and includes accessibility attributes
 */

import React from 'react';
import { cn } from '@/lib/utils';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  fullScreen?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
};

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  (
    {
      size = 'md',
      label = 'Loading...',
      fullScreen = false,
      className,
    },
    ref,
  ) => {
    const spinner = (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center',
          className,
        )}
        role="status"
        aria-label={label}
        aria-live="polite"
      >
        <div
          className={cn(
            'animate-spin rounded-full border-2 border-current border-t-transparent',
            sizeClasses[size],
          )}
        />
      </div>
    );

    if (fullScreen) {
      return (
        <div className="fixed inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
          <div className="flex flex-col items-center gap-4">
            {spinner}
            {label && (
              <p className="text-sm text-muted-foreground">{label}</p>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center gap-2">
        {spinner}
        {label && (
          <p className="text-sm text-muted-foreground">{label}</p>
        )}
      </div>
    );
  },
);

LoadingSpinner.displayName = 'LoadingSpinner';

export { LoadingSpinner };
