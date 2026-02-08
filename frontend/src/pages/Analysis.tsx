import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";
import { SpiderWeb } from "@/components/analysis/SpiderWeb";
import { PerformanceGraph } from "@/components/analysis/PerformanceGraph";
import { TrendingUp, TrendingDown, Target, AlertTriangle, ChevronDown, ChevronUp, ChevronRight, CheckCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { analysisApi } from "@/api/analysis";
import { toast } from "sonner";

interface TopicStats {
  topic: string;
  mastery_score: number;
  questions_attempted: number;
  questions_correct: number;
  trend: 'improving' | 'declining' | 'stable';
}

interface BreakdownTopic {
  topic: string;
  score: number;
}


interface SubjectStat {
  subject: string;
  average_mastery: number;
  total_questions: number;
  total_correct: number;
  weak_topics: number;
  strong_topics: number;
  topics: TopicStats[];
}

interface WeakArea {
  topic: string;
  subject: string;
  mastery_score: number;
  recommendation: string;
}

interface Recommendation {
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  action_url?: string;
}

interface TopicBreakdown {
  name: string;
  score: number;
  chapters: Array<{
    name: string;
    score: number;
    topics: Array<{
      name: string;
      score: number;
    }>;
  }>;
}

interface PerformanceTrend {
  date: string;
  accuracy: number;
}

interface HierarchyItem {
  id: string;
  name: string;
  chapters?: Array<{
    name: string;
    topics?: Array<{
      name: string;
    }>;
  }>;
}



const Analysis = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [hierarchy, setHierarchy] = useState<HierarchyItem[]>([]);
  const [performanceTrend, setPerformanceTrend] = useState<PerformanceTrend[]>([]);
  const [weakAreas, setWeakAreas] = useState<WeakArea[]>([]);
  const [subjectStats, setSubjectStats] = useState<SubjectStat[]>([]);
  const [topicBreakdown, setTopicBreakdown] = useState<TopicBreakdown[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [hier, trend, weak, stats, recs] = await Promise.all([
        analysisApi.getHierarchy().catch(() => []),
        analysisApi.getPerformanceTrend().catch(() => []),
        analysisApi.getWeakAreas().catch(() => []),
        analysisApi.getSubjectComparison().catch(() => []),
        analysisApi.getRecommendations().catch(() => [])
      ]);

      setHierarchy(hier);
      setPerformanceTrend(trend);
      setWeakAreas(weak);
      setSubjectStats(stats);
      setRecommendations(recs);

      // Build spider web data structure
      if (hier.length > 0 && stats.length > 0) {
        const breakdownPromises = hier.map((h: HierarchyItem) =>
          analysisApi.getTopicBreakdown(h.name).catch(() => [])
        );
        const breakdowns = await Promise.all(breakdownPromises);

        const formattedSpiderData = hier.map((h: HierarchyItem, idx: number) => {
          const subjectTopics = breakdowns[idx] || [];
          const chapterNodes = (h.chapters || []).map((chap) => {
            const chapTopics = (chap.topics || []).map((t) => {
              const stat = (subjectTopics as BreakdownTopic[]).find((st) => st.topic === t.name);

              return {
                name: t.name,
                score: stat ? Math.round(stat.score) : 0
              };
            });

            const totalScore = chapTopics.reduce((acc: number, t: { name: string; score: number }) => acc + t.score, 0);
            const avgScore = chapTopics.length > 0 ? Math.round(totalScore / chapTopics.length) : 0;

            return {
              name: chap.name,
              score: avgScore,
              topics: chapTopics
            };
          });

          const statsObj = stats.find((s: SubjectStat) => s.subject === h.name);

          return {
            name: h.name,
            score: statsObj ? Math.round(statsObj.average_mastery) : 0,
            chapters: chapterNodes
          };
        });

        setTopicBreakdown(formattedSpiderData);
      }

    } catch (error) {
      console.error('Failed to load analysis data:', error);
      toast.error("Failed to load analysis data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Derived Overall Stats
  const overallMastery = subjectStats.length > 0
    ? Math.round(subjectStats.reduce((acc, s) => acc + s.average_mastery, 0) / subjectStats.length)
    : 0;

  const totalQuestions = subjectStats.reduce((acc, s) => acc + s.total_questions, 0);
  const totalCorrect = subjectStats.reduce((acc, s) => acc + s.total_correct, 0);
  const overallAccuracy = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;

  const weakTopicsCount = subjectStats.reduce((acc, s) => acc + s.weak_topics, 0);
  const strongTopicsCount = subjectStats.reduce((acc, s) => acc + s.strong_topics, 0);

  // Flattened topic list for the list view
  const allTopicsList = subjectStats.flatMap(s =>
    (s.topics || []).map((t: TopicStats) => ({
      ...t,
      subject: s.subject,
      strength: t.mastery_score >= 85 ? 'strong' : t.mastery_score < 70 ? 'weak' : 'average'
    }))
  );

  if (loading) {
    return (
      <MainLayout>
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </MainLayout>
    );
  }

  if (subjectStats.length === 0) {
    return (
      <MainLayout>
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="text-center py-20">
            <AlertTriangle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">No Analysis Data Available</h2>
            <p className="text-muted-foreground mb-6">
              Take some tests to see your performance analysis
            </p>
            <Button onClick={() => navigate('/tests')}>
              Create Your First Test
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-4 sm:p-6 lg:p-8 space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Performance Analysis</h1>
          <p className="text-sm sm:text-base text-muted-foreground mt-1">
            Detailed breakdown of your strengths and weaknesses across all topics
          </p>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Overall Score</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1">{overallMastery}%</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">{hierarchy.length} subjects</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Questions Solved</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1">{totalQuestions}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">{overallAccuracy}% accuracy</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Weak Areas</p>
              <p className="text-xl sm:text-2xl font-bold text-red-400 mt-1">{weakTopicsCount}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">Need improvement</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Strong Areas</p>
              <p className="text-xl sm:text-2xl font-bold text-green-400 mt-1">{strongTopicsCount}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">Well mastered</p>
            </CardContent>
          </Card>
        </div>

        {/* Overview Content */}
        <div className="space-y-6">

          {/* Insights Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            {/* Weak Areas */}
            <Card className="flex flex-col h-[500px] lg:h-[650px]">
              <CardHeader className="shrink-0">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500" />
                  <CardTitle className="text-base sm:text-lg">Areas Needing Attention</CardTitle>
                </div>
                <CardDescription>Topics where your performance is below average</CardDescription>
              </CardHeader>
              <CardContent className="flex-1 min-h-0 p-0">
                <ScrollArea className="h-full px-6 pb-6">
                  <div className="space-y-3">
                    {weakAreas.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center mb-3">
                          <Target className="h-6 w-6 text-green-500" />
                        </div>
                        <p className="text-sm font-medium text-foreground">All Clear!</p>
                        <p className="text-xs text-muted-foreground">No weak areas identified yet.</p>
                      </div>
                    ) : (
                      weakAreas.map((area: WeakArea) => (
                        <div
                          key={area.topic}
                          className="group p-4 rounded-xl border border-border/50 bg-secondary/20 hover:bg-secondary/40 hover:border-primary/20 transition-all duration-200"
                        >
                          <div className="flex flex-col gap-2">
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="font-semibold text-foreground text-sm sm:text-base truncate group-hover:text-primary transition-colors">
                                  {area.topic}
                                </div>
                                <div className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider font-medium opacity-70">
                                  {area.subject}
                                </div>
                              </div>
                              <div className="flex flex-col items-end shrink-0 gap-1">
                                <Badge variant="outline" className="bg-red-500/10 text-red-500 border-red-500/20 px-1.5 py-0 font-bold">
                                  {Math.round(area.mastery_score)}%
                                </Badge>
                                <div className="flex items-center gap-0.5 text-[10px] text-red-400 font-medium">
                                  <TrendingDown className="h-3 w-3" />
                                  <span>Weak</span>
                                </div>
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground leading-relaxed bg-background/40 p-2 rounded-md border border-border/30">
                              <span className="font-medium text-primary/80 mr-1">Tip:</span>
                              {area.recommendation}
                            </div>
                            <Button
                              className="w-full bg-primary/10 hover:bg-primary/20 text-primary border-none shadow-sm h-8 text-xs font-bold"
                              variant="ghost"
                              onClick={() => navigate(`/tests?search=${encodeURIComponent(area.topic)}`)}
                            >
                              Practice Topic
                              <ChevronRight className="h-3 w-3 ml-auto opacity-70" />
                            </Button>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Spider Web Visualization */}
            {topicBreakdown.length > 0 && (
              <SpiderWeb
                data={topicBreakdown}
                className="h-[500px] lg:h-[650px]"
              />
            )}
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5 text-primary" />
                  Personalized Recommendations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendations.map((rec: Recommendation, idx: number) => (
                    <Card
                      key={idx}
                      className={`cursor-pointer hover:border-primary/50 transition-colors ${rec.priority === 'high' ? 'border-red-500/30' :
                        rec.priority === 'medium' ? 'border-yellow-500/30' :
                          'border-green-500/30'
                        }`}
                      onClick={() => rec.action_url && navigate(rec.action_url)}
                    >
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h4 className="font-medium text-sm">{rec.title}</h4>
                          <Badge
                            variant="outline"
                            className={
                              rec.priority === 'high' ? 'bg-red-500/20 text-red-400 border-red-500/20' :
                                rec.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/20' :
                                  'bg-green-500/20 text-green-400 border-green-500/20'
                            }
                          >
                            {rec.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{rec.description}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Performance Trends Over Time */}
          <PerformanceGraph
            title="Performance Trends"
            description="Track your progress over time"
            data={performanceTrend.map(pt => ({
              date: new Date(pt.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
              overall: pt.accuracy,
              // Assuming simplified trend data for now until backend supports per-subject daily trend
            }))}
            chartType="line"
            showSubjects={false} // Disable until backend sends per-subject trend data
          />

          {/* Subject Wise Breakdown */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-foreground tracking-tight">Subject Wise Breakdown</h2>
                <p className="text-sm text-muted-foreground mt-1">Topic-level performance across all subjects</p>
              </div>
            </div>

            <Tabs defaultValue="all" className="w-full">
              <TabsList className="shrink-0 w-fit mb-4">
                <TabsTrigger value="all">All Topics</TabsTrigger>
                {hierarchy.map(h => (
                  <TabsTrigger key={h.id} value={h.name.toLowerCase()} className="capitalize">
                    {h.name}
                  </TabsTrigger>
                ))}
              </TabsList>

              <TabsContent value="all" className="flex-1 min-h-0 mt-4 data-[state=active]:flex flex-col">
                <ScrollArea className="h-[500px] lg:h-[650px] pr-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-4">
                    {allTopicsList.map((metric: TopicStats & { subject: string; strength: string }) => (
                      <Card key={metric.topic} className="hover:shadow-md transition-all duration-200 border-border/50 group">
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between gap-4">
                            <div className="space-y-1.5 flex-1 min-w-0">
                              <CardTitle className="text-base font-semibold truncate pr-2 group-hover:text-primary transition-colors">
                                {metric.topic}
                              </CardTitle>
                              <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-2">
                                  <div className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                                  <span className="truncate text-[10px] text-muted-foreground uppercase tracking-widest font-bold">{metric.subject}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <Badge
                                    variant="outline"
                                    className={cn(
                                      "text-[10px] capitalize border font-bold",
                                      metric.mastery_score >= 85 ? "bg-green-500/10 text-green-600 border-green-200" :
                                        metric.mastery_score >= 70 ? "bg-yellow-500/10 text-yellow-600 border-yellow-200" :
                                          "bg-red-500/10 text-red-600 border-red-200"
                                    )}
                                  >
                                    {metric.strength}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                            <div className="flex flex-col items-end shrink-0">
                              <div className={cn(
                                "text-lg font-black",
                                metric.mastery_score >= 85 ? "text-green-600" :
                                  metric.mastery_score >= 70 ? "text-yellow-600" :
                                    "text-red-600"
                              )}>
                                {Math.round(metric.mastery_score)}%
                              </div>
                              <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Mastery</span>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                          <div className="grid grid-cols-2 gap-y-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-2">
                              <Target className="h-3.5 w-3.5 shrink-0 opacity-70" />
                              <span>{metric.questions_attempted} Attempted</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <CheckCircle className="h-3.5 w-3.5 shrink-0 opacity-70" />
                              <span>{metric.questions_correct} Correct</span>
                            </div>
                            <div className="flex items-center gap-2 col-span-2 pt-2 border-t mt-1">
                              <div className="flex-1 h-1.5 bg-secondary/50 rounded-full overflow-hidden">
                                <div
                                  className="h-full transition-all duration-500"
                                  style={{
                                    width: `${Math.round((metric.questions_correct / metric.questions_attempted) * 100) || 0}%`,
                                    backgroundColor: 'hsl(var(--primary))'
                                  }}
                                />
                              </div>
                              <span className="text-[10px] font-bold text-foreground">
                                {Math.round((metric.questions_correct / metric.questions_attempted) * 100) || 0}% Accuracy
                              </span>
                            </div>
                          </div>
                          <Button
                            className="w-full bg-primary hover:bg-primary/90 shadow-sm h-9 text-xs font-bold"
                            onClick={() => navigate(`/tests?search=${encodeURIComponent(metric.topic)}`)}
                          >
                            Practice Topic
                            <ChevronRight className="h-3.5 w-3.5 ml-auto opacity-70" />
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>

              {/* Individual Subject Tabs */}
              {hierarchy.map(h => {
                const subjectData = subjectStats.find(s => s.subject === h.name);
                const topics = subjectData?.topics || [];

                return (
                  <TabsContent key={h.id} value={h.name.toLowerCase()} className="mt-0">
                    {topics.length === 0 ? (
                      <Card className="border-dashed border-2">
                        <CardContent className="py-12 text-center">
                          <AlertTriangle className="h-10 w-10 text-muted-foreground mx-auto mb-4 opacity-50" />
                          <h3 className="text-lg font-medium text-foreground">No data available</h3>
                          <p className="text-sm text-muted-foreground mt-2">
                            Take more tests in {h.name} to see your performance breakdown.
                          </p>
                        </CardContent>
                      </Card>
                    ) : (
                      <ScrollArea className="h-[500px] lg:h-[650px] pr-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pb-4">
                          {topics.map((metric: TopicStats) => (
                            <Card key={metric.topic} className="hover:shadow-md transition-all duration-200 border-border/50 group">
                              <CardHeader className="pb-3">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="space-y-1.5 flex-1 min-w-0">
                                    <CardTitle className="text-base font-semibold truncate pr-2 group-hover:text-primary transition-colors">
                                      {metric.topic}
                                    </CardTitle>
                                    <div className="flex items-center gap-2">
                                      <Badge
                                        variant="outline"
                                        className={cn(
                                          "text-[10px] border font-bold",
                                          metric.mastery_score >= 85 ? "bg-green-500/10 text-green-600 border-green-200" :
                                            metric.mastery_score >= 70 ? "bg-yellow-500/10 text-yellow-600 border-yellow-200" :
                                              "bg-red-500/10 text-red-600 border-red-200"
                                        )}
                                      >
                                        {metric.mastery_score >= 85 ? 'Strong' : metric.mastery_score >= 70 ? 'Average' : 'Weak'}
                                      </Badge>
                                    </div>
                                  </div>
                                  <div className="flex flex-col items-end shrink-0">
                                    <div className={cn(
                                      "text-lg font-black",
                                      metric.mastery_score >= 85 ? "text-green-600" :
                                        metric.mastery_score >= 70 ? "text-yellow-600" :
                                          "text-red-600"
                                    )}>
                                      {Math.round(metric.mastery_score)}%
                                    </div>
                                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Mastery</span>
                                  </div>
                                </div>
                              </CardHeader>
                              <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-y-2 text-xs text-muted-foreground">
                                  <div className="flex items-center gap-2">
                                    <Target className="h-3.5 w-3.5 shrink-0 opacity-70" />
                                    <span>{metric.questions_attempted} Qs</span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <CheckCircle className="h-3.5 w-3.5 shrink-0 opacity-70" />
                                    <span>{metric.questions_correct} Correct</span>
                                  </div>
                                  <div className="flex-1 h-1 bg-secondary/50 rounded-full overflow-hidden col-span-2 mt-1">
                                    <div
                                      className="h-full transition-all duration-500"
                                      style={{
                                        width: `${metric.mastery_score}%`,
                                        backgroundColor: metric.mastery_score >= 85 ? '#22c55e' : metric.mastery_score >= 70 ? '#eab308' : '#ef4444'
                                      }}
                                    />
                                  </div>
                                </div>
                                <Button
                                  className="w-full bg-primary hover:bg-primary/90 shadow-sm h-9 text-xs font-bold"
                                  onClick={() => navigate(`/tests?search=${encodeURIComponent(metric.topic)}`)}
                                >
                                  Practice Topic
                                  <ChevronRight className="h-3.5 w-3.5 ml-auto opacity-70" />
                                </Button>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </ScrollArea>
                    )}
                  </TabsContent>
                );
              })}
            </Tabs>
          </div>
        </div>
      </div>
    </MainLayout >
  );
};

export default Analysis;
