/**
 * Admin Panel Type Definitions
 * Defines all TypeScript interfaces for the extraction management module
 */

// Enums
export type ExtractionStage = 'queued' | 'validation' | 'upload' | 'extraction' | 'completed' | 'failed';
export type ProcessingStatus = 'pending' | 'tagged' | 'error';

// Core Domain Interfaces
export interface ExtractionJob {
  id: string;
  book_id: string | null;
  title?: string | null;  // Admin-entered name for display in listing
  source_pdf_filename: string;
  stage: ExtractionStage;
  progress: number;
  questions_extracted: number;
  created_at: string;
  completed_at: string | null;
}

export interface RawQuestion {
  id: string;
  job_id: string;
  question_number: string;
  question_text: string;
  options: string[];
  page_number: number | null;
  chapter_context: string | null;
  topic_context: string | null;
  sub_topic_context: string | null;
  raw_images: ImageData[] | null;
  raw_tables: TableData[] | null;
  processing_status: ProcessingStatus;
  error_message: string | null;
  question_id: string | null;
  created_at: string;
  updated_at?: string;
}

export interface ImageData {
  id: string;
  filename: string;
  page_number: number;
  size: number;
  url?: string;
}

export interface TableData {
  id: string;
  table_html: string;
  page_number: number;
}

export interface ExtractionJobDetail {
  job: ExtractionJob;
  book: Book | null;
  hierarchy: ChapterWithTopics[];
  statistics: JobStatistics;
}

export interface Book {
  id: string;
  title: string;
  grade_level: number;
  subject: string;
}

export interface ChapterWithTopics {
  chapter: Chapter;
  topics: Topic[];
}

export interface Chapter {
  id: string;
  book_id: string;
  title: string;
  chapter_number: number;
}

export interface Topic {
  id: string;
  chapter_id: string;
  title: string;
  topic_number: number;
}

// Filter and Pagination Interfaces
export interface QuestionFilters {
  processing_status?: ProcessingStatus;
  chapter_context?: string;
  topic_context?: string;
  page_number_min?: number;
  page_number_max?: number;
  search_query?: string;
}

export interface JobFilters {
  stage?: ExtractionStage;
  grade_level?: number;
}

export interface PaginationState {
  page: number;
  page_size: number;
  total: number;
}

export interface SortConfig {
  field: 'created_at' | 'completed_at' | 'questions_extracted';
  order: 'asc' | 'desc';
}

// Statistics and Results Interfaces
export interface JobStatistics {
  total_questions: number;
  questions_by_status: Record<ProcessingStatus, number>;
  questions_by_chapter: Record<string, number>;
  finalization_rate: number;
  average_questions_per_page: number;
}

export interface BulkOperationResult {
  successful: string[];
  failed: Array<{ id: string; error: string }>;
  total: number;
  success_count: number;
  failure_count: number;
}

// Request/Response Types
export interface QuestionUpdateRequest {
  question_text?: string;
  options?: string[];
  chapter_context?: string;
  topic_context?: string;
  sub_topic_context?: string;
  page_number?: number | null;
}

export interface FinalizeRequest {
  question_ids: string[];
}

export interface BulkDeleteRequest {
  question_ids: string[];
}

export interface ExportRequest {
  format: 'csv' | 'json' | 'excel';
  filters?: QuestionFilters;
  question_ids?: string[];
}
