import { useState } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle, XCircle, HelpCircle, Lightbulb, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Option {
  id: string;
  text: string;
}

interface QuestionCardProps {
  questionNumber: number;
  totalQuestions: number;
  question: string;
  options: Option[];
  correctAnswer?: string;
  explanation?: string;
  difficulty: "easy" | "medium" | "hard";
  topic: string;
  subject: string;
  onAnswer?: (answerId: string) => void;
}

export function QuestionCard({
  questionNumber,
  totalQuestions,
  question,
  options,
  correctAnswer,
  explanation,
  difficulty,
  topic,
  subject,
  onAnswer,
  selectedAnswer,
  showFeedback = false,
}: QuestionCardProps & { selectedAnswer?: string | null; showFeedback?: boolean }) {
  const [showExplanation, setShowExplanation] = useState(false);
  const isAnswered = selectedAnswer != null;
  const isCorrect = selectedAnswer === correctAnswer;

  const handleSelect = (optionId: string) => {
    if (showFeedback && isAnswered) return; // Prevent changing if feedback is shown
    onAnswer?.(optionId);
  };

  const getOptionStyle = (optionId: string) => {
    // 1. If not showing feedback (Test Mode), just highlight selected
    if (!showFeedback) {
      return selectedAnswer === optionId
        ? "border-primary bg-primary/10 ring-1 ring-primary"
        : "border-border hover:border-primary/50 hover:bg-secondary/50";
    }

    // 2. Feedback Mode (Practice/Result)
    if (!isAnswered) return "border-border";

    if (optionId === correctAnswer) {
      return "border-green-500 bg-green-500/10";
    }

    if (optionId === selectedAnswer && !isCorrect) {
      return "border-red-500 bg-red-500/10";
    }

    return "border-border opacity-50";
  };

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/30">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-muted-foreground">
            Question {questionNumber} of {totalQuestions}
          </span>
          {/* Metadata hidden as requested */}
        </div>
      </div>

      {/* Question - ADHD-friendly: Larger, more readable */}
      <div className="p-6">
        <p className="text-xl text-foreground leading-relaxed mb-6 font-medium">{question}</p>

        {/* Options - Large touch targets (52px+) */}
        <div className="space-y-3">
          {options.map((option, index) => (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id)}
              className={cn(
                "w-full text-left p-4 min-h-[52px] rounded-xl border-2 transition-all duration-200 flex items-start gap-3",
                "active:scale-[0.98]", // Instant feedback on tap
                getOptionStyle(option.id)
              )}
            >
              <span className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-base font-semibold shrink-0 transition-all",
                selectedAnswer === option.id
                  ? "bg-primary text-primary-foreground scale-110"
                  : "bg-secondary text-muted-foreground"
              )}>
                {String.fromCharCode(65 + index)}
              </span>
              <span className="text-foreground flex-1 text-base leading-relaxed pt-0.5">{option.text}</span>

              {showFeedback && isAnswered && option.id === correctAnswer && (
                <CheckCircle className="h-6 w-6 text-success shrink-0" />
              )}
              {showFeedback && isAnswered && option.id === selectedAnswer && !isCorrect && (
                <XCircle className="h-6 w-6 text-destructive shrink-0" />
              )}
            </button>
          ))}
        </div>

        {/* Explanation - Only show if feedback enabled */}
        {showFeedback && isAnswered && explanation && (
          <div className="mt-6 animate-in fade-in slide-in-from-top-2">
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="flex items-center gap-2 text-primary hover:underline text-sm font-medium"
            >
              <Lightbulb className="h-4 w-4" />
              {showExplanation ? "Hide" : "Show"} Explanation
              {showExplanation ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
            {showExplanation && (
              <div className="mt-3 p-4 rounded-lg bg-blue-50/50 dark:bg-blue-900/20 text-muted-foreground text-sm leading-relaxed border border-blue-100 dark:border-blue-900/50">
                {explanation}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer - Only show in feedback mode */}
      {showFeedback && isAnswered && (
        <div className={cn(
          "px-6 py-4 border-t border-border flex items-center justify-between",
          isCorrect ? "bg-green-50/50 dark:bg-green-900/10" : "bg-red-50/50 dark:bg-red-900/10"
        )}>
          <div className={cn(
            "flex items-center gap-2 text-sm font-medium",
            isCorrect ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
          )}>
            {isCorrect ? (
              <>
                <CheckCircle className="h-4 w-4" />
                Correct Answer
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4" />
                Incorrect Answer
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
