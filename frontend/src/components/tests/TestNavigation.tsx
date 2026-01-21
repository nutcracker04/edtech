import { cn } from '@/lib/utils';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle, Circle, AlertCircle } from 'lucide-react';

interface TestNavigationProps {
  totalQuestions: number;
  currentQuestion: number;
  onNavigate: (index: number) => void;
  answeredQuestions: Set<number>;
  markedForReview: Set<number>;
}

export function TestNavigation({
  totalQuestions,
  currentQuestion,
  onNavigate,
  answeredQuestions,
  markedForReview,
}: TestNavigationProps) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden h-[500px] flex flex-col">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="font-semibold text-foreground">Questions</h3>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 grid grid-cols-6 gap-2">
          {Array.from({ length: totalQuestions }).map((_, index) => {
            const isAnswered = answeredQuestions.has(index);
            const isMarked = markedForReview.has(index);
            const isCurrent = index === currentQuestion;

            return (
              <button
                key={index}
                onClick={() => onNavigate(index)}
                className={cn(
                  'w-full aspect-square rounded-lg transition-all font-medium text-sm flex items-center justify-center relative',
                  isCurrent
                    ? 'ring-2 ring-primary'
                    : '',
                  isAnswered
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-secondary border border-border hover:border-primary/50'
                )}
                title={`Question ${index + 1}${isMarked ? ' (Marked for review)' : ''}`}
              >
                {index + 1}
                {isMarked && (
                  <AlertCircle className="absolute top-0.5 right-0.5 h-3 w-3 text-yellow-400" />
                )}
              </button>
            );
          })}
        </div>
      </ScrollArea>

      {/* Legend */}
      <div className="border-t border-border p-4 space-y-2 text-xs">
        <div className="flex items-center gap-2">
          <Circle className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">Not Answered</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-green-400" />
          <span className="text-muted-foreground">Answered</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-yellow-400" />
          <span className="text-muted-foreground">Marked for Review</span>
        </div>
      </div>
    </div>
  );
}
