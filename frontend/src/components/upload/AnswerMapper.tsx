import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Question {
  question_number: number;
  question_text: string;
  options: Array<{ id: string; text: string }>;
}

interface AnswerMapperProps {
  questions: Question[];
  answers: Record<number, string>;
  onAnswersChange: (answers: Record<number, string>) => void;
  onSubmit: () => void;
  onBack: () => void;
}

export function AnswerMapper({
  questions,
  answers,
  onAnswersChange,
  onSubmit,
  onBack,
}: AnswerMapperProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const handleAnswerChange = (questionNumber: number, answer: string) => {
    onAnswersChange({
      ...answers,
      [questionNumber]: answer,
    });
  };

  const currentQuestion = questions[currentQuestionIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = (answeredCount / questions.length) * 100;

  const goToNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const goToPrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const goToQuestion = (index: number) => {
    setCurrentQuestionIndex(index);
  };

  const isAnswered = (questionNumber: number) => {
    return questionNumber in answers;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Map Your Answers</h2>
        <p className="text-muted-foreground">
          Select the answers you marked on the test
        </p>
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span>Progress</span>
            <span>{answeredCount} / {questions.length} answered</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Question Navigator */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Questions</CardTitle>
              <CardDescription>Click to navigate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-5 lg:grid-cols-4 gap-2">
                {questions.map((q, index) => (
                  <Button
                    key={q.question_number}
                    variant={currentQuestionIndex === index ? 'default' : 'outline'}
                    size="sm"
                    className={cn(
                      'relative',
                      isAnswered(q.question_number) && currentQuestionIndex !== index && 'border-green-500'
                    )}
                    onClick={() => goToQuestion(index)}
                  >
                    {q.question_number}
                    {isAnswered(q.question_number) && (
                      <CheckCircle2 className="absolute -top-1 -right-1 h-3 w-3 text-green-500" />
                    )}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Current Question */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Question {currentQuestion.question_number}</CardTitle>
                  <CardDescription className="mt-2">
                    {currentQuestion.question_text.substring(0, 100)}
                    {currentQuestion.question_text.length > 100 && '...'}
                  </CardDescription>
                </div>
                {isAnswered(currentQuestion.question_number) && (
                  <Badge className="bg-green-500">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Answered
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Question Text */}
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm whitespace-pre-wrap">{currentQuestion.question_text}</p>
              </div>

              {/* Options */}
              <div>
                <Label className="text-base mb-3 block">Select your answer:</Label>
                <RadioGroup
                  value={answers[currentQuestion.question_number] || ''}
                  onValueChange={(value) => handleAnswerChange(currentQuestion.question_number, value)}
                >
                  <div className="space-y-3">
                    {currentQuestion.options.map((option) => (
                      <div
                        key={option.id}
                        className={cn(
                          'flex items-start space-x-3 p-4 rounded-lg border-2 transition-colors cursor-pointer',
                          answers[currentQuestion.question_number] === option.id
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50'
                        )}
                        onClick={() => handleAnswerChange(currentQuestion.question_number, option.id)}
                      >
                        <RadioGroupItem value={option.id} id={`option-${option.id}`} />
                        <Label
                          htmlFor={`option-${option.id}`}
                          className="flex-1 cursor-pointer font-normal"
                        >
                          <span className="font-medium mr-2">{option.id}.</span>
                          {option.text}
                        </Label>
                      </div>
                    ))}
                  </div>
                </RadioGroup>
              </div>

              {/* Navigation */}
              <div className="flex justify-between pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={goToPrevious}
                  disabled={currentQuestionIndex === 0}
                >
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground self-center">
                  {currentQuestionIndex + 1} / {questions.length}
                </span>
                {currentQuestionIndex < questions.length - 1 ? (
                  <Button onClick={goToNext}>
                    Next
                  </Button>
                ) : (
                  <Button
                    onClick={onSubmit}
                    disabled={answeredCount < questions.length}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Submit Answers
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back to Questions
        </Button>
        {answeredCount === questions.length && currentQuestionIndex !== questions.length - 1 && (
          <Button
            onClick={onSubmit}
            className="bg-green-600 hover:bg-green-700"
          >
            Submit Answers ({answeredCount})
          </Button>
        )}
      </div>
    </div>
  );
}
