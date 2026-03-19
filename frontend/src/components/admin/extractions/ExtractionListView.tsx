/**
 * Extraction List View Component
 * Displays paginated list of extraction jobs with filtering and sorting.
 * Subscribes to Supabase Realtime for live progress updates.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useExtractionManagement } from '@/contexts/ExtractionManagementContext';
import { adminExtractionService } from '@/services/adminExtractionService';
import { supabase } from '@/integrations/supabase/client';
import { ArrowLeft, Trash2 } from 'lucide-react';
import type { ExtractionJob } from '@/types/admin';

export function ExtractionListView() {
  const navigate = useNavigate();
  const {
    state,
    setJobs,
    setJobsLoading,
    setJobsError,
    setJobPagination,
    updateJobInList,
    upsertJobInList,
    removeJobFromList,
  } = useExtractionManagement();
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      setJobsLoading(true);
      try {
        const jobs = await adminExtractionService.listJobs({
          filters: state.jobFilters,
          sort: state.jobSort,
          pagination: state.jobPagination,
        });
        setJobs(jobs);
      } catch (error) {
        console.error('Error fetching jobs:', error);
        setJobsError(error instanceof Error ? error : new Error('Failed to fetch jobs'));
      } finally {
        setJobsLoading(false);
      }
    };

    fetchJobs();
  }, [state.jobFilters, state.jobSort, state.jobPagination, setJobs, setJobsLoading, setJobsError]);

  // Real-time subscription for extraction job progress updates
  useEffect(() => {
    const channel = supabase
      .channel('extraction-jobs-list')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'extraction_jobs',
        },
        (payload) => {
          if (payload.eventType === 'INSERT' && payload.new) {
            upsertJobInList(payload.new as ExtractionJob);
          } else if (payload.eventType === 'UPDATE' && payload.new) {
            updateJobInList((payload.new as ExtractionJob).id, payload.new as Partial<ExtractionJob>);
          } else if (payload.eventType === 'DELETE' && payload.old) {
            removeJobFromList((payload.old as ExtractionJob).id);
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [updateJobInList, upsertJobInList, removeJobFromList]);

  const handleJobClick = (jobId: string) => {
    navigate(`/admin/extractions/${jobId}`);
  };

  const handleDeleteJob = async (jobId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent navigation when clicking delete
    
    if (!confirm('Delete this import job and all its raw questions? This cannot be undone.')) {
      return;
    }

    setDeletingJobId(jobId);
    try {
      await adminExtractionService.deleteJob(jobId);
      // Refresh the list
      const jobs = await adminExtractionService.listJobs({
        filters: state.jobFilters,
        sort: state.jobSort,
        pagination: state.jobPagination,
      });
      setJobs(jobs);
    } catch (error) {
      console.error('Error deleting job:', error);
      alert('Failed to delete import job');
    } finally {
      setDeletingJobId(null);
    }
  };

  const handlePageChange = (page: number) => {
    setJobPagination({ ...state.jobPagination, page });
  };

  const handleBackToAdmin = () => {
    navigate('/admin');
  };

  if (state.jobsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading import jobs...</p>
        </div>
      </div>
    );
  }

  if (state.jobsError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-destructive mb-4">Error: {state.jobsError.message}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <button
          onClick={handleBackToAdmin}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Admin Dashboard
        </button>
        <h1 className="text-3xl font-bold mb-2">Question imports</h1>
        <p className="text-muted-foreground">
          Review and manage batches of raw questions (manual import or legacy jobs), then finalize into the repository.
        </p>
      </div>

      {state.jobs.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No import jobs found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {state.jobs.map((job) => (
            <div
              key={job.id}
              className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors relative group"
            >
              <div onClick={() => handleJobClick(job.id)} className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-lg">{job.title || job.source_pdf_filename}</h3>
                  <p className="text-sm text-muted-foreground">
                    Stage: <span className="font-medium">{job.stage}</span>
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Questions: <span className="font-medium">{job.questions_extracted}</span>
                  </p>
                </div>
                <div className="text-right flex items-start gap-4">
                  <div>
                    <div className="text-2xl font-bold text-primary">{job.progress}%</div>
                    <p className="text-xs text-muted-foreground">
                      {new Date(job.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteJob(job.id, e)}
                    disabled={deletingJobId === job.id}
                    className="p-2 text-destructive hover:bg-destructive/10 rounded transition-colors disabled:opacity-50"
                    title="Delete job"
                  >
                    {deletingJobId === job.id ? (
                      <div className="animate-spin h-4 w-4 border-2 border-destructive border-t-transparent rounded-full" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {state.jobPagination.total > state.jobPagination.page_size && (
        <div className="mt-8 flex justify-center gap-2">
          <button
            onClick={() => handlePageChange(state.jobPagination.page - 1)}
            disabled={state.jobPagination.page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2">
            Page {state.jobPagination.page} of{' '}
            {Math.ceil(state.jobPagination.total / state.jobPagination.page_size)}
          </span>
          <button
            onClick={() => handlePageChange(state.jobPagination.page + 1)}
            disabled={
              state.jobPagination.page >=
              Math.ceil(state.jobPagination.total / state.jobPagination.page_size)
            }
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
