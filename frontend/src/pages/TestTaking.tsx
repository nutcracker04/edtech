import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { QuestionRenderer } from '@/components/questions/QuestionRenderer';
import { TestTimer } from '@/components/tests/TestTimer';
import { TestNavigation } from '@/components/tests/TestNavigation';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AlertTriangle, Loader2, Eye, EyeOff, Save, CheckCircle2 } from 'lucide-react';
import { Question } from '@/types';
import { testApi } from '@/api/test';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface TestSession {
  testId: string;
  questions: Question[];
  duration: number;
}

const TestTaking = () => {
  const { testId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [session, setSession] = useState<TestSession | null>(null);

  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(new Set());

  // ADHD-friendly: Timer visibility toggle (hidden by default)
  const [showTimer, setShowTimer] = useState(false);

  // Auto-save indicator
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Time tracking
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>({});
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  const [showSubmitDialog, setShowSubmitDialog] = useState(false);

  /* ---------------------------------- LOAD TEST ---------------------------------- */

  useEffect(() => {
    if (!testId) return;

    const loadTest = async () => {
      try {
        const data = await testApi.getTest(testId);

        setSession({
          testId: data.id,
          questions: data.questions,
          duration: data.duration,
        });

        const initialTime: Record<number, number> = {};
        data.questions.forEach((_: any, idx: number) => {
          initialTime[idx] = 0;
        });
        setTimeSpent(initialTime);
      } catch {
        toast.error('Failed to load test');
        navigate('/tests');
      } finally {
        setLoading(false);
      }
    };

    loadTest();
  }, [testId, navigate]);

  /* -------------------------- TIME PER QUESTION TRACKER -------------------------- */

  useEffect(() => {
    if (!session) return;

    timerRef.current = setInterval(() => {
      setTimeSpent(prev => ({
        ...prev,
        [currentQuestion]: (prev[currentQuestion] || 0) + 1,
      }));
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [currentQuestion, session]);

  /* -------------------------- AUTO-SAVE (ADHD-FRIENDLY) -------------------------- */

  useEffect(() => {
    // Auto-save every 30 seconds
    autoSaveRef.current = setInterval(() => {
      if (Object.keys(answers).length > 0) {
        setIsSaving(true);
        // Simulate save (in real implementation, call API)
        setTimeout(() => {
          setLastSaved(new Date());
          setIsSaving(false);
        }, 500);
      }
    }, 30000);

    return () => {
      if (autoSaveRef.current) clearInterval(autoSaveRef.current);
    };
  }, [answers]);

  /* ---------------------------------- HANDLERS ---------------------------------- */

  const handleAnswer = (answer: any) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion]: answer,
    }));
  };

  const handleMarkForReview = () => {
    setMarkedForReview(prev => {
      const next = new Set(prev);
      next.has(currentQuestion)
        ? next.delete(currentQuestion)
        : next.add(currentQuestion);
      return next;
    });
  };

  const handleNavigate = (index: number) => {
    setCurrentQuestion(index);
  };

  const answeredQuestions = new Set(
    Object.keys(answers).map(k => Number(k))
  );

  const unansweredCount = session ? session.questions.length - answeredQuestions.size : 0;

  /* -------------------------------- SUBMISSION -------------------------------- */

  const submitTest = useCallback(
    async (auto = false) => {
      if (!session || submitting) return;

      setSubmitting(true);

      try {
        const attempts = session.questions.map((q, index) => ({
          question_id: q.id,
          selected_answer: answers[index] || null,
          time_spent: timeSpent[index] || 0,
          marked_for_review: markedForReview.has(index),
        }));

        await testApi.submitTest({
          test_id: session.testId,
          attempts,
        });

        toast.success('Test submitted successfully! 🎉');
        navigate(`/tests/${session.testId}/results`);
      } catch (error) {
        console.error('Submission error:', error);
        toast.error('Failed to submit test');
        setSubmitting(false);
      }
    },
    [answers, timeSpent, markedForReview, session, submitting, navigate]
  );

  const handleSubmitClick = () => {
    if (!session) return;

    if (answeredQuestions.size < session.questions.length) {
      setShowSubmitDialog(true);
    } else {
      submitTest(false);
    }
  };

  const handleTimeUp = useCallback(() => {
    submitTest(true);
  }, [submitTest]);

  /* ---------------------------------- RENDER ---------------------------------- */

  if (loading || !session) {
    return (
      <MainLayout>
        <div className="flex flex-col items-center justify-center py-20 gap-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-muted-foreground">Loading your test...</p>
        </div>
      </MainLayout>
    );
  }

  const currentQData = session.questions[currentQuestion];
  const progressPercent = ((currentQuestion + 1) / session.questions.length) * 100;

  return (
    <MainLayout>
      {/* ADHD-Friendly: Calm background during tests */}
      <div className="min-h-screen bg-muted/30">
        {/* ============ TOP BAR - Minimal, non-distracting ============ */}
        <div className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b">
          <div className="container mx-auto px-4 py-3">
            <div className="flex items-center justify-between gap-4">
              {/* Left: Question Progress */}
              <div className="flex items-center gap-3">
                <span className="text-lg font-semibold text-foreground">
                  Q {currentQuestion + 1}
                  <span className="text-muted-foreground font-normal">/{session.questions.length}</span>
                </span>

                {/* Progress dots - Color coded */}
                <div className="hidden sm:flex items-center gap-1">
                  {session.questions.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setCurrentQuestion(idx)}
                      className={cn(
                        "w-2.5 h-2.5 rounded-full transition-all",
                        idx === currentQuestion && "ring-2 ring-primary ring-offset-2",
                        answeredQuestions.has(idx)
                          ? "bg-success"
                          : markedForReview.has(idx)
                            ? "bg-warning"
                            : "bg-muted-foreground/30"
                      )}
                      title={
                        answeredQuestions.has(idx)
                          ? "Answered"
                          : markedForReview.has(idx)
                            ? "Marked for review"
                            : "Not answered"
                      }
                    />
                  ))}
                </div>
              </div>

              {/* Center: Auto-save indicator */}
              <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                {isSaving ? (
                  <>
                    <Save className="h-3.5 w-3.5 animate-pulse" />
                    <span>Saving...</span>
                  </>
                ) : lastSaved ? (
                  <>
                    <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                    <span>Auto-saved</span>
                  </>
                ) : null}
              </div>

              {/* Right: Timer (Optional - ADHD friendly) */}
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTimer(!showTimer)}
                  className="text-muted-foreground"
                >
                  {showTimer ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  <span className="ml-1 hidden sm:inline">
                    {showTimer ? 'Hide Timer' : 'Show Timer'}
                  </span>
                </Button>

                {showTimer && (
                  <TestTimer
                    duration={session.duration}
                    onTimeUp={handleTimeUp}
                  />
                )}
              </div>
            </div>

            {/* Progress bar */}
            <Progress value={progressPercent} className="h-1 mt-3" />
          </div>
        </div>

        {/* ============ MAIN CONTENT - Focus Area ============ */}
        <div className="container mx-auto px-4 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* MAIN QUESTION AREA - 3/4 width on desktop */}
            <div className="lg:col-span-3 space-y-6">
              {/* Question Card - Large, readable */}
              <QuestionRenderer
                question={currentQData}
                questionNumber={currentQuestion + 1}
                totalQuestions={session.questions.length}
                onAnswer={handleAnswer}
                currentAnswer={answers[currentQuestion]}
                showFeedback={false}
              />

              {/* ============ ACTION BUTTONS - Large touch targets (48px+) ============ */}
              <div className="flex flex-col sm:flex-row gap-3">
                {/* Mark for Review */}
                <Button
                  onClick={handleMarkForReview}
                  variant={markedForReview.has(currentQuestion) ? 'secondary' : 'outline'}
                  className="touch-target text-base"
                >
                  {markedForReview.has(currentQuestion) ? '✓ Marked' : '🔖 Mark for Review'}
                </Button>

                {/* Navigation */}
                <div className="flex gap-3 flex-1">
                  <Button
                    onClick={() => setCurrentQuestion(q => Math.max(0, q - 1))}
                    disabled={currentQuestion === 0}
                    variant="outline"
                    className="flex-1 touch-target text-base"
                  >
                    ← Previous
                  </Button>
                  <Button
                    onClick={() => setCurrentQuestion(q => Math.min(session.questions.length - 1, q + 1))}
                    disabled={currentQuestion === session.questions.length - 1}
                    className="flex-1 touch-target text-base"
                  >
                    Next →
                  </Button>
                </div>
              </div>

              {/* Submit Button with Reminder */}
              <div className="space-y-2">
                {unansweredCount > 0 && (
                  <p className="text-sm text-warning text-center">
                    ⚠️ {unansweredCount} question{unansweredCount > 1 ? 's' : ''} left unanswered
                  </p>
                )}
                <Button
                  onClick={handleSubmitClick}
                  disabled={submitting}
                  size="lg"
                  className="w-full touch-target text-lg bg-success hover:bg-success/90"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      Submit Test
                      {unansweredCount > 0 && (
                        <span className="ml-2 text-sm opacity-80">
                          ({answeredQuestions.size}/{session.questions.length})
                        </span>
                      )}
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* SIDEBAR - Question Navigation (hidden on mobile) */}
            <div className="hidden lg:block">
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
      </div>

      {/* ============ INCOMPLETE SUBMISSION DIALOG ============ */}
      <Dialog open={showSubmitDialog} onOpenChange={setShowSubmitDialog}>
        <DialogContent className="rounded-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <AlertTriangle className="h-5 w-5 text-warning" />
              You have unanswered questions
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <p className="text-muted-foreground">
              {unansweredCount} question{unansweredCount > 1 ? 's are' : ' is'} still unanswered.
              Are you sure you want to submit?
            </p>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1 touch-target"
                onClick={() => setShowSubmitDialog(false)}
              >
                Go Back
              </Button>
              <Button
                className="flex-1 touch-target"
                onClick={() => {
                  setShowSubmitDialog(false);
                  submitTest(false);
                }}
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
