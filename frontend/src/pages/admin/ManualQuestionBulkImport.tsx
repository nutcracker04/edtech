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
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "page_number": 1,
    "chapter_context": "Exact chapter title (or slug) from the book",
    "topic_context": "Exact topic title (or slug) from the chapter",
    "sub_topic_context": "",
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
                  Each object maps to one <code className="text-xs">raw_questions</code> row:{' '}
                  <code className="text-xs">question_number</code>, <code className="text-xs">question_text</code>,{' '}
                  <code className="text-xs">options</code>, <code className="text-xs">page_number</code>, contexts,{' '}
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
              <TabsList className="mb-4">
                <TabsTrigger value="editor">Editor</TabsTrigger>
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
              <TabsContent value="hints">
                <ul className="list-disc pl-5 space-y-2 text-sm text-muted-foreground">
                  <li>
                    <strong className="text-foreground">options</strong>: list of strings; use at least two for MCQ
                    finalization.
                  </li>
                  <li>
                    <strong className="text-foreground">raw_images</strong> / <strong className="text-foreground">raw_tables</strong>:
                    JSON arrays; use <code className="text-xs">[]</code> if none.
                  </li>
                  <li>
                    After import, open the job to edit rows, delete bad lines, or bulk finalize — unchanged workflow.
                  </li>
                </ul>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
