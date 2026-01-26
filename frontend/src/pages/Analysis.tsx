import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { PerformanceRadar } from "@/components/dashboard/PerformanceRadar";
import { SpiderWeb } from "@/components/analysis/SpiderWeb";
import { PerformanceGraph } from "@/components/analysis/PerformanceGraph";
import { TrendingUp, TrendingDown, Target, AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { analysisApi } from "@/api/analysis";
import { toast } from "sonner";

const Analysis = () => {
  const [loading, setLoading] = useState(true);
  const [hierarchy, setHierarchy] = useState<any[]>([]);
  const [performanceTrend, setPerformanceTrend] = useState<any[]>([]);
  const [weakAreas, setWeakAreas] = useState<any[]>([]);
  const [subjectStats, setSubjectStats] = useState<any[]>([]);
  const [topicBreakdown, setTopicBreakdown] = useState<any[]>([]); // For spider web

  const [selectedSubject, setSelectedSubject] = useState<string>("all");
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [hier, trend, weak, stats] = await Promise.all([
        analysisApi.getHierarchy(),
        analysisApi.getPerformanceTrend(), // Default 30 days
        analysisApi.getWeakAreas(),
        analysisApi.getSubjectComparison()
      ]);

      setHierarchy(hier);
      setPerformanceTrend(trend);
      setWeakAreas(weak);
      setSubjectStats(stats);

      // Load initial topic breakdown (all subjects or first subject)
      // For spider web, we need structured data. 
      // Let's fetch topic breakdown for each subject to build the spider web structure
      const breakdownPromises = hier.map((h: any) => analysisApi.getTopicBreakdown(h.name));
      const breakdowns = await Promise.all(breakdownPromises);

      // Map back to spider web structure
      const formattedSpiderData = hier.map((h: any, idx: number) => {
        // We have stats for topics. We need to group them into "chapters". 
        // Logic: Backend `get_topic_breakdown` returns flat list of topics with scores.
        // We need to map these topics to chapters using hierarchy.

        const subjectTopics = breakdowns[idx];
        const chapterNodes = h.chapters.map((chap: any) => {
          const chapTopics = chap.topics.map((t: any) => {
            const stat = subjectTopics.find((st: any) => st.topic === t.name);
            return {
              name: t.name,
              score: stat ? stat.score : 0
            };
          });

          // Chapter score is average of topic scores
          const totalScore = chapTopics.reduce((acc: number, t: any) => acc + t.score, 0);
          const avgScore = chapTopics.length > 0 ? Math.round(totalScore / chapTopics.length) : 0;

          return {
            name: chap.name,
            score: avgScore,
            topics: chapTopics
          };
        });

        // Subject score
        const statsObj = stats.find((s: any) => s.subject === h.name);

        return {
          name: h.name,
          score: statsObj ? statsObj.average_mastery : 0,
          chapters: chapterNodes
        };
      });

      setTopicBreakdown(formattedSpiderData);

    } catch (error) {
      console.error(error);
      toast.error("Failed to load analysis data");
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
    s.topics.map((t: any) => ({
      ...t,
      subject: s.subject,
      strength: t.mastery_score >= 85 ? 'strong' : t.mastery_score < 70 ? 'weak' : 'average'
    }))
  );

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

        {/* Insights Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Weak Areas */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-500" />
                <CardTitle className="text-base sm:text-lg">Areas Needing Attention</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 sm:space-y-4 max-h-[400px] overflow-y-auto pr-2">
                {weakAreas.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">Great job! No weak areas identified yet.</p>
                ) : (
                  weakAreas.map((area: any) => (
                    <Card key={area.topic} className="bg-secondary/30 border-border hover:border-yellow-500/50 transition-colors">
                      <CardContent className="pt-4">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                          <div className="min-w-0">
                            <span className="font-medium text-foreground text-sm sm:text-base">{area.topic}</span>
                            <span className="text-muted-foreground ml-2 text-xs sm:text-sm">({area.subject})</span>
                          </div>
                          <div className="flex items-center gap-1 text-red-400 flex-shrink-0">
                            <TrendingDown className="h-4 w-4" />
                            <Badge variant="outline" className="bg-red-500/20 text-red-400 border-red-500/20">
                              {Math.round(area.mastery_score)}%
                            </Badge>
                          </div>
                        </div>
                        <p className="text-xs sm:text-sm text-muted-foreground">{area.recommendation}</p>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </CardContent>
          </Card>

          {/* Spider Web Visualization */}
          {topicBreakdown.length > 0 && <SpiderWeb data={topicBreakdown} />}
        </div>

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

        {/* Topic Breakdown List */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto">
            <TabsTrigger value="all" className="text-xs sm:text-sm py-2">All Topics</TabsTrigger>
            {hierarchy.map(h => (
              <TabsTrigger key={h.id} value={h.name.toLowerCase()} className="text-xs sm:text-sm py-2 capitalize">
                {h.name}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="all" className="space-y-4 mt-4 sm:mt-6">
            <div className="space-y-3">
              {allTopicsList.map((metric: any) => (
                <Card key={metric.topic} className="overflow-hidden">
                  <button
                    onClick={() => setExpandedTopic(expandedTopic === metric.topic ? null : metric.topic)}
                    className="w-full p-3 sm:p-4 hover:bg-secondary/30 transition-colors flex items-center justify-between gap-2 sm:gap-3"
                  >
                    <div className="flex items-center gap-2 sm:gap-3 flex-1 text-left min-w-0">
                      <div className="w-1 h-6 sm:h-8 rounded-full shrink-0" style={{
                        backgroundColor: metric.mastery_score >= 85 ? '#22c55e' : metric.mastery_score >= 70 ? '#eab308' : '#ef4444'
                      }} />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                        <div className="text-xs text-muted-foreground">{metric.subject}</div>
                      </div>
                      <div className="flex items-center gap-2 sm:gap-4 mr-2 sm:mr-4 flex-shrink-0">
                        <div className="text-right">
                          <div className="text-base sm:text-lg font-bold text-foreground">{Math.round(metric.mastery_score)}%</div>
                          <div className="text-[10px] sm:text-xs text-muted-foreground">
                            {Math.round((metric.questions_correct / metric.questions_attempted) * 100) || 0}% accuracy
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {metric.trend === 'improving' && <TrendingUp className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-green-400" />}
                          {metric.trend === 'declining' && <TrendingDown className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-red-400" />}
                          {metric.trend === 'stable' && <Target className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-yellow-400" />}
                        </div>
                      </div>
                    </div>
                    {expandedTopic === metric.topic ? (
                      <ChevronUp className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0" />
                    ) : (
                      <ChevronDown className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground shrink-0" />
                    )}
                  </button>

                  {/* Expanded Content */}
                  {expandedTopic === metric.topic && (
                    <div className="border-t border-border p-3 sm:p-4 space-y-3 sm:space-y-4 bg-secondary/20">
                      <div>
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-2 mb-2">
                          <span className="text-xs sm:text-sm font-medium text-foreground">Mastery Progress</span>
                          <span className="text-[10px] sm:text-xs text-muted-foreground">{metric.questionsAttempted} questions</span>
                        </div>
                        <Progress value={metric.masteryScore} className="h-2" />
                      </div>

                      <Button variant="outline" className="w-full mt-2 sm:mt-3" size="sm">
                        Practice {metric.topic}
                      </Button>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Individual Subject Tabs */}
          {hierarchy.map(h => (
            <TabsContent key={h.id} value={h.name.toLowerCase()} className="space-y-4 sm:space-y-6 mt-4 sm:mt-6">
              <div className="space-y-3">
                {subjectStats
                  .find(s => s.subject === h.name)
                  ?.topics.map((metric: any) => (
                    <div
                      key={metric.topic}
                      className="bg-card border border-border rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                    >
                      <div className="min-w-0">
                        <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                        <div className="text-xs sm:text-sm text-muted-foreground">{Math.round(metric.mastery_score)}% mastery</div>
                      </div>
                      <div className="text-base sm:text-lg font-bold text-primary flex-shrink-0">{Math.round(metric.mastery_score)}%</div>
                    </div>
                  )) || <p className="text-sm text-muted-foreground">No data available for this subject.</p>}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </MainLayout>
  );
};

export default Analysis;
