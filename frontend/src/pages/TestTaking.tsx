import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { QuestionRenderer } from '@/components/questions/QuestionRenderer';
import { TestTimer } from '@/components/tests/TestTimer';
import { TestNavigation } from '@/components/tests/TestNavigation';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { Question } from '@/types';
import { questionBankService } from '@/services/mockData';

interface TestSession {
  testId: string;
  questions: Question[];
  duration: number;
}

const TestTaking = () => {
  const { testId } = useParams();
  const navigate = useNavigate();

  // Mock test session
  const [session] = useState<TestSession>({
    testId: testId || 'test-1',
    questions: questionBankService.getRandomQuestions(25),
    duration: 60,
  });

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(new Set());
  const [showSubmitDialog, setShowSubmitDialog] = useState(false);
  const [testCompleted, setTestCompleted] = useState(false);
  const [score, setScore] = useState(0);

  const question = session.questions[currentQuestion];
  const answeredQuestions = new Set(Object.keys(answers).map(k => parseInt(k)));

  const handleAnswer = (answer: any) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion]: answer,
    }));
  };

  const handleMarkForReview = () => {
    const newMarked = new Set(markedForReview);
    if (newMarked.has(currentQuestion)) {
      newMarked.delete(currentQuestion);
    } else {
      newMarked.add(currentQuestion);
    }
    setMarkedForReview(newMarked);
  };

  const handleNavigate = (index: number) => {
    setCurrentQuestion(index);
  };

  const handleTimeUp = () => {
    submitTest();
  };

  const submitTest = () => {
    // Calculate score
    let correct = 0;
    Object.entries(answers).forEach(([qIdx, answer]) => {
      if (session.questions[parseInt(qIdx)].correctAnswer === answer) {
        correct++;
      }
    });

    const finalScore = Math.round((correct / session.questions.length) * 100);
    setScore(finalScore);
    setTestCompleted(true);
  };

  const handleSubmitClick = () => {
    if (answeredQuestions.size < session.questions.length) {
      setShowSubmitDialog(true);
    } else {
      submitTest();
    }
  };

  if (testCompleted) {
    return (
      <MainLayout>
        <div className="p-8 max-w-2xl mx-auto space-y-8">
          {/* Results Header */}
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <div className="relative w-32 h-32">
                <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                  <circle
                    cx="60"
                    cy="60"
                    r="54"
                    fill="none"
                    stroke="hsl(var(--secondary))"
                    strokeWidth="8"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="54"
                    fill="none"
                    stroke={score >= 75 ? '#22c55e' : score >= 50 ? '#eab308' : '#ef4444'}
                    strokeWidth="8"
                    strokeDasharray={`${(score / 100) * (54 * 2 * Math.PI)} ${54 * 2 * Math.PI}`}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-foreground">{score}%</div>
                    <div className="text-xs text-muted-foreground">Score</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h1 className="text-3xl font-bold text-foreground">Test Completed!</h1>
              <p className="text-muted-foreground mt-2">
                {score >= 75 && '🎉 Excellent performance!'}
                {score >= 50 && score < 75 && '✅ Good effort! Room for improvement.'}
                {score < 50 && '📚 Keep practicing, you\'ll improve soon!'}
              </p>
            </div>
          </div>

          {/* Score Breakdown */}
          <div className="bg-card border border-border rounded-xl p-6 space-y-4">
            <h2 className="text-lg font-semibold text-foreground">Performance Summary</h2>

            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 rounded-lg bg-secondary/30">
                <div className="text-2xl font-bold text-primary">
                  {Object.values(answers).filter((ans, idx) =>
                    session.questions[idx]?.correctAnswer === ans
                  ).length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">Correct</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-secondary/30">
                <div className="text-2xl font-bold text-red-400">
                  {Object.values(answers).filter((ans, idx) =>
                    session.questions[idx]?.correctAnswer !== ans
                  ).length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">Incorrect</div>
              </div>
              <div className="text-center p-4 rounded-lg bg-secondary/30">
                <div className="text-2xl font-bold text-yellow-400">
                  {session.questions.length - Object.keys(answers).length}
                </div>
                <div className="text-xs text-muted-foreground mt-1">Unanswered</div>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-primary/10 border border-primary/20 rounded-xl p-6 space-y-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-primary mt-0.5 shrink-0" />
              <div>
                <p className="font-semibold text-foreground">Next Steps</p>
                <ul className="text-sm text-muted-foreground space-y-1 mt-2">
                  <li>• Review your weak areas in the Analysis section</li>
                  <li>• Take focused practice tests on struggling topics</li>
                  <li>• Attempt another test in 2-3 days to track progress</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              onClick={() => navigate('/analysis')}
              variant="outline"
              className="flex-1"
            >
              View Analysis
            </Button>
            <Button
              onClick={() => navigate('/practice')}
              className="flex-1"
            >
              Practice More
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-8 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Question Area */}
          <div className="lg:col-span-3 space-y-6">
            {/* Timer */}
            <TestTimer
              duration={session.duration}
              onTimeUp={handleTimeUp}
            />

            {/* Question Renderer - Supports all answer types */}
            <QuestionRenderer
              question={question}
              questionNumber={currentQuestion + 1}
              totalQuestions={session.questions.length}
              onAnswer={handleAnswer}
              currentAnswer={answers[currentQuestion]}
            />

            {/* Question Actions */}
            <div className="flex gap-3">
              <Button
                onClick={handleMarkForReview}
                variant={markedForReview.has(currentQuestion) ? 'default' : 'outline'}
                className="flex-1"
              >
                {markedForReview.has(currentQuestion) ? '✓ Marked' : 'Mark for Review'}
              </Button>
            </div>

            {/* Navigation Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
                disabled={currentQuestion === 0}
                variant="outline"
                className="flex-1"
              >
                ← Previous
              </Button>
              <Button
                onClick={() => setCurrentQuestion(prev => Math.min(session.questions.length - 1, prev + 1))}
                disabled={currentQuestion === session.questions.length - 1}
                className="flex-1"
              >
                Next →
              </Button>
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleSubmitClick}
              size="lg"
              className="w-full bg-green-600 hover:bg-green-700"
            >
              Submit Test
              {answeredQuestions.size < session.questions.length && (
                <span className="ml-2 text-xs opacity-75">
                  ({answeredQuestions.size}/{session.questions.length} answered)
                </span>
              )}
            </Button>
          </div>

          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <TestNavigation
              totalQuestions={session.questions.length}
              currentQuestion={currentQuestion}
              onNavigate={handleNavigate}
              answeredQuestions={answeredQuestions}
              markedForReview={markedForReview}
            />
          </div>
        </div>
      </div>

      {/* Incomplete Submission Dialog */}
      <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Incomplete Test
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <p className="text-muted-foreground">
              You have not answered {session.questions.length - answeredQuestions.size} question(s).
            </p>
            <p className="text-sm text-muted-foreground">
              Do you want to submit anyway? Unanswered questions will be marked as incorrect.
            </p>

            <div className="flex gap-3">
              <Button
                onClick={() => setShowSubmitDialog(false)}
                variant="outline"
                className="flex-1"
              >
                Continue Test
              </Button>
              <Button
                onClick={() => {
                  setShowSubmitDialog(false);
                  submitTest();
                }}
                className="flex-1"
              >
                Submit Anyway
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </MainLayout>
  );
};

export default TestTaking;
