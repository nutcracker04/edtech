from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
from datetime import datetime
import uuid

from app.utils.auth import get_current_user
from app.database import supabase
from app.services.ocr_service import extract_questions_from_image, classify_question_subject
from app.services.question_parser import parse_ocr_text_to_questions
from app.services.test_service import create_test
from app.models.upload import (
    UploadResponse,
    UploadStatusResponse,
    QuestionConfirmRequest,
    ExtractedQuestion
)
from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/test-paper", response_model=UploadResponse)
async def upload_test_paper(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload test paper image for OCR processing.
    """
    user_id = current_user["user_id"]
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
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
        
        # Create upload record
        upload_record = {
            "user_id": user_id,
            "test_image_url": public_url,
            "processing_status": "pending",
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("uploaded_tests").insert(upload_record).execute()
        upload_id = result.data[0]["id"]
        
        # Start OCR processing (async in background would be better for production)
        try:
            # Update status to processing
            supabase.table("uploaded_tests")\
                .update({"processing_status": "processing"})\
                .eq("id", upload_id)\
                .execute()
            
            # Extract questions
            extracted_questions = await extract_questions_from_image(file_content)
            
            # Classify subjects
            for question in extracted_questions:
                if not question.subject:
                    question.subject = await classify_question_subject(question.question_text)
            
            # Update record with extracted questions
            supabase.table("uploaded_tests")\
                .update({
                    "extracted_questions": [q.model_dump() for q in extracted_questions],
                    "processing_status": "completed",
                    "processed_at": datetime.utcnow().isoformat()
                })\
                .eq("id", upload_id)\
                .execute()
        
        except Exception as e:
            # Update status to failed
            supabase.table("uploaded_tests")\
                .update({
                    "processing_status": "failed",
                    "error_message": str(e)
                })\
                .eq("id", upload_id)\
                .execute()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OCR processing failed: {str(e)}"
            )
        
        return UploadResponse(
            id=upload_id,
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
    """
    user_id = current_user["user_id"]
    
    # Get upload record
    result = supabase.table("uploaded_tests")\
        .select("*")\
        .eq("id", upload_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    record = result.data[0]
    
    # Calculate progress
    progress_map = {
        "pending": 10,
        "processing": 50,
        "completed": 100,
        "failed": 0
    }
    
    extracted_questions = None
    if record["processing_status"] == "completed":
        extracted_questions = [
            ExtractedQuestion(**q) for q in record["extracted_questions"]
        ]
    
    return UploadStatusResponse(
        id=upload_id,
        status=record["processing_status"],
        progress=progress_map.get(record["processing_status"], 0),
        extracted_questions=extracted_questions,
        error_message=record.get("error_message")
    )


@router.post("/confirm")
async def confirm_questions(
    request: QuestionConfirmRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Confirm and save the extracted questions as a test.
    User can edit questions before confirming.
    """
    user_id = current_user["user_id"]
    
    # Verify upload belongs to user
    upload_result = supabase.table("uploaded_tests")\
        .select("*")\
        .eq("id", request.upload_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not upload_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
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
