import { useState, useEffect } from "react";
import { testApi } from "@/api/test";
import { MainLayout } from "@/components/layout/MainLayout";
import { ChevronRight, Filter, Plus, BookOpen, FileText, Search } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { TestScheduler } from "@/components/tests/TestScheduler";
import { TestCreationDialog } from "@/components/tests/TestCreationDialog";
import { PyqsDialog } from "@/components/tests/PyqsDialog";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { TestCard } from "@/components/tests/TestCard";
import { toast } from "sonner";
import { useNavigate, useSearchParams } from "react-router-dom";

interface Test {
  id: string;
  title: string;
  subject: string;
  type: "full" | "topic" | "adaptive";
  questions: number;
  duration: number;
  score?: number;
  date: string;
  status: "completed" | "in_progress" | "upcoming";
  scheduledAt?: Date | null;
}

type TestCategory = 'all' | 'my_tests' | 'pyq_chapter' | 'pyq_mock' | 'physics_pyq' | 'chemistry_pyq' | 'maths_pyq' | 'physics_topic' | 'chemistry_topic' | 'maths_topic';

const Tests = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || "";

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showPyqsDialog, setShowPyqsDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleImmediately, setScheduleImmediately] = useState(false);
  const [currentTestConfig, setCurrentTestConfig] = useState<any>(null);
  const [tests, setTests] = useState<Test[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<TestCategory>('all');
  const [searchQuery, setSearchQuery] = useState(initialSearch);

  useEffect(() => {
    loadTests();
  }, []);

  const loadTests = async () => {
    try {
      setIsLoading(true);
      const data = await testApi.getTests();
      // Map backend data to local Test interface
      const mappedTests = data.map((t: any) => ({
        id: t.id,
        title: t.title,
        subject: t.subject || "All Subjects",
        type: t.type,
        questions: t.questions?.length || 0,
        duration: t.duration,
        score: t.max_score > 0 ? Math.round((t.score / t.max_score) * 100) : undefined,
        date: new Date(t.created_at).toLocaleDateString(),
        status: t.status,
        scheduledAt: t.scheduled_at ? new Date(t.scheduled_at) : null
      }));
      setTests(mappedTests);
    } catch (error) {
      console.error("Failed to load tests", error);
      toast.error("Failed to load tests");
    } finally {
      setIsLoading(false);
    }
  };

  const filteredTests = tests.filter(test => {
    // Basic Search
    if (searchQuery && !test.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }

    // Category Filtering
    switch (selectedCategory) {
      case 'my_tests':
        return test.status === 'completed' || test.status === 'in_progress';
      case 'pyq_chapter':
        return test.title.toLowerCase().includes("pyq") && test.type === 'topic'; // Assumption
      case 'physics_pyq':
        return test.title.toLowerCase().includes("pyq") && test.subject?.toLowerCase() === 'physics';
      case 'chemistry_pyq':
        return test.title.toLowerCase().includes("pyq") && test.subject?.toLowerCase() === 'chemistry';
      case 'maths_pyq':
        return test.title.toLowerCase().includes("pyq") && test.subject?.toLowerCase() === 'mathematics';
      case 'pyq_mock':
        return test.title.toLowerCase().includes("pyq") && test.type === 'full';
      case 'physics_topic':
        return (test.type === 'topic' || test.type === 'adaptive') && test.subject?.toLowerCase() === 'physics';
      case 'chemistry_topic':
        return (test.type === 'topic' || test.type === 'adaptive') && test.subject?.toLowerCase() === 'chemistry';
      case 'maths_topic':
        return (test.type === 'topic' || test.type === 'adaptive') && test.subject?.toLowerCase() === 'mathematics';
      default:
        return true;
    }
  });


  const handleCreateSuccess = (testId?: string) => {
    // Refresh test list logic would go here
    if (testId) {
      navigate(`/test/${testId}`);
    } else {
      navigate(0); // Fallback to refresh if no ID (shouldn't happen with new logic)
    }
  };

  const handleScheduleTest = (scheduledDate: Date) => {
    console.log('Scheduling test for:', scheduledDate, currentTestConfig);
    toast.success(`Test scheduled for ${scheduledDate.toLocaleString()}`);
    setShowScheduleDialog(false);
    setShowCreateDialog(false);
    setScheduleImmediately(false);
    // TODO: Actually create test in database with scheduled_at
  };

  interface SidebarItemProps {
    active: boolean;
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
    badge?: string;
  }

  const SidebarItem = ({ active, label, onClick, icon, badge }: SidebarItemProps) => (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center w-full px-4 py-2 text-sm font-medium transition-colors rounded-md",
        active
          ? "bg-primary text-primary-foreground"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      {icon && <span className="mr-2">{icon}</span>}
      <span className="flex-1 text-left">{label}</span>
      {badge && (
        <Badge variant={active ? "secondary" : "outline"} className="ml-2 text-[10px] h-5">
          {badge}
        </Badge>
      )}
      {!active && <ChevronRight className="w-3 h-3 opacity-50" />}
    </button>
  );

  return (
    <MainLayout>
      <div className="flex h-[calc(100vh-theme(spacing.4))] overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 flex flex-col border-r bg-card/50 hidden md:flex shrink-0">
          <div className="p-4 border-b space-y-2">
            <Button onClick={() => setShowCreateDialog(true)} className="w-full justify-start">
              <Plus className="mr-2 h-4 w-4" /> Create Test
            </Button>
            <Button
              variant={selectedCategory === 'my_tests' ? 'default' : 'outline'}
              onClick={() => setSelectedCategory('my_tests')}
              className={cn("w-full justify-start", selectedCategory === 'my_tests' && "bg-primary text-primary-foreground hover:bg-primary/90")}
            >
              <FileText className="mr-2 h-4 w-4" /> My Tests
            </Button>
          </div>
          <ScrollArea className="flex-1 py-4">
            <div className="space-y-6 px-2">
              {/* PYQS Section */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  PYQ as Chapter-wise Tests
                </h3>
                <div className="space-y-1">
                  <SidebarItem
                    label="Physics PYQ"
                    active={selectedCategory === 'physics_pyq'}
                    onClick={() => setSelectedCategory('physics_pyq')}
                  />
                  <SidebarItem
                    label="Chemistry PYQ"
                    active={selectedCategory === 'chemistry_pyq'}
                    onClick={() => setSelectedCategory('chemistry_pyq')}

                  />
                  <SidebarItem
                    label="Mathematics PYQ"
                    active={selectedCategory === 'maths_pyq'}
                    onClick={() => setSelectedCategory('maths_pyq')}
                  />
                </div>
              </div>

              {/* PYQs as Mock Tests */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  PYQs as Mock Tests
                </h3>
                <div className="space-y-1">
                  {/* Placeholder items from image */}
                  <SidebarItem
                    label="2026 PYQs"
                    active={false}
                    onClick={() => { }}
                  />
                  <SidebarItem
                    label="2025 PYQs"
                    active={false}
                    onClick={() => { }}
                  />
                  <SidebarItem
                    label="2024 PYQs"
                    active={false}
                    onClick={() => { }}
                  />
                  <SidebarItem
                    label="2023 PYQs"
                    active={false}
                    onClick={() => { }}
                  />
                </div>
              </div>

              {/* Topic & Chapter wise */}
              <div>
                <h3 className="px-2 mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Topic & Chapter-wise
                </h3>
                <div className="space-y-1">
                  <SidebarItem
                    label="Physics"
                    active={selectedCategory === 'physics_topic'}
                    onClick={() => setSelectedCategory('physics_topic')}
                  />
                  <SidebarItem
                    label="Chemistry"
                    active={selectedCategory === 'chemistry_topic'}
                    onClick={() => setSelectedCategory('chemistry_topic')}
                  />
                  <SidebarItem
                    label="Mathematics"
                    active={selectedCategory === 'maths_topic'}
                    onClick={() => setSelectedCategory('maths_topic')}
                  />
                </div>
              </div>
            </div>
          </ScrollArea>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0 bg-background">
          {/* Content Area */}
          <div className="flex-1 overflow-hidden p-6 relative">
            <ScrollArea className="h-full pr-4">
              {/* Filter Chips / Tabs equivalent */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                {selectedCategory !== 'my_tests' && (
                  <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0">
                    <Button
                      variant={selectedCategory === 'all' ? 'default' : 'outline'}
                      size="sm"
                      className="rounded-full"
                      onClick={() => setSelectedCategory('all')}
                    >
                      All
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                    >
                      Available
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                    >
                      Upcoming
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="rounded-full"
                      onClick={() => setSelectedCategory('my_tests')}
                    >
                      Attempted
                    </Button>
                  </div>
                )}
                {/* Search Bar */}
                <div className="relative w-full sm:w-auto">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <input
                    placeholder="Search Tests"
                    className="pl-8 h-9 w-full sm:w-64 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {/* Test Grid */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 pb-10">
                {filteredTests.length > 0 ? (
                  filteredTests.map((test) => (
                    <TestCard key={test.id} test={test} />
                  ))
                ) : (
                  <div className="col-span-full flex flex-col items-center justify-center py-20 text-muted-foreground">
                    <div className="h-16 w-16 bg-muted/50 rounded-full flex items-center justify-center mb-4">
                      <FileText className="h-8 w-8 opacity-50" />
                    </div>
                    <h3 className="text-lg font-medium mb-1">No tests found</h3>
                    <p>Try adjusting your search or filters</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>

      {/* Create Test Dialog */}
      <TestCreationDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={handleCreateSuccess}
      />

      {/* PYQS Dialog */}
      <PyqsDialog
        open={showPyqsDialog}
        onOpenChange={setShowPyqsDialog}
      />

      {/* Schedule Test Dialog */}
      <Dialog open={showScheduleDialog} onOpenChange={setShowScheduleDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Schedule Test</DialogTitle>
          </DialogHeader>
          <TestScheduler
            testTitle={currentTestConfig?.title || 'Test'}
            testDuration={currentTestConfig?.duration || 60}
            onSchedule={handleScheduleTest}
            onCancel={() => {
              setShowScheduleDialog(false);
              setScheduleImmediately(false);
            }}
          />
        </DialogContent>
      </Dialog>
    </MainLayout>
  );
};

export default Tests;
