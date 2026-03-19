/**
 * Admin: bulk manual import of raw_questions for a book (replaces PDF extraction upload).
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ArrowLeft,
  BookOpen,
  ClipboardCopy,
  Loader2,
  Upload,
  ListTree,
  FileJson,
} from 'lucide-react';
import { toast } from 'sonner';
import { adminExtractionService } from '@/services/adminExtractionService';

const JSON_TEMPLATE = `[
  {
    "question_number": "1",
    "question_text": "Your question text here",
    "answer_type": "mcq_single",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "A",
    "page_number": 1,
    "chapter_context": "Exact chapter title (or slug) from the book",
    "topic_context": "Exact topic title (or slug) from the chapter",
    "sub_topic_context": "",
    "marks": null,
    "negative_marks": null,
    "bloom_level": null,
    "raw_images": [],
    "raw_tables": []
  }
]`;

type ImportBook = { id: string; title: string; subject: string; grade_level: number };

export default function ManualQuestionBulkImport() {
  const navigate = useNavigate();
  const [books, setBooks] = useState<ImportBook[]>([]);
  const [bookId, setBookId] = useState<string>('');
  const [jobTitle, setJobTitle] = useState('');
  const [jsonText, setJsonText] = useState(JSON.stringify(JSON.parse(JSON_TEMPLATE), null, 2));
  const [outline, setOutline] = useState<string>('');
  const [loadingBooks, setLoadingBooks] = useState(true);
  const [loadingOutline, setLoadingOutline] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formQn, setFormQn] = useState('1');
  const [formText, setFormText] = useState('');
  const [formAnswerType, setFormAnswerType] = useState('mcq_single');
  const [formOptions, setFormOptions] = useState('Opt A\nOpt B\nOpt C\nOpt D');
  const [formCorrect, setFormCorrect] = useState('A');
  const [formPage, setFormPage] = useState('1');
  const [formChapter, setFormChapter] = useState('');
  const [formTopic, setFormTopic] = useState('');
  const [formSubtopic, setFormSubtopic] = useState('');
  const [formMarks, setFormMarks] = useState('');
  const [formNeg, setFormNeg] = useState('');
  const [formBloom, setFormBloom] = useState('');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoadingBooks(true);
      try {
        const data = await adminExtractionService.listImportBooks();
        if (!cancelled) setBooks(data);
      } catch (e) {
        if (!cancelled) toast.error(e instanceof Error ? e.message : 'Could not load books');
      } finally {
        if (!cancelled) setLoadingBooks(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loadOutline = useCallback(async () => {
    if (!bookId) {
      toast.error('Select a book first');
      return;
    }
    setLoadingOutline(true);
    try {
      const o = await adminExtractionService.getImportBookOutline(bookId);
      const lines: string[] = [];
      for (const ch of o.chapters) {
        lines.push(`Chapter: ${ch.title} (slug: ${ch.slug})`);
        for (const t of ch.topics) {
          lines.push(`  • Topic: ${t.title} (slug: ${t.slug})`);
        }
        lines.push('');
      }
      setOutline(lines.join('\n') || 'No chapters found for this book.');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not load outline');
      setOutline('');
    } finally {
      setLoadingOutline(false);
    }
  }, [bookId]);

  useEffect(() => {
    if (!bookId) {
      setOutline('');
      return;
    }
    void loadOutline();
  }, [bookId, loadOutline]);

  const selectedBook = useMemo(() => books.find((b) => b.id === bookId), [books, bookId]);

  const handlePasteTemplate = () => {
    setJsonText(JSON.stringify(JSON.parse(JSON_TEMPLATE), null, 2));
    toast.message('Template applied');
  };

  const appendFormRowToJson = () => {
    if (!formText.trim()) {
      toast.error('Question text is required');
      return;
    }
    const opts = formOptions
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    const intLike = formAnswerType === 'integer' || formAnswerType === 'numerical' || formAnswerType === 'subjective';
    if (!intLike && opts.length < 2) {
      toast.error('Add at least two options (one per line) for MCQ');
      return;
    }
    if (!intLike && !formCorrect.trim()) {
      toast.error('Correct answer is required for MCQ');
      return;
    }
    if (intLike && !formCorrect.trim()) {
      toast.error('Correct answer is required');
      return;
    }
    const row: Record<string, unknown> = {
      question_number: formQn.trim() || '1',
      question_text: formText.trim(),
      answer_type: formAnswerType,
      options: intLike ? [] : opts,
      correct_answer: formCorrect.trim(),
      page_number: formPage.trim() ? parseInt(formPage, 10) : 1,
      chapter_context: formChapter.trim() || null,
      topic_context: formTopic.trim() || null,
      sub_topic_context: formSubtopic.trim() || null,
      marks: formMarks.trim() ? parseFloat(formMarks) : null,
      negative_marks: formNeg.trim() ? parseFloat(formNeg) : null,
      bloom_level: formBloom.trim() || null,
      raw_images: [],
      raw_tables: [],
    };
    let arr: unknown[];
    try {
      const parsed = JSON.parse(jsonText);
      if (!Array.isArray(parsed)) throw new Error('not array');
      arr = parsed;
    } catch {
      toast.error('Fix JSON array first, or reset to template');
      return;
    }
    arr.push(row);
    setJsonText(JSON.stringify(arr, null, 2));
    toast.success('Appended to JSON payload');
  };

  const handleSubmit = async () => {
    if (!bookId) {
      toast.error('Select a book');
      return;
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(jsonText);
    } catch {
      toast.error('Invalid JSON — fix syntax and try again');
      return;
    }
    if (!Array.isArray(parsed) || parsed.length === 0) {
      toast.error('JSON must be a non-empty array of question objects');
      return;
    }

    setSubmitting(true);
    try {
      const result = await adminExtractionService.createManualImport({
        book_id: bookId,
        job_title: jobTitle.trim() || null,
        questions: parsed as Record<string, unknown>[],
      });
      toast.success(`Imported ${result.questions_created} questions`);
      navigate(`/admin/extractions/${result.job_id}`);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Import failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="container max-w-5xl py-8">
        <Button variant="ghost" className="mb-4 gap-2 -ml-2" onClick={() => navigate('/admin')}>
          <ArrowLeft className="h-4 w-4" />
          Admin dashboard
        </Button>

        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Upload className="h-8 w-8 text-primary" />
            Bulk question import
          </h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Create a completed import job and load every field for each question as JSON. Then use{' '}
            <strong>Extraction management</strong> to review, edit, delete, and finalize into the repository — same
            as before, without any PDF pipeline.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookOpen className="h-5 w-5" />
                Book & job
              </CardTitle>
              <CardDescription>
                Link this batch to a book record (required for chapter/topic mapping when you finalize).
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Book</Label>
                {loadingBooks ? (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Loading books…
                  </div>
                ) : books.length === 0 ? (
                  <Alert variant="destructive">
                    <AlertTitle>No books</AlertTitle>
                    <AlertDescription>
                      Add books (and chapters/topics) in your database first, then refresh this page.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <Select value={bookId} onValueChange={setBookId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose a book" />
                    </SelectTrigger>
                    <SelectContent>
                      {books.map((b) => (
                        <SelectItem key={b.id} value={b.id}>
                          {b.title} — {b.subject}, class {b.grade_level}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="job-title">Job title (optional)</Label>
                <Input
                  id="job-title"
                  placeholder="e.g. Unit 3 manual entry — Jan 2025"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Shown in the extraction job list. Defaults to your JSON batch only if left empty.
                </p>
              </div>

              {selectedBook && (
                <div className="rounded-lg border bg-muted/40 p-3 text-sm">
                  <p className="font-medium">{selectedBook.title}</p>
                  <p className="text-muted-foreground">
                    {selectedBook.subject} · Class {selectedBook.grade_level}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <ListTree className="h-5 w-5" />
                Chapter & topic reference
              </CardTitle>
              <CardDescription>
                Use these exact titles (or slugs) in <code className="text-xs">chapter_context</code> and{' '}
                <code className="text-xs">topic_context</code> so finalization can map rows to your hierarchy.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button type="button" variant="outline" size="sm" onClick={() => void loadOutline()} disabled={!bookId || loadingOutline}>
                {loadingOutline ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Refresh outline
              </Button>
              <ScrollArea className="h-[220px] w-full rounded-md border p-3">
                <pre className="text-xs font-mono whitespace-pre-wrap text-muted-foreground">
                  {outline || (bookId ? 'Loading…' : 'Select a book to load outline.')}
                </pre>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6 border-2">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <FileJson className="h-5 w-5" />
                  Question payload (JSON array)
                </CardTitle>
                <CardDescription className="mt-1 max-w-3xl">
                  Full staging row: <code className="text-xs">question_number</code>,{' '}
                  <code className="text-xs">question_text</code>, <code className="text-xs">answer_type</code>,{' '}
                  <code className="text-xs">options</code>, <code className="text-xs">correct_answer</code>,{' '}
                  <code className="text-xs">page_number</code>, chapter/topic contexts, marks, bloom,{' '}
                  <code className="text-xs">raw_images</code>, <code className="text-xs">raw_tables</code>.
                </CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handlePasteTemplate} className="shrink-0">
                <ClipboardCopy className="h-4 w-4 mr-2" />
                Reset to template
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="editor">
              <TabsList className="mb-4 flex-wrap h-auto gap-1">
                <TabsTrigger value="editor">JSON editor</TabsTrigger>
                <TabsTrigger value="form">Form builder</TabsTrigger>
                <TabsTrigger value="hints">Field hints</TabsTrigger>
              </TabsList>
              <TabsContent value="editor" className="space-y-4">
                <Textarea
                  value={jsonText}
                  onChange={(e) => setJsonText(e.target.value)}
                  className="min-h-[320px] font-mono text-sm"
                  spellCheck={false}
                />
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => void handleSubmit()} disabled={submitting || !bookId}>
                    {submitting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Importing…
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Import all questions
                      </>
                    )}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => navigate('/admin/extractions')}>
                    Open extraction management
                  </Button>
                </div>
              </TabsContent>
              <TabsContent value="form" className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Fill one question, then <strong>Append to JSON array</strong>. Repeat for the whole book, then import once.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Question #</Label>
                    <Input value={formQn} onChange={(e) => setFormQn(e.target.value)} className="font-mono" />
                  </div>
                  <div className="space-y-2">
                    <Label>Answer type</Label>
                    <Select value={formAnswerType} onValueChange={setFormAnswerType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="mcq_single">mcq_single</SelectItem>
                        <SelectItem value="mcq_multiple">mcq_multiple</SelectItem>
                        <SelectItem value="integer">integer</SelectItem>
                        <SelectItem value="numerical">numerical</SelectItem>
                        <SelectItem value="subjective">subjective</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2 sm:col-span-2">
                    <Label>Question text</Label>
                    <Textarea value={formText} onChange={(e) => setFormText(e.target.value)} rows={3} className="font-mono text-sm" />
                  </div>
                  <div className="space-y-2 sm:col-span-2">
                    <Label>Options (one per line; leave empty for integer/numerical/subjective)</Label>
                    <Textarea value={formOptions} onChange={(e) => setFormOptions(e.target.value)} rows={5} className="font-mono text-sm" />
                  </div>
                  <div className="space-y-2">
                    <Label>Correct answer</Label>
                    <Input
                      value={formCorrect}
                      onChange={(e) => setFormCorrect(e.target.value)}
                      placeholder="A or A,C / numeric / rubric text"
                      className="font-mono"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Page</Label>
                    <Input value={formPage} onChange={(e) => setFormPage(e.target.value)} type="number" min={1} />
                  </div>
                  <div className="space-y-2">
                    <Label>Chapter context</Label>
                    <Input value={formChapter} onChange={(e) => setFormChapter(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Topic context</Label>
                    <Input value={formTopic} onChange={(e) => setFormTopic(e.target.value)} />
                  </div>
                  <div className="space-y-2 sm:col-span-2">
                    <Label>Sub-topic</Label>
                    <Input value={formSubtopic} onChange={(e) => setFormSubtopic(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Marks</Label>
                    <Input value={formMarks} onChange={(e) => setFormMarks(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label>Negative marks</Label>
                    <Input value={formNeg} onChange={(e) => setFormNeg(e.target.value)} />
                  </div>
                  <div className="space-y-2 sm:col-span-2">
                    <Label>Bloom level</Label>
                    <Input value={formBloom} onChange={(e) => setFormBloom(e.target.value)} />
                  </div>
                </div>
                <Button type="button" variant="secondary" onClick={appendFormRowToJson}>
                  Append to JSON array
                </Button>
              </TabsContent>
              <TabsContent value="hints">
                <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
                  <li>
                    <strong className="text-foreground">correct_answer</strong>: MCQ uses labels (A, B, …); multiple
                    correct: <code className="text-xs">A,C</code>. Integer/numerical/subjective use free text.
                  </li>
                  <li>
                    <strong className="text-foreground">answer_type</strong> drives validation and approval into{' '}
                    <code className="text-xs">questions.answer_type</code>.
                  </li>
                  <li>
                    <strong className="text-foreground">raw_images</strong> / <strong className="text-foreground">raw_tables</strong>:
                    JSON arrays; use <code className="text-xs">[]</code> if none. Images often use{' '}
                    <code className="text-xs">{`{"url":"..."}`}</code> or <code className="text-xs">path</code>.
                  </li>
                  <li>After import, use <strong>Staging questions</strong> on the job to review, reject, reinstate, or approve.</li>
                </ul>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
