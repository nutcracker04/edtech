"""
Admin Extractions Router

This module provides REST API endpoints for managing book extraction jobs,
reviewing extracted content, and finalizing questions into the main repository.

The router is organized under the /admin/extractions prefix and includes:
- Extraction job listing and details
- Raw question CRUD operations
- Question finalization workflow
- Bulk operations (finalize, delete)
- Data export functionality
- Statistics and search capabilities

Requirements: 8.1, 8.2, 8.3, 1.1-1.5, 2.1-2.5, 3.1-3.6, 4.1-4.5, 5.1-5.10,
9.1-9.6, 10.1-10.5, 11.1-11.7, 14.1-14.5, 35.1-35.5
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse
from typing import Optional, List
from uuid import UUID
import logging

from app.database import get_supabase
from app.services.extraction_service import ExtractionService
from app.services.staging_finalization_service import StagingFinalizationService
from app.services.validation import QuestionValidator
from app.models.admin import (
    JobListFilters,
    JobListSort,
    PaginationParams,
    QuestionUpdateRequest,
    FinalizeRequest,
    BulkOperationResult,
    BulkDeleteRequest,
    ReviewStatusBatchRequest,
    QuestionFilters,
    ExtractionJobDetail,
    RawQuestionResponse,
    ValidationErrorResponse,
    ManualImportRequest,
    ManualImportResponse,
)
from app.models.extraction import ExtractionJob, RawQuestion, ProcessingStatus
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class QuestionsListResponse(BaseModel):
    questions: List[RawQuestion]
    total: int

# Create router with /extractions prefix (will be registered under /admin in main.py)
router = APIRouter(
    prefix="/extractions",
    tags=["admin-extractions"],
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    }
)


# ============================================================================
# Dependencies
# ============================================================================

async def verify_admin_token():
    """
    Verify admin authentication token.
    
    This is a placeholder for authentication verification.
    In production, this would validate JWT tokens and check admin permissions.
    
    Requirements: 8.2, 8.3
    """
    # TODO: Implement actual token verification
    # For now, this is a pass-through that allows all requests
    return True


async def get_extraction_service(db_client=Depends(get_supabase)):
    """
    Dependency injection for ExtractionService.
    
    Requirements: 8.3
    """
    return ExtractionService(db_client)


async def get_staging_finalization_service(db_client=Depends(get_supabase)):
    """Finalize staging rows into canonical questions via Supabase."""
    return StagingFinalizationService(db_client)


# ============================================================================
# Manual import (no PDF) — register before /{job_id} routes
# ============================================================================

@router.get(
    "/import/books",
    summary="List books for manual question import",
    description="Returns extraction_books if present, otherwise canonical books.",
)
async def list_books_for_import(
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        return service.list_books_for_manual_import()
    except Exception as e:
        logger.error("list_books_for_import: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list books")


@router.get(
    "/import/books/{book_id}/outline",
    summary="Chapter and topic titles for import JSON",
)
async def get_book_outline_for_import(
    book_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        return service.get_book_outline_for_import(book_id)
    except Exception as e:
        logger.error("get_book_outline_for_import: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load outline")


@router.post(
    "/import/manual",
    response_model=ManualImportResponse,
    summary="Bulk-create raw questions from manual data",
    description="Creates a completed extraction job linked to the book and inserts all raw_questions.",
)
async def create_manual_import(
    body: ManualImportRequest,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        job_id, n = await service.create_manual_import_job(
            body.book_id,
            body.job_title,
            body.questions,
        )
        return ManualImportResponse(job_id=job_id, questions_created=n)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("create_manual_import: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create manual import",
        )


# ============================================================================
# Extraction Job Endpoints (4.2)
# ============================================================================

@router.get(
    "",
    response_model=List[ExtractionJob],
    summary="List extraction jobs",
    description="Retrieve all extraction jobs with optional filtering, sorting, and pagination"
)
async def list_extraction_jobs(
    stage: Optional[str] = Query(None, description="Filter by stage"),
    grade_level: Optional[int] = Query(None, description="Filter by grade level (7, 8, 9, 10)"),
    sort_field: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    List all extraction jobs with filtering, sorting, and pagination.
    
    Query Parameters:
    - stage: Filter by extraction stage (queued, validation, upload, extraction, completed, failed)
    - grade_level: Filter by grade level (7, 8, 9, 9, 10)
    - sort_field: Sort by 'created_at', 'completed_at', or 'questions_extracted'
    - sort_order: Sort order 'asc' or 'desc'
    - page: Page number (1-indexed)
    - page_size: Items per page (1-100)
    
    Returns:
    - List of ExtractionJob objects
    
    HTTP Status Codes:
    - 200: Success
    - 400: Invalid parameters
    - 500: Server error
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4, 10.5, 14.1, 14.2, 14.5
    """
    try:
        filters = JobListFilters(stage=stage, grade_level=grade_level)
        sort = JobListSort(field=sort_field, order=sort_order)
        pagination = PaginationParams(page=page, page_size=page_size)
        
        jobs, total = service.list_jobs(filters, sort, pagination)
        logger.info(f"Retrieved {len(jobs)} jobs (total: {total})")
        return jobs
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing extraction jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve extraction jobs"
        )


