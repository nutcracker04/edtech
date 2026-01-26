from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ParseQuestionsRequest(BaseModel):
    text: str


class QuestionOption(BaseModel):
    id: str
    text: str


class ParsedQuestion(BaseModel):
    question_text: str
    options: List[QuestionOption]
    correct_answer: str
    difficulty_level: str
    subject: str | None = None
    chapter: str | None = None
    topic: str | None = None


class ParseQuestionsResponse(BaseModel):
    questions: List[ParsedQuestion]
    count: int


@router.post("/parse-questions", response_model=ParseQuestionsResponse)
async def parse_questions(
    request: ParseQuestionsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Parse multiple-choice questions from raw text using AI.
    
    Accepts text in various formats and returns structured questions with tag suggestions.
    """
    if not ai_service:
        raise HTTPException(
            status_code=503,
            detail="AI service not configured. Please set GROQ_API_KEY."
        )
    
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text content is required"
        )
    
    try:
        questions = ai_service.parse_questions_from_text(request.text)
        
        return ParseQuestionsResponse(
            questions=questions,
            count=len(questions)
        )
        
    except Exception as e:
        print(f"Error in parse_questions endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse questions: {str(e)}"
        )


@router.get("/tag-hierarchy")
async def get_tag_hierarchy(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the complete tag hierarchy with IDs for mapping AI suggestions.
    
    Returns subjects, chapters, and topics with their IDs and relationships.
    """
    if not ai_service:
        raise HTTPException(
            status_code=503,
            detail="AI service not configured."
        )
    
    try:
        # Get hierarchy with IDs
        hierarchy = ai_service.get_tag_hierarchy_with_ids()
        
        return {
            "hierarchy": hierarchy,
            "count": {
                "subjects": len(hierarchy),
                "chapters": sum(len(s["chapters"]) for s in hierarchy.values()),
                "topics": sum(
                    len(c["topics"]) 
                    for s in hierarchy.values() 
                    for c in s["chapters"].values()
                )
            }
        }
        
    except Exception as e:
        print(f"Error fetching tag hierarchy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tag hierarchy: {str(e)}"
        )
