/**
 * Admin Extraction Service
 * Centralized API client for all extraction management operations
 */

import {
  ExtractionJob,
  RawQuestion,
  ExtractionJobDetail,
  JobStatistics,
  BulkOperationResult,
  QuestionUpdateRequest,
  FinalizeRequest,
  BulkDeleteRequest,
  ExportRequest,
  QuestionFilters,
  JobFilters,
  SortConfig,
  PaginationState,
} from '@/types/admin';
import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ListJobsParams {
  filters?: JobFilters;
  sort?: SortConfig;
  pagination?: PaginationState;
}

interface ListQuestionsParams {
  jobId: string;
  filters?: QuestionFilters;
  pagination?: PaginationState;
}

interface SearchQuestionsParams {
  jobId: string;
  query: string;
  filters?: QuestionFilters;
  pagination?: PaginationState;
}

class AdminExtractionService {
  private async getAuthToken(): Promise<string> {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      throw new Error('Authentication token not found. Please log in.');
    }
    return session.access_token;
  }

  private buildQueryParams(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (typeof value === 'object') {
          searchParams.append(key, JSON.stringify(value));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });
    return searchParams.toString();
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }
    return response.json();
  }

  /**
   * List all extraction jobs with optional filtering, sorting, and pagination
   */
  async listJobs(params?: ListJobsParams): Promise<ExtractionJob[]> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const queryParams = this.buildQueryParams({
      stage: params?.filters?.stage,
      grade_level: params?.filters?.grade_level,
      sort_field: params?.sort?.field,
      sort_order: params?.sort?.order,
      page: params?.pagination?.page,
      page_size: params?.pagination?.page_size,
    });

    const url = `${API_BASE_URL}/admin/extractions${queryParams ? `?${queryParams}` : ''}`;
    console.log('Fetching jobs from:', url);
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    console.log('Response status:', response.status);
    console.log('Response headers:', Object.fromEntries(response.headers.entries()));
    
    const data = await this.handleResponse<ExtractionJob[]>(response);
    console.log('Parsed response data:', data);
    console.log('Data type:', typeof data);
    console.log('Data is array:', Array.isArray(data));
    
    return data;
  }

  /**
   * Get detailed information about a specific extraction job
   */
  async getJobDetails(jobId: string): Promise<ExtractionJobDetail> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/${jobId}`;
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<ExtractionJobDetail>(response);
  }

  /**
   * List raw questions for a specific extraction job
   */
  async listQuestions(params: ListQuestionsParams): Promise<RawQuestion[]> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const queryParams = this.buildQueryParams({
      processing_status: params.filters?.processing_status,
      chapter_context: params.filters?.chapter_context,
      topic_context: params.filters?.topic_context,
      page_number_min: params.filters?.page_number_min,
      page_number_max: params.filters?.page_number_max,
      page: params.pagination?.page,
      page_size: params.pagination?.page_size,
    });

    const url = `${API_BASE_URL}/admin/extractions/${params.jobId}/questions${queryParams ? `?${queryParams}` : ''}`;
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<RawQuestion[]>(response);
  }

  /**
   * Update a raw question
   */
  async updateQuestion(questionId: string, updates: QuestionUpdateRequest): Promise<RawQuestion> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/questions/${questionId}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers,
      body: JSON.stringify(updates),
    });

    return this.handleResponse<RawQuestion>(response);
  }

  /**
   * Delete a raw question
   */
  async deleteQuestion(questionId: string): Promise<void> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/questions/${questionId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to delete question: ${response.status}`);
    }
  }

  /**
   * Finalize a single raw question
   */
  async finalizeQuestion(questionId: string): Promise<RawQuestion> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const request: FinalizeRequest = { question_ids: [questionId] };
    const url = `${API_BASE_URL}/admin/extractions/questions/finalize`;
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    const result = await this.handleResponse<BulkOperationResult>(response);
    if (result.failure_count > 0) {
      throw new Error(result.failed[0]?.error || 'Finalization failed');
    }

    // Return the finalized question (in real scenario, would fetch it)
    return {} as RawQuestion;
  }

  /**
   * Finalize multiple raw questions in bulk
   */
  async bulkFinalizeQuestions(questionIds: string[]): Promise<BulkOperationResult> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const request: FinalizeRequest = { question_ids: questionIds };
    const url = `${API_BASE_URL}/admin/extractions/questions/finalize`;
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    return this.handleResponse<BulkOperationResult>(response);
  }

  /**
   * Delete multiple raw questions in bulk
   */
  async bulkDeleteQuestions(questionIds: string[]): Promise<BulkOperationResult> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const request: BulkDeleteRequest = { question_ids: questionIds };
    const url = `${API_BASE_URL}/admin/extractions/questions/bulk`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers,
      body: JSON.stringify(request),
    });

    return this.handleResponse<BulkOperationResult>(response);
  }

  /**
   * Get extracted markdown content for an extraction job (from Supabase storage)
   */
  async getExtractedContent(jobId: string): Promise<{ content: string; job_id: string }> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/${jobId}/extracted-content`;
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<{ content: string; job_id: string }>(response);
  }

  /**
   * Get statistics for an extraction job
   */
  async getJobStatistics(jobId: string): Promise<JobStatistics> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/${jobId}/stats`;
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<JobStatistics>(response);
  }

  /**
   * Delete an extraction job
   */
  async deleteJob(jobId: string): Promise<void> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const url = `${API_BASE_URL}/admin/extractions/${jobId}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to delete job: ${response.status}`);
    }
  }

  /**
   * Search raw questions with full-text search
   */
  async searchQuestions(params: SearchQuestionsParams): Promise<RawQuestion[]> {
    const token = await this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    };

    const queryParams = this.buildQueryParams({
      query: params.query,
      processing_status: params.filters?.processing_status,
      chapter_context: params.filters?.chapter_context,
      topic_context: params.filters?.topic_context,
      page_number_min: params.filters?.page_number_min,
      page_number_max: params.filters?.page_number_max,
      page: params.pagination?.page,
      page_size: params.pagination?.page_size,
    });

    const url = `${API_BASE_URL}/admin/extractions/${params.jobId}/questions/search${queryParams ? `?${queryParams}` : ''}`;
    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<RawQuestion[]>(response);
  }

  /**
   * Export extraction data in specified format
   */
  async exportData(jobId: string, request: ExportRequest): Promise<Blob> {
    const token = await this.getAuthToken();
    const headers = {
      Authorization: `Bearer ${token}`,
    };

    const queryParams = this.buildQueryParams({
      format: request.format,
    });

    const url = `${API_BASE_URL}/admin/extractions/${jobId}/export${queryParams ? `?${queryParams}` : ''}`;
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        filters: request.filters,
        question_ids: request.question_ids,
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }

    return response.blob();
  }
}

export const adminExtractionService = new AdminExtractionService();
