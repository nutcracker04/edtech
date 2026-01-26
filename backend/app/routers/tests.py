from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.utils.auth import get_current_user
from app.database import supabase
from app.models.test import Test, TestCreateRequest, TestSubmitRequest
from app.services.test_service import create_test, generate_adaptive_test, generate_test, submit_test_attempts

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.get("/", response_model=List[Test])
async def get_user_tests(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tests for the current user.
    Optionally filter by status.
    """
    try:
        user_id = current_user["user_id"]
        
        query = supabase.table("tests").select("*").eq("user_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).execute()
        
        # Ensure questions field is always a list
        if result.data:
            for test in result.data:
                if test.get("questions") is None:
                    test["questions"] = []
        
        return result.data
    except Exception as e:
        print(f"Error in get_user_tests: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tests: {str(e)}"
        )


@router.get("/{test_id}", response_model=Test)
async def get_test(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific test by ID.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("tests")\
        .select("*")\
        .eq("id", test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    return result.data[0]


@router.post("/create", response_model=dict)
async def create_new_test(
    request: TestCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new test based on the request parameters.
    """
    user_id = current_user["user_id"]
    
    # For adaptive tests, generate questions based on performance
    if request.type == "adaptive":
        questions = await generate_adaptive_test(
            user_id=user_id,
            num_questions=request.number_of_questions,
            subject_id=request.subject_id
        )
    else:
        # Generate standard test with filters
        questions = await generate_test(
            user_id=user_id, 
            num_questions=request.number_of_questions,
            subject_id=request.subject_id,
            chapter_ids=request.chapter_ids,
            topic_ids=request.topic_ids,
            difficulty=request.difficulty
        )
    
    # Create the test
    test_id = await create_test(
        user_id=user_id,
        title=request.title,
        test_type=request.type,
        questions=[q.model_dump() for q in questions],
        duration=request.duration,
        subject=request.subject,
        subject_id=request.subject_id
    )
    
    return {
        "test_id": test_id,
        "message": "Test created successfully"
    }


@router.post("/submit", response_model=dict)
async def submit_test(
    request: TestSubmitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit test attempts and calculate score.
    """
    user_id = current_user["user_id"]
    
    # Verify test belongs to user
    test_result = supabase.table("tests")\
        .select("*")\
        .eq("id", request.test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not test_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Submit attempts and calculate score
    result = await submit_test_attempts(
        test_id=request.test_id,
        user_id=user_id,
        attempts=request.attempts
    )
    
    return result


@router.patch("/{test_id}/start")
async def start_test(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark test as started.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("tests")\
        .update({
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat()
        })\
        .eq("id", test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    return {"message": "Test started"}


@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a test.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("tests")\
        .delete()\
        .eq("id", test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    return {"message": "Test deleted successfully"}


@router.get("/{test_id}/attempts")
async def get_test_attempts(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all attempts for a specific test.
    """
    user_id = current_user["user_id"]
    
    # Verify test belongs to user
    test_result = supabase.table("tests")\
        .select("id")\
        .eq("id", test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not test_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Get attempts
    attempts_result = supabase.table("test_attempts")\
        .select("*")\
        .eq("test_id", test_id)\
        .execute()
    
    return attempts_result.data


@router.get("/{test_id}/results")
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed test results including question-by-question breakdown.
    """
    user_id = current_user["user_id"]
    
    # Get test details
    test_result = supabase.table("tests")\
        .select("*")\
        .eq("id", test_id)\
        .eq("user_id", user_id)\
        .execute()
    
    if not test_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    test = test_result.data[0]
    
    # Get all attempts for this test
    attempts_result = supabase.table("test_attempts")\
        .select("*")\
        .eq("test_id", test_id)\
        .execute()
    
    attempts = attempts_result.data
    
    # Get question details
    question_ids = [a["question_id"] for a in attempts]
    questions_result = supabase.table("repository_questions")\
        .select("*")\
        .in_("id", question_ids)\
        .execute()
    
    question_map = {q["id"]: q for q in questions_result.data}
    
    # Get topic names
    topic_ids = list(set([q.get("topic_id") for q in questions_result.data if q.get("topic_id")]))
    topics_result = supabase.table("topics")\
        .select("id, name")\
        .in_("id", topic_ids)\
        .execute()
    
    topic_map = {t["id"]: t["name"] for t in topics_result.data}
    
    # Get subject names
    subject_ids = list(set([q.get("subject_id") for q in questions_result.data if q.get("subject_id")]))
    subjects_result = supabase.table("subjects")\
        .select("id, name")\
        .in_("id", subject_ids)\
        .execute()
    
    subject_map = {s["id"]: s["name"] for s in subjects_result.data}
    
    # Build detailed attempts list
    detailed_attempts = []
    total_time = 0
    topic_stats = {}
    
    for attempt in attempts:
        question = question_map.get(attempt["question_id"])
        if not question:
            continue
        
        topic_id = question.get("topic_id")
        topic_name = topic_map.get(topic_id, "Unknown")
        subject_name = subject_map.get(question.get("subject_id"), "Unknown")
        
        # Track topic stats
        if topic_name not in topic_stats:
            topic_stats[topic_name] = {"correct": 0, "total": 0}
        
        topic_stats[topic_name]["total"] += 1
        if attempt["is_correct"]:
            topic_stats[topic_name]["correct"] += 1
        
        total_time += attempt.get("time_spent", 0)
        
        detailed_attempts.append({
            "question_id": attempt["question_id"],
            "question_text": question["question_text"],
            "selected_answer": attempt["selected_answer"],
            "correct_answer": question["correct_answer"],
            "is_correct": attempt["is_correct"],
            "time_spent": attempt.get("time_spent", 0),
            "marked_for_review": attempt.get("marked_for_review", False),
            "topic": topic_name,
            "subject": subject_name
        })
    
    # Build topic breakdown
    topic_breakdown = [
        {
            "topic": topic,
            "correct": stats["correct"],
            "total": stats["total"],
            "accuracy": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        }
        for topic, stats in topic_stats.items()
    ]
    
    return {
        "test_id": test_id,
        "title": test["title"],
        "score": test.get("score", 0),
        "max_score": test.get("max_score", len(attempts) * 4),
        "total_questions": len(attempts),
        "correct_answers": sum(1 for a in attempts if a["is_correct"]),
        "time_taken": total_time,
        "attempts": detailed_attempts,
        "topic_breakdown": topic_breakdown
    }

