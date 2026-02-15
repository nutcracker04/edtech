import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { testApi } from '@/api/test';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TestTimeAnalysis } from '@/components/analysis/TestTimeAnalysis';
import { ArrowLeft, Trophy, Clock, Target, TrendingUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const TestResults = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!testId) return;
    loadResults();
  }, [testId]);

  const loadResults = async () => {
    try {
      const data = await testApi.getTestResults(testId!);
      setResults(data);
    } catch (error) {
      console.error('Failed to load results:', error);
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
      <MainLayout>
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
        </div>
      </MainLayout>
    );
  }

  if (!results) {
    return (
      <MainLayout>
        <div className="text-center py-20">
          <p className="text-muted-foreground">Failed to load test results</p>
          <Button onClick={() => navigate('/tests')} className="mt-4">
            Back to Tests
          </Button>
        </div>
      </MainLayout>
    );
  }

  const scorePercentage = (results.score / results.max_score) * 100;

  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/tests')}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Tests
          </Button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold">{results.title}</h1>
              <p className="text-muted-foreground mt-1">Test Results & Analysis</p>
            </div>
            <Badge
              variant={scorePercentage >= 70 ? 'default' : scorePercentage >= 50 ? 'secondary' : 'destructive'}
              className="text-lg px-4 py-2"
            >
              {scorePercentage.toFixed(0)}%
            </Badge>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Trophy className="h-4 w-4" />
                Score
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {results.score} / {results.max_score}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {scorePercentage.toFixed(1)}%
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Target className="h-4 w-4" />
                Accuracy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {results.correct_answers} / {results.total_questions}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {((results.correct_answers / results.total_questions) * 100).toFixed(1)}% correct
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Time Taken
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{formatTime(results.time_taken)}</p>
              <p className="text-sm text-muted-foreground mt-1">
                {formatTime(Math.round(results.time_taken / results.total_questions))} avg
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Performance
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">
                {scorePercentage >= 80 ? 'Excellent' : scorePercentage >= 60 ? 'Good' : 'Needs Work'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {results.topic_breakdown?.length || 0} topics covered
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Analysis Tabs */}
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="time-analysis">Time Analysis</TabsTrigger>
            <TabsTrigger value="questions">Questions</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Topic Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.topic_breakdown?.map((topic: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">{topic.topic}</p>
                        <p className="text-sm text-muted-foreground">
                          {topic.correct} / {topic.total} correct
                        </p>
                      </div>
                      <Badge variant={topic.accuracy >= 70 ? 'default' : 'destructive'}>
                        {topic.accuracy.toFixed(0)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="time-analysis">
            <TestTimeAnalysis testId={testId!} />
          </TabsContent>

          <TabsContent value="questions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Question-by-Question Review</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.attempts?.map((attempt: any, idx: number) => (
                    <div
                      key={idx}
                      className={`p-4 border rounded-lg ${
                        attempt.is_correct
                          ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
                          : 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">Question {idx + 1}</span>
                          <Badge variant="outline" className="text-xs">
                            {attempt.subject}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {attempt.topic}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-muted-foreground">
                            {formatTime(attempt.time_spent)}
                          </span>
                          <Badge variant={attempt.is_correct ? 'default' : 'destructive'}>
                            {attempt.is_correct ? 'Correct' : 'Incorrect'}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm mb-2">{attempt.question_text}</p>
                      <div className="text-sm space-y-1">
                        <p>
                          <span className="text-muted-foreground">Your answer:</span>{' '}
                          <span className={attempt.is_correct ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                            {attempt.selected_answer || 'Not answered'}
                          </span>
                        </p>
                        {!attempt.is_correct && (
                          <p>
                            <span className="text-muted-foreground">Correct answer:</span>{' '}
                            <span className="text-green-600 dark:text-green-400">
                              {attempt.correct_answer}
                            </span>
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
};

export default TestResults;
