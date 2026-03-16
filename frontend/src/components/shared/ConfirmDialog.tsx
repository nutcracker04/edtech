/**
 * ConfirmDialog Component
 * Modal dialog for confirmations with keyboard navigation support
 * Supports Enter to confirm, Escape to cancel
 * Includes ARIA attributes for screen readers
 */

import React, { useEffect } from 'react';
import { Modal } from './Modal';
import { Button } from './Button';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDangerous?: boolean;
  isLoading?: boolean;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
}

const ConfirmDialog = React.forwardRef<HTMLDivElement, ConfirmDialogProps>(
  (
    {
      isOpen,
      title,
      message,
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      isDangerous = false,
      isLoading = false,
      onConfirm,
      onCancel,
    },
    ref,
  ) => {
    useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (!isOpen) return;

        if (e.key === 'Enter') {
          e.preventDefault();
          onConfirm();
        }
      };

      if (isOpen) {
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
      }
    }, [isOpen, onConfirm]);

    return (
      <Modal
        ref={ref}
        isOpen={isOpen}
        onClose={onCancel}
        title={title}
        size="sm"
        closeOnEscape={true}
        closeOnBackdropClick={true}
        footer={
          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
              aria-label={cancelText}
            >
              {cancelText}
            </Button>
            <Button
              variant={isDangerous ? 'danger' : 'primary'}
              onClick={onConfirm}
              isLoading={isLoading}
              loadingText="Confirming..."
              aria-label={confirmText}
            >
              {confirmText}
            </Button>
          </div>
        }
      >
        <p className="text-muted-foreground">{message}</p>
      </Modal>
    );
  },
);

ConfirmDialog.displayName = 'ConfirmDialog';

export { ConfirmDialog };
