/**
 * Extraction Management Module
 * Entry point for the extraction management feature with routing
 */

import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ExtractionManagementProvider } from '@/contexts/ExtractionManagementContext';

// Lazy load components for code splitting
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
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading extraction management...</p>
      </div>
    </div>
  );
}

export function ExtractionManagement() {
  return (
    <ExtractionManagementProvider>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<ExtractionListView />} />
          <Route path="/:jobId" element={<ExtractionDetailView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ExtractionManagementProvider>
  );
}

export default ExtractionManagement;
