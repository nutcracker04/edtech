import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { Calendar, Clock, Target, ChevronRight, Filter, Plus, CalendarClock } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdaptiveTestConfig } from "@/components/tests/AdaptiveTestConfig";
import { TestScheduler } from "@/components/tests/TestScheduler";
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
}

const tests: Test[] = [
  {
    id: "1",
    title: "JEE Main Mock Test #5",
    subject: "All Subjects",
    type: "full",
    questions: 75,
    duration: 180,
    score: 245,
    date: "2026-01-10",
    status: "completed",
  },
  {
    id: "2",
    title: "Physics - Mechanics",
    subject: "Physics",
    type: "topic",
    questions: 30,
    duration: 45,
    score: 78,
    date: "2026-01-09",
    status: "completed",
  },
  {
    id: "3",
    title: "Organic Chemistry Practice",
    subject: "Chemistry",
    type: "practice",
    questions: 20,
    duration: 30,
    date: "2026-01-12",
    status: "in_progress",
  },
  {
    id: "4",
    title: "Calculus - Integration",
    subject: "Mathematics",
    type: "topic",
    questions: 25,
    duration: 40,
    date: "2026-01-08",
    status: "completed",
    score: 88,
  },
  {
    id: "5",
    title: "JEE Advanced Mock Test #2",
    subject: "All Subjects",
    type: "full",
    questions: 54,
    duration: 180,
    date: "2026-01-15",
    status: "upcoming",
  },
];

const scheduledTests = [
  {
    id: 's1',
    title: 'Physics - Thermodynamics',
    type: 'topic',
    subject: 'physics',
    duration: 45,
    scheduledAt: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
    status: 'upcoming' as const,
  },
  {
    id: 's2',
    title: 'JEE Main Mock Test #6',
    type: 'full',
    duration: 180,
    scheduledAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // Tomorrow
    status: 'upcoming' as const,
  },
];

const Tests = () => {
  const navigate = useNavigate();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);
  const [scheduleImmediately, setScheduleImmediately] = useState(false);
  const [currentTestConfig, setCurrentTestConfig] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'scheduled'>('all');

  const handleCreateAdaptiveTest = async (config: any) => {
    setCurrentTestConfig({ ...config, type: 'adaptive', title: 'Adaptive Test' });

    if (scheduleImmediately) {
      setShowCreateDialog(false);
      setShowScheduleDialog(true);
    } else {
      // Create test immediately
      setIsLoading(true);
      try {
        setTimeout(() => {
          console.log('Creating adaptive test with config:', config);
          toast.success('Test created successfully!');
          setShowCreateDialog(false);
        }, 1000);
      } finally {
        setIsLoading(false);
      }
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
                      className="px-3 sm:px-4 lg:px-6 py-3 sm:py-4 hover:bg-secondary/30 transition-colors cursor-pointer"
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
                          <ChevronRight className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0 ml-auto" />
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
                    test={test}
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
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto w-[95vw] sm:w-full">
          <DialogHeader>
            <DialogTitle className="text-lg sm:text-xl">Create New Test</DialogTitle>
          </DialogHeader>

          <Tabs defaultValue="adaptive" className="w-full">
            <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto">
              <TabsTrigger value="adaptive" className="text-xs sm:text-sm py-2">Adaptive</TabsTrigger>
              <TabsTrigger value="full" className="text-xs sm:text-sm py-2">Full Mock</TabsTrigger>
              <TabsTrigger value="topic" className="text-xs sm:text-sm py-2">Topic</TabsTrigger>
              <TabsTrigger value="custom" className="text-xs sm:text-sm py-2">Custom</TabsTrigger>
            </TabsList>

            {/* Adaptive Test */}
            <TabsContent value="adaptive" className="space-y-4 mt-4">
              <div>
                <p className="text-sm text-muted-foreground mb-4">
                  Create a personalized test based on your performance data. The algorithm will focus on your weak areas while maintaining your strengths.
                </p>
              </div>

              {/* Schedule Option */}
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-secondary/30">
                <Checkbox
                  id="schedule-later"
                  checked={scheduleImmediately}
                  onCheckedChange={(checked) => setScheduleImmediately(checked as boolean)}
                />
                <Label htmlFor="schedule-later" className="text-sm cursor-pointer">
                  Schedule for later instead of starting immediately
                </Label>
              </div>

              <AdaptiveTestConfig
                onSubmit={handleCreateAdaptiveTest}
                isLoading={isLoading}
              />
            </TabsContent>

            {/* Full Mock Test */}
            <TabsContent value="full" className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-secondary/30 text-sm text-muted-foreground">
                <p className="mb-3">
                  <strong>JEE Main Full Mock Test</strong> - Simulate the actual exam experience with 75 questions across all three subjects.
                </p>
                <ul className="space-y-2 ml-4 text-xs">
                  <li>• Physics: 25 questions</li>
                  <li>• Chemistry: 25 questions</li>
                  <li>• Mathematics: 25 questions</li>
                  <li>• Duration: 180 minutes</li>
                  <li>• Difficulty: Mixed</li>
                </ul>
              </div>
              <Button size="lg" className="w-full">
                Start Full Mock Test
              </Button>
            </TabsContent>

            {/* Topic Test */}
            <TabsContent value="topic" className="space-y-4 mt-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Select Subject
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {['physics', 'chemistry', 'mathematics'].map(subject => (
                      <button
                        key={subject}
                        className="p-3 rounded-lg border-2 border-border hover:border-primary/50 text-sm text-foreground capitalize"
                      >
                        {subject}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Select Topic
                  </label>
                  <div className="p-3 rounded-lg border border-border text-sm text-muted-foreground bg-secondary/30">
                    Select a subject first
                  </div>
                </div>

                <Button size="lg" className="w-full" disabled>
                  Create Topic Test
                </Button>
              </div>
            </TabsContent>

            {/* Custom Test */}
            <TabsContent value="custom" className="space-y-4 mt-4">
              <div className="p-4 rounded-lg bg-secondary/30 text-sm text-muted-foreground">
                <p>Create a fully customized test by selecting specific subjects, topics, and difficulty levels.</p>
              </div>
              <Button size="lg" className="w-full">
                Build Custom Test
              </Button>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>

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
