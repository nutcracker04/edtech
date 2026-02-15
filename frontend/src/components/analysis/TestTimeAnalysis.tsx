import { useEffect, useState } from 'react';
import { testApi } from '@/api/test';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Clock, TrendingUp, TrendingDown, Target, Zap, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

interface TestTimeAnalysisProps {
  testId: string;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export const TestTimeAnalysis = ({ testId }: TestTimeAnalysisProps) => {
  const [timeData, setTimeData] = useState<any>(null);
  const [journeyData, setJourneyData] = useState<any>(null);
  const [difficultyData, setDifficultyData] = useState<any>(null);
  const [efficiencyData, setEfficiencyData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalysisData();
  }, [testId]);

  const loadAnalysisData = async () => {
    try {
      const [time, journey, difficulty, efficiency] = await Promise.all([
        testApi.getTimeAnalysis(testId),
        testApi.getJourneyAnalysis(testId),
        testApi.getDifficultyAnalysis(testId),
        testApi.getEfficiencyAnalysis(testId)
      ]);

      setTimeData(time);
      setJourneyData(journey);
      setDifficultyData(difficulty);
      setEfficiencyData(efficiency);
    } catch (error) {
      console.error('Failed to load analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  if (!timeData) return null;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              <span className="text-2xl font-bold">{formatTime(timeData.total_time)}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg per Question</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-500" />
              <span className="text-2xl font-bold">{formatTime(Math.round(timeData.avg_time_per_question))}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Navigation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              <span className="text-2xl font-bold">{journeyData?.navigation_patterns?.total_navigations || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {journeyData?.navigation_patterns?.jumps || 0} jumps
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Answer Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-500" />
              <span className="text-2xl font-bold">{journeyData?.answer_change_stats?.modifications || 0}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {journeyData?.answer_change_stats?.total_changes || 0} total changes
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="subject" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="subject">By Subject</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="journey">Journey</TabsTrigger>
          <TabsTrigger value="difficulty">Difficulty</TabsTrigger>
          <TabsTrigger value="efficiency">Efficiency</TabsTrigger>
        </TabsList>

        {/* Subject Breakdown */}
        <TabsContent value="subject" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Time Distribution by Subject</CardTitle>
              <CardDescription>How you spent time across different subjects</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Pie Chart */}
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={timeData.subject_breakdown}
                      dataKey="total_time"
                      nameKey="subject"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry) => `${entry.subject}: ${formatTime(entry.total_time)}`}
                    >
                      {timeData.subject_breakdown.map((_: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => formatTime(value)} />
                  </PieChart>
                </ResponsiveContainer>

                {/* Bar Chart */}
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={timeData.subject_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="subject" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => formatTime(value)} />
                    <Legend />
                    <Bar dataKey="total_time" fill="#3b82f6" name="Time (seconds)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Subject Details */}
              <div className="mt-6 space-y-3">
                {timeData.subject_breakdown.map((subject: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                      />
                      <div>
                        <p className="font-medium">{subject.subject}</p>
                        <p className="text-sm text-muted-foreground">
                          {subject.question_count} questions • {subject.correct_count} correct
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatTime(subject.total_time)}</p>
                      <p className="text-sm text-muted-foreground">
                        {formatTime(Math.round(subject.avg_time_per_question))} avg
                      </p>
                      <Badge variant={subject.accuracy >= 70 ? 'default' : 'destructive'} className="mt-1">
                        {subject.accuracy.toFixed(0)}% accuracy
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Question-wise Breakdown */}
        <TabsContent value="questions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Time Spent per Question</CardTitle>
              <CardDescription>Detailed breakdown of time on each question</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={timeData.questions}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="question_order" label={{ value: 'Question Number', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip
                    formatter={(value: number) => formatTime(value)}
                    labelFormatter={(label) => `Question ${label + 1}`}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="time_spent" stroke="#3b82f6" name="Time Spent" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>

              {/* Question List */}
              <div className="mt-6 space-y-2 max-h-96 overflow-y-auto">
                {timeData.questions.map((q: any, idx: number) => (
                  <div
                    key={idx}
                    className={cn(
                      "flex items-center justify-between p-3 border rounded-lg",
                      q.is_correct ? "bg-green-50 dark:bg-green-950/20" : "bg-red-50 dark:bg-red-950/20"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-lg">Q{q.question_order + 1}</span>
                      <div>
                        <p className="text-sm font-medium">{q.subject} • {q.topic}</p>
                        <div className="flex gap-2 mt-1">
                          {q.marked_for_review && (
                            <Badge variant="outline" className="text-xs">Marked</Badge>
                          )}
                          {q.view_count > 1 && (
                            <Badge variant="secondary" className="text-xs">
                              Viewed {q.view_count}x
                            </Badge>
                          )}
                          {q.answer_changed_count > 0 && (
                            <Badge variant="secondary" className="text-xs">
                              Changed {q.answer_changed_count}x
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-lg">{formatTime(q.time_spent)}</p>
                      <Badge variant={q.is_correct ? 'default' : 'destructive'}>
                        {q.is_correct ? 'Correct' : 'Incorrect'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Journey Analysis */}
        <TabsContent value="journey" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Test Journey Analysis</CardTitle>
              <CardDescription>How you navigated through the test</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Navigation Patterns */}
              <div>
                <h3 className="font-semibold mb-3">Navigation Patterns</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">
                      {journeyData?.navigation_patterns?.next_clicks || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Next Clicks</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-orange-600">
                      {journeyData?.navigation_patterns?.previous_clicks || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Previous Clicks</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-purple-600">
                      {journeyData?.navigation_patterns?.jumps || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Jumps</p>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-2xl font-bold text-green-600">
                      {journeyData?.navigation_patterns?.review_navigations || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Review Visits</p>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div>
                <h3 className="font-semibold mb-3">Activity Timeline</h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {journeyData?.timeline?.slice(0, 50).map((event: any, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-2 border-l-2 border-primary pl-4">
                      {event.type === 'navigation' ? (
                        <>
                          <Zap className="h-4 w-4 mt-0.5 text-blue-500" />
                          <div className="flex-1">
                            <p className="text-sm">
                              Navigated from Q{(event.from_index ?? -1) + 1} to Q{event.to_index + 1}
                              <Badge variant="outline" className="ml-2 text-xs">
                                {event.navigation_type}
                              </Badge>
                            </p>
                            <p className="text-xs text-muted-foreground">
                              Spent {formatTime(event.time_on_previous || 0)} on previous
                            </p>
                          </div>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="h-4 w-4 mt-0.5 text-orange-500" />
                          <div className="flex-1">
                            <p className="text-sm">
                              Changed answer for Q{event.question_index + 1}
                              <Badge variant="outline" className="ml-2 text-xs">
                                {event.change_type}
                              </Badge>
                            </p>
                          </div>
                        </>
                      )}
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Difficulty Analysis */}
        <TabsContent value="difficulty" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Question Difficulty by Time</CardTitle>
              <CardDescription>Questions categorized by time spent relative to average</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['very_slow', 'slow', 'normal', 'fast', 'very_fast'].map((category) => {
                  const questions = difficultyData?.questions?.filter((q: any) => q.time_category === category) || [];
                  if (questions.length === 0) return null;

                  const categoryInfo = {
                    very_slow: { label: 'Very Slow', color: 'bg-red-500', icon: TrendingDown },
                    slow: { label: 'Slow', color: 'bg-orange-500', icon: TrendingDown },
                    normal: { label: 'Normal', color: 'bg-blue-500', icon: Target },
                    fast: { label: 'Fast', color: 'bg-green-500', icon: TrendingUp },
                    very_fast: { label: 'Very Fast', color: 'bg-emerald-500', icon: TrendingUp }
                  }[category];

                  const Icon = categoryInfo?.icon || Target;

                  return (
                    <div key={category} className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <div className={cn("w-3 h-3 rounded-full", categoryInfo?.color)} />
                        <h4 className="font-semibold">{categoryInfo?.label}</h4>
                        <Badge variant="outline">{questions.length} questions</Badge>
                      </div>
                      <div className="space-y-2">
                        {questions.map((q: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between text-sm p-2 bg-muted/50 rounded">
                            <span>Q{q.question_order + 1} - {q.subject}</span>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{formatTime(q.time_spent)}</span>
                              <Badge variant={q.is_correct ? 'default' : 'destructive'} className="text-xs">
                                {q.is_correct ? '✓' : '✗'}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Efficiency Analysis */}
        <TabsContent value="efficiency" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Subject Efficiency Analysis</CardTitle>
              <CardDescription>Time efficiency vs accuracy correlation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {efficiencyData?.subjects?.map((subject: any, idx: number) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold text-lg">{subject.subject}</h4>
                      <Badge
                        variant={subject.efficiency_score > 1 ? 'default' : 'secondary'}
                        className="text-sm"
                      >
                        Efficiency: {subject.efficiency_score.toFixed(2)}
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Time</p>
                        <p className="text-lg font-semibold">{formatTime(subject.total_time)}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Avg per Question</p>
                        <p className="text-lg font-semibold">{formatTime(Math.round(subject.avg_time_per_question))}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Accuracy</p>
                        <p className="text-lg font-semibold">{subject.accuracy.toFixed(0)}%</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Time per Correct</p>
                        <p className="text-lg font-semibold">{formatTime(Math.round(subject.time_per_correct))}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {efficiencyData?.most_efficient && (
                <div className="mt-6 p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    🎯 Most Efficient: {efficiencyData.most_efficient.subject}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                    Best balance of accuracy ({efficiencyData.most_efficient.accuracy.toFixed(0)}%) and time usage
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
