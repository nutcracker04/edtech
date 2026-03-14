from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.utils.auth import get_current_user
from app.database import supabase
from app.models.test import Test, TestCreateRequest, TestSubmitRequest
from app.services.test_service import create_test, generate_adaptive_test, generate_test, submit_test_attempts, generate_pyq_test
from app.services.test_session_manager import TestSessionManager, TestPaperConfig
from app.models.test_engine import TestSession, SessionStatus, PaperType

router = APIRouter(prefix="/api/tests", tags=["tests"])

# Initialize TestSessionManager
test_session_manager = TestSessionManager(supabase)


@router.get("/", response_model=List[Test])
async def get_user_tests(
    status_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all tests for the current user.
    Optionally filter by status.
    Uses new test_sessions table with backward compatibility.
    """
    try:
        user_id = current_user["user_id"]
        
        # Query test_sessions table with test_papers join
        query = supabase.table("test_sessions")\
            .select("*, test_papers!inner(*)")\
            .eq("student_id", user_id)
        
        if status_filter:
            query = query.eq("status", status_filter)
        
        result = query.order("created_at", desc=True).execute()
        
        # Transform to backward-compatible format
        tests = []
        for session in result.data:
            test_paper = session.get("test_papers", {})
            
            # Get questions for this test paper
            questions_result = supabase.table("test_paper_questions")\
                .select("*, questions!inner(*)")\
                .eq("test_paper_id", test_paper.get("id"))\
                .order("sort_order")\
                .execute()
            
            questions = [q.get("questions", {}) for q in questions_result.data]
            
            tests.append({
                "id": session.get("id"),
                "user_id": user_id,
                "title": test_paper.get("title", ""),
                "type": test_paper.get("paper_type", "custom"),
                "subject": test_paper.get("subject"),
                "status": session.get("status", "in_progress"),
                "score": float(session.get("total_marks_obtained", 0)) if session.get("total_marks_obtained") else None,
                "max_score": float(test_paper.get("total_marks", 0)),
                "duration": test_paper.get("duration_minutes"),
                "questions": questions,
                "created_at": session.get("created_at"),
                "started_at": session.get("started_at"),
                "completed_at": session.get("submitted_at")
            })
        
        return tests
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
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific test by ID.
    Uses new test_sessions table with backward compatibility.
    """
    user_id = current_user["user_id"]
    
    # Query test_sessions with test_papers join
    result = supabase.table("test_sessions")\
        .select("*, test_papers!inner(*)")\
        .eq("id", test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    session = result.data[0]
    test_paper = session.get("test_papers", {})
    
    # Get questions for this test paper
    questions_result = supabase.table("test_paper_questions")\
        .select("*, questions!inner(*)")\
        .eq("test_paper_id", test_paper.get("id"))\
        .order("sort_order")\
        .execute()
    
    questions = [q.get("questions", {}) for q in questions_result.data]
    
    return {
        "id": session.get("id"),
        "user_id": user_id,
        "title": test_paper.get("title", ""),
        "type": test_paper.get("paper_type", "custom"),
        "subject": test_paper.get("subject"),
        "status": session.get("status", "in_progress"),
        "score": float(session.get("total_marks_obtained", 0)) if session.get("total_marks_obtained") else None,
        "max_score": float(test_paper.get("total_marks", 0)),
        "duration": test_paper.get("duration_minutes"),
        "questions": questions,
        "created_at": session.get("created_at"),
        "started_at": session.get("started_at"),
        "completed_at": session.get("submitted_at")
    }


@router.post("/create", response_model=dict)
async def create_new_test(
    request: TestCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new test based on the request parameters.
    Uses TestSessionManager to create test paper and start session.
    """
    user_id = current_user["user_id"]
    
    # For adaptive tests, generate questions based on performance
    if request.type == "adaptive":
        questions = await generate_adaptive_test(
            user_id=user_id,
            num_questions=request.number_of_questions,
            subject_id=request.subject_id
        )
    elif request.source == "pyq":
        # Generate test from PYQ questions
        questions = await generate_pyq_test(
            user_id=user_id,
            num_questions=request.number_of_questions,
            subject_id=request.subject_id,
            chapter_ids=request.chapter_ids,
            topic_ids=request.topic_ids
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
    
    # Create test paper using TestSessionManager
    from decimal import Decimal
    config = TestPaperConfig(
        title=request.title,
        subject=request.subject,
        grade_level=request.get("grade_level", 10),  # Default to grade 10
        duration_minutes=request.duration,
        total_marks=Decimal(request.number_of_questions * 4),  # 4 marks per question
        question_count=request.number_of_questions,
        created_by=UUID(user_id),
        paper_type=PaperType.CUSTOM,
        is_published=True
    )
    
    result = test_session_manager.create_test_paper(config)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create test paper: {result.error}"
        )
    
    # Start a session for this test paper
    session = test_session_manager.start_session(
        paper_id=result.test_paper.id,
        student_id=UUID(user_id)
    )
    
    return {
        "test_id": str(session.id),
        "message": "Test created successfully"
    }


@router.post("/submit", response_model=dict)
async def submit_test(
    request: TestSubmitRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit test attempts and calculate score.
    Uses TestSessionManager to submit session and calculate score with negative marking.
    Also saves navigation log and answer changes for journey analysis.
    """
    user_id = current_user["user_id"]
    
    # Verify test session belongs to user
    session_result = supabase.table("test_sessions")\
        .select("*")\
        .eq("id", request.test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    
    # Submit session using TestSessionManager
    result = test_session_manager.submit_session(
        session_id=UUID(str(request.test_id)),
        attempts=request.attempts
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit test: {result.error}"
        )
    
    # Save navigation log and answer changes for time analysis
    from app.services.time_analysis_service import save_navigation_log, save_answer_changes
    
    try:
        if request.navigation_log:
            await save_navigation_log(request.test_id, user_id, request.navigation_log)
        
        if request.answer_changes:
            await save_answer_changes(request.test_id, user_id, request.answer_changes)
    except Exception as e:
        # Don't fail submission if tracking fails
        print(f"Warning: Failed to save tracking data: {str(e)}")
    
    return {
        "test_id": str(request.test_id),
        "score": float(result.total_marks),
        "max_score": float(result.max_marks),
        "percentage": float(result.percentage),
        "rank": result.rank,
        "correct_count": result.correct_count,
        "attempted_count": result.attempted_count,
        "message": "Test submitted successfully"
    }


@router.patch("/{test_id}/start")
async def start_test(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Mark test session as started.
    Updates test_sessions table.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("test_sessions")\
        .update({
            "status": "in_progress",
            "started_at": datetime.utcnow().isoformat()
        })\
        .eq("id", test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    
    return {"message": "Test started"}


@router.delete("/{test_id}")
async def delete_test(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a test session.
    Deletes from test_sessions table (attempts cascade delete automatically).
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("test_sessions")\
        .delete()\
        .eq("id", test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    
    return {"message": "Test deleted successfully"}


@router.get("/{test_id}/attempts")
async def get_test_attempts(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all attempts for a specific test session.
    Uses new attempts table.
    """
    user_id = current_user["user_id"]
    
    # Verify test session belongs to user
    session_result = supabase.table("test_sessions")\
        .select("id")\
        .eq("id", test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    
    # Get attempts from new attempts table
    attempts_result = supabase.table("attempts")\
        .select("*")\
        .eq("session_id", test_id)\
        .execute()
    
    return attempts_result.data


@router.get("/{test_id}/results")
async def get_test_results(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed test results including question-by-question breakdown.
    Uses new test_sessions, attempts, and questions tables.
    """
    user_id = current_user["user_id"]
    
    # Get test session with test paper details
    session_result = supabase.table("test_sessions")\
        .select("*, test_papers!inner(*)")\
        .eq("id", test_id)\
        .eq("student_id", user_id)\
        .execute()
    
    if not session_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test session not found"
        )
    
    session = session_result.data[0]
    test_paper = session.get("test_papers", {})
    
    # Get all attempts for this session with question details
    attempts_result = supabase.table("attempts")\
        .select("*, questions!inner(*)")\
        .eq("session_id", test_id)\
        .execute()
    
    attempts = attempts_result.data
    
    # Get topic names for questions
    question_ids = [a["question_id"] for a in attempts]
    questions_result = supabase.table("questions")\
        .select("id, topic_id, topics!inner(id, name, chapters!inner(id, name))")\
        .in_("id", question_ids)\
        .execute()
    
    question_topic_map = {}
    for q in questions_result.data:
        topic = q.get("topics", {})
        chapter = topic.get("chapters", {})
        question_topic_map[q["id"]] = {
            "topic": topic.get("name", "Unknown"),
            "chapter": chapter.get("name", "Unknown")
        }
    
    # Build detailed attempts list
    detailed_attempts = []
    total_time = 0
    topic_stats = {}
    
    for attempt in attempts:
        question = attempt.get("questions", {})
        question_id = attempt["question_id"]
        topic_info = question_topic_map.get(question_id, {"topic": "Unknown", "chapter": "Unknown"})
        topic_name = topic_info["topic"]
        
        # Track topic stats
        if topic_name not in topic_stats:
            topic_stats[topic_name] = {"correct": 0, "total": 0}
        
        topic_stats[topic_name]["total"] += 1
        if attempt.get("is_correct"):
            topic_stats[topic_name]["correct"] += 1
        
        total_time += attempt.get("time_spent_seconds", 0)
        
        # Get correct answer
        answer_result = supabase.table("answers")\
            .select("correct_answer")\
            .eq("question_id", question_id)\
            .execute()
        
        correct_answer = answer_result.data[0].get("correct_answer") if answer_result.data else None
        
        detailed_attempts.append({
            "question_id": question_id,
            "question_text": question.get("question_text", ""),
            "selected_answer": attempt.get("student_answer"),
            "correct_answer": correct_answer,
            "is_correct": attempt.get("is_correct", False),
            "time_spent": attempt.get("time_spent_seconds", 0),
            "marked_for_review": attempt.get("flagged", False),
            "topic": topic_name,
            "subject": test_paper.get("subject", "Unknown")
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
        "test_id": str(test_id),
        "title": test_paper.get("title", ""),
        "score": float(session.get("total_marks_obtained", 0)),
        "max_score": float(test_paper.get("total_marks", 0)),
        "total_questions": len(attempts),
        "correct_answers": sum(1 for a in attempts if a.get("is_correct")),
        "time_taken": total_time,
        "attempts": detailed_attempts,
        "topic_breakdown": topic_breakdown
    }


@router.get("/{test_id}/time-analysis")
async def get_test_time_analysis(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive time-based analysis for a test.
    Includes time breakdown by question, subject, and topic.
    """
    from app.services.time_analysis_service import get_test_time_breakdown
    
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
    
    analysis = await get_test_time_breakdown(test_id, user_id)
    return analysis


@router.get("/{test_id}/journey-analysis")
async def get_test_journey(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get test journey analysis showing navigation patterns and answer changes.
    """
    from app.services.time_analysis_service import get_test_journey_analysis
    
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
    
    journey = await get_test_journey_analysis(test_id, user_id)
    return journey


@router.get("/{test_id}/difficulty-analysis")
async def get_question_difficulty_analysis(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze question difficulty based on time spent.
    Identifies questions that took unusually long or short time.
    """
    from app.services.time_analysis_service import get_question_difficulty_by_time
    
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
    
    analysis = await get_question_difficulty_by_time(test_id, user_id)
    return {"questions": analysis}


@router.get("/{test_id}/efficiency-analysis")
async def get_subject_efficiency(
    test_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze time efficiency per subject.
    Shows which subjects take more time and their accuracy correlation.
    """
    from app.services.time_analysis_service import get_subject_time_efficiency
    
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
    
    efficiency = await get_subject_time_efficiency(test_id, user_id)
    return efficiency