@router.get(
    "/{job_id}",
    response_model=ExtractionJobDetail,
    summary="Get extraction job details",
    description="Retrieve detailed information about a specific extraction job"
)
async def get_extraction_job_details(
    job_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Get detailed information about a specific extraction job.
    
    Path Parameters:
    - job_id: UUID of the extraction job
    
    Returns:
    - ExtractionJobDetail object with job metadata, book info, hierarchy, and statistics
    
    HTTP Status Codes:
    - 200: Success
    - 404: Job not found
    - 500: Server error
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4, 10.5, 14.1, 14.2, 14.5
    """
    try:
        job_detail = await service.get_job_details(job_id)
        if not job_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found"
            )
        return job_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job details for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job details"
        )


@router.get(
    "/{job_id}/extracted-content",
    summary="Get extracted markdown content",
    description="Retrieve the extracted markdown content from Supabase storage for a completed job",
)
async def get_extracted_content(
    job_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    db_client=Depends(get_supabase),
):
    """
    Get the extracted markdown content (combined.md) for an extraction job.
    Content is stored in Supabase extraction-artifacts bucket.
    """
    try:
        job_result = db_client.table("extraction_jobs").select("extracted_path, stage").eq("id", str(job_id)).execute()
        if not job_result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        
        extracted_path = job_result.data[0].get("extracted_path")
        if not extracted_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No extracted content found. Content may still be processing or was not uploaded.",
            )
        
        # Supabase path format: job_id/combined.md (no leading slash, no absolute path)
        if extracted_path.startswith("/") or "\\" in extracted_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extracted content is stored locally. Re-run extraction to store in Supabase.",
            )
        storage_path = extracted_path if extracted_path.endswith(".md") else f"{extracted_path}/combined.md"
        
        from app.services.storage_manager import StorageManager
        storage = StorageManager(db_client)
        content = storage.get_extracted_content(storage_path)
        
        if content is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extracted content not found in storage",
            )
        
        return {"content": content, "job_id": str(job_id)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extracted content for {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve extracted content",
        )


@router.get(
    "/{job_id}/stats",
    summary="Get extraction job statistics",
    description="Retrieve statistics for a specific extraction job"
)
async def get_extraction_job_stats(
    job_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Get statistics for a specific extraction job.
    
    Path Parameters:
    - job_id: UUID of the extraction job
    
    Returns:
    - JobStatistics object with aggregated data
    
    HTTP Status Codes:
    - 200: Success
    - 404: Job not found
    - 500: Server error
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 14.1, 14.2, 14.5
    """
    try:
        stats = await service.get_job_statistics(job_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found"
            )
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving stats for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job statistics"
        )


