import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, Target, TrendingUp, Award } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface AnalysisResult {
  test_id: string;
  total_questions: number;
  correct_answers: number;
  incorrect_answers: number;
  unanswered: number;
  score: number;
  subject_breakdown?: {
    [subject: string]: {
      correct: number;
      total: number;
      percentage: number;
    };
  };
}

interface UploadAnalysisProps {
  result: AnalysisResult;
  onNewUpload: () => void;
}

export function UploadAnalysis({ result, onNewUpload }: UploadAnalysisProps) {
  const navigate = useNavigate();

  const accuracy = Math.round((result.correct_answers / result.total_questions) * 100);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceMessage = (score: number) => {
    if (score >= 90) return 'Outstanding performance!';
    if (score >= 80) return 'Excellent work!';
    if (score >= 70) return 'Good job!';
    if (score >= 60) return 'Keep practicing!';
    return 'Need more practice';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
          <Award className="h-8 w-8 text-green-600" />
        </div>
        <h2 className="text-3xl font-bold">Test Analysis Complete!</h2>
        <p className="text-muted-foreground">
          Your test has been analyzed and saved to your dashboard
        </p>
      </div>

      {/* Score Card */}
      <Card className="border-2">
        <CardHeader className="text-center pb-4">
          <CardTitle className="text-6xl font-bold">
            <span className={getScoreColor(result.score)}>{result.score}%</span>
          </CardTitle>
          <CardDescription className="text-lg">
            {getPerformanceMessage(result.score)}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <CheckCircle2 className="h-6 w-6 text-green-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-600">{result.correct_answers}</p>
              <p className="text-sm text-muted-foreground">Correct</p>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <XCircle className="h-6 w-6 text-red-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-red-600">{result.incorrect_answers}</p>
              <p className="text-sm text-muted-foreground">Incorrect</p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <Target className="h-6 w-6 text-gray-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-gray-600">{result.unanswered}</p>
              <p className="text-sm text-muted-foreground">Unanswered</p>
            </div>
          </div>

          <div className="mt-6">
            <div className="flex justify-between text-sm mb-2">
              <span>Overall Accuracy</span>
              <span className="font-medium">{accuracy}%</span>
            </div>
            <Progress value={accuracy} className="h-3" />
          </div>
        </CardContent>
      </Card>

      {/* Subject Breakdown */}
      {result.subject_breakdown && Object.keys(result.subject_breakdown).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Subject-wise Performance</CardTitle>
            <CardDescription>Detailed breakdown by subject</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(result.subject_breakdown).map(([subject, data]) => (
              <div key={subject} className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="capitalize">{subject}</Badge>
                    <span className="text-sm text-muted-foreground">
                      {data.correct} / {data.total} correct
                    </span>
                  </div>
                  <span className={`font-medium ${getScoreColor(data.percentage)}`}>
                    {data.percentage.toFixed(1)}%
                  </span>
                </div>
                <Progress value={data.percentage} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Next Steps
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Review incorrect answers in the Analysis section</li>
            <li>Practice weak topics to improve your score</li>
            <li>Take more tests to track your progress</li>
            <li>Check your performance dashboard for detailed insights</li>
          </ul>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => navigate('/analysis')}
        >
          View Detailed Analysis
        </Button>
        <Button
          variant="outline"
          className="flex-1"
          onClick={() => navigate(`/test/${result.test_id}`)}
        >
          Review Answers
        </Button>
        <Button
          className="flex-1"
          onClick={onNewUpload}
        >
          Upload Another Test
        </Button>
      </div>
    </div>
  );
}
