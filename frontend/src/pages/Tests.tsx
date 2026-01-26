import { useState, useEffect } from "react";
import { testApi } from "@/api/test";
import { MainLayout } from "@/components/layout/MainLayout";
import { Calendar, Clock, Target, ChevronRight, Filter, Plus, CalendarClock } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TestScheduler } from "@/components/tests/TestScheduler";
import { TestCreationDialog } from "@/components/tests/TestCreationDialog";
import { ScheduledTestCard } from "@/components/tests/ScheduledTestCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

interface Test {
  id: string;
  title: string;
  subject: string;
  type: "full" | "topic" | "practice";
  questions: number;
  duration: number;
  score?: number;
  date: string;
  status: "completed" | "in_progress" | "upcoming";
  scheduledAt?: Date | null;
}

const Tests = () => {
  const navigate = useNavigate();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleImmediately, setScheduleImmediately] = useState(false);
  const [currentTestConfig, setCurrentTestConfig] = useState<any>(null);
  const [tests, setTests] = useState<Test[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'scheduled'>('all');

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

  const scheduledTests = tests.filter(t => t.status === 'upcoming');

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

  const handleStartScheduledTest = (testId: string) => {
    navigate(`/test/${testId}`);
  };

  const handleEditScheduledTest = (testId: string) => {
    toast.info('Rescheduling feature coming soon');
  };

  const handleDeleteScheduledTest = (testId: string) => {
    toast.success('Test removed from schedule');
    // TODO: Delete from database
  };

  const getStatusBadge = (status: Test["status"]) => {
    switch (status) {
      case "completed":
        return "bg-green-500/20 text-green-400";
      case "in_progress":
        return "bg-primary/20 text-primary";
      case "upcoming":
        return "bg-secondary text-muted-foreground";
    }
  };

  const getTypeBadge = (type: Test["type"]) => {
    switch (type) {
      case "full":
        return "bg-purple-500/20 text-purple-400";
      case "topic":
        return "bg-blue-500/20 text-blue-400";
      case "practice":
        return "bg-orange-500/20 text-orange-400";
    }
  };

  return (
    <MainLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">My Tests</h1>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <Button variant="outline" size="sm" className="flex-1 sm:flex-initial">
              <Filter className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Filter</span>
            </Button>
            <Button
              size="sm"
              onClick={() => setShowCreateDialog(true)}
              className="flex-1 sm:flex-initial"
            >
              <Plus className="h-4 w-4 sm:mr-2" />
              <span className="hidden sm:inline">Create Test</span>
              <span className="sm:hidden">Create</span>
            </Button>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs sm:text-sm text-muted-foreground">Total Tests</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground">23</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs sm:text-sm text-muted-foreground">Avg Score</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground">76%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs sm:text-sm text-muted-foreground">Best Score</p>
              <p className="text-xl sm:text-2xl font-bold text-green-400">92%</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-xs sm:text-sm text-muted-foreground">Time Spent</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground">42h</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for All Tests vs Scheduled */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'all' | 'scheduled')} className="space-y-4">
          <TabsList>
            <TabsTrigger value="all">All Tests</TabsTrigger>
            <TabsTrigger value="scheduled">
              <CalendarClock className="h-4 w-4 mr-2" />
              Scheduled ({scheduledTests.length})
            </TabsTrigger>
          </TabsList>

          {/* All Tests Tab */}
          <TabsContent value="all" className="space-y-0">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm sm:text-base">Recent Tests</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {tests.map((test) => (
                    <div
                      key={test.id}
                      className="px-3 sm:px-4 lg:px-6 py-3 sm:py-4 hover:bg-secondary/30 transition-colors"
                    >
                      <div className="flex flex-col gap-3">
                        {/* Title and Badges Row */}
                        <div className="flex items-start justify-between gap-2">
                          <h3 className="font-medium text-foreground text-sm sm:text-base flex-1 min-w-0 pr-2">
                            {test.title}
                          </h3>
                          <div className="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
                            <Badge variant="outline" className={cn("text-xs whitespace-nowrap", getTypeBadge(test.type))}>
                              {test.type}
                            </Badge>
                            <Badge variant="outline" className={cn("text-xs capitalize whitespace-nowrap", getStatusBadge(test.status))}>
                              {test.status.replace("_", " ")}
                            </Badge>
                          </div>
                        </div>

                        {/* Metadata Row */}
                        <div className="flex flex-wrap items-center gap-x-3 sm:gap-x-4 gap-y-1 text-xs sm:text-sm text-muted-foreground">
                          <span className="whitespace-nowrap">{test.subject}</span>
                          <span className="hidden sm:inline">•</span>
                          <span className="flex items-center gap-1 whitespace-nowrap">
                            <Target className="h-3 w-3 sm:h-3.5 sm:w-3.5 shrink-0" />
                            {test.questions} questions
                          </span>
                          <span className="hidden sm:inline">•</span>
                          <span className="flex items-center gap-1 whitespace-nowrap">
                            <Clock className="h-3 w-3 sm:h-3.5 sm:w-3.5 shrink-0" />
                            {test.duration} min
                          </span>
                          <span className="hidden sm:inline">•</span>
                          <span className="flex items-center gap-1 whitespace-nowrap">
                            <Calendar className="h-3 w-3 sm:h-3.5 sm:w-3.5 shrink-0" />
                            {test.date}
                          </span>
                        </div>

                        {/* Score and Action Row */}
                        <div className="flex items-center justify-between gap-2 pt-1">
                          {test.score !== undefined && (
                            <Badge
                              variant="outline"
                              className={cn(
                                "text-xs sm:text-sm whitespace-nowrap",
                                test.score >= 80 ? "bg-green-500/20 text-green-400 border-green-500/20" :
                                  test.score >= 60 ? "bg-primary/20 text-primary border-primary/20" :
                                    "bg-red-500/20 text-red-400 border-red-500/20"
                              )}
                            >
                              {test.score}%
                            </Badge>
                          )}
                          {test.status === 'completed' ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => navigate(`/tests/${test.id}/results`)}
                              className="ml-auto"
                            >
                              View Results
                              <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => navigate(`/test/${test.id}`)}
                              className="ml-auto"
                            >
                              {test.status === 'in_progress' ? 'Continue' : 'Start'}
                              <ChevronRight className="h-4 w-4 ml-1" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scheduled Tests Tab */}
          <TabsContent value="scheduled" className="space-y-4">
            {scheduledTests.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <CalendarClock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Scheduled Tests</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Schedule tests to stay organized and get reminders
                  </p>
                  <Button onClick={() => setShowCreateDialog(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Schedule a Test
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {scheduledTests.map((test) => (
                  <ScheduledTestCard
                    key={test.id}
                    test={test as any}
                    onStart={handleStartScheduledTest}
                    onEdit={handleEditScheduledTest}
                    onDelete={handleDeleteScheduledTest}
                  />
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Create Test Dialog */}
      <TestCreationDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onSuccess={handleCreateSuccess}
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
