"""
Admin Panel API Models and Schemas

This module defines Pydantic models for the admin panel API, including:
- Request/response models for extraction job management
- Filtering, sorting, and pagination models
- Finalization and bulk operation models
- Response models for job details and statistics

Requirements: 1.2, 3.2, 5.1, 9.4
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal

from app.models.extraction import ExtractionStage, ProcessingStatus, ExtractionJob, RawQuestion
from app.models.question import Question, QuestionType, Difficulty
from app.models.hierarchy import Book, Chapter, Topic


class JobListFilters(BaseModel):
    """
    Filters for listing extraction jobs.
    
    Supports filtering by:
    - stage: Extraction job stage (queued, validation, upload, extraction, completed, failed)
    - grade_level: Grade level (7, 8, 9, 10)
    
    Requirements: 1.3, 1.4
    """
    stage: Optional[ExtractionStage] = None
    grade_level: Optional[int] = None

    @field_validator('grade_level')
    @classmethod
    def validate_grade_level(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in [7, 8, 9, 10]:
            raise ValueError('grade_level must be in [7, 8, 9, 10]')
        return v


class JobListSort(BaseModel):
    """
    Sorting configuration for extraction jobs list.
    
    Supports sorting by:
    - created_at: Job creation timestamp
    - completed_at: Job completion timestamp
    - questions_extracted: Number of questions extracted
    
    Requirements: 1.5
    """
    field: str = Field(..., description="Sort field: 'created_at', 'completed_at', or 'questions_extracted'")
    order: str = Field(default="desc", description="Sort order: 'asc' or 'desc'")

    @field_validator('field')
    @classmethod
    def validate_field(cls, v: str) -> str:
        valid_fields = ['created_at', 'completed_at', 'questions_extracted']
        if v not in valid_fields:
            raise ValueError(f'field must be one of {valid_fields}')
        return v

    @field_validator('order')
    @classmethod
    def validate_order(cls, v: str) -> str:
        if v not in ['asc', 'desc']:
            raise ValueError("order must be 'asc' or 'desc'")
        return v


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    
    Requirements: 1.1, 11.7
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")


class QuestionUpdateRequest(BaseModel):
    """
    Request model for updating a raw question.
    
    Allows updating:
    - question_text: The question content
    - options: List of answer options
    - chapter_context: Chapter context for hierarchy mapping
    - topic_context: Topic context for hierarchy mapping
    - sub_topic_context: Sub-topic context
    - page_number: Page number in the source PDF
    
    Requirements: 3.2, 3.3, 3.4
    """
    question_text: Optional[str] = Field(None, min_length=1, description="Question text (non-empty)")
    options: Optional[List[str]] = Field(None, min_items=2, description="List of options (at least 2)")
    chapter_context: Optional[str] = Field(None, description="Chapter context for hierarchy mapping")
    topic_context: Optional[str] = Field(None, description="Topic context for hierarchy mapping")
    sub_topic_context: Optional[str] = None
    page_number: Optional[int] = Field(None, ge=1, description="Page number in source PDF")

    @field_validator('options')
    @classmethod
    def validate_options(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) < 2:
                raise ValueError('options must have at least 2 items')
            if any(not opt or not isinstance(opt, str) for opt in v):
                raise ValueError('all options must be non-empty strings')
        return v


class ManualRawQuestionItem(BaseModel):
    """One raw question row for manual bulk import (matches raw_questions shape)."""

    question_number: str = Field(..., min_length=1)
    question_text: str = Field(..., min_length=1)
    options: List[str] = Field(default_factory=list)
    page_number: Optional[int] = Field(default=None, ge=1)
    chapter_context: Optional[str] = None
    topic_context: Optional[str] = None
    sub_topic_context: Optional[str] = None
    raw_images: Optional[List[Dict[str, Any]]] = None
    raw_tables: Optional[List[Dict[str, Any]]] = None


class ManualImportRequest(BaseModel):
    """Create a completed extraction job and bulk-insert raw_questions (no PDF pipeline)."""

    book_id: UUID
    job_title: Optional[str] = Field(None, description="Display name in job list")
    questions: List[ManualRawQuestionItem] = Field(..., min_length=1, max_length=10000)


class ManualImportResponse(BaseModel):
    job_id: UUID
    questions_created: int


class FinalizeRequest(BaseModel):
    """
    Request model for finalizing one or more raw questions.
    
    Requirements: 5.1, 9.1
    """
    question_ids: List[UUID] = Field(..., min_items=1, description="List of raw question IDs to finalize")


class BulkDeleteRequest(BaseModel):
    """Bulk delete raw questions by id."""

    question_ids: List[UUID] = Field(..., min_length=1)


class BulkOperationResult(BaseModel):
    """
    Response model for bulk operations (finalize, delete).
    
    Contains:
    - successful: List of IDs that succeeded
    - failed: List of failed operations with error details
    - total: Total number of items processed
    - success_count: Number of successful operations
    - failure_count: Number of failed operations
    
    Requirements: 9.4
    """
    successful: List[UUID] = Field(default_factory=list, description="IDs of successfully processed items")
    failed: List[Dict[str, Any]] = Field(default_factory=list, description="Failed items with error details")
    total: int = Field(..., description="Total number of items processed")
    success_count: int = Field(..., description="Number of successful operations")
    failure_count: int = Field(..., description="Number of failed operations")


class QuestionFilters(BaseModel):
    """
    Filters for searching and filtering raw questions.
    
    Supports filtering by:
    - processing_status: pending, tagged, error
    - chapter_context: Chapter name
    - topic_context: Topic name
    - page_number_min: Minimum page number
    - page_number_max: Maximum page number
    - search_query: Full-text search on question_text
    
    Requirements: 11.2, 11.3, 11.4, 11.5, 11.6
    """
    processing_status: Optional[ProcessingStatus] = None
    chapter_context: Optional[str] = None
    topic_context: Optional[str] = None
    page_number_min: Optional[int] = Field(None, ge=1, description="Minimum page number")
    page_number_max: Optional[int] = Field(None, ge=1, description="Maximum page number")
    search_query: Optional[str] = Field(None, min_length=1, description="Full-text search query")

    @field_validator('page_number_min', 'page_number_max')
    @classmethod
    def validate_page_numbers(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError('page numbers must be >= 1')
        return v


class JobStatistics(BaseModel):
    """
    Statistics for an extraction job.
    
    Contains:
    - total_questions: Total number of raw questions
    - questions_by_status: Count of questions by processing status
    - questions_by_chapter: Distribution of questions across chapters
    - finalization_rate: Percentage of questions that have been finalized
    - average_questions_per_page: Average questions per page
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """
    total_questions: int = Field(default=0, ge=0, description="Total number of raw questions")
    questions_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of questions by processing status (pending, tagged, error)"
    )
    questions_by_chapter: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution of questions across chapters"
    )
    finalization_rate: Decimal = Field(
        default=Decimal('0'),
        ge=0,
        le=100,
        description="Percentage of questions that have been finalized (0-100)"
    )
    average_questions_per_page: Decimal = Field(
        default=Decimal('0'),
        description="Average number of questions per page"
    )


class ChapterWithTopics(BaseModel):
    """
    Response model containing a chapter and its associated topics.
    
    Used in ExtractionJobDetail to provide hierarchical structure.
    
    Requirements: 2.4
    """
    chapter: Chapter
    topics: List[Topic] = Field(default_factory=list, description="Topics within this chapter")


class ExtractionJobDetail(BaseModel):
    """
    Detailed response model for a single extraction job.
    
    Contains:
    - job: The extraction job metadata
    - book: Associated book information
    - hierarchy: Hierarchical structure (chapters and topics)
    - statistics: Aggregate statistics for the job
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    job: ExtractionJob
    book: Optional[Book] = None
    hierarchy: List[ChapterWithTopics] = Field(default_factory=list, description="Hierarchical structure")
    statistics: JobStatistics = Field(default_factory=JobStatistics, description="Job statistics")


class RawQuestionResponse(BaseModel):
    """
    Response model for a raw question with all associated data.
    
    Includes:
    - question: The raw question data
    - images: Associated images
    - tables: Associated tables
    
    Requirements: 2.2, 20.2, 20.3, 20.4
    """
    question: RawQuestion
    images: List[Dict[str, Any]] = Field(default_factory=list, description="Associated images")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="Associated tables")


class ValidationError(BaseModel):
    """
    Model for validation errors in responses.
    
    Requirements: 3.6, 12.6
    """
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code for programmatic handling")


class ValidationErrorResponse(BaseModel):
    """
    Response model for validation errors.
    
    Requirements: 3.6, 12.6, 14.3
    """
    errors: List[ValidationError] = Field(..., description="List of validation errors")
    message: str = Field(default="Validation failed", description="General error message")
