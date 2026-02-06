import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { QuestionRenderer } from '@/components/questions/QuestionRenderer';
import { TestTimer } from '@/components/tests/TestTimer';
import { TestNavigation } from '@/components/tests/TestNavigation';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { AlertTriangle, Loader2 } from 'lucide-react';
import { Question } from '@/types';
import { testApi } from '@/api/test';
import { toast } from 'sonner';

interface TestSession {
  testId: string;
  questions: Question[];
  duration: number;
}

const TestTaking = () => {
  const { testId } = useParams();
  const navigate = useNavigate();

  const storageKey = `test-session-${testId}`;

  // Load persisted state from sessionStorage
  const loadPersistedState = () => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        return {
          answers: parsed.answers || {},
          markedForReview: new Set<number>(parsed.markedForReview || []),
          timeSpent: parsed.timeSpent || {},
          currentQuestion: parsed.currentQuestion || 0,
        };
      }
    } catch (error) {
      console.error('Failed to load persisted state:', error);
    }
    return null;
  };

  const persistedState = loadPersistedState();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [session, setSession] = useState<TestSession | null>(null);

  const [currentQuestion, setCurrentQuestion] = useState(persistedState?.currentQuestion || 0);
  const [answers, setAnswers] = useState<Record<number, any>>(persistedState?.answers || {});
  const [markedForReview, setMarkedForReview] = useState<Set<number>>(persistedState?.markedForReview || new Set());

  // Time tracking
  const [timeSpent, setTimeSpent] = useState<Record<number, number>>(persistedState?.timeSpent || {});
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const [showSubmitDialog, setShowSubmitDialog] = useState(false);

  // Persist state to sessionStorage whenever it changes
  useEffect(() => {
    if (!session) return;

    const stateToSave = {
      answers,
      markedForReview: Array.from(markedForReview),
      timeSpent,
      currentQuestion,
    };

    try {
      sessionStorage.setItem(storageKey, JSON.stringify(stateToSave));
    } catch (error) {
      console.error('Failed to persist state:', error);
    }
  }, [answers, markedForReview, timeSpent, currentQuestion, session, storageKey]);

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

        // Only initialize time if not already persisted
        if (!persistedState?.timeSpent || Object.keys(persistedState.timeSpent).length === 0) {
          const initialTime: Record<number, number> = {};
          data.questions.forEach((_: any, idx: number) => {
            initialTime[idx] = 0;
          });
          setTimeSpent(initialTime);
        }
      } catch {
        toast.error('Failed to load test');
        navigate('/tests');
      } finally {
        setLoading(false);
      }
    };

    loadTest();
  }, [testId, navigate]);

  // Warn user before closing/refreshing during test
  useEffect(() => {
    if (!session) return;

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = 'Your test progress will be saved, but the timer will continue. Are you sure you want to leave?';
      return e.returnValue;
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [session]);

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

        // Clear persisted state after successful submission
        try {
          sessionStorage.removeItem(storageKey);
        } catch (error) {
          console.error('Failed to clear persisted state:', error);
        }

        toast.success('Test submitted successfully');
        navigate(`/tests/${session.testId}/results`);
      } catch (error) {
        console.error('Submission error:', error);
        toast.error('Failed to submit test');
        setSubmitting(false);
      }
    },
    [answers, timeSpent, markedForReview, session, submitting, navigate, storageKey]
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
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </MainLayout>
    );
  }

  const currentQData = session.questions[currentQuestion];

  return (
    <MainLayout>
      <div className="container mx-auto py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* MAIN CONTENT */}
          <div className="lg:col-span-3 space-y-6">
            <TestTimer
              duration={session.duration}
              onTimeUp={handleTimeUp}
              testId={session.testId}
            />

            <QuestionRenderer
              question={currentQData}
              questionNumber={currentQuestion + 1}
              totalQuestions={session.questions.length}
              onAnswer={handleAnswer}
              currentAnswer={answers[currentQuestion]}
              showFeedback={false}
            />

            {/* hidden per-question time */}
            <div className="hidden">
              Time spent: {timeSpent[currentQuestion]}s
            </div>

            {/* QUESTION ACTIONS */}
            <div className="flex gap-3">
              <Button
                onClick={handleMarkForReview}
                variant={
                  markedForReview.has(currentQuestion)
                    ? 'default'
                    : 'outline'
                }
                className="flex-1"
              >
                {markedForReview.has(currentQuestion)
                  ? '✓ Marked'
                  : 'Mark for Review'}
              </Button>
            </div>

            {/* NAVIGATION */}
            <div className="flex gap-3">
              <Button
                onClick={() =>
                  setCurrentQuestion(q => Math.max(0, q - 1))
                }
                disabled={currentQuestion === 0}
                variant="outline"
                className="flex-1"
              >
                ← Previous
              </Button>
              <Button
                onClick={() =>
                  setCurrentQuestion(q =>
                    Math.min(session.questions.length - 1, q + 1)
                  )
                }
                disabled={
                  currentQuestion === session.questions.length - 1
                }
                className="flex-1"
              >
                Next →
              </Button>
            </div>

            {/* SUBMIT */}
            <Button
              onClick={handleSubmitClick}
              disabled={submitting}
              size="lg"
              className="w-full bg-green-600 hover:bg-green-700"
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  Submit Test
                  {answeredQuestions.size <
                    session.questions.length && (
                      <span className="ml-2 text-xs opacity-75">
                        ({answeredQuestions.size}/
                        {session.questions.length} answered)
                      </span>
                    )}
                </>
              )}
            </Button>
          </div>

          {/* SIDEBAR */}
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

      {/* INCOMPLETE SUBMISSION DIALOG */}
      <Dialog
        open={showSubmitDialog}
        onOpenChange={setShowSubmitDialog}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Incomplete Test
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <p className="text-muted-foreground">
              You have not answered{' '}
              {session.questions.length -
                answeredQuestions.size}{' '}
              question(s).
            </p>

            <div className="flex gap-3">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => setShowSubmitDialog(false)}
              >
                Continue Test
              </Button>
              <Button
                className="flex-1"
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
