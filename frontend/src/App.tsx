import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Practice from "./pages/Practice";
import Analysis from "./pages/Analysis";
import Tests from "./pages/Tests";
import UploadTest from "./pages/UploadTest";
import Settings from "./pages/Settings";
import AdminDashboard from "./pages/admin/AdminDashboard";
import HierarchyManager from "./pages/admin/HierarchyManager";
import QuestionTagging from "./pages/admin/QuestionTagging";
import AdminPaperUpload from "./pages/admin/PaperUpload";

import TestTaking from "./pages/TestTaking";
import NotFound from "./pages/NotFound";
import { AIAssistant } from "./components/ai/AIAssistant";
import { AIAssistantButton } from "./components/ai/AIAssistantButton";

const queryClient = new QueryClient();

const App = () => {
  const [isAIOpen, setIsAIOpen] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <BrowserRouter>
            <Routes>
              {/* Public routes */}
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
              <Route path="/practice" element={
                <ProtectedRoute>
                  <Practice />
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
              <Route path="/upload-test" element={
                <ProtectedRoute>
                  <UploadTest />
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
              <Route path="/admin/hierarchy" element={
                <ProtectedRoute>
                  <HierarchyManager />
                </ProtectedRoute>
              } />
              <Route path="/admin/tagging" element={
                <ProtectedRoute>
                  <QuestionTagging />
                </ProtectedRoute>
              } />
              <Route path="/admin/upload" element={
                <ProtectedRoute>
                  <AdminPaperUpload />
                </ProtectedRoute>
              } />

              {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>

          {/* AI Assistant */}
          <AIAssistantButton onClick={() => setIsAIOpen(true)} isOpen={isAIOpen} />
          <AIAssistant isOpen={isAIOpen} onClose={() => setIsAIOpen(false)} />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
