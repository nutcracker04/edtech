/**
 * Admin question pipeline: import → review batches → approve/reject.
 * Replaces the old separate "extraction management" route.
 */

import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ExtractionManagementProvider } from '@/contexts/ExtractionManagementContext';
import { QuestionStagingLayout } from './QuestionStagingLayout';
import ManualQuestionBulkImport from './ManualQuestionBulkImport';

const ExtractionListView = lazy(() =>
  import('@/components/admin/extractions/ExtractionListView').then((m) => ({
    default: m.ExtractionListView,
  }))
);

const ExtractionDetailView = lazy(() =>
  import('@/components/admin/extractions/ExtractionDetailView').then((m) => ({
    default: m.ExtractionDetailView,
  }))
);

function LoadingFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    </div>
  );
}

export default function QuestionStaging() {
  return (
    <ExtractionManagementProvider>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route element={<QuestionStagingLayout />}>
            <Route index element={<ExtractionListView />} />
            <Route path="import" element={<ManualQuestionBulkImport />} />
            <Route path="jobs/:jobId" element={<ExtractionDetailView />} />
            <Route path="*" element={<Navigate to="/admin/questions" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </ExtractionManagementProvider>
  );
}
