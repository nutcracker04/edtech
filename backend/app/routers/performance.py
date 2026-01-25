from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from app.utils.auth import get_current_user
from app.database import supabase

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/topic-mastery")
async def get_topic_mastery(
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topic mastery data for the current user.
    Optionally filter by subject.
    """
    user_id = current_user["user_id"]
    
    query = supabase.table("topic_mastery").select("*").eq("user_id", user_id)
    
    if subject:
        query = query.eq("subject", subject)
    
    result = query.order("mastery_score", desc=False).execute()
    
    return result.data


@router.get("/weak-topics")
async def get_weak_topics(
    threshold: float = 70.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topics where user's mastery is below threshold.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .lt("mastery_score", threshold)\
        .order("mastery_score", desc=False)\
        .execute()
    
    return result.data


@router.get("/strong-topics")
async def get_strong_topics(
    threshold: float = 85.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topics where user has strong mastery.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("mastery_score", threshold)\
        .order("mastery_score", desc=True)\
        .execute()
    
    return result.data


@router.get("/subject-performance")
async def get_subject_performance(
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated performance by subject.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Aggregate by subject
    subject_data = {}
    for record in result.data:
        subject = record["subject"]
        if subject not in subject_data:
            subject_data[subject] = {
                "subject": subject,
                "topics": [],
                "average_score": 0,
                "total_questions": 0,
                "total_correct": 0
            }
        
        subject_data[subject]["topics"].append(record)
        subject_data[subject]["total_questions"] += record["questions_attempted"]
        subject_data[subject]["total_correct"] += record["questions_correct"]
    
    # Calculate averages
    for subject in subject_data.values():
        if subject["total_questions"] > 0:
            subject["average_score"] = (
                subject["total_correct"] / subject["total_questions"] * 100
            )
        
        # Calculate topic mastery average
        if subject["topics"]:
            subject["average_mastery"] = sum(
                t["mastery_score"] for t in subject["topics"]
            ) / len(subject["topics"])
    
    return list(subject_data.values())


@router.get("/activity")
async def get_user_activity(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user activity for the last N days.
    Used for streak tracking and progress visualization.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    result = supabase.table("user_activity")\
        .select("*")\
        .eq("user_id", user_id)\
        .gte("date", start_date.isoformat())\
        .order("date", desc=True)\
        .execute()
    
    return result.data


@router.get("/streak")
async def get_current_streak(
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate current streak (consecutive days of activity).
    """
    user_id = current_user["user_id"]
    
    # Get all activity records ordered by date descending
    result = supabase.table("user_activity")\
        .select("date, questions_solved")\
        .eq("user_id", user_id)\
        .order("date", desc=True)\
        .execute()
    
    if not result.data:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Calculate current streak
    current_streak = 0
    today = datetime.utcnow().date()
    
    for i, record in enumerate(result.data):
        record_date = datetime.fromisoformat(record["date"]).date()
        expected_date = today - timedelta(days=i)
        
        if record_date == expected_date and record["questions_solved"] > 0:
            current_streak += 1
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    
    for record in reversed(result.data):
        record_date = datetime.fromisoformat(record["date"]).date()
        
        if record["questions_solved"] > 0:
            if prev_date is None or (record_date - prev_date).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
            prev_date = record_date
        else:
            temp_streak = 0
            prev_date = None
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak
    }


@router.get("/overall-stats")
async def get_overall_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get overall performance statistics.
    """
    user_id = current_user["user_id"]
    
    # Get topic mastery data
    mastery_result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Get tests data
    tests_result = supabase.table("tests")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Get activity data
    activity_result = supabase.table("user_activity")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Calculate statistics
    total_questions = sum(t["questions_attempted"] for t in mastery_result.data)
    total_correct = sum(t["questions_correct"] for t in mastery_result.data)
    accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    completed_tests = [t for t in tests_result.data if t["status"] == "completed"]
    avg_test_score = (
        sum(t["score"] for t in completed_tests if t["score"]) / len(completed_tests)
        if completed_tests else 0
    )
    
    total_time = sum(a["time_spent"] for a in activity_result.data)
    
    # Categorize topics
    weak_topics = [t for t in mastery_result.data if t["mastery_score"] < 70]
    strong_topics = [t for t in mastery_result.data if t["mastery_score"] >= 85]
    
    return {
        "total_questions_attempted": total_questions,
        "total_correct_answers": total_correct,
        "overall_accuracy": round(accuracy, 2),
        "tests_completed": len(completed_tests),
        "average_test_score": round(avg_test_score, 2),
        "total_study_time_seconds": total_time,
        "weak_topics_count": len(weak_topics),
        "strong_topics_count": len(strong_topics)
    }
