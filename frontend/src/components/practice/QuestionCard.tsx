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
}: QuestionCardProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const isAnswered = selectedAnswer !== null;
  const isCorrect = selectedAnswer === correctAnswer;

  const handleSelect = (optionId: string) => {
    if (isAnswered) return;
    setSelectedAnswer(optionId);
    onAnswer?.(optionId);
  };

  const getDifficultyColor = () => {
    switch (difficulty) {
      case "easy":
        return "bg-green-500/20 text-green-400";
      case "medium":
        return "bg-yellow-500/20 text-yellow-400";
      case "hard":
        return "bg-red-500/20 text-red-400";
    }
  };

  const getOptionStyle = (optionId: string) => {
    if (!isAnswered) {
      return selectedAnswer === optionId
        ? "border-primary bg-primary/10"
        : "border-border hover:border-primary/50 hover:bg-secondary/50";
    }
    
    if (optionId === correctAnswer) {
      return "border-green-500 bg-green-500/10";
    }
    
    if (optionId === selectedAnswer && !isCorrect) {
      return "border-red-500 bg-red-500/10";
    }
    
    return "border-border opacity-50";
  };

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">
            Question {questionNumber} of {totalQuestions}
          </span>
          <span className={cn("px-2 py-0.5 rounded text-xs font-medium", getDifficultyColor())}>
            {difficulty}
          </span>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="px-2 py-0.5 rounded bg-secondary">{subject}</span>
          <span className="px-2 py-0.5 rounded bg-secondary">{topic}</span>
        </div>
      </div>

      {/* Question */}
      <div className="p-6">
        <p className="text-lg text-foreground leading-relaxed mb-6">{question}</p>

        {/* Options */}
        <div className="space-y-3">
          {options.map((option, index) => (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id)}
              className={cn(
                "w-full text-left p-4 rounded-lg border transition-all duration-200 flex items-start gap-3",
                getOptionStyle(option.id)
              )}
              disabled={isAnswered}
            >
              <span className="w-6 h-6 rounded-full bg-secondary flex items-center justify-center text-sm font-medium shrink-0">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="text-foreground flex-1">{option.text}</span>
              {isAnswered && option.id === correctAnswer && (
                <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
              )}
              {isAnswered && option.id === selectedAnswer && !isCorrect && (
                <XCircle className="h-5 w-5 text-red-500 shrink-0" />
              )}
            </button>
          ))}
        </div>

        {/* Explanation */}
        {isAnswered && explanation && (
          <div className="mt-6">
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="flex items-center gap-2 text-primary hover:underline text-sm"
            >
              <Lightbulb className="h-4 w-4" />
              {showExplanation ? "Hide" : "Show"} Explanation
              {showExplanation ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
            {showExplanation && (
              <div className="mt-3 p-4 rounded-lg bg-secondary/30 text-muted-foreground text-sm leading-relaxed">
                {explanation}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      {isAnswered && (
        <div className="px-6 py-4 border-t border-border flex items-center justify-between bg-secondary/30">
          <div className={cn(
            "flex items-center gap-2 text-sm font-medium",
            isCorrect ? "text-green-500" : "text-red-500"
          )}>
            {isCorrect ? (
              <>
                <CheckCircle className="h-4 w-4" />
                Correct! Great job! 🎉
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4" />
                Incorrect. Learn from this!
              </>
            )}
          </div>
          <Button variant="default" size="sm">
            Next Question →
          </Button>
        </div>
      )}
    </div>
  );
}