@router.delete(
    "/{job_id}",
    summary="Delete an extraction job",
    description="Delete an extraction job and all associated data"
)
async def delete_extraction_job(
    job_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Delete an extraction job and all associated data (raw questions, pages, blocks).
    
    Path Parameters:
    - job_id: UUID of the extraction job
    
    Returns:
    - Success message
    
    HTTP Status Codes:
    - 200: Success
    - 404: Job not found
    - 500: Server error
    """
    try:
        success = await service.delete_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found"
            )
        return {"message": "Extraction job deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete extraction job"
        )


# ============================================================================
# Raw Question CRUD Endpoints (4.3)
# ============================================================================

@router.get(
    "/{job_id}/questions",
    response_model=QuestionsListResponse,
    summary="List raw questions for a job",
    description="Retrieve all raw questions for a specific extraction job with pagination total"
)
async def list_raw_questions(
    job_id: UUID,
    processing_status: Optional[str] = Query(None, description="Filter by status"),
    chapter_context: Optional[str] = Query(None, description="Filter by chapter"),
    topic_context: Optional[str] = Query(None, description="Filter by topic"),
    page_number_min: Optional[int] = Query(None, ge=1, description="Minimum page number"),
    page_number_max: Optional[int] = Query(None, ge=1, description="Maximum page number"),
    search_query: Optional[str] = Query(None, min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    List raw questions for a specific extraction job with filtering and pagination.
    
    Path Parameters:
    - job_id: UUID of the extraction job
    
    Query Parameters:
    - processing_status: Filter by status (pending, tagged, error)
    - chapter_context: Filter by chapter context
    - topic_context: Filter by topic context
    - page_number_min: Minimum page number
    - page_number_max: Maximum page number
    - search_query: Full-text search query
    - page: Page number (1-indexed)
    - page_size: Items per page (1-100)
    
    Returns:
    - List of RawQuestion objects
    
    HTTP Status Codes:
    - 200: Success
    - 400: Invalid parameters
    - 404: Job not found
    - 500: Server error
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 14.2, 14.3, 14.4
    """
    try:
        filters = QuestionFilters(
            processing_status=processing_status,
            chapter_context=chapter_context,
            topic_context=topic_context,
            page_number_min=page_number_min,
            page_number_max=page_number_max,
            search_query=search_query,
        )
        pagination = PaginationParams(page=page, page_size=page_size)
        
        questions, total = await service.list_questions(job_id, filters, pagination)
        if questions is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extraction job {job_id} not found"
            )
        logger.info(f"Retrieved {len(questions)} questions for job {job_id} (total: {total})")
        return QuestionsListResponse(questions=questions, total=total)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing questions for job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve questions"
        )


