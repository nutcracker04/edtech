/**
 * ToastContainer Component
 * Container for managing multiple toast notifications
 * Handles positioning and lifecycle management
 */

import React, { useState, useCallback } from 'react';
import { Toast, ToastType } from './Toast';

export interface ToastMessage {
  id: string;
  message: string;
  type?: ToastType;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface ToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  maxToasts?: number;
}

const positionClasses = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
};

const ToastContainer = React.forwardRef<HTMLDivElement, ToastContainerProps>(
  (
    {
      position = 'top-right',
      maxToasts = 5,
    },
    ref,
  ) => {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const addToast = useCallback(
      (message: string, type: ToastType = 'info', duration = 5000) => {
        const id = `toast-${Date.now()}-${Math.random()}`;
        const newToast: ToastMessage = { id, message, type, duration };

        setToasts((prev) => {
          const updated = [...prev, newToast];
          return updated.slice(-maxToasts);
        });

        return id;
      },
      [maxToasts],
    );

    const removeToast = useCallback((id: string) => {
      setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    // Expose methods via ref
    React.useImperativeHandle(ref, () => ({
      addToast,
      removeToast,
      success: (message: string, duration?: number) =>
        addToast(message, 'success', duration),
      error: (message: string, duration?: number) =>
        addToast(message, 'error', duration),
      info: (message: string, duration?: number) =>
        addToast(message, 'info', duration),
      warning: (message: string, duration?: number) =>
        addToast(message, 'warning', duration),
    }));

    return (
      <div
        className={`fixed ${positionClasses[position]} z-50 flex flex-col gap-2 pointer-events-none`}
        role="region"
        aria-label="Notifications"
        aria-live="polite"
        aria-atomic="false"
      >
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast
              {...toast}
              onClose={removeToast}
            />
          </div>
        ))}
      </div>
    );
  },
);

ToastContainer.displayName = 'ToastContainer';

export { ToastContainer };
