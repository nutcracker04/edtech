from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.utils.auth import get_current_user
from app.database import supabase
from app.models.repository import (
    Subject, SubjectCreate,
    Chapter, ChapterCreate,
    Topic, TopicCreate,
    RepositoryQuestion, RepositoryQuestionCreate,
    QuestionTagRequest
)

router = APIRouter(prefix="/api/repository", tags=["repository"])

# --- Subjects ---

@router.get("/subjects", response_model=List[Subject])
async def get_subjects():
    result = supabase.table("subjects").select("*").execute()
    return result.data

@router.post("/subjects", response_model=Subject)
async def create_subject(subject: SubjectCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = supabase.table("subjects").insert(subject.model_dump()).execute()
    return result.data[0]

# --- Chapters ---

@router.get("/chapters", response_model=List[Chapter])
async def get_chapters(subject_id: Optional[UUID] = None):
    query = supabase.table("chapters").select("*")
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    result = query.execute()
    return result.data

@router.post("/chapters", response_model=Chapter)
async def create_chapter(chapter: ChapterCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = supabase.table("chapters").insert(chapter.model_dump()).execute()
    return result.data[0]

# --- Topics ---

@router.get("/topics", response_model=List[Topic])
async def get_topics(chapter_id: Optional[UUID] = None):
    query = supabase.table("topics").select("*")
    if chapter_id:
        query = query.eq("chapter_id", str(chapter_id))
    result = query.execute()
    return result.data

@router.post("/topics", response_model=Topic)
async def create_topic(topic: TopicCreate, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = supabase.table("topics").insert(topic.model_dump()).execute()
    return result.data[0]

# --- Questions ---

@router.get("/questions/untagged", response_model=List[RepositoryQuestion])
async def get_untagged_questions(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = supabase.table("repository_questions").select("*").eq("is_tagged", False).execute()
    return result.data

@router.get("/questions/tagged", response_model=List[RepositoryQuestion])
async def get_tagged_questions(
    subject_id: Optional[UUID] = None,
    chapter_id: Optional[UUID] = None,
    topic_id: Optional[UUID] = None
):
    query = supabase.table("repository_questions").select("*").eq("is_tagged", True)
    if subject_id:
        query = query.eq("subject_id", str(subject_id))
    if chapter_id:
        query = query.eq("chapter_id", str(chapter_id))
    if topic_id:
        query = query.eq("topic_id", str(topic_id))
    
    result = query.execute()
    return result.data

@router.post("/questions/tag/{question_id}")
async def tag_question(
    question_id: UUID,
    tag_data: QuestionTagRequest,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = {
        "subject_id": str(tag_data.subject_id),
        "chapter_id": str(tag_data.chapter_id),
        "topic_id": str(tag_data.topic_id),
        "is_tagged": True,
        "updated_at": datetime.utcnow().isoformat()
    }
    if tag_data.difficulty_level:
        update_data["difficulty_level"] = tag_data.difficulty_level
        
    result = supabase.table("repository_questions").update(update_data).eq("id", str(question_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Question not found")
        
    return {"message": "Question tagged successfully", "question": result.data[0]}

@router.post("/questions/bulk-import-from-upload/{upload_id}")
async def import_questions_from_upload(
    upload_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get the upload record
    upload_result = supabase.table("uploaded_tests").select("*").eq("id", str(upload_id)).execute()
    if not upload_result.data:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    upload = upload_result.data[0]
    questions = upload.get("extracted_questions", [])
    
    if not questions:
        raise HTTPException(status_code=400, detail="No questions found in this upload")
    
    repo_questions = []
    for q in questions:
        repo_questions.append({
            "question_text": q.get("question_text"),
            "options": q.get("options", []),
            "correct_answer": q.get("correct_answer"),
            "source_paper_id": str(upload_id),
            "is_tagged": False
        })
    
    if repo_questions:
        supabase.table("repository_questions").insert(repo_questions).execute()
        
    return {"message": f"Successfully imported {len(repo_questions)} questions to untagged repository"}

@router.post("/questions/manual")
async def create_manual_question(
    question_data: RepositoryQuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a question manually (text-based input)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    question_dict = question_data.model_dump()
    question_dict["is_tagged"] = False
    question_dict["source_paper_id"] = None
    
    result = supabase.table("repository_questions").insert(question_dict).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create question")
    
    return {"message": "Question created successfully", "question": result.data[0]}

