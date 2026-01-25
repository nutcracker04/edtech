import { MainLayout } from "@/components/layout/MainLayout";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { SubjectCard } from "@/components/dashboard/SubjectCard";
import { PerformanceRadar } from "@/components/dashboard/PerformanceRadar";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { StreakCard } from "@/components/dashboard/StreakCard";
import { UpcomingTestsWidget } from "@/components/dashboard/UpcomingTestsWidget";
import { usePerformance, useSubjectPerformance } from "@/hooks/usePerformance";
import { Calculator, Atom, FlaskConical, Loader2, BookOpen, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { DashboardSkeleton } from "@/components/ui/loading-skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";

const subjectIcons = {
  physics: <Atom className="h-5 w-5" />,
  chemistry: <FlaskConical className="h-5 w-5" />,
  mathematics: <Calculator className="h-5 w-5" />,
};

const Dashboard = () => {
  const navigate = useNavigate();
  const { userPerformance, isLoading } = usePerformance();
  const physicsPerf = useSubjectPerformance('physics');

  // Transform subject performance data for display
  const subjectData = userPerformance?.subjectPerformance.map(perf => ({
    title: perf.subject.charAt(0).toUpperCase() + perf.subject.slice(1),
    icon: subjectIcons[perf.subject as keyof typeof subjectIcons],
    score: Math.round(perf.averageScore),
    change: 0, // TODO: Calculate from trend
    topics: perf.topicMastery.slice(0, 3).map(topic => ({
      name: topic.topic,
      mastery: Math.round(topic.masteryScore),
    })),
  })) || [];

  // Transform physics data for radar chart
  const radarData = physicsPerf?.topicMasteries.map(topic => ({
    subject: topic.topic,
    score: Math.round(topic.masteryScore),
    fullMark: 100,
  })) || [];

  if (isLoading) {
    return (
      <MainLayout>
        <DashboardSkeleton />
      </MainLayout>
    );
  }

  // Show empty state if no data
  if (!userPerformance || userPerformance.subjectPerformance.length === 0) {
    return (
      <MainLayout>
        <div className="p-8 animate-fade-in">
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground mb-8">
            Track your progress and identify areas for improvement
          </p>

          <EmptyState
            icon={Target}
            title="Welcome to Your Dashboard!"
            description="Start taking tests or practicing questions to see your performance data and analytics here. Your journey to success begins with the first test!"
            action={{
              label: 'Take a Practice Test',
              onClick: () => navigate('/practice'),
            }}
            secondaryAction={{
              label: 'Upload a Test',
              onClick: () => navigate('/upload-test'),
            }}
          />

          {/* Quick Start Guide */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="hover-lift">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold">Take Tests</h3>
                </div>
                <p className="text-sm text-muted-foreground">
                  Create adaptive tests based on your performance or practice specific topics.
                </p>
              </CardContent>
            </Card>

            <Card className="hover-lift">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full bg-green-500/10 flex items-center justify-center">
                    <Target className="h-5 w-5 text-green-500" />
                  </div>
                  <h3 className="font-semibold">Track Progress</h3>
                </div>
                <p className="text-sm text-muted-foreground">
                  Monitor your performance across subjects and identify weak areas.
                </p>
              </CardContent>
            </Card>

            <Card className="hover-lift">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full bg-blue-500/10 flex items-center justify-center">
                    <Atom className="h-5 w-5 text-blue-500" />
                  </div>
                  <h3 className="font-semibold">Improve Skills</h3>
                </div>
                <p className="text-sm text-muted-foreground">
                  Get personalized recommendations for weak topics.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 lg:space-y-8 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Track your progress and identify areas for improvement
          </p>
        </div>

        {/* Stats */}
        <StatsGrid />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Charts and Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {/* Subject Cards */}
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-4">Subject Performance</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {subjectData.map((subject, index) => (
                  <div
                    key={subject.title}
                    className="animate-slide-up"
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <SubjectCard {...subject} />
                  </div>
                ))}
              </div>
            </div>

            {/* Performance Radar */}
            <PerformanceRadar data={radarData} title="Physics Topic Analysis" />

            {/* Recent Activity */}
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-4">Recent Activity</h2>
              <RecentActivity />
            </div>
          </div>

          {/* Right Column - Sidebar Widgets */}
          <div className="space-y-6">
            {/* Upcoming Tests */}
            <UpcomingTestsWidget />

            {/* Streak Card */}
            <StreakCard />
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;
