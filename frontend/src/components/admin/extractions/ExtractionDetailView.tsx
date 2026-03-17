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

export function ExtractionDetailView() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [extractedContent, setExtractedContent] = useState<string | null>(null);
  const [extractedContentLoading, setExtractedContentLoading] = useState(false);
  const [extractedContentError, setExtractedContentError] = useState<string | null>(null);
  const [showExtractedContent, setShowExtractedContent] = useState(false);
  const {
    state,
    setCurrentJob,
    setCurrentJobLoading,
    setCurrentJobError,
    setQuestions,
    setQuestionsLoading,
    setQuestionsError,
    setQuestionPagination,
    updateQuestion,
    removeQuestion,
    selectQuestion,
    deselectQuestion,
    selectAllQuestions,
    deselectAllQuestions,
    setOperationInProgress,
    setOperationError,
  } = useExtractionManagement();
  const selectedQuestionIds = state.selectedQuestionIds;

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
            onClick={() => navigate('/admin/extractions')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Back to List
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
            onClick={() => navigate('/admin/extractions')}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Back to List
          </button>
        </div>
      </div>
    );
  }

  const { job, book, statistics } = state.currentJob;

  return (
    <div className="container mx-auto py-8">
      <button
        onClick={() => navigate('/admin/extractions')}
        className="mb-6 px-4 py-2 border rounded hover:bg-accent"
      >
        ← Back to List
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">{book?.title || job.source_pdf_filename}</h1>
        <p className="text-muted-foreground">
          Extraction Management &gt; {book?.title || 'Unknown Book'}
        </p>
      </div>

      {/* Job Metadata Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Job Information</h2>
          <div className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Filename</p>
              <p className="font-medium">{job.source_pdf_filename}</p>
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
              <p className="text-2xl font-bold">{(statistics.finalization_rate * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Questions per Page</p>
              <p className="font-medium">{statistics.average_questions_per_page.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Extracted Content Section (from Supabase) */}
      <div className="border rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Extracted Content</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Raw markdown extracted from the PDF, stored in Supabase.
        </p>
        {!showExtractedContent ? (
          <button
            onClick={handleViewExtractedContent}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            View Extracted Markdown
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

      {/* Questions Section with CRUD and Finalize */}
      <div className="border rounded-lg p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold">Extracted Questions (Raw Data)</h2>
          <div className="flex gap-2">
            <button
              onClick={() => selectAllQuestions(state.questions.map((q) => q.id))}
              className="px-3 py-1.5 text-sm border rounded hover:bg-accent"
            >
              Select All
            </button>
            <button
              onClick={() => deselectAllQuestions()}
              className="px-3 py-1.5 text-sm border rounded hover:bg-accent"
            >
              Deselect All
            </button>
            <button
              onClick={async () => {
                const ids = Array.from(state.selectedQuestionIds);
                if (ids.length === 0) {
                  alert('Select questions to add to repository');
                  return;
                }
                setOperationInProgress(true);
                setOperationError(null);
                try {
                  const result = await adminExtractionService.bulkFinalizeQuestions(ids);
                  if (result.failure_count > 0) {
                    setOperationError(new Error(`${result.failure_count} failed: ${result.failed?.[0]?.error ?? 'Unknown'}`));
                  }
                  if (result.success_count > 0) {
                    const jobDetail = await adminExtractionService.getJobDetails(jobId!);
                    setCurrentJob(jobDetail);
                    const { questions, total } = await adminExtractionService.listQuestions({
                      jobId: jobId!,
                      filters: state.questionFilters,
                      pagination: state.questionPagination,
                    });
                    setQuestions(questions);
                    setQuestionPagination({ ...state.questionPagination, total });
                    deselectAllQuestions();
                  }
                } catch (e) {
                  setOperationError(e instanceof Error ? e : new Error('Finalization failed'));
                  alert(e instanceof Error ? e.message : 'Finalization failed');
                } finally {
                  setOperationInProgress(false);
                }
              }}
              disabled={selectedQuestionIds.size === 0 || state.operationInProgress}
              className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90 disabled:opacity-50"
            >
              {state.operationInProgress ? 'Adding...' : `Add to Repository (${selectedQuestionIds.size})`}
            </button>
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
                        <p>Options: {question.options?.length ?? 0}</p>
                        {question.chapter_context && <p>Chapter: {question.chapter_context}</p>}
                        {question.topic_context && <p>Topic: {question.topic_context}</p>}
                        {question.page_number && <p>Page: {question.page_number}</p>}
                      </div>
                    </div>
                                <div className="flex gap-2 shrink-0">
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
    </div>
  );
}
