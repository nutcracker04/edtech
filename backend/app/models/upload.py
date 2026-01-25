from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ExtractedQuestion(BaseModel):
    question_number: int
    question_text: str
    options: List[Dict[str, str]]  # [{"id": "A", "text": "..."}, ...]
    confidence: float  # OCR confidence score
    subject: Optional[str] = None
    topic: Optional[str] = None


class UploadResponse(BaseModel):
    id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    message: str
    uploaded_at: datetime


class UploadedTest(BaseModel):
    id: str
    user_id: str
    test_image_url: str
    response_image_url: Optional[str] = None
    extracted_questions: List[ExtractedQuestion]
    processing_status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


class QuestionConfirmRequest(BaseModel):
    upload_id: str
    questions: List[Dict[str, Any]]  # Confirmed/edited questions
    user_answers: Optional[Dict[int, str]] = None  # Question number -> selected answer


class UploadStatusResponse(BaseModel):
    id: str
    status: str
    progress: int  # 0-100
    extracted_questions: Optional[List[ExtractedQuestion]] = None
    error_message: Optional[str] = None
