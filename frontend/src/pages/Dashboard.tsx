import { MainLayout } from "@/components/layout/MainLayout";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { SubjectCard } from "@/components/dashboard/SubjectCard";
import { UpcomingTestsWidget } from "@/components/dashboard/UpcomingTestsWidget";

import { usePerformance, useSubjectPerformance } from "@/hooks/usePerformance";
import { Calculator, Atom, FlaskConical, Loader2, BookOpen, Target, AlertTriangle, TrendingDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { DashboardSkeleton } from "@/components/ui/loading-skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
            description="Start taking tests or uploading papers to see your performance data and analytics here. Your journey to success begins with the first test!"
            action={{
              label: 'Take a Test',
              onClick: () => navigate('/tests'),
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

        {/* Subject Performance */}
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

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Combined Topic Mastery Area */}
          <div className="space-y-6">
            <Card className="flex flex-col h-[500px]">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-xl">
                      <Target className="h-5 w-5 text-primary" />
                      Topic Mastery Analysis
                    </CardTitle>
                    <p className="text-sm text-muted-foreground">Comprehensive view of your learning progress</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex-1 min-h-0 pt-0">
                <Tabs defaultValue="all" className="h-full flex flex-col">
                  <TabsList className="mb-4 grid w-full grid-cols-3">
                    <TabsTrigger value="all">All Topics</TabsTrigger>
                    <TabsTrigger value="weak" className="text-red-500">Weak Areas</TabsTrigger>
                    <TabsTrigger value="strong" className="text-green-500">Strong Areas</TabsTrigger>
                  </TabsList>

                  <div className="flex-1 min-h-0">
                    <TabsContent value="all" className="h-full m-0">
                      <ScrollArea className="h-[360px] pr-4">
                        <div className="space-y-4">
                          {/* Weak Topics Section */}
                          <div className="space-y-2">
                            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Needs Improvement</h4>
                            {physicsPerf?.topicMasteries.filter(t => t.masteryScore < 70).map(topic => (
                              <div key={`weak-${topic.topic}`} className="p-3 rounded-xl border border-red-500/10 bg-red-500/5 hover:bg-red-500/10 transition-all">
                                <div className="flex items-center justify-between gap-4">
                                  <div className="min-w-0">
                                    <span className="font-semibold text-sm block truncate">{topic.topic}</span>
                                    <span className="text-[10px] text-muted-foreground">Mastery: {Math.round(topic.masteryScore)}%</span>
                                  </div>
                                  <Badge variant="outline" className="text-red-500 bg-red-500/10 border-red-500/20 text-[10px] font-black">
                                    WEAK
                                  </Badge>
                                </div>
                                <Progress value={topic.masteryScore} className="h-1 mt-2 bg-red-200/20" indicatorClassName="bg-red-500" />
                              </div>
                            ))}
                            {/* Sample Weak Data */}
                            <div className="p-3 rounded-xl border border-red-500/10 bg-red-500/5">
                              <div className="flex items-center justify-between gap-4">
                                <div className="min-w-0">
                                  <span className="font-semibold text-sm block">Integration by Parts</span>
                                  <span className="text-[10px] text-muted-foreground">Mastery: 45%</span>
                                </div>
                                <Badge variant="outline" className="text-red-500 bg-red-500/10 border-red-500/20 text-[10px] font-black">WEAK</Badge>
                              </div>
                              <Progress value={45} className="h-1 mt-2 bg-red-200/20" indicatorClassName="bg-red-500" />
                            </div>
                          </div>

                          {/* Strong Topics Section */}
                          <div className="space-y-2 pb-4">
                            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Your Strengths</h4>
                            {physicsPerf?.topicMasteries.filter(t => t.masteryScore >= 85).map(topic => (
                              <div key={`strong-${topic.topic}`} className="p-3 rounded-xl border border-green-500/10 bg-green-500/5 hover:bg-green-500/10 transition-all">
                                <div className="flex items-center justify-between gap-4">
                                  <div className="min-w-0">
                                    <span className="font-semibold text-sm block truncate">{topic.topic}</span>
                                    <span className="text-[10px] text-muted-foreground">Mastery: {Math.round(topic.masteryScore)}%</span>
                                  </div>
                                  <Badge variant="outline" className="text-green-500 bg-green-500/10 border-green-500/20 text-[10px] font-black">
                                    STRONG
                                  </Badge>
                                </div>
                                <Progress value={topic.masteryScore} className="h-1 mt-2 bg-green-200/20" indicatorClassName="bg-green-500" />
                              </div>
                            ))}
                            {/* Sample Strong Data */}
                            <div className="p-3 rounded-xl border border-green-500/10 bg-green-500/5">
                              <div className="flex items-center justify-between gap-4">
                                <div className="min-w-0">
                                  <span className="font-semibold text-sm block">Chemical Bonding</span>
                                  <span className="text-[10px] text-muted-foreground">Mastery: 92%</span>
                                </div>
                                <Badge variant="outline" className="text-green-500 bg-green-500/10 border-green-500/20 text-[10px] font-black">STRONG</Badge>
                              </div>
                              <Progress value={92} className="h-1 mt-2 bg-green-200/20" indicatorClassName="bg-green-500" />
                            </div>
                            <div className="p-3 rounded-xl border border-green-500/10 bg-green-500/5">
                              <div className="flex items-center justify-between gap-4">
                                <div className="min-w-0">
                                  <span className="font-semibold text-sm block">Vector Algebra</span>
                                  <span className="text-[10px] text-muted-foreground">Mastery: 88%</span>
                                </div>
                                <Badge variant="outline" className="text-green-500 bg-green-500/10 border-green-500/20 text-[10px] font-black">STRONG</Badge>
                              </div>
                              <Progress value={88} className="h-1 mt-2 bg-green-200/20" indicatorClassName="bg-green-500" />
                            </div>
                          </div>
                        </div>
                      </ScrollArea>
                    </TabsContent>

                    <TabsContent value="weak" className="h-full m-0">
                      <ScrollArea className="h-[360px] pr-4">
                        <div className="space-y-3">
                          {physicsPerf?.topicMasteries.filter(t => t.masteryScore < 70).map(topic => (
                            <div key={`weak-tab-${topic.topic}`} className="p-4 rounded-xl border border-red-500/10 bg-red-500/5">
                              <div className="flex justify-between items-start mb-2">
                                <h5 className="font-bold text-sm text-foreground">{topic.topic}</h5>
                                <span className="text-xs font-black text-red-500">{Math.round(topic.masteryScore)}%</span>
                              </div>
                              <Progress value={topic.masteryScore} className="h-1.5" indicatorClassName="bg-red-500" />
                              <p className="text-[10px] text-muted-foreground mt-2">Recommended: Practice Topic-wise test</p>
                            </div>
                          ))}
                          <div className="p-4 rounded-xl border border-red-500/10 bg-red-500/5">
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-bold text-sm text-foreground">Integration by Parts</h5>
                              <span className="text-xs font-black text-red-500">45%</span>
                            </div>
                            <Progress value={45} className="h-1.5" indicatorClassName="bg-red-500" />
                            <p className="text-[10px] text-muted-foreground mt-2">High weightage topic - requires attention</p>
                          </div>
                        </div>
                      </ScrollArea>
                    </TabsContent>

                    <TabsContent value="strong" className="h-full m-0">
                      <ScrollArea className="h-[360px] pr-4">
                        <div className="space-y-3">
                          {physicsPerf?.topicMasteries.filter(t => t.masteryScore >= 85).map(topic => (
                            <div key={`strong-tab-${topic.topic}`} className="p-4 rounded-xl border border-green-500/10 bg-green-500/5">
                              <div className="flex justify-between items-start mb-2">
                                <h5 className="font-bold text-sm text-foreground">{topic.topic}</h5>
                                <span className="text-xs font-black text-green-500">{Math.round(topic.masteryScore)}%</span>
                              </div>
                              <Progress value={topic.masteryScore} className="h-1.5" indicatorClassName="bg-green-500" />
                            </div>
                          ))}
                          <div className="p-4 rounded-xl border border-green-500/10 bg-green-500/5">
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-bold text-sm text-foreground">Chemical Bonding</h5>
                              <span className="text-xs font-black text-green-500">92%</span>
                            </div>
                            <Progress value={92} className="h-1.5" indicatorClassName="bg-green-500" />
                          </div>
                          <div className="p-4 rounded-xl border border-green-500/10 bg-green-500/5">
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-bold text-sm text-foreground">Vector Algebra</h5>
                              <span className="text-xs font-black text-green-500">88%</span>
                            </div>
                            <Progress value={88} className="h-1.5" indicatorClassName="bg-green-500" />
                          </div>
                        </div>
                      </ScrollArea>
                    </TabsContent>
                  </div>
                </Tabs>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Sidebar Widgets */}
          <div className="space-y-6">
            {/* Upcoming Tests Widget (if you want to keep it or move it) */}
            <UpcomingTestsWidget />
          </div>
        </div>


      </div>
    </MainLayout>
  );
};

export default Dashboard;
