from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from app.utils.auth import get_current_user
from app.database import supabase
from app.services.analytics_aggregator import AnalyticsAggregator

router = APIRouter(prefix="/api/performance", tags=["performance"])

# Initialize AnalyticsAggregator
analytics_aggregator = AnalyticsAggregator(supabase)


@router.get("/topic-mastery")
async def get_topic_mastery(
    subject: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topic mastery data for the current user.
    Uses new student_topic_mastery table.
    Optionally filter by subject.
    """
    user_id = current_user["user_id"]
    
    query = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)
    
    if subject:
        query = query.eq("books.subject", subject)
    
    result = query.order("accuracy_pct", desc=False).execute()
    
    # Transform to include topic and subject names
    mastery_data = []
    for record in result.data:
        topic = record.get("topics", {})
        book = record.get("books", {})
        mastery_data.append({
            "id": record.get("id"),
            "student_id": record.get("student_id"),
            "topic_id": record.get("topic_id"),
            "topic": topic.get("title", "Unknown"),
            "subject": book.get("subject", "Unknown"),
            "questions_attempted": record.get("questions_attempted", 0),
            "questions_correct": record.get("questions_correct", 0),
            "accuracy_pct": float(record.get("accuracy_pct", 0)),
            "mastery_level": record.get("mastery_level", "not_started"),
            "last_attempted_at": record.get("last_attempted_at")
        })
    
    return mastery_data


@router.get("/weak-topics")
async def get_weak_topics(
    threshold: float = 70.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topics where user's mastery is below threshold.
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)\
        .lt("accuracy_pct", threshold)\
        .order("accuracy_pct", desc=False)\
        .execute()
    
    # Transform to include topic and subject names
    weak_topics = []
    for record in result.data:
        topic = record.get("topics", {})
        book = record.get("books", {})
        weak_topics.append({
            "id": record.get("id"),
            "topic": topic.get("title", "Unknown"),
            "subject": book.get("subject", "Unknown"),
            "accuracy_pct": float(record.get("accuracy_pct", 0)),
            "mastery_level": record.get("mastery_level", "not_started"),
            "questions_attempted": record.get("questions_attempted", 0)
        })
    
    return weak_topics


@router.get("/strong-topics")
async def get_strong_topics(
    threshold: float = 85.0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get topics where user has strong mastery.
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)\
        .gte("accuracy_pct", threshold)\
        .order("accuracy_pct", desc=True)\
        .execute()
    
    # Transform to include topic and subject names
    strong_topics = []
    for record in result.data:
        topic = record.get("topics", {})
        book = record.get("books", {})
        strong_topics.append({
            "id": record.get("id"),
            "topic": topic.get("title", "Unknown"),
            "subject": book.get("subject", "Unknown"),
            "accuracy_pct": float(record.get("accuracy_pct", 0)),
            "mastery_level": record.get("mastery_level", "mastered"),
            "questions_attempted": record.get("questions_attempted", 0)
        })
    
    return strong_topics


@router.get("/subject-performance")
async def get_subject_performance(
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated performance by subject.
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("student_topic_mastery")\
        .select("*, books!inner(subject)")\
        .eq("student_id", user_id)\
        .execute()
    
    # Aggregate by subject
    subject_data = {}
    for record in result.data:
        book = record.get("books", {})
        subject = book.get("subject", "Unknown")
        
        if subject not in subject_data:
            subject_data[subject] = {
                "subject": subject,
                "topics": [],
                "average_score": 0,
                "total_questions": 0,
                "total_correct": 0
            }
        
        subject_data[subject]["topics"].append(record)
        subject_data[subject]["total_questions"] += record.get("questions_attempted", 0)
        subject_data[subject]["total_correct"] += record.get("questions_correct", 0)
    
    # Calculate averages
    for subject in subject_data.values():
        if subject["total_questions"] > 0:
            subject["average_score"] = (
                subject["total_correct"] / subject["total_questions"] * 100
            )
        
        # Calculate topic mastery average
        if subject["topics"]:
            subject["average_mastery"] = sum(
                float(t.get("accuracy_pct", 0)) for t in subject["topics"]
            ) / len(subject["topics"])
    
    return list(subject_data.values())


@router.get("/activity")
async def get_user_activity(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user activity for the last N days.
    Uses new daily_activity table.
    Used for streak tracking and progress visualization.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    result = supabase.table("daily_activity")\
        .select("*")\
        .eq("student_id", user_id)\
        .gte("activity_date", start_date.isoformat())\
        .order("activity_date", desc=True)\
        .execute()
    
    return result.data


@router.get("/streak")
async def get_current_streak(
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate current streak (consecutive days of activity).
    Uses new daily_activity table.
    """
    user_id = current_user["user_id"]
    
    # Get all activity records ordered by date descending
    result = supabase.table("daily_activity")\
        .select("activity_date, questions_attempted")\
        .eq("student_id", user_id)\
        .order("activity_date", desc=True)\
        .execute()
    
    if not result.data:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Calculate current streak
    current_streak = 0
    today = datetime.utcnow().date()
    
    for i, record in enumerate(result.data):
        record_date = datetime.fromisoformat(record["activity_date"]).date()
        expected_date = today - timedelta(days=i)
        
        if record_date == expected_date and record.get("questions_attempted", 0) > 0:
            current_streak += 1
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    
    for record in reversed(result.data):
        record_date = datetime.fromisoformat(record["activity_date"]).date()
        
        if record.get("questions_attempted", 0) > 0:
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
    Uses new student_topic_mastery, test_sessions, and daily_activity tables.
    """
    user_id = current_user["user_id"]
    
    # Get topic mastery data
    mastery_result = supabase.table("student_topic_mastery")\
        .select("*")\
        .eq("student_id", user_id)\
        .execute()
    
    # Get test sessions data
    sessions_result = supabase.table("test_sessions")\
        .select("*")\
        .eq("student_id", user_id)\
        .execute()
    
    # Get daily activity data
    activity_result = supabase.table("daily_activity")\
        .select("*")\
        .eq("student_id", user_id)\
        .execute()
    
    # Calculate statistics
    total_questions = sum(t.get("questions_attempted", 0) for t in mastery_result.data)
    total_correct = sum(t.get("questions_correct", 0) for t in mastery_result.data)
    accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    completed_sessions = [s for s in sessions_result.data if s.get("status") == "submitted"]
    avg_test_score = 0
    if completed_sessions:
        total_score = sum(float(s.get("total_marks_obtained", 0)) for s in completed_sessions)
        total_max = sum(float(s.get("test_papers", {}).get("total_marks", 0)) for s in completed_sessions if s.get("test_papers"))
        avg_test_score = (total_score / total_max * 100) if total_max > 0 else 0
    
    total_time_minutes = sum(a.get("time_spent_minutes", 0) for a in activity_result.data)
    
    # Categorize topics by accuracy
    weak_topics = [t for t in mastery_result.data if float(t.get("accuracy_pct", 0)) < 70]
    strong_topics = [t for t in mastery_result.data if float(t.get("accuracy_pct", 0)) >= 85]
    
    return {
        "total_questions_attempted": total_questions,
        "total_correct_answers": total_correct,
        "overall_accuracy": round(accuracy, 2),
        "tests_completed": len(completed_sessions),
        "average_test_score": round(avg_test_score, 2),
        "total_study_time_minutes": total_time_minutes,
        "weak_topics_count": len(weak_topics),
        "strong_topics_count": len(strong_topics)
    }