@router.put(
    "/questions/{question_id}",
    response_model=RawQuestion,
    summary="Update a raw question",
    description="Update the content of a raw question"
)
async def update_raw_question(
    question_id: UUID,
    updates: QuestionUpdateRequest,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Update a raw question with new content.
    
    Path Parameters:
    - question_id: UUID of the raw question
    
    Request Body:
    - QuestionUpdateRequest with fields to update
    
    Returns:
    - Updated RawQuestion object
    
    HTTP Status Codes:
    - 200: Success
    - 400: Validation error
    - 404: Question not found
    - 409: Conflict (e.g., question already finalized)
    - 500: Server error
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 14.2, 14.3, 14.4
    """
    try:
        # Validate the update request
        validation_result = QuestionValidator.validate_update(updates)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_result.to_dict()
            )
        
        # Perform the update
        updated_question = await service.update_question(question_id, updates)
        if not updated_question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Raw question {question_id} not found"
            )
        return updated_question
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update question"
        )


@router.delete(
    "/questions/{question_id}",
    summary="Delete a raw question",
    description="Delete a raw question and its associated data"
)
async def delete_raw_question(
    question_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Delete a raw question and its associated images and tables.
    
    Path Parameters:
    - question_id: UUID of the raw question
    
    Returns:
    - Success message
    
    HTTP Status Codes:
    - 200: Success
    - 404: Question not found
    - 409: Conflict (question already finalized)
    - 500: Server error
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.2, 4.3, 4.4, 4.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 14.2, 14.3, 14.4
    """
    try:
        success = await service.delete_question(question_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete a finalized question"
            )
        return {"message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete question"
        )


@router.post(
    "/questions/reject-batch",
    response_model=BulkOperationResult,
    summary="Reject staging questions (bulk)",
)
async def reject_questions_batch(
    body: ReviewStatusBatchRequest,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        return await service.bulk_set_review_status(body.question_ids, ProcessingStatus.REJECTED)
    except Exception as e:
        logger.error("reject batch: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject questions")


@router.post(
    "/questions/reinstate-batch",
    response_model=BulkOperationResult,
    summary="Reinstate rejected staging questions (bulk)",
)
async def reinstate_questions_batch(
    body: ReviewStatusBatchRequest,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        return await service.bulk_set_review_status(body.question_ids, ProcessingStatus.PENDING)
    except Exception as e:
        logger.error("reinstate batch: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reinstate questions")


@router.post(
    "/questions/{question_id}/reject",
    response_model=RawQuestion,
    summary="Reject one staging question",
)
async def reject_one_question(
    question_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        q = await service.set_raw_question_review_status(question_id, ProcessingStatus.REJECTED)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        return q
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/questions/{question_id}/reinstate",
    response_model=RawQuestion,
    summary="Reinstate one rejected question to pending",
)
async def reinstate_one_question(
    question_id: UUID,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    try:
        q = await service.set_raw_question_review_status(question_id, ProcessingStatus.PENDING)
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        return q
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Finalization and Bulk Operation Endpoints (4.4)
# ============================================================================

@router.post(
    "/questions/finalize",
    response_model=BulkOperationResult,
    summary="Finalize raw questions",
    description="Finalize one or more raw questions into the main repository"
)
async def finalize_questions(
    request: FinalizeRequest,
    _admin: bool = Depends(verify_admin_token),
    service: StagingFinalizationService = Depends(get_staging_finalization_service),
):
    """
    Finalize one or more raw questions into the main question repository.
    
    Request Body:
    - FinalizeRequest with list of question IDs to finalize
    
    Returns:
    - BulkOperationResult with successful and failed operations
    
    HTTP Status Codes:
    - 200: Success (with partial failures possible)
    - 400: Invalid request
    - 500: Server error
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 35.1, 35.2, 35.3, 35.4, 35.5
    """
    try:
        if not request.question_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one question ID is required"
            )
        
        result = service.bulk_finalize_questions(request.question_ids)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to finalize questions"
        )


@router.post(
    "/questions/bulk-delete",
    response_model=BulkOperationResult,
    summary="Bulk delete raw questions (JSON body)",
    description="Preferred: JSON body with question_ids. DELETE with query params is deprecated.",
)
async def bulk_delete_questions_body(
    request: BulkDeleteRequest,
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    if not request.question_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one question ID is required",
        )
    try:
        return await service.bulk_delete_questions(request.question_ids)
    except Exception as e:
        logger.error(f"Error bulk deleting questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete questions",
        )


@router.delete(
    "/questions/bulk",
    response_model=BulkOperationResult,
    summary="Bulk delete raw questions (query params)",
    description="Delete multiple raw questions. Prefer POST /questions/bulk-delete with JSON body.",
)
async def bulk_delete_questions(
    question_ids: List[UUID] = Query(..., description="List of question IDs to delete"),
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Delete multiple raw questions in a single bulk operation.
    
    Query Parameters:
    - question_ids: List of question IDs to delete
    
    Returns:
    - BulkOperationResult with successful and failed deletions
    
    HTTP Status Codes:
    - 200: Success (with partial failures possible)
    - 400: Invalid request
    - 500: Server error
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 35.1, 35.2, 35.3, 35.4, 35.5
    """
    try:
        if not question_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one question ID is required"
            )
        
        result = await service.bulk_delete_questions(question_ids)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error bulk deleting questions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete questions"
        )


@router.post(
    "/{job_id}/export",
    summary="Export extraction data",
    description="Export extraction job data in various formats"
)
async def export_extraction_data(
    job_id: UUID,
    format: str = Query("csv", description="Export format (csv, json, excel)"),
    _admin: bool = Depends(verify_admin_token),
    service: ExtractionService = Depends(get_extraction_service),
):
    """
    Export extraction job data in the specified format.
    
    Path Parameters:
    - job_id: UUID of the extraction job
    
    Query Parameters:
    - format: Export format (csv, json, excel)
    
    Returns:
    - File download with exported data
    
    HTTP Status Codes:
    - 200: Success
    - 400: Invalid format
    - 404: Job not found
    - 500: Server error
    
    Requirements: 35.1, 35.2, 35.3, 35.4, 35.5
    """
    try:
        valid_formats = ["csv", "json", "excel"]
        if format not in valid_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # TODO: Implement export functionality
        # This would generate and return the file based on the format
        return {
            "message": "Export functionality not yet implemented",
            "job_id": str(job_id),
            "format": format
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting job {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export data"
        )
