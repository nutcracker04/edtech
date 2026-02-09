
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.database import supabase
from app.utils.auth import get_current_user
from app.services.pyq_service import pyq_service

router = APIRouter(prefix="/api/pyq", tags=["pyq"])

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
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
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
        
    # Delete Questions first (if no cascade)
    supabase.table("pyq_questions").delete().eq("paper_id", str(paper_id)).execute()
    
    # Delete Paper
    res = supabase.table("pyq_papers").delete().eq("id", str(paper_id)).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    return {"message": "Paper deleted successfully"}

@router.delete("/questions/{question_id}")
async def delete_question(question_id: UUID, current_user: dict = Depends(get_current_user)):
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
        
    res = supabase.table("pyq_questions").update(question_data).eq("id", str(question_id)).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Question not found")
    return res.data[0]
