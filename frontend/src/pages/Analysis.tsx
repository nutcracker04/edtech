import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { PerformanceRadar } from "@/components/dashboard/PerformanceRadar";
import { SpiderWeb } from "@/components/analysis/SpiderWeb";
import { PerformanceGraph } from "@/components/analysis/PerformanceGraph";
import { usePerformance } from "@/hooks/usePerformance";
import { TrendingUp, TrendingDown, Target, AlertTriangle, CheckCircle, ChevronDown, ChevronUp, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const physicsTopics = [
  { subject: "Mechanics", score: 85, fullMark: 100 },
  { subject: "Thermodynamics", score: 72, fullMark: 100 },
  { subject: "Electromagnetism", score: 68, fullMark: 100 },
  { subject: "Optics", score: 75, fullMark: 100 },
  { subject: "Modern Physics", score: 60, fullMark: 100 },
  { subject: "Waves", score: 82, fullMark: 100 },
];

const chemistryTopics = [
  { subject: "Organic", score: 80, fullMark: 100 },
  { subject: "Inorganic", score: 65, fullMark: 100 },
  { subject: "Physical", score: 70, fullMark: 100 },
  { subject: "Equilibrium", score: 78, fullMark: 100 },
  { subject: "Electrochemistry", score: 55, fullMark: 100 },
  { subject: "Coordination", score: 62, fullMark: 100 },
];

const mathTopics = [
  { subject: "Calculus", score: 90, fullMark: 100 },
  { subject: "Algebra", score: 85, fullMark: 100 },
  { subject: "Coordinate Geometry", score: 75, fullMark: 100 },
  { subject: "Trigonometry", score: 88, fullMark: 100 },
  { subject: "Probability", score: 70, fullMark: 100 },
  { subject: "Vectors", score: 82, fullMark: 100 },
];

const weakAreas = [
  { topic: "Electrochemistry", subject: "Chemistry", score: 55, recommendation: "Focus on cell potentials and Nernst equation" },
  { topic: "Modern Physics", subject: "Physics", score: 60, recommendation: "Review photoelectric effect and atomic structure" },
  { topic: "Coordination Chemistry", subject: "Chemistry", score: 62, recommendation: "Practice isomerism and crystal field theory" },
];

const strongAreas = [
  { topic: "Calculus", subject: "Mathematics", score: 90 },
  { topic: "Trigonometry", subject: "Mathematics", score: 88 },
  { topic: "Mechanics", subject: "Physics", score: 85 },
];

const Analysis = () => {
  const { performanceMetrics, overallStats } = usePerformance();
  const [expandedTopic, setExpandedTopic] = useState<string | null>(null);

  // Mock data for demonstration - in real app would come from performanceMetrics
  const mockPerformanceMetrics = performanceMetrics.length > 0 ? performanceMetrics : [
    { subject: 'physics', topic: 'Kinematics', masteryScore: 85, questionsAttempted: 15, accuracy: 87, trend: 'improving' as const, strength: 'strong' as const, recommendations: ['Practice projectile motion problems'] },
    { subject: 'physics', topic: 'Mechanics', masteryScore: 78, questionsAttempted: 12, accuracy: 78, trend: 'stable' as const, strength: 'average' as const, recommendations: ['Focus on circular motion'] },
    { subject: 'physics', topic: 'Thermodynamics', masteryScore: 65, questionsAttempted: 10, accuracy: 65, trend: 'declining' as const, strength: 'weak' as const, recommendations: ['Review first law of thermodynamics', 'Practice entropy problems'] },
    { subject: 'chemistry', topic: 'Organic Chemistry', masteryScore: 82, questionsAttempted: 14, accuracy: 86, trend: 'improving' as const, strength: 'strong' as const, recommendations: [] },
    { subject: 'chemistry', topic: 'Physical Chemistry', masteryScore: 71, questionsAttempted: 11, accuracy: 73, trend: 'stable' as const, strength: 'average' as const, recommendations: ['Work on equilibrium calculations'] },
    { subject: 'mathematics', topic: 'Calculus', masteryScore: 90, questionsAttempted: 16, accuracy: 94, trend: 'improving' as const, strength: 'strong' as const, recommendations: [] },
  ];

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
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1">{overallStats.averageMastery}%</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">{overallStats.totalTopicsCovered} topics covered</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Questions Solved</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1">{overallStats.totalQuestionsAttempted}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">{overallStats.overallAccuracy}% accuracy</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Weak Areas</p>
              <p className="text-xl sm:text-2xl font-bold text-red-400 mt-1">{overallStats.weakTopicsCount}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">Need improvement</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4">
              <p className="text-[10px] sm:text-xs text-muted-foreground uppercase tracking-wider">Strong Areas</p>
              <p className="text-xl sm:text-2xl font-bold text-green-400 mt-1">{overallStats.strongTopicsCount}</p>
              <p className="text-[10px] sm:text-xs text-muted-foreground mt-2">Well mastered</p>
            </CardContent>
          </Card>
        </div>

        {/* Insights Section - MOVED ABOVE TABS */}
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
              <div className="space-y-3 sm:space-y-4">
                {weakAreas.map((area) => (
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
                            {area.score}%
                          </Badge>
                        </div>
                      </div>
                      <p className="text-xs sm:text-sm text-muted-foreground">{area.recommendation}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Strong Areas */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />
                <CardTitle className="text-base sm:text-lg">Your Strengths</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 sm:space-y-4">
                {strongAreas.map((area) => (
                  <Card key={area.topic} className="bg-green-500/10 border-green-500/20 hover:border-green-500/50 transition-colors">
                    <CardContent className="pt-4">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                        <div className="min-w-0">
                          <span className="font-medium text-foreground text-sm sm:text-base">{area.topic}</span>
                          <span className="text-muted-foreground ml-2 text-xs sm:text-sm">({area.subject})</span>
                        </div>
                        <div className="flex items-center gap-1 text-green-400 flex-shrink-0">
                          <TrendingUp className="h-4 w-4" />
                          <Badge variant="outline" className="bg-green-500/20 text-green-400 border-green-500/20">
                            {area.score}%
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Recommended Next Steps */}
              <Card className="mt-4 sm:mt-6 bg-primary/10 border-primary/20">
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="h-4 w-4 text-primary" />
                    <span className="font-medium text-foreground text-sm sm:text-base">Recommended Focus</span>
                  </div>
                  <p className="text-xs sm:text-sm text-muted-foreground">
                    Based on your performance, we recommend focusing on Electrochemistry 
                    and Modern Physics this week. Practice 15-20 questions daily in these topics.
                  </p>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </div>

        {/* Spider Web Visualization */}
        <SpiderWeb
          data={[
            {
              name: 'Physics',
              score: 75,
              chapters: [
                {
                  name: 'Mechanics',
                  score: 85,
                  topics: [
                    { name: 'Kinematics', score: 90 },
                    { name: 'Dynamics', score: 85 },
                    { name: 'Circular Motion', score: 80 },
                    { name: 'Rotational Motion', score: 82 },
                  ],
                },
                {
                  name: 'Thermodynamics',
                  score: 68,
                  topics: [
                    { name: 'First Law', score: 75 },
                    { name: 'Second Law', score: 65 },
                    { name: 'Entropy', score: 60 },
                    { name: 'Heat Engines', score: 70 },
                  ],
                },
                {
                  name: 'Electromagnetism',
                  score: 72,
                  topics: [
                    { name: 'Electric Fields', score: 80 },
                    { name: 'Magnetic Fields', score: 70 },
                    { name: 'Induction', score: 68 },
                    { name: 'AC Circuits', score: 70 },
                  ],
                },
              ],
            },
            {
              name: 'Chemistry',
              score: 71,
              chapters: [
                {
                  name: 'Organic',
                  score: 80,
                  topics: [
                    { name: 'Alkanes', score: 85 },
                    { name: 'Alkenes', score: 82 },
                    { name: 'Aromatic', score: 75 },
                  ],
                },
                {
                  name: 'Inorganic',
                  score: 65,
                  topics: [
                    { name: 'Periodic Table', score: 70 },
                    { name: 'Coordination', score: 62 },
                    { name: 'Metals', score: 63 },
                  ],
                },
                {
                  name: 'Physical',
                  score: 68,
                  topics: [
                    { name: 'Equilibrium', score: 72 },
                    { name: 'Kinetics', score: 68 },
                    { name: 'Electrochemistry', score: 64 },
                  ],
                },
              ],
            },
            {
              name: 'Mathematics',
              score: 83,
              chapters: [
                {
                  name: 'Calculus',
                  score: 90,
                  topics: [
                    { name: 'Limits', score: 92 },
                    { name: 'Derivatives', score: 90 },
                    { name: 'Integration', score: 88 },
                  ],
                },
                {
                  name: 'Algebra',
                  score: 85,
                  topics: [
                    { name: 'Polynomials', score: 88 },
                    { name: 'Matrices', score: 85 },
                    { name: 'Determinants', score: 82 },
                  ],
                },
                {
                  name: 'Geometry',
                  score: 75,
                  topics: [
                    { name: 'Coordinate Geometry', score: 78 },
                    { name: 'Vectors', score: 75 },
                    { name: '3D Geometry', score: 72 },
                  ],
                },
              ],
            },
          ]}
        />

        {/* Performance Trends Over Time */}
        <PerformanceGraph
          title="Performance Trends"
          description="Track your progress over time across all subjects"
          data={[
            { date: 'Jan 1', physics: 65, chemistry: 60, mathematics: 70, overall: 65 },
            { date: 'Jan 5', physics: 68, chemistry: 63, mathematics: 72, overall: 68 },
            { date: 'Jan 10', physics: 72, chemistry: 66, mathematics: 75, overall: 71 },
            { date: 'Jan 15', physics: 75, chemistry: 70, mathematics: 80, overall: 75 },
            { date: 'Jan 20', physics: 78, chemistry: 72, mathematics: 83, overall: 78 },
            { date: 'Jan 24', physics: 75, chemistry: 71, mathematics: 83, overall: 76 },
          ]}
          chartType="line"
          showSubjects={true}
        />

        {/* Topic Breakdown Section - BELOW INSIGHTS */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto">
            <TabsTrigger value="all" className="text-xs sm:text-sm py-2">All Topics</TabsTrigger>
            <TabsTrigger value="physics" className="text-xs sm:text-sm py-2">Physics</TabsTrigger>
            <TabsTrigger value="chemistry" className="text-xs sm:text-sm py-2">Chemistry</TabsTrigger>
            <TabsTrigger value="mathematics" className="text-xs sm:text-sm py-2">Mathematics</TabsTrigger>
          </TabsList>

          {/* All Topics */}
          <TabsContent value="all" className="space-y-4 mt-4 sm:mt-6">
            <div className="space-y-3">
              {mockPerformanceMetrics.map((metric) => (
                <Card key={metric.topic} className="overflow-hidden">
                  <button
                    onClick={() => setExpandedTopic(expandedTopic === metric.topic ? null : metric.topic)}
                    className="w-full p-3 sm:p-4 hover:bg-secondary/30 transition-colors flex items-center justify-between gap-2 sm:gap-3"
                  >
                    <div className="flex items-center gap-2 sm:gap-3 flex-1 text-left min-w-0">
                      <div className="w-1 h-6 sm:h-8 rounded-full shrink-0" style={{
                        backgroundColor: metric.strength === 'strong' ? '#22c55e' : metric.strength === 'average' ? '#eab308' : '#ef4444'
                      }} />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                        <div className="text-xs text-muted-foreground">{metric.subject}</div>
                      </div>
                      <div className="flex items-center gap-2 sm:gap-4 mr-2 sm:mr-4 flex-shrink-0">
                        <div className="text-right">
                          <div className="text-base sm:text-lg font-bold text-foreground">{metric.masteryScore}%</div>
                          <div className="text-[10px] sm:text-xs text-muted-foreground">{metric.accuracy}% accuracy</div>
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

                      {metric.recommendations && metric.recommendations.length > 0 && (
                        <div>
                          <p className="text-xs sm:text-sm font-medium text-foreground mb-2">Recommendations</p>
                          <ul className="space-y-1">
                            {metric.recommendations.map((rec, i) => (
                              <li key={i} className="text-xs sm:text-sm text-muted-foreground flex items-start gap-2">
                                <span className="text-primary mt-1">•</span>
                                <span>{rec}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <Button variant="outline" className="w-full mt-2 sm:mt-3" size="sm">
                        Practice {metric.topic}
                      </Button>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Physics Tab */}
          <TabsContent value="physics" className="space-y-4 sm:space-y-6 mt-4 sm:mt-6">
            <PerformanceRadar data={physicsTopics} title="Physics Topics" />
            <div className="space-y-3">
              {mockPerformanceMetrics.filter(m => m.subject === 'physics').map((metric) => (
                <div
                  key={metric.topic}
                  className="bg-card border border-border rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                    <div className="text-xs sm:text-sm text-muted-foreground">{metric.masteryScore}% mastery</div>
                  </div>
                  <div className="text-base sm:text-lg font-bold text-primary flex-shrink-0">{metric.masteryScore}%</div>
                </div>
              ))}
            </div>
          </TabsContent>

          {/* Chemistry Tab */}
          <TabsContent value="chemistry" className="space-y-4 sm:space-y-6 mt-4 sm:mt-6">
            <PerformanceRadar data={chemistryTopics} title="Chemistry Topics" />
            <div className="space-y-3">
              {mockPerformanceMetrics.filter(m => m.subject === 'chemistry').map((metric) => (
                <div
                  key={metric.topic}
                  className="bg-card border border-border rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                    <div className="text-xs sm:text-sm text-muted-foreground">{metric.masteryScore}% mastery</div>
                  </div>
                  <div className="text-base sm:text-lg font-bold text-primary flex-shrink-0">{metric.masteryScore}%</div>
                </div>
              ))}
            </div>
          </TabsContent>

          {/* Mathematics Tab */}
          <TabsContent value="mathematics" className="space-y-4 sm:space-y-6 mt-4 sm:mt-6">
            <PerformanceRadar data={mathTopics} title="Mathematics Topics" />
            <div className="space-y-3">
              {mockPerformanceMetrics.filter(m => m.subject === 'mathematics').map((metric) => (
                <div
                  key={metric.topic}
                  className="bg-card border border-border rounded-lg p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-foreground text-sm sm:text-base truncate">{metric.topic}</div>
                    <div className="text-xs sm:text-sm text-muted-foreground">{metric.masteryScore}% mastery</div>
                  </div>
                  <div className="text-base sm:text-lg font-bold text-primary flex-shrink-0">{metric.masteryScore}%</div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>

      </div>
    </MainLayout>
  );
};

export default Analysis;
