import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Practice from "./pages/Practice";
import Analysis from "./pages/Analysis";
import Tests from "./pages/Tests";
import Settings from "./pages/Settings";
import RevisionCapsules from "./pages/RevisionCapsules";
import TestTaking from "./pages/TestTaking";
import NotFound from "./pages/NotFound";
import { AIAssistant } from "./components/ai/AIAssistant";
import { AIAssistantButton } from "./components/ai/AIAssistantButton";

const queryClient = new QueryClient();

const App = () => {
  const [isAIOpen, setIsAIOpen] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/analysis" element={<Analysis />} />
            <Route path="/tests" element={<Tests />} />
            <Route path="/test/:testId" element={<TestTaking />} />
            <Route path="/revision-capsules" element={<RevisionCapsules />} />
            <Route path="/settings" element={<Settings />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
        
        {/* AI Assistant */}
        <AIAssistantButton onClick={() => setIsAIOpen(true)} isOpen={isAIOpen} />
        <AIAssistant isOpen={isAIOpen} onClose={() => setIsAIOpen(false)} />
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
