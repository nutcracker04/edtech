import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { QuestionCard } from "@/components/practice/QuestionCard";
import { PracticeModeSelector, PracticeMode } from "@/components/practice/PracticeModeSelector";
import { SubjectSelector, TopicSelector } from "@/components/practice/TopicSelector";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Clock, Target, Brain, ChevronLeft, ChevronRight } from "lucide-react";
import { Subject } from "@/types";
import { questionBankService } from "@/services/mockData";
import { usePerformance } from "@/hooks/usePerformance";

const Practice = () => {
  const [mode, setMode] = useState<PracticeMode | null>(null);
  const [subject, setSubject] = useState<Subject | null>(null);
  const [topic, setTopic] = useState<string | null>(null);
  const [sessionStarted, setSessionStarted] = useState(false);
  
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [correctAnswers, setCorrectAnswers] = useState(0);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [sessionQuestions, setSessionQuestions] = useState<any[]>([]);
  
  const { recordAttempts } = usePerformance();

  const startPracticeSession = () => {
    let questions: any[] = [];

    if (mode === 'adaptive') {
      // Get random mix of questions
      questions = questionBankService.getRandomQuestions(15);
    } else if (mode === 'topic-focus' && subject && topic) {
      // Get questions from specific topic
      questions = questionBankService.getQuestionsFiltered({
        subject,
        topic,
        limit: 10,
      });
    } else if (mode === 'subject-focus' && subject) {
      // Get all questions from subject
      questions = questionBankService.getQuestionsBySubject(subject, 15);
    }

    if (questions.length === 0) {
      questions = questionBankService.getRandomQuestions(10);
    }

    setSessionQuestions(questions);
    setSessionStarted(true);
    setCurrentQuestion(0);
    setCorrectAnswers(0);
    setAnsweredCount(0);
  };

  const handleAnswer = (answerId: string) => {
    setAnsweredCount((prev) => prev + 1);
    if (answerId === sessionQuestions[currentQuestion].correctAnswer) {
      setCorrectAnswers((prev) => prev + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestion < sessionQuestions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion((prev) => prev - 1);
    }
  };

  const handleEndSession = () => {
    setSessionStarted(false);
    setMode(null);
    setSubject(null);
    setTopic(null);
  };

  const progress = sessionQuestions.length > 0 ? ((answeredCount) / sessionQuestions.length) * 100 : 0;

  if (!sessionStarted) {
    return (
      <MainLayout>
        <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto space-y-6 sm:space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Practice Mode</h1>
            <p className="text-sm sm:text-base text-muted-foreground mt-1">
              Choose how you want to practice and improve your skills
            </p>
          </div>

          {/* Mode Selection */}
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Select Practice Mode</h2>
            <PracticeModeSelector
              selectedMode={mode}
              onModeSelect={setMode}
            />
          </div>

          {/* Subject Selection - Show for topic/subject focus modes */}
          {(mode === 'topic-focus' || mode === 'subject-focus') && (
            <div>
              <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Select Subject</h2>
              <SubjectSelector
                selectedSubject={subject}
                onSubjectSelect={setSubject}
              />
            </div>
          )}

          {/* Topic Selection - Show only for topic-focus mode */}
          {mode === 'topic-focus' && subject && (
            <div>
              <h2 className="text-base sm:text-lg font-semibold text-foreground mb-3 sm:mb-4">Select Topic</h2>
              <TopicSelector
                subject={subject}
                selectedTopic={topic}
                onTopicSelect={setTopic}
              />
            </div>
          )}

          {/* Start Button */}
          <div className="flex gap-3">
            <Button
              onClick={startPracticeSession}
              disabled={!mode || (mode === 'topic-focus' && (!subject || !topic)) || (mode === 'subject-focus' && !subject)}
              size="lg"
              className="flex-1"
            >
              Start Practice Session
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  // Practice session view
  return (
    <MainLayout>
      <div className="p-8 max-w-4xl mx-auto space-y-6">
        {/* Header Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-card border border-border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-secondary">
              <Clock className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Time Elapsed</p>
              <p className="text-lg font-semibold text-foreground">12:34</p>
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-secondary">
              <Target className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Accuracy</p>
              <p className="text-lg font-semibold text-foreground">
                {answeredCount > 0 ? Math.round((correctAnswers / answeredCount) * 100) : 0}%
              </p>
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-secondary">
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Difficulty</p>
              <p className="text-lg font-semibold text-foreground capitalize">
                {sessionQuestions[currentQuestion]?.difficulty || 'medium'}
              </p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Progress</span>
            <span className="text-sm text-foreground">{answeredCount} / {sessionQuestions.length}</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Question Card */}
        {sessionQuestions.length > 0 && (
          <QuestionCard
            questionNumber={currentQuestion + 1}
            totalQuestions={sessionQuestions.length}
            {...sessionQuestions[currentQuestion]}
            onAnswer={handleAnswer}
          />
        )}

        {/* Navigation Buttons */}
        <div className="flex gap-3 justify-between">
          <Button
            onClick={handlePreviousQuestion}
            disabled={currentQuestion === 0}
            variant="outline"
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <Button
            onClick={handleEndSession}
            variant="outline"
            className="text-destructive"
          >
            End Session
          </Button>

          <Button
            onClick={handleNextQuestion}
            disabled={currentQuestion === sessionQuestions.length - 1}
          >
            Next
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </MainLayout>
  );
};

export default Practice;
