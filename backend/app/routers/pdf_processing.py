"""
API endpoints for PDF processing and question extraction.

This module provides RESTful endpoints for uploading PDFs, tracking processing status,
retrieving results, and validating PDF structure before processing.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os
import uuid
from datetime import datetime

from app.services.pdf_extraction.document_processor import DocumentProcessor
from app.services.pdf_extraction.models import BookMetadata


router = APIRouter(prefix="/api/pdf", tags=["pdf-processing"])

# Initialize document processor
processor = DocumentProcessor()


# Response Models
class UploadResponse(BaseModel):
    """Response for PDF upload endpoint"""
    job_id: str = Field(..., description="Unique job identifier for tracking")
    status: str = Field(..., description="Initial status: 'queued' or 'processing'")
    message: str = Field(..., description="Human-readable status message")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class StatusResponse(BaseModel):
    """Response for status check endpoint"""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current processing stage")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_stage: str = Field(..., description="Current processing stage")
    is_complete: bool = Field(..., description="Whether processing is complete")
    error: Optional[str] = Field(None, description="Error message if failed")
    current_chapter: Optional[str] = Field(None, description="Current chapter being processed")
    current_topic: Optional[str] = Field(None, description="Current topic being processed")
    questions_extracted: int = Field(..., description="Number of questions extracted so far")


class ResultStatistics(BaseModel):
    """Statistics about extraction results"""
    questions_written: int = Field(..., description="Questions successfully written to database")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="Success rate percentage")
    failed_links: int = Field(..., description="Number of failed relationship links")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")


class ResultResponse(BaseModel):
    """Response for result retrieval endpoint"""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Processing status")
    statistics: Optional[ResultStatistics] = Field(None, description="Extraction statistics")
    error: Optional[str] = Field(None, description="Error message if failed")


class ValidationResponse(BaseModel):
    """Response for PDF validation endpoint"""
    is_valid: bool = Field(..., description="Whether PDF structure is valid")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Structure confidence score")
    chapter_count: int = Field(..., description="Number of detected chapters")
    errors: List[str] = Field(default_factory=list, description="Validation errors if any")


# Helper function to save uploaded file
def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """Save uploaded file to destination path"""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "wb") as buffer:
        content = upload_file.file.read()
        buffer.write(content)


# Background task for processing PDF
def process_pdf_background(job_id: str, pdf_path: str, metadata: BookMetadata) -> None:
    """Background task to process PDF"""
    try:
        processor.process_pdf(pdf_path, metadata, job_id=job_id)
    except Exception as e:
        # Error is already logged and stored in processor
        pass


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF file to process"),
    title: str = Form(..., description="Book title"),
    subject: str = Form(..., description="Subject: Physics, Chemistry, or Mathematics"),
    grade_level: str = Form(..., description="Grade level (1-12)"),
    publisher: str = Form(..., description="Publisher name"),
    edition: Optional[str] = Form(None, description="Edition information"),
    isbn: Optional[str] = Form(None, description="ISBN number")
):
    """
    Upload a PDF file for question extraction.
    
    This endpoint accepts a PDF file along with metadata and starts an asynchronous
    processing job. Returns a job ID that can be used to track progress and retrieve results.
    
    **File Requirements:**
    - Must be a valid PDF file
    - Maximum size: 100MB
    - Must contain structured educational content
    
    **Processing:**
    - Processing happens asynchronously in the background
    - Use the returned job_id to check status via /api/pdf/status/{job_id}
    - Results can be retrieved via /api/pdf/result/{job_id} when complete
    """
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Validate file size (100MB limit)
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 100MB (got {file_size / 1024 / 1024:.2f}MB)"
        )
    
    # Create metadata object
    try:
        metadata = BookMetadata(
            title=title,
            subject=subject,
            grade_level=grade_level,
            publisher=publisher,
            edition=edition,
            isbn=isbn
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid metadata: {str(e)}"
        )
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    upload_dir = "backend/data/uploads"
    pdf_path = os.path.join(upload_dir, f"{job_id}.pdf")
    
    try:
        save_upload_file(file, pdf_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )
    
    # Start background processing
    background_tasks.add_task(process_pdf_background, job_id, pdf_path, metadata)
    
    return UploadResponse(
        job_id=job_id,
        status="queued",
        message="PDF uploaded successfully and queued for processing",
        uploaded_at=datetime.utcnow()
    )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_processing_status(job_id: str):
    """
    Get the processing status of a PDF extraction job.
    
    Returns the current status, progress percentage, and current processing stage.
    
    **Status Values:**
    - `queued`: Job is waiting to start
    - `processing`: Job is currently being processed
    - `completed`: Job completed successfully
    - `failed`: Job failed with errors
    
    **Progress:**
    - 0-100: Percentage of completion
    - Progress is updated as the job moves through different stages
    """
    status_info = processor.get_processing_status(job_id)
    
    if status_info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return StatusResponse(
        job_id=job_id,
        status=status_info.current_stage.value,
        progress=status_info.progress,
        current_stage=status_info.current_stage.value,
        is_complete=status_info.is_complete,
        error=status_info.error,
        current_chapter=status_info.current_chapter,
        current_topic=status_info.current_topic,
        questions_extracted=status_info.questions_extracted
    )


@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_processing_result(job_id: str):
    """
    Get the results of a completed PDF extraction job.
    
    Returns statistics about the extraction process and a list of extracted question IDs.
    
    **Note:** This endpoint only returns results for completed jobs.
    For jobs that are still processing, use /api/pdf/status/{job_id} instead.
    """
    result = processor.get_result(job_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found or not yet completed"
        )
    
    # Build statistics if job was successful
    statistics = None
    
    if result.success:
        statistics = ResultStatistics(
            questions_written=result.questions_written,
            success_rate=result.success_rate,
            failed_links=result.failed_links,
            processing_time_seconds=result.processing_time_seconds
        )
    
    return ResultResponse(
        job_id=job_id,
        status="completed" if result.success else "failed",
        statistics=statistics,
        error=result.error if not result.success else None
    )


@router.post("/validate", response_model=ValidationResponse)
async def validate_pdf_structure(
    file: UploadFile = File(..., description="PDF file to validate")
):
    """
    Validate PDF structure before processing.
    
    This endpoint analyzes the PDF structure to determine if it's suitable for
    question extraction. It returns a confidence score and detected chapter count.
    
    **Use this endpoint to:**
    - Check if a PDF is suitable for processing before uploading
    - Get an estimate of the document structure
    - Identify potential issues early
    
    **Validation Criteria:**
    - Structure confidence >= 0.7 is considered valid
    - At least one chapter must be detected
    - PDF must have recognizable structure (chapters, topics, sections)
    """
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF"
        )
    
    # Save temporary file for validation
    temp_id = str(uuid.uuid4())
    temp_dir = "backend/data/temp"
    temp_path = os.path.join(temp_dir, f"{temp_id}.pdf")
    
    try:
        save_upload_file(file, temp_path)
        
        # Validate structure
        validation_result = processor.validate_pdf_structure(temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            confidence=validation_result.confidence,
            chapter_count=validation_result.chapter_count,
            errors=validation_result.errors
        )
    
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
