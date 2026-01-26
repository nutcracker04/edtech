import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  Target, 
  TrendingUp,
  AlertCircle,
  BarChart3,
  Loader2,
  Brain,
  Lightbulb
} from 'lucide-react';
import { testApi } from '@/api/test';
import { toast } from 'sonner';

interface TestResult {
  test_id: string;
  title: string;
  score: number;
  max_score: number;
  total_questions: number;
  correct_answers: number;
  time_taken: number;
  attempts: Array<{
    question_id: string;
    question_text: string;
    selected_answer: string | null;
    correct_answer: string;
    is_correct: boolean;
    time_spent: number;
    topic: string;
    subject: string;
  }>;
  topic_breakdown: Array<{
    topic: string;
    correct: number;
    total: number;
    accuracy: number;
  }>;
}

const TestResults = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<TestResult | null>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);

  useEffect(() => {
    if (!testId) return;
    loadResults();
  }, [testId]);

  const loadResults = async () => {
    try {
      const data = await testApi.getTestResults(testId!);
      setResult(data);
    } catch (error) {
      toast.error('Failed to load test results');
      navigate('/tests');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !result) {
    return (
      <MainLayout>
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </MainLayout>
    );
  }

  const percentage = Math.round((result.score / result.max_score) * 100);
  const accuracy = Math.round((result.correct_answers / result.total_questions) * 100);

  return (
    <MainLayout>
      <div className="container mx-auto py-6 space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Test Completed!</h1>
          <p className="text-muted-foreground">{result.title}</p>
        </div>

        {/* Score Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-2">
                <Target className="h-8 w-8 mx-auto text-primary" />
                <p className="text-sm text-muted-foreground">Score</p>
                <p className="text-3xl font-bold">{result.score}/{result.max_score}</p>
                <p className="text-xs text-muted-foreground">{percentage}%</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-2">
                <CheckCircle className="h-8 w-8 mx-auto text-green-500" />
                <p className="text-sm text-muted-foreground">Correct</p>
                <p className="text-3xl font-bold text-green-500">{result.correct_answers}</p>
                <p className="text-xs text-muted-foreground">{accuracy}% accuracy</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-2">
                <XCircle className="h-8 w-8 mx-auto text-red-500" />
                <p className="text-sm text-muted-foreground">Incorrect</p>
                <p className="text-3xl font-bold text-red-500">
                  {result.total_questions - result.correct_answers}
                </p>
                <p className="text-xs text-muted-foreground">
                  {Math.round(((result.total_questions - result.correct_answers) / result.total_questions) * 100)}%
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-2">
                <Clock className="h-8 w-8 mx-auto text-blue-500" />
                <p className="text-sm text-muted-foreground">Time Taken</p>
                <p className="text-3xl font-bold">{Math.floor(result.time_taken / 60)}m</p>
                <p className="text-xs text-muted-foreground">{result.time_taken % 60}s</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Indicator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Performance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Overall Score</span>
                <span className="text-sm text-muted-foreground">{percentage}%</span>
              </div>
              <Progress value={percentage} className="h-3" />
            </div>
            
            {percentage >= 80 && (
              <div className="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div>
                  <p className="font-medium text-green-500">Excellent Performance!</p>
                  <p className="text-sm text-muted-foreground">You've demonstrated strong understanding of the topics.</p>
                </div>
              </div>
            )}
            
            {percentage >= 60 && percentage < 80 && (
              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-500">Good Effort!</p>
                  <p className="text-sm text-muted-foreground">Review the topics where you struggled to improve further.</p>
                </div>
              </div>
            )}
            
            {percentage < 60 && (
              <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                <div>
                  <p className="font-medium text-red-500">Needs Improvement</p>
                  <p className="text-sm text-muted-foreground">Focus on practicing the weak areas identified below.</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Topic Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Topic-wise Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {result.topic_breakdown.map((topic) => (
                <div key={topic.topic} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{topic.topic}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        {topic.correct}/{topic.total}
                      </span>
                      <Badge variant={topic.accuracy >= 70 ? 'default' : 'destructive'}>
                        {Math.round(topic.accuracy)}%
                      </Badge>
                    </div>
                  </div>
                  <Progress value={topic.accuracy} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Question-by-Question Review */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Review</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {result.attempts.map((attempt, index) => (
                <div
                  key={attempt.question_id}
                  className={`p-4 rounded-lg border ${
                    attempt.is_correct
                      ? 'bg-green-500/5 border-green-500/20'
                      : 'bg-red-500/5 border-red-500/20'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {attempt.is_correct ? (
                      <CheckCircle className="h-5 w-5 text-green-500 mt-1" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-500 mt-1" />
                    )}
                    <div className="flex-1 space-y-2">
                      <div className="flex justify-between">
                        <p className="font-medium">Question {index + 1}</p>
                        <Badge variant="outline" className="text-xs">
                          {attempt.topic}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{attempt.question_text}</p>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">Your answer: </span>
                          <span className={attempt.is_correct ? 'text-green-500' : 'text-red-500'}>
                            {attempt.selected_answer || 'Not answered'}
                          </span>
                        </div>
                        {!attempt.is_correct && (
                          <div>
                            <span className="text-muted-foreground">Correct answer: </span>
                            <span className="text-green-500">{attempt.correct_answer}</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span>{attempt.time_spent}s</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={() => navigate('/analysis')} className="flex-1">
            View Detailed Analysis
          </Button>
          <Button onClick={() => navigate('/tests')} variant="outline" className="flex-1">
            Back to Tests
          </Button>
        </div>
      </div>
    </MainLayout>
  );
};

export default TestResults;
