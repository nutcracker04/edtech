/**
 * Edit full raw_questions staging row (all architecture fields).
 */

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import type { RawQuestion, QuestionUpdateRequest } from '@/types/admin';
import { adminExtractionService } from '@/services/adminExtractionService';

const ANSWER_TYPES = [
  { value: 'mcq_single', label: 'MCQ single' },
  { value: 'mcq_multiple', label: 'MCQ multiple' },
  { value: 'integer', label: 'Integer' },
  { value: 'numerical', label: 'Numerical' },
  { value: 'subjective', label: 'Subjective' },
  { value: 'true_false', label: 'True / false' },
  { value: 'fill_blank', label: 'Fill blank' },
  { value: 'match', label: 'Match' },
];

function coerceOptions(q: RawQuestion): string[] {
  const o = q.options;
  if (!Array.isArray(o)) return [];
  return o.map((x) => {
    if (typeof x === 'string') return x;
    if (x && typeof x === 'object' && 'text' in x) return String((x as { text: string }).text);
    return String(x);
  });
}

export interface RawQuestionEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  question: RawQuestion | null;
  onSaved: () => void;
}

export function RawQuestionEditorDialog({
  open,
  onOpenChange,
  question,
  onSaved,
}: RawQuestionEditorDialogProps) {
  const [questionNumber, setQuestionNumber] = useState('');
  const [questionText, setQuestionText] = useState('');
  const [options, setOptions] = useState<string[]>(['', '']);
  const [correctAnswer, setCorrectAnswer] = useState('');
  const [answerType, setAnswerType] = useState('mcq_single');
  const [pageNumber, setPageNumber] = useState<string>('');
  const [chapterContext, setChapterContext] = useState('');
  const [topicContext, setTopicContext] = useState('');
  const [subTopicContext, setSubTopicContext] = useState('');
  const [marks, setMarks] = useState('');
  const [negativeMarks, setNegativeMarks] = useState('');
  const [bloomLevel, setBloomLevel] = useState('');
  const [imagesJson, setImagesJson] = useState('[]');
  const [tablesJson, setTablesJson] = useState('[]');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!question || !open) return;
    setQuestionNumber(question.question_number || '');
    setQuestionText(question.question_text || '');
    const opts = coerceOptions(question);
    setOptions(opts.length > 0 ? opts : ['', '']);
    setCorrectAnswer(question.correct_answer ?? '');
    setAnswerType((question.answer_type || 'mcq_single').toLowerCase());
    setPageNumber(question.page_number != null ? String(question.page_number) : '');
    setChapterContext(question.chapter_context ?? '');
    setTopicContext(question.topic_context ?? '');
    setSubTopicContext(question.sub_topic_context ?? '');
    setMarks(question.marks != null ? String(question.marks) : '');
    setNegativeMarks(question.negative_marks != null ? String(question.negative_marks) : '');
    setBloomLevel(question.bloom_level ?? '');
    try {
      setImagesJson(JSON.stringify(question.raw_images ?? [], null, 2));
    } catch {
      setImagesJson('[]');
    }
    try {
      setTablesJson(JSON.stringify(question.raw_tables ?? [], null, 2));
    } catch {
      setTablesJson('[]');
    }
  }, [question, open]);

  const isIntegerLike = answerType === 'integer' || answerType === 'numerical';

  const updateOption = (i: number, v: string) => {
    const next = [...options];
    next[i] = v;
    setOptions(next);
  };

  const addOption = () => setOptions([...options, '']);

  const removeOption = (i: number) => {
    if (options.length <= 1) return;
    setOptions(options.filter((_, idx) => idx !== i));
  };

  const handleSave = async () => {
    if (!question) return;
    if (!questionText.trim()) {
      toast.error('Question text is required');
      return;
    }
    let raw_images: unknown[] | undefined;
    let raw_tables: unknown[] | undefined;
    try {
      raw_images = JSON.parse(imagesJson || '[]');
      if (!Array.isArray(raw_images)) throw new Error('raw_images must be a JSON array');
    } catch (e) {
      toast.error('Invalid raw_images JSON');
      return;
    }
    try {
      raw_tables = JSON.parse(tablesJson || '[]');
      if (!Array.isArray(raw_tables)) throw new Error('raw_tables must be a JSON array');
    } catch {
      toast.error('Invalid raw_tables JSON');
      return;
    }

    const trimmedOpts = options.map((o) => o.trim()).filter(Boolean);
    const payload: QuestionUpdateRequest = {
      question_number: questionNumber.trim(),
      question_text: questionText.trim(),
      options: isIntegerLike ? [] : trimmedOpts,
      correct_answer: correctAnswer.trim() || null,
      answer_type: answerType,
      chapter_context: chapterContext.trim() || undefined,
      topic_context: topicContext.trim() || undefined,
      sub_topic_context: subTopicContext.trim() || undefined,
      page_number: pageNumber.trim() ? parseInt(pageNumber, 10) : null,
      raw_images,
      raw_tables,
      bloom_level: bloomLevel.trim() || null,
    };
    if (marks.trim()) payload.marks = parseFloat(marks);
    else payload.marks = null;
    if (negativeMarks.trim()) payload.negative_marks = parseFloat(negativeMarks);
    else payload.negative_marks = null;

    if (!isIntegerLike && trimmedOpts.length > 0 && trimmedOpts.length < 2) {
      toast.error('Add at least two options for MCQ, or switch answer type to integer/numerical');
      return;
    }

    setSaving(true);
    try {
      await adminExtractionService.updateQuestion(question.id, payload);
      toast.success('Question saved');
      onSaved();
      onOpenChange(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[92vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit staging question</DialogTitle>
          <DialogDescription>
            All fields map to <code className="text-xs">raw_questions</code> before you approve into the bank.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-2 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>Question number</Label>
            <Input value={questionNumber} onChange={(e) => setQuestionNumber(e.target.value)} className="font-mono" />
          </div>
          <div className="space-y-2">
            <Label>Page number</Label>
            <Input
              type="number"
              min={1}
              value={pageNumber}
              onChange={(e) => setPageNumber(e.target.value)}
              className="font-mono"
            />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Answer type</Label>
            <Select value={answerType} onValueChange={setAnswerType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ANSWER_TYPES.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Question text</Label>
            <Textarea
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              rows={5}
              className="font-mono text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label>Chapter context</Label>
            <Input value={chapterContext} onChange={(e) => setChapterContext(e.target.value)} placeholder="Title or slug" />
          </div>
          <div className="space-y-2">
            <Label>Topic context</Label>
            <Input value={topicContext} onChange={(e) => setTopicContext(e.target.value)} placeholder="Title or slug" />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Sub-topic</Label>
            <Input value={subTopicContext} onChange={(e) => setSubTopicContext(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Marks</Label>
            <Input value={marks} onChange={(e) => setMarks(e.target.value)} placeholder="optional" />
          </div>
          <div className="space-y-2">
            <Label>Negative marks</Label>
            <Input value={negativeMarks} onChange={(e) => setNegativeMarks(e.target.value)} placeholder="optional" />
          </div>
          <div className="space-y-2 sm:col-span-2">
            <Label>Bloom level</Label>
            <Input value={bloomLevel} onChange={(e) => setBloomLevel(e.target.value)} placeholder="optional" />
          </div>
        </div>

        {!isIntegerLike && (
          <div className="space-y-3 border rounded-lg p-3">
            <div className="flex items-center justify-between">
              <Label>Options</Label>
              <Button type="button" variant="outline" size="sm" onClick={addOption}>
                <Plus className="h-3 w-3 mr-1" />
                Add
              </Button>
            </div>
            <div className="space-y-2">
              {options.map((opt, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <Badge variant="secondary" className="w-8 shrink-0 justify-center">
                    {String.fromCharCode(65 + idx)}
                  </Badge>
                  <Input
                    value={opt}
                    onChange={(e) => updateOption(idx, e.target.value)}
                    className="font-mono text-sm"
                  />
                  <Button type="button" variant="ghost" size="icon" onClick={() => removeOption(idx)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2">
          <Label>Correct answer</Label>
          <Input
            value={correctAnswer}
            onChange={(e) => setCorrectAnswer(e.target.value)}
            placeholder={isIntegerLike ? 'e.g. 42' : 'e.g. A or A,C for multiple'}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground">
            MCQ: option labels A,B,… — use one letter or comma-separated (A,C) for multiple correct.
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-2">
            <Label>raw_images (JSON array)</Label>
            <Textarea value={imagesJson} onChange={(e) => setImagesJson(e.target.value)} rows={6} className="font-mono text-xs" />
          </div>
          <div className="space-y-2">
            <Label>raw_tables (JSON array)</Label>
            <Textarea value={tablesJson} onChange={(e) => setTablesJson(e.target.value)} rows={6} className="font-mono text-xs" />
          </div>
        </div>

        {question?.processing_status === 'tagged' && (
          <p className="text-sm text-muted-foreground">This row is already approved; editing keeps the staging copy in sync for audit.</p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={() => void handleSave()} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
