/**
 * Tests for Shared UI Components
 * Validates accessibility, functionality, and responsive design
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  Button,
  IconButton,
  Modal,
  ConfirmDialog,
  Table,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Pagination,
  TextInput,
  TextArea,
  Select,
  Checkbox,
  Toast,
  LoadingSpinner,
  ProgressBar,
  ErrorMessage,
} from '../index';

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('supports loading state', () => {
    render(<Button isLoading loadingText="Loading...">Click me</Button>);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('disables button when loading', () => {
    render(<Button isLoading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('supports different variants', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-primary');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-secondary');

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-destructive');
  });

  it('has minimum 44px touch target size', () => {
    render(<Button>Touch me</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('min-h-[44px]', 'min-w-[44px]');
  });

  it('supports ARIA labels', () => {
    render(<Button aria-label="Custom label">Button</Button>);
    expect(screen.getByRole('button', { name: /custom label/i })).toBeInTheDocument();
  });
});

describe('IconButton Component', () => {
  it('requires ARIA label', () => {
    render(
      <IconButton aria-label="Close">
        <span>×</span>
      </IconButton>
    );
    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('has minimum 44px touch target size', () => {
    render(
      <IconButton aria-label="Test">
        <span>Icon</span>
      </IconButton>
    );
    const button = screen.getByRole('button');
    expect(button).toHaveClass('min-h-[44px]', 'min-w-[44px]');
  });

  it('supports loading state', () => {
    render(
      <IconButton aria-label="Loading" isLoading>
        <span>Icon</span>
      </IconButton>
    );
    expect(screen.getByRole('button')).toBeDisabled();
  });
});

describe('Modal Component', () => {
  it('renders when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('closes on Escape key', async () => {
    const onClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('closes on backdrop click', () => {
    const onClose = jest.fn();
    const { container } = render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    const backdrop = container.querySelector('[role="presentation"]');
    fireEvent.click(backdrop!);
    expect(onClose).toHaveBeenCalled();
  });

  it('has proper ARIA attributes', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        <p>Modal content</p>
      </Modal>
    );
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
  });
});

describe('ConfirmDialog Component', () => {
  it('renders with title and message', () => {
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirm"
        message="Are you sure?"
        onConfirm={() => {}}
        onCancel={() => {}}
      />
    );
    expect(screen.getByText('Confirm')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button clicked', async () => {
    const onConfirm = jest.fn();
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirm"
        message="Are you sure?"
        onConfirm={onConfirm}
        onCancel={() => {}}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /confirm/i }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when cancel button clicked', () => {
    const onCancel = jest.fn();
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirm"
        message="Are you sure?"
        onConfirm={() => {}}
        onCancel={onCancel}
      />
    );
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('confirms on Enter key', () => {
    const onConfirm = jest.fn();
    render(
      <ConfirmDialog
        isOpen={true}
        title="Confirm"
        message="Are you sure?"
        onConfirm={onConfirm}
        onCancel={() => {}}
      />
    );
    fireEvent.keyDown(document, { key: 'Enter' });
    expect(onConfirm).toHaveBeenCalled();
  });
});

describe('Table Component', () => {
  const columns = [
    { key: 'name' as const, label: 'Name' },
    { key: 'age' as const, label: 'Age', sortable: true },
  ];

  const data = [
    { id: '1', name: 'John', age: 30 },
    { id: '2', name: 'Jane', age: 25 },
  ];

  it('renders table with data', () => {
    render(
      <Table
        columns={columns}
        data={data}
        rowKey="id"
      />
    );
    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('Jane')).toBeInTheDocument();
  });

  it('renders column headers', () => {
    render(
      <Table
        columns={columns}
        data={data}
        rowKey="id"
      />
    );
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Age')).toBeInTheDocument();
  });

  it('calls onSort when sortable column clicked', () => {
    const onSort = jest.fn();
    render(
      <Table
        columns={columns}
        data={data}
        rowKey="id"
        onSort={onSort}
      />
    );
    fireEvent.click(screen.getByText('Age'));
    expect(onSort).toHaveBeenCalledWith('age', 'asc');
  });

  it('calls onRowClick when row clicked', () => {
    const onRowClick = jest.fn();
    render(
      <Table
        columns={columns}
        data={data}
        rowKey="id"
        onRowClick={onRowClick}
      />
    );
    fireEvent.click(screen.getByText('John'));
    expect(onRowClick).toHaveBeenCalledWith(data[0]);
  });
});

describe('Card Component', () => {
  it('renders card with content', () => {
    render(
      <Card>
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders card with header and title', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Card Title</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card content</p>
        </CardContent>
      </Card>
    );
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });
});

describe('Pagination Component', () => {
  it('renders pagination controls', () => {
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={() => {}}
      />
    );
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={() => {}}
      />
    );
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(
      <Pagination
        currentPage={5}
        totalPages={5}
        onPageChange={() => {}}
      />
    );
    expect(screen.getByRole('button', { name: /next/i })).toBeDisabled();
  });

  it('calls onPageChange when page input changes', () => {
    const onPageChange = jest.fn();
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={onPageChange}
      />
    );
    const input = screen.getByRole('spinbutton');
    fireEvent.change(input, { target: { value: '3' } });
    expect(onPageChange).toHaveBeenCalledWith(3);
  });
});

describe('TextInput Component', () => {
  it('renders input with label', () => {
    render(
      <TextInput label="Name" />
    );
    expect(screen.getByLabelText('Name')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <TextInput label="Name" error="Name is required" />
    );
    expect(screen.getByText('Name is required')).toBeInTheDocument();
  });

  it('has minimum 44px touch target size', () => {
    render(
      <TextInput label="Name" />
    );
    expect(screen.getByLabelText('Name')).toHaveClass('min-h-[44px]');
  });

  it('shows required indicator', () => {
    render(
      <TextInput label="Name" required />
    );
    expect(screen.getByText('*')).toBeInTheDocument();
  });
});

describe('TextArea Component', () => {
  it('renders textarea with label', () => {
    render(
      <TextArea label="Description" />
    );
    expect(screen.getByLabelText('Description')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <TextArea label="Description" error="Description is required" />
    );
    expect(screen.getByText('Description is required')).toBeInTheDocument();
  });
});

describe('Select Component', () => {
  const options = [
    { value: '1', label: 'Option 1' },
    { value: '2', label: 'Option 2' },
  ];

  it('renders select with options', () => {
    render(
      <Select label="Choose" options={options} />
    );
    expect(screen.getByLabelText('Choose')).toBeInTheDocument();
    expect(screen.getByText('Option 1')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <Select label="Choose" options={options} error="Selection required" />
    );
    expect(screen.getByText('Selection required')).toBeInTheDocument();
  });
});

describe('Checkbox Component', () => {
  it('renders checkbox with label', () => {
    render(
      <Checkbox label="Agree" />
    );
    expect(screen.getByLabelText('Agree')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(
      <Checkbox label="Agree" error="You must agree" />
    );
    expect(screen.getByText('You must agree')).toBeInTheDocument();
  });

  it('can be checked', async () => {
    const user = userEvent.setup();
    render(
      <Checkbox label="Agree" />
    );
    const checkbox = screen.getByLabelText('Agree');
    await user.click(checkbox);
    expect(checkbox).toBeChecked();
  });
});

describe('LoadingSpinner Component', () => {
  it('renders spinner with label', () => {
    render(
      <LoadingSpinner label="Loading..." />
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('has proper ARIA attributes', () => {
    render(
      <LoadingSpinner label="Loading..." />
    );
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('supports full screen mode', () => {
    const { container } = render(
      <LoadingSpinner fullScreen label="Loading..." />
    );
    expect(container.querySelector('.fixed')).toBeInTheDocument();
  });
});

describe('ProgressBar Component', () => {
  it('renders progress bar', () => {
    render(
      <ProgressBar value={50} />
    );
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays percentage', () => {
    render(
      <ProgressBar value={75} showPercentage />
    );
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('has proper ARIA attributes', () => {
    render(
      <ProgressBar value={50} />
    );
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });
});

describe('ErrorMessage Component', () => {
  it('renders error message', () => {
    render(
      <ErrorMessage message="Something went wrong" />
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('displays retry button', () => {
    const onRetry = jest.fn();
    render(
      <ErrorMessage message="Error" onRetry={onRetry} />
    );
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it('has proper ARIA attributes', () => {
    render(
      <ErrorMessage message="Error" />
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});
