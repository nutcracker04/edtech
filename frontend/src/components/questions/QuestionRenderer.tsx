import { Question, AnswerType } from '@/types';
import { QuestionCard } from '@/components/practice/QuestionCard';
import { IntegerInput } from './IntegerInput';
import { MultiSelect } from './MultiSelect';
import { MatchFollowing } from './MatchFollowing';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface QuestionRendererProps {
  question: Question;
  questionNumber: number;
  totalQuestions: number;
  onAnswer: (answer: any) => void;
  currentAnswer?: any;
}

export function QuestionRenderer({
  question,
  questionNumber,
  totalQuestions,
  onAnswer,
  currentAnswer,
}: QuestionRendererProps) {
  const answerType = question.answerType || 'single_choice';

  const getDifficultyColor = () => {
    switch (question.difficulty) {
      case 'easy':
        return 'bg-green-500/20 text-green-400';
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'hard':
        return 'bg-red-500/20 text-red-400';
    }
  };

  // For single_choice, use the existing QuestionCard component
  if (answerType === 'single_choice') {
    return (
      <QuestionCard
        questionNumber={questionNumber}
        totalQuestions={totalQuestions}
        question={question.question}
        options={question.options}
        correctAnswer={question.correctAnswer as string}
        explanation={question.explanation}
        difficulty={question.difficulty}
        topic={question.topic}
        subject={question.subject}
        onAnswer={onAnswer}
      />
    );
  }

  // For other types, render with custom components
  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">
              Question {questionNumber} of {totalQuestions}
            </span>
            <Badge variant="outline" className={cn('text-xs', getDifficultyColor())}>
              {question.difficulty}
            </Badge>
            {answerType !== 'single_choice' && (
              <Badge variant="secondary" className="text-xs">
                {answerType.replace('_', ' ')}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Badge variant="outline">{question.subject}</Badge>
            <Badge variant="outline">{question.topic}</Badge>
          </div>
        </div>
      </CardHeader>

      {/* Question Content */}
      <CardContent className="p-6">
        {answerType === 'integer' && (
          <IntegerInput
            value={currentAnswer || ''}
            onChange={onAnswer}
            min={question.integerRange?.min}
            max={question.integerRange?.max}
            questionText={question.question}
          />
        )}

        {answerType === 'multiple_choice' && (
          <MultiSelect
            options={question.options}
            selectedValues={currentAnswer || []}
            onChange={onAnswer}
            questionText={question.question}
            minSelections={question.minSelections}
            maxSelections={question.maxSelections}
          />
        )}

        {answerType === 'match_following' && question.leftColumn && question.rightColumn && (
          <MatchFollowing
            leftColumn={question.leftColumn}
            rightColumn={question.rightColumn}
            matches={currentAnswer || {}}
            onChange={onAnswer}
            questionText={question.question}
          />
        )}

        {answerType === 'assertion_reason' && (
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm whitespace-pre-wrap">{question.question}</p>
            </div>
            <div className="grid grid-cols-1 gap-3">
              {question.options.map((option) => (
                <button
                  key={option.id}
                  onClick={() => onAnswer(option.id)}
                  className={cn(
                    'p-4 rounded-lg border-2 text-left transition-colors',
                    currentAnswer === option.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <div className="font-medium mb-1">{option.id}.</div>
                  <div className="text-sm">{option.text}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {answerType === 'comprehension' && (
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm whitespace-pre-wrap">{question.question}</p>
            </div>
            <div className="space-y-3">
              {question.options.map((option) => (
                <button
                  key={option.id}
                  onClick={() => onAnswer(option.id)}
                  className={cn(
                    'w-full p-4 rounded-lg border-2 text-left transition-colors',
                    currentAnswer === option.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}
                >
                  <span className="font-medium mr-2">{option.id}.</span>
                  {option.text}
                </button>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
