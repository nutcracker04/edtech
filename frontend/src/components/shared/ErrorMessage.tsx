/**
 * ErrorMessage Component
 * Reusable error message component with retry option
 * Includes ARIA attributes for screen reader announcements
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Button } from './Button';

export interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  details?: string;
  className?: string;
  fullScreen?: boolean;
}

const ErrorMessage = React.forwardRef<HTMLDivElement, ErrorMessageProps>(
  (
    {
      title = 'Error',
      message,
      onRetry,
      retryLabel = 'Retry',
      details,
      className,
      fullScreen = false,
    },
    ref,
  ) => {
    const content = (
      <div
        ref={ref}
        className={cn(
          'rounded-lg border border-destructive/50 bg-destructive/10 p-4',
          className,
        )}
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
      >
        <div className="flex gap-3">
          <div className="flex-shrink-0">
            <svg
              className="h-5 w-5 text-destructive"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-destructive mb-1">{title}</h3>
            <p className="text-sm text-destructive/90 mb-2">{message}</p>
            {details && (
              <details className="text-xs text-destructive/80 mb-3">
                <summary className="cursor-pointer font-medium">
                  Details
                </summary>
                <pre className="mt-2 overflow-auto bg-destructive/5 p-2 rounded text-xs">
                  {details}
                </pre>
              </details>
            )}
            {onRetry && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRetry}
                aria-label={retryLabel}
              >
                {retryLabel}
              </Button>
            )}
          </div>
        </div>
      </div>
    );

    if (fullScreen) {
      return (
        <div className="fixed inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm z-50">
          <div className="max-w-md w-full mx-4">
            {content}
          </div>
        </div>
      );
    }

    return content;
  },
);

ErrorMessage.displayName = 'ErrorMessage';

export { ErrorMessage };
