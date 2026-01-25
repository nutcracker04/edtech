import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Edit2, Check, X, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ExtractedQuestion {
  question_number: number;
  question_text: string;
  options: Array<{ id: string; text: string }>;
  confidence: number;
  subject?: string;
  topic?: string;
}

interface QuestionMapperProps {
  questions: ExtractedQuestion[];
  onQuestionsChange: (questions: ExtractedQuestion[]) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export function QuestionMapper({
  questions,
  onQuestionsChange,
  onConfirm,
  onCancel,
}: QuestionMapperProps) {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editedQuestion, setEditedQuestion] = useState<ExtractedQuestion | null>(null);

  const startEdit = (index: number) => {
    setEditingIndex(index);
    setEditedQuestion({ ...questions[index] });
  };

  const saveEdit = () => {
    if (editingIndex !== null && editedQuestion) {
      const newQuestions = [...questions];
      newQuestions[editingIndex] = editedQuestion;
      onQuestionsChange(newQuestions);
      setEditingIndex(null);
      setEditedQuestion(null);
    }
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditedQuestion(null);
  };

  const updateEditedQuestion = (field: keyof ExtractedQuestion, value: any) => {
    if (editedQuestion) {
      setEditedQuestion({ ...editedQuestion, [field]: value });
    }
  };

  const updateOption = (optionIndex: number, value: string) => {
    if (editedQuestion) {
      const newOptions = [...editedQuestion.options];
      newOptions[optionIndex] = { ...newOptions[optionIndex], text: value };
      setEditedQuestion({ ...editedQuestion, options: newOptions });
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 80) {
      return <Badge className="bg-green-500">High ({confidence.toFixed(0)}%)</Badge>;
    } else if (confidence >= 60) {
      return <Badge className="bg-yellow-500">Medium ({confidence.toFixed(0)}%)</Badge>;
    } else {
      return <Badge className="bg-red-500">Low ({confidence.toFixed(0)}%)</Badge>;
    }
  };

  const averageConfidence = questions.length > 0
    ? questions.reduce((sum, q) => sum + q.confidence, 0) / questions.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Review Extracted Questions</h2>
          <p className="text-muted-foreground">
            {questions.length} questions extracted • Average confidence: {averageConfidence.toFixed(0)}%
          </p>
        </div>
        {averageConfidence < 70 && (
          <div className="flex items-center gap-2 text-yellow-600">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm">Low confidence - please review carefully</span>
          </div>
        )}
      </div>

      {/* Questions List */}
      <div className="space-y-4">
        {questions.map((question, index) => (
          <Card key={index} className={cn(question.confidence < 60 && 'border-yellow-500')}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1 flex-1">
                  <CardTitle className="text-lg">
                    Question {question.question_number}
                  </CardTitle>
                  <div className="flex gap-2">
                    {getConfidenceBadge(question.confidence)}
                    {question.subject && (
                      <Badge variant="outline">{question.subject}</Badge>
                    )}
                  </div>
                </div>
                {editingIndex === index ? (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={cancelEdit}>
                      <X className="h-4 w-4 mr-1" />
                      Cancel
                    </Button>
                    <Button size="sm" onClick={saveEdit}>
                      <Check className="h-4 w-4 mr-1" />
                      Save
                    </Button>
                  </div>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => startEdit(index)}>
                    <Edit2 className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {editingIndex === index && editedQuestion ? (
                // Edit Mode
                <>
                  <div className="space-y-2">
                    <Label>Question Text</Label>
                    <Textarea
                      value={editedQuestion.question_text}
                      onChange={(e) => updateEditedQuestion('question_text', e.target.value)}
                      rows={4}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Subject</Label>
                    <Select
                      value={editedQuestion.subject}
                      onValueChange={(value) => updateEditedQuestion('subject', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select subject" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="physics">Physics</SelectItem>
                        <SelectItem value="chemistry">Chemistry</SelectItem>
                        <SelectItem value="mathematics">Mathematics</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Options</Label>
                    {editedQuestion.options.map((option, optIndex) => (
                      <div key={option.id} className="flex gap-2">
                        <Badge variant="outline" className="w-8 justify-center">
                          {option.id}
                        </Badge>
                        <Input
                          value={option.text}
                          onChange={(e) => updateOption(optIndex, e.target.value)}
                          placeholder={`Option ${option.id}`}
                        />
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                // View Mode
                <>
                  <div>
                    <p className="text-sm font-medium mb-2">Question:</p>
                    <p className="text-sm whitespace-pre-wrap">{question.question_text}</p>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">Options:</p>
                    <div className="space-y-2">
                      {question.options.map((option) => (
                        <div key={option.id} className="flex gap-2 text-sm">
                          <Badge variant="outline" className="w-8 justify-center">
                            {option.id}
                          </Badge>
                          <span>{option.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={onConfirm} disabled={editingIndex !== null}>
          Confirm Questions ({questions.length})
        </Button>
      </div>
    </div>
  );
}
