import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { LayoutProvider } from "./contexts/LayoutContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Mistakes from "./pages/Mistakes";
import RevisionCapsulesPage from "./pages/RevisionCapsulesPage";

import Analysis from "./pages/AnalysisNew";
import Landing from "./pages/Landing";
import Tests from "./pages/Tests";
import Settings from "./pages/Settings";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ExtractionManagement from "./pages/admin/ExtractionManagement";
import ManualQuestionBulkImport from "./pages/admin/ManualQuestionBulkImport";
import TestTaking from "./pages/TestTaking";
import TestResults from "./pages/TestResults";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LayoutProvider>
          <TooltipProvider>
            <Toaster />
            <Sonner />
            <BrowserRouter>
              <Routes>
                {/* Public routes */}
                <Route path="/landing" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/onboarding" element={<Onboarding />} />

                {/* Protected routes */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <Index />
                  </ProtectedRoute>
                } />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } />
                <Route path="/mistakes" element={
                  <ProtectedRoute>
                    <Mistakes />
                  </ProtectedRoute>
                } />
                <Route path="/revision-capsules" element={
                  <ProtectedRoute>
                    <RevisionCapsulesPage />
                  </ProtectedRoute>
                } />

                <Route path="/analysis" element={
                  <ProtectedRoute>
                    <Analysis />
                  </ProtectedRoute>
                } />
                <Route path="/tests" element={
                  <ProtectedRoute>
                    <Tests />
                  </ProtectedRoute>
                } />
                <Route path="/test/:testId" element={
                  <ProtectedRoute>
                    <TestTaking />
                  </ProtectedRoute>
                } />
                <Route path="/tests/:testId/results" element={
                  <ProtectedRoute>
                    <TestResults />
                  </ProtectedRoute>
                } />

                <Route path="/settings" element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                } />

                <Route path="/admin" element={
                  <ProtectedRoute>
                    <AdminDashboard />
                  </ProtectedRoute>
                } />

                <Route path="/admin/pdf-upload" element={<Navigate to="/admin/question-import" replace />} />
                <Route path="/admin/question-import" element={
                  <ProtectedRoute>
                    <ManualQuestionBulkImport />
                  </ProtectedRoute>
                } />

                <Route path="/admin/extractions/*" element={
                  <ProtectedRoute>
                    <ExtractionManagement />
                  </ProtectedRoute>
                } />


                {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </BrowserRouter>
          </TooltipProvider>
        </LayoutProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
