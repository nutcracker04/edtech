/**
 * Extraction Detail View Component
 * Displays detailed information about a specific extraction job.
 * Subscribes to Supabase Realtime for live progress updates.
 * Shows extracted content from Supabase storage.
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useExtractionManagement } from '@/contexts/ExtractionManagementContext';
import { adminExtractionService } from '@/services/adminExtractionService';
import { supabase } from '@/integrations/supabase/client';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Pencil, Ban, RotateCcw } from 'lucide-react';
import type { ProcessingStatus, RawQuestion } from '@/types/admin';
import { RawQuestionEditorDialog } from '@/components/admin/staging/RawQuestionEditorDialog';

type ReviewTab = 'all' | ProcessingStatus;

export function ExtractionDetailView() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [extractedContent, setExtractedContent] = useState<string | null>(null);
  const [extractedContentLoading, setExtractedContentLoading] = useState(false);
  const [extractedContentError, setExtractedContentError] = useState<string | null>(null);
  const [showExtractedContent, setShowExtractedContent] = useState(false);
  const [reviewTab, setReviewTab] = useState<ReviewTab>('pending');
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<RawQuestion | null>(null);
  const {
    state,
    setCurrentJob,
    setCurrentJobLoading,
    setCurrentJobError,
    setQuestions,
    setQuestionsLoading,
    setQuestionsError,
    setQuestionFilters,
    setQuestionPagination,
    removeQuestion,
    selectQuestion,
    deselectQuestion,
    selectAllQuestions,
    deselectAllQuestions,
    setOperationInProgress,
    setOperationError,
  } = useExtractionManagement();
  const selectedQuestionIds = state.selectedQuestionIds;

  const applyReviewTab = (t: ReviewTab) => {
    setReviewTab(t);
    setQuestionFilters(t === 'all' ? {} : { processing_status: t });
    setQuestionPagination({ ...state.questionPagination, page: 1 });
    deselectAllQuestions();
  };

  const refreshQuestions = async () => {
    if (!jobId) return;
    const filters = reviewTab === 'all' ? {} : { processing_status: reviewTab };
    const { questions, total } = await adminExtractionService.listQuestions({
      jobId,
      filters,
      pagination: state.questionPagination,
    });
    setQuestions(questions);
    setQuestionPagination({ ...state.questionPagination, total });
  };

  useEffect(() => {
    if (!jobId) return;

    const fetchJobDetails = async () => {
      setCurrentJobLoading(true);
      try {
        const jobDetail = await adminExtractionService.getJobDetails(jobId);
        setCurrentJob(jobDetail);
      } catch (error) {
        setCurrentJobError(error instanceof Error ? error : new Error('Failed to fetch job details'));
      } finally {
        setCurrentJobLoading(false);
      }
    };

    fetchJobDetails();
  }, [jobId, setCurrentJob, setCurrentJobLoading, setCurrentJobError]);

  useEffect(() => {
    if (!jobId) return;
    setReviewTab('pending');
    setQuestionFilters({ processing_status: 'pending' });
  }, [jobId, setQuestionFilters]);

  // Real-time subscription for this job's progress updates
  useEffect(() => {
    if (!jobId) return;

    const channel = supabase
      .channel(`extraction-job-${jobId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'extraction_jobs',
          filter: `id=eq.${jobId}`,
        },
        async () => {
          // Refetch full job details to get latest progress/stage/statistics
          try {
            const jobDetail = await adminExtractionService.getJobDetails(jobId);
            setCurrentJob(jobDetail);
          } catch {
            // Ignore refetch errors
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [jobId, setCurrentJob]);

  useEffect(() => {
    if (!jobId) return;

    const fetchQuestions = async () => {
      setQuestionsLoading(true);
      try {
        const { questions, total } = await adminExtractionService.listQuestions({
          jobId,
          filters: state.questionFilters,
          pagination: state.questionPagination,
        });
        setQuestions(questions);
        setQuestionPagination({ ...state.questionPagination, total });
      } catch (error) {
        setQuestionsError(error instanceof Error ? error : new Error('Failed to fetch questions'));
      } finally {
        setQuestionsLoading(false);
      }
    };

    fetchQuestions();
  }, [jobId, state.questionFilters, state.questionPagination.page, state.questionPagination.page_size, setQuestions, setQuestionsLoading, setQuestionsError, setQuestionPagination]);

  const handlePageChange = (page: number) => {
    setQuestionPagination({ ...state.questionPagination, page });
  };

  const handleViewExtractedContent = async () => {
    if (!jobId) return;
    setShowExtractedContent(true);
    if (extractedContent !== null) return; // Already loaded
    setExtractedContentLoading(true);
    setExtractedContentError(null);
    try {
      const { content } = await adminExtractionService.getExtractedContent(jobId);
      setExtractedContent(content);
    } catch (error) {
      setExtractedContentError(error instanceof Error ? error.message : 'Failed to load extracted content');
    } finally {
      setExtractedContentLoading(false);
    }
  };

  if (state.currentJobLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading job details...</p>
        </div>
      </div>
    );
  }

  if (state.currentJobError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-destructive mb-4">Error: {state.currentJobError.message}</p>
          <button
            onClick={() => navigate('/admin/questions')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Back to batches
          </button>
        </div>
      </div>
    );
  }

  if (!state.currentJob) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">Job not found</p>
          <button
            onClick={() => navigate('/admin/questions')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Back to batches
          </button>
        </div>
      </div>
    );
  }

  const { job, book, statistics } = state.currentJob;
  const isManualImport = job.source_pdf_filename === 'manual-import';

  return (
    <div className="container mx-auto py-8">
      <button
        onClick={() => navigate('/admin/questions')}
        className="mb-6 px-4 py-2 border rounded hover:bg-accent"
      >
        ← All batches
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{book?.title || job.title || job.source_pdf_filename}</h1>
        <p className="text-muted-foreground">
          Questions · Batch · {book?.title || job.title || 'Unknown book'}
        </p>
      </div>

      {/* Job Metadata Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Job Information</h2>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">{isManualImport ? 'Source' : 'Filename'}</p>
              <p className="font-medium">
                {isManualImport ? 'Manual bulk import' : job.source_pdf_filename}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Stage</p>
              <p className="font-medium">{job.stage}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Progress</p>
              <p className="font-medium">{job.progress}%</p>
            </div>
            {book && (
              <div>
                <p className="text-sm text-muted-foreground">Grade Level</p>
                <p className="font-medium">Grade {book.grade_level}</p>
              </div>
            )}
          </div>
        </div>

        {/* Statistics Section */}
        <div className="border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Statistics</h2>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Total Questions</p>
              <p className="text-2xl font-bold">{statistics.total_questions}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Finalization Rate</p>
              <p className="text-2xl font-bold">{(Number(statistics.finalization_rate ?? 0) * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Questions per Page</p>
              <p className="font-medium">{Number(statistics.average_questions_per_page ?? 0).toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Legacy PDF markdown (hidden for manual imports) */}
      {!isManualImport && (
        <div className="border rounded-lg p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Extracted content (PDF jobs)</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Raw markdown from automated PDF extraction, if stored in Supabase.
          </p>
          {!showExtractedContent ? (
            <button
              onClick={handleViewExtractedContent}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
            >
              View extracted markdown
            </button>
          ) : extractedContentLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
              <p className="text-muted-foreground">Loading extracted content...</p>
            </div>
          ) : extractedContentError ? (
            <div className="text-center py-8">
              <p className="text-destructive mb-4">{extractedContentError}</p>
              <button
                onClick={handleViewExtractedContent}
                className="px-4 py-2 border rounded hover:bg-accent"
              >
                Retry
              </button>
            </div>
          ) : extractedContent ? (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">
                  {extractedContent.length.toLocaleString()} characters
                </span>
                <button
                  onClick={() => setShowExtractedContent(false)}
                  className="text-sm text-muted-foreground hover:text-foreground"
                >
                  Collapse
                </button>
              </div>
              <pre className="p-4 bg-muted rounded-lg overflow-auto max-h-96 text-sm whitespace-pre-wrap font-mono">
                {extractedContent}
              </pre>
            </div>
          ) : null}
        </div>
      )}

      {/* Staging workspace: filter, edit, reject, approve */}
      <div className="border rounded-lg p-6">
        <div className="flex flex-col gap-4 mb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-semibold">Staging questions</h2>
            <Tabs
              value={reviewTab}
              onValueChange={(v) => applyReviewTab(v as ReviewTab)}
              className="w-full sm:w-auto"
            >
              <TabsList className="flex-wrap h-auto gap-1">
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="pending">Pending review</TabsTrigger>
                <TabsTrigger value="rejected">Rejected</TabsTrigger>
                <TabsTrigger value="tagged">Approved</TabsTrigger>
                <TabsTrigger value="failed">Failed / error</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
          <p className="text-sm text-muted-foreground">
            One place to review imports: edit every field, delete bad rows, reject, reinstate, or approve into the question bank.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectAllQuestions(state.questions.map((q) => q.id))}
            >
              Select all (page)
            </Button>
            <Button variant="outline" size="sm" onClick={() => deselectAllQuestions()}>
              Deselect all
            </Button>
            <Button
              size="sm"
              onClick={async () => {
                const ids = Array.from(state.selectedQuestionIds);
                if (ids.length === 0) {
                  alert('Select questions to approve');
                  return;
                }
                setOperationInProgress(true);
                setOperationError(null);
                try {
                  const result = await adminExtractionService.bulkFinalizeQuestions(ids);
                  if (result.failure_count > 0) {
                    setOperationError(
                      new Error(`${result.failure_count} failed: ${result.failed?.[0]?.error ?? 'Unknown'}`)
                    );
                  }
                  if (result.success_count > 0) {
                    const jobDetail = await adminExtractionService.getJobDetails(jobId!);
                    setCurrentJob(jobDetail);
                    await refreshQuestions();
                    deselectAllQuestions();
                  }
                } catch (e) {
                  setOperationError(e instanceof Error ? e : new Error('Approve failed'));
                  alert(e instanceof Error ? e.message : 'Approve failed');
                } finally {
                  setOperationInProgress(false);
                }
              }}
              disabled={selectedQuestionIds.size === 0 || state.operationInProgress}
            >
              {state.operationInProgress ? 'Approving…' : `Approve (${selectedQuestionIds.size})`}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={async () => {
                const ids = Array.from(state.selectedQuestionIds);
                if (ids.length === 0) {
                  alert('Select questions to reject');
                  return;
                }
                setOperationInProgress(true);
                try {
                  await adminExtractionService.bulkRejectQuestions(ids);
                  const jobDetail = await adminExtractionService.getJobDetails(jobId!);
                  setCurrentJob(jobDetail);
                  await refreshQuestions();
                  deselectAllQuestions();
                } catch (e) {
                  alert(e instanceof Error ? e.message : 'Reject failed');
                } finally {
                  setOperationInProgress(false);
                }
              }}
              disabled={selectedQuestionIds.size === 0 || state.operationInProgress}
            >
              <Ban className="h-3.5 w-3.5 mr-1" />
              Reject ({selectedQuestionIds.size})
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                const ids = Array.from(state.selectedQuestionIds);
                if (ids.length === 0) {
                  alert('Select rejected questions to reinstate');
                  return;
                }
                setOperationInProgress(true);
                try {
                  await adminExtractionService.bulkReinstateQuestions(ids);
                  const jobDetail = await adminExtractionService.getJobDetails(jobId!);
                  setCurrentJob(jobDetail);
                  await refreshQuestions();
                  deselectAllQuestions();
                } catch (e) {
                  alert(e instanceof Error ? e.message : 'Reinstate failed');
                } finally {
                  setOperationInProgress(false);
                }
              }}
              disabled={selectedQuestionIds.size === 0 || state.operationInProgress}
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" />
              Reinstate ({selectedQuestionIds.size})
            </Button>
          </div>
        </div>

        {state.operationError && (
          <div className="mb-4 p-4 bg-destructive/10 text-destructive rounded-lg">
            {state.operationError.message}
          </div>
        )}

        {state.questionsLoading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-muted-foreground">Loading questions...</p>
          </div>
        ) : state.questionsError ? (
          <div className="text-center py-8">
            <p className="text-destructive">Error: {state.questionsError.message}</p>
          </div>
        ) : state.questions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No questions found</p>
          </div>
        ) : (
          <>
            <div className="space-y-4">
              {state.questions.map((question) => (
                <div
                  key={question.id}
                  className={`p-4 border rounded bg-muted/50 ${selectedQuestionIds.has(question.id) ? 'ring-2 ring-primary' : ''}`}
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <input
                          type="checkbox"
                          checked={selectedQuestionIds.has(question.id)}
                          onChange={(e) =>
                            e.target.checked ? selectQuestion(question.id) : deselectQuestion(question.id)
                          }
                          className="rounded"
                        />
                        <h3 className="font-medium flex-1 truncate">{question.question_text}</h3>
                        <span className="text-xs px-2 py-1 rounded bg-primary/10 text-primary shrink-0">
                          {question.processing_status}
                        </span>
                      </div>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>
                          #{question.question_number} · type: {question.answer_type ?? '—'} · options:{' '}
                          {question.options?.length ?? 0}
                        </p>
                        {question.correct_answer != null && question.correct_answer !== '' && (
                          <p>Correct: {question.correct_answer}</p>
                        )}
                        {question.chapter_context && <p>Chapter: {question.chapter_context}</p>}
                        {question.topic_context && <p>Topic: {question.topic_context}</p>}
                        {question.page_number != null && <p>Page: {question.page_number}</p>}
                        {(question.marks != null || question.negative_marks != null) && (
                          <p>
                            Marks: {question.marks ?? '—'} / neg: {question.negative_marks ?? '—'}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingQuestion(question);
                          setEditorOpen(true);
                        }}
                        disabled={state.operationInProgress}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <button
                        onClick={async () => {
                          if (!confirm('Delete this question?')) return;
                          setOperationInProgress(true);
                          try {
                            await adminExtractionService.deleteQuestion(question.id);
                            removeQuestion(question.id);
                            const jobDetail = await adminExtractionService.getJobDetails(jobId!);
                            setCurrentJob(jobDetail);
                          } catch (e) {
                            alert(e instanceof Error ? e.message : 'Delete failed');
                          } finally {
                            setOperationInProgress(false);
                          }
                        }}
                        disabled={!!question.question_id || state.operationInProgress}
                        title={question.question_id ? 'Cannot delete finalized question' : 'Delete'}
                        className="px-2 py-1 text-sm text-destructive hover:bg-destructive/10 rounded disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {state.questionPagination.total > state.questionPagination.page_size && (
              <div className="mt-6 flex justify-center gap-2">
                <button
                  onClick={() => handlePageChange(state.questionPagination.page - 1)}
                  disabled={state.questionPagination.page === 1}
                  className="px-4 py-2 border rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2">
                  Page {state.questionPagination.page} of{' '}
                  {Math.ceil(state.questionPagination.total / state.questionPagination.page_size)}
                </span>
                <button
                  onClick={() => handlePageChange(state.questionPagination.page + 1)}
                  disabled={
                    state.questionPagination.page >=
                    Math.ceil(state.questionPagination.total / state.questionPagination.page_size)
                  }
                  className="px-4 py-2 border rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <RawQuestionEditorDialog
        open={editorOpen}
        onOpenChange={(o) => {
          setEditorOpen(o);
          if (!o) setEditingQuestion(null);
        }}
        question={editingQuestion}
        onSaved={async () => {
          if (jobId) {
            try {
              const jobDetail = await adminExtractionService.getJobDetails(jobId);
              setCurrentJob(jobDetail);
            } catch {
              /* ignore */
            }
          }
          await refreshQuestions();
        }}
      />
    </div>
  );
}
