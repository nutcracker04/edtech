
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.database import supabase
from app.utils.auth import get_current_user
from app.services.pyq_service import pyq_service

router = APIRouter(prefix="/api/pyq", tags=["pyq"])

@router.get("/hierarchy")
async def get_tag_hierarchy(current_user: dict = Depends(get_current_user)):
    """
    Get the Subject -> Chapter -> Topic hierarchy for filters.
    """
    return pyq_service.get_structured_hierarchy()

@router.get("/questions")
async def get_pyq_questions(
    subject_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get questions filtered by subject, chapter, or topic.
    """
    query = supabase.table("pyq_questions").select("*")
    
    if subject_id:
        query = query.eq("subject_id", subject_id)
        
    if chapter_id:
        # Use array contains for flexible matching if stored as array, 
        # but also check primary column just in case.
        # Ideally, we should unify. Given pyq_service writes both, we can check array 'contains'.
        # However, PostgREST syntax for array contains is `cs`.
        # For simplicity and reliability with `pyq_service` logic (which sets both), checking single column might be faster if indexed?
        # Let's check the array column `chapter_ids` using `cs` filter:
        # query = query.cs("chapter_ids", [chapter_id])
        # BUT pyq_service ALSO sets `chapter_id` (singular). Let's use singular for now as it's simpler.
        query = query.eq("chapter_id", chapter_id)
        
    if topic_id:
        query = query.eq("topic_id", topic_id)
        
    res = query.order("created_at", desc=True).limit(50).execute()
    return res.data


@router.post("/upload")
async def upload_pyq_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    exam_type: str = Form(...),
    exam_date: str = Form(...), # ISO date string
    exam_session: str = Form(...),
    current_user: dict = Depends(get_current_user)
):
    # if current_user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Not authorized")
        
    # Read file content
    content = await file.read()
    
    # Create DB Record in pyq_papers
    paper_data = {
        "exam_type": exam_type,
        "exam_date": exam_date,
        "exam_session": exam_session,
        "processing_status": "pending"
    }
    
    res = supabase.table("pyq_papers").insert(paper_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create paper record")
    
    paper_id = res.data[0]["id"]
    
    # Start Background Processing
    background_tasks.add_task(pyq_service.process_pyq_paper, content, paper_id, paper_data)
    
    return {"message": "Paper uploaded and processing started", "paper_id": paper_id}

@router.get("/papers")
async def get_pyq_papers(current_user: dict = Depends(get_current_user)):
    # if current_user.get("role") != "admin":
    #     raise HTTPException(status_code=403, detail="Not authorized")
        
    res = supabase.table("pyq_papers").select("*").order("created_at", desc=True).execute()
    return res.data

@router.get("/papers/{paper_id}/questions")
async def get_paper_questions(paper_id: UUID, current_user: dict = Depends(get_current_user)):
    # Verify paper exists
    # ...
    
    # Fetch questions
    res = supabase.table("pyq_questions").select("*").eq("paper_id", str(paper_id)).order("question_number").execute()
    return res.data

@router.delete("/papers/{paper_id}")
async def delete_paper(paper_id: UUID, current_user: dict = Depends(get_current_user)):
    # if current_user.get("role") != "admin": # Uncomment when role check is active
    #     raise HTTPException(status_code=403, detail="Not authorized")
        
    # Delete Images from Storage first
    try:
        # Fetch all questions for this paper to get image URLs
        questions_res = supabase.table("pyq_questions").select("image_url").eq("paper_id", str(paper_id)).execute()
        if questions_res.data:
            image_urls = [q["image_url"] for q in questions_res.data if q.get("image_url")]
            if image_urls:
                pyq_service.delete_images_from_storage(image_urls)
    except Exception as e:
        print(f"Error cleaning up images: {e}")
        # Continue with DB deletion even if storage cleanup fails

    # Delete Questions first (if no cascade)
    supabase.table("pyq_questions").delete().eq("paper_id", str(paper_id)).execute()
    
    # Delete Paper
    res = supabase.table("pyq_papers").delete().eq("id", str(paper_id)).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    return {"message": "Paper deleted successfully"}

@router.delete("/questions/{question_id}")
async def delete_question(question_id: UUID, current_user: dict = Depends(get_current_user)):
    # Delete Image from Storage first
    try:
        question_res = supabase.table("pyq_questions").select("image_url").eq("id", str(question_id)).single().execute()
        if question_res.data and question_res.data.get("image_url"):
            pyq_service.delete_images_from_storage([question_res.data["image_url"]])
    except Exception as e:
        print(f"Error cleaning up image: {e}")

    res = supabase.table("pyq_questions").delete().eq("id", str(question_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted"}

class UpdateQuestionRequest(dict):
    pass # Accept any dict for now to be flexible

@router.put("/questions/{question_id}")
async def update_question(question_id: UUID, question_data: dict, current_user: dict = Depends(get_current_user)):
    # Remove id if present to avoid changing PK
    if "id" in question_data:
        del question_data["id"]
        
    # Handle array fields if they exist in payload
    # This basic update works because Supabase/Postgres handles the JSON->Array conversion if the keys match column names
    # But we might need explicit handling if the payload sends them as None or if we need to sync legacy fields
    
    # Sync legacy fields for backward compatibility (optional, but good for safety)
    if "chapter_ids" in question_data and question_data["chapter_ids"] and len(question_data["chapter_ids"]) > 0:
        question_data["chapter_id"] = question_data["chapter_ids"][0]
    
    if "topic_ids" in question_data and question_data["topic_ids"] and len(question_data["topic_ids"]) > 0:
        question_data["topic_id"] = question_data["topic_ids"][0]

    res = supabase.table("pyq_questions").update(question_data).eq("id", str(question_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return res.data[0]
