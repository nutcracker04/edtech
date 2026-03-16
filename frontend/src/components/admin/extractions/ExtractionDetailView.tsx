/**
 * Extraction Detail View Component
 * Displays detailed information about a specific extraction job
 */

import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useExtractionManagement } from '@/contexts/ExtractionManagementContext';
import { adminExtractionService } from '@/services/adminExtractionService';

export function ExtractionDetailView() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const {
    state,
    setCurrentJob,
    setCurrentJobLoading,
    setCurrentJobError,
    setQuestions,
    setQuestionsLoading,
    setQuestionsError,
    setQuestionPagination,
  } = useExtractionManagement();

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

    const fetchQuestions = async () => {
      setQuestionsLoading(true);
      try {
        const questions = await adminExtractionService.listQuestions({
          jobId,
          filters: state.questionFilters,
          pagination: state.questionPagination,
        });
        setQuestions(questions);
      } catch (error) {
        setQuestionsError(error instanceof Error ? error : new Error('Failed to fetch questions'));
      } finally {
        setQuestionsLoading(false);
      }
    };

    fetchQuestions();
  }, [jobId, state.questionFilters, state.questionPagination, setQuestions, setQuestionsLoading, setQuestionsError]);

  const handlePageChange = (page: number) => {
    setQuestionPagination({ ...state.questionPagination, page });
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

      {/* Questions Section */}
      <div className="border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Extracted Questions</h2>

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
                <div key={question.id} className="p-4 border rounded bg-muted/50">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium flex-1">{question.question_text}</h3>
                    <span className="text-xs px-2 py-1 rounded bg-primary/10 text-primary">
                      {question.processing_status}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <p>Options: {question.options.length}</p>
                    {question.chapter_context && <p>Chapter: {question.chapter_context}</p>}
                    {question.topic_context && <p>Topic: {question.topic_context}</p>}
                    {question.page_number && <p>Page: {question.page_number}</p>}
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
