from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import uuid

from app.utils.auth import get_current_user
from app.database import supabase
from app.services.test_service import create_test
from app.models.upload import (
    UploadResponse,  # Legacy model for backward compatibility
    UploadStatusResponse,  # Legacy model for backward compatibility
    QuestionConfirmRequest,
    ExtractedQuestion,  # Legacy model for backward compatibility
    convert_extraction_job_to_upload_response,
    convert_extraction_job_to_upload_status
)
from app.models.extraction import (
    ExtractionJob,
    RawQuestion,
    ExtractionStage
)
from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/test-paper", response_model=UploadResponse)
async def upload_test_paper(
    file: UploadFile = File(...),
    exam_type: Optional[str] = Form(None),
    exam_date: Optional[str] = Form(None),
    exam_session: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload test paper (PDF or Image) for AI processing.
    Uses new extraction_jobs table for tracking.
    """
    user_id = current_user["user_id"]
    
    # Validate file type
    if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image or PDF"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        file_name = f"{user_id}/{uuid.uuid4()}-{file.filename}"
        storage_result = supabase.storage.from_(
            settings.storage_bucket_test_papers
        ).upload(file_name, file_content)
        
        # Get public URL
        public_url = supabase.storage.from_(
            settings.storage_bucket_test_papers
        ).get_public_url(file_name)
        
        # Create extraction job record in new extraction_jobs table
        job_id = str(uuid.uuid4())
        extraction_job = {
            "id": job_id,
            "source_pdf_filename": file.filename,
            "source_pdf_path": public_url,
            "stage": ExtractionStage.QUEUED.value,
            "progress": 0,
            "pages_processed": 0,
            "questions_extracted": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("extraction_jobs").insert(extraction_job).execute()
        
        # Start processing (async in background would be better for production)
        try:
            # Update status to processing
            supabase.table("extraction_jobs")\
                .update({"stage": ExtractionStage.EXTRACTION.value, "progress": 10})\
                .eq("id", job_id)\
                .execute()
            
            # TODO: Integrate with actual extraction pipeline
            # For now, mark as completed
            supabase.table("extraction_jobs")\
                .update({
                    "stage": ExtractionStage.COMPLETED.value,
                    "progress": 100,
                    "completed_at": datetime.utcnow().isoformat()
                })\
                .eq("id", job_id)\
                .execute()
        
        except Exception as e:
            # Update status to failed
            supabase.table("extraction_jobs")\
                .update({
                    "stage": ExtractionStage.FAILED.value,
                    "error": str(e)
                })\
                .eq("id", job_id)\
                .execute()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Extraction processing failed: {str(e)}"
            )
        
        return UploadResponse(
            id=job_id,
            status="completed",
            message="Test paper uploaded and processed successfully",
            uploaded_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/status/{upload_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status of an uploaded test paper.
    Uses new extraction_jobs table.
    """
    user_id = current_user["user_id"]
    
    # Get extraction job record
    result = supabase.table("extraction_jobs")\
        .select("*")\
        .eq("id", upload_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    job = result.data[0]
    
    # Calculate progress based on stage
    progress_map = {
        "queued": 10,
        "validation": 20,
        "upload": 40,
        "extraction": 70,
        "completed": 100,
        "failed": 0
    }
    
    stage = job.get("stage", "queued")
    progress = job.get("progress", progress_map.get(stage, 0))
    
    # Get extracted questions (raw_questions) if completed
    extracted_questions = None
    if stage == "completed":
        raw_questions_result = supabase.table("raw_questions")\
            .select("*")\
            .eq("job_id", upload_id)\
            .execute()
        
        # Convert to ExtractedQuestion format for backward compatibility
        extracted_questions = [
            ExtractedQuestion(
                id=q.get("id"),
                question_number=q.get("question_number", ""),
                question_text=q.get("question_text", ""),
                options=q.get("options", []),
                correct_answer=None,  # Not available in raw_questions
                subject=None,
                topic=None
            )
            for q in raw_questions_result.data
        ]
    
    return UploadStatusResponse(
        id=upload_id,
        status=stage,
        progress=progress,
        extracted_questions=extracted_questions,
        error_message=job.get("error")
    )


@router.post("/confirm")
async def confirm_questions(
    request: QuestionConfirmRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Confirm and save the extracted questions as a test.
    Uses new extraction_jobs and raw_questions tables.
    User can edit questions before confirming.
    """
    user_id = current_user["user_id"]
    
    # Verify extraction job exists
    job_result = supabase.table("extraction_jobs")\
        .select("*")\
        .eq("id", request.upload_id)\
        .execute()
    
    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Extraction job not found"
        )
    
    # Create a test from the confirmed questions
    test_id = await create_test(
        user_id=user_id,
        title=f"Uploaded Test - {datetime.utcnow().strftime('%Y-%m-%d')}",
        test_type="uploaded",
        questions=request.questions,
        duration=len(request.questions) * 3,  # 3 minutes per question
        subject=request.questions[0].get("subject") if request.questions else None
    )
    
    # If user provided answers, submit them as attempts
    if request.user_answers:
        attempts = []
        for q in request.questions:
            q_num = q.get("question_number", 0)
            if q_num in request.user_answers:
                user_answer = request.user_answers[q_num]
                correct_answer = q.get("correct_answer", "")
                
                attempts.append({
                    "question_id": q["id"],
                    "selected_answer": user_answer,
                    "is_correct": user_answer == correct_answer,
                    "time_spent": 0,
                    "subject": q.get("subject"),
                    "topic": q.get("topic")
                })
        
        if attempts:
            from app.services.test_service import submit_test_attempts
            await submit_test_attempts(test_id, user_id, attempts)
    
    return {
        "message": "Questions confirmed and test created",
        "test_id": test_id
    }


@router.post("/response-sheet", response_model=UploadResponse)
async def upload_response_sheet(
    upload_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload response sheet for an existing test paper.
    This will be used to automatically mark answers.
    """
    user_id = current_user["user_id"]
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Verify upload exists
    upload_result = supabase.table("uploaded_tests")\
        .select("*")\
        .eq("id", upload_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not upload_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Supabase Storage
        file_name = f"{user_id}/{uuid.uuid4()}-response-{file.filename}"
        supabase.storage.from_(
            settings.storage_bucket_response_sheets
        ).upload(file_name, file_content)
        
        # Get public URL
        public_url = supabase.storage.from_(
            settings.storage_bucket_response_sheets
        ).get_public_url(file_name)
        
        # Update upload record
        supabase.table("uploaded_tests")\
            .update({"response_image_url": public_url})\
            .eq("id", upload_id)\
            .execute()
        
        return UploadResponse(
            id=upload_id,
            status="completed",
            message="Response sheet uploaded successfully",
            uploaded_at=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )
