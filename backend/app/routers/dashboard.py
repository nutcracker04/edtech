"""
Dashboard API endpoints
Provides data for the Dashboard page including metrics, streaks, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from app.utils.auth import get_current_user
from app.database import supabase
from app.models.dashboard import (
    DashboardData,
    DashboardMetrics,
    StreakData,
    SubjectPerformance,
    ActivityItem,
    UpcomingTest,
    Recommendation,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user performance metrics for the Dashboard.
    Returns: accuracy percentage, questions solved, study hours, tests completed
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
    
    # Calculate metrics
    total_questions = sum(t.get("questions_attempted", 0) for t in mastery_result.data)
    total_correct = sum(t.get("questions_correct", 0) for t in mastery_result.data)
    accuracy_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    completed_tests = [t for t in tests_result.data if t.get("status") == "completed"]
    tests_completed = len(completed_tests)
    
    # Calculate study hours from activity
    total_time_seconds = sum(a.get("time_spent", 0) for a in activity_result.data)
    study_hours = total_time_seconds / 3600
    
    return DashboardMetrics(
        accuracy_percentage=round(accuracy_percentage, 2),
        questions_solved=total_questions,
        study_hours=round(study_hours, 2),
        tests_completed=tests_completed
    )


@router.get("/streak", response_model=StreakData)
async def get_streak_data(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current streak and milestone status.
    Milestones: 7, 14, 30 days
    """
    user_id = current_user["user_id"]
    
    # Get all activity records ordered by date descending
    result = supabase.table("user_activity")\
        .select("date, questions_solved")\
        .eq("user_id", user_id)\
        .order("date", desc=True)\
        .execute()
    
    if not result.data:
        return StreakData(current_streak=0, streak_milestone_reached=False)
    
    # Calculate current streak
    current_streak = 0
    today = datetime.utcnow().date()
    
    for i, record in enumerate(result.data):
        record_date = datetime.fromisoformat(record["date"]).date()
        expected_date = today - timedelta(days=i)
        
        if record_date == expected_date and record.get("questions_solved", 0) > 0:
            current_streak += 1
        else:
            break
    
    # Check if milestone reached
    milestone_reached = current_streak in [7, 14, 30]
    milestone_value = current_streak if milestone_reached else None
    
    return StreakData(
        current_streak=current_streak,
        streak_milestone_reached=milestone_reached,
        milestone_value=milestone_value
    )


@router.get("/subjects", response_model=List[SubjectPerformance])
async def get_subject_performance(
    current_user: dict = Depends(get_current_user)
):
    """
    Get performance data for all enrolled subjects.
    Returns subject name, accuracy, questions solved, and trend.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Aggregate by subject
    subject_data = {}
    for record in result.data:
        subject = record.get("subject", "Unknown")
        subject_id = record.get("subject_id", subject)
        
        if subject_id not in subject_data:
            subject_data[subject_id] = {
                "subject_id": subject_id,
                "subject_name": subject,
                "total_questions": 0,
                "total_correct": 0,
                "topics": [],
                "prev_accuracy": None,
            }
        
        subject_data[subject_id]["topics"].append(record)
        subject_data[subject_id]["total_questions"] += record.get("questions_attempted", 0)
        subject_data[subject_id]["total_correct"] += record.get("questions_correct", 0)
    
    # Calculate accuracy and trend
    subjects = []
    for subject_id, data in subject_data.items():
        accuracy = (data["total_correct"] / data["total_questions"] * 100) if data["total_questions"] > 0 else 0
        
        # Determine trend (simplified: based on average mastery score)
        if data["topics"]:
            avg_mastery = sum(t.get("mastery_score", 0) for t in data["topics"]) / len(data["topics"])
            if avg_mastery >= 80:
                trend = "up"
            elif avg_mastery >= 60:
                trend = "flat"
            else:
                trend = "down"
        else:
            trend = "flat"
        
        subjects.append(SubjectPerformance(
            subject_id=subject_id,
            subject_name=data["subject_name"],
            accuracy_percentage=round(accuracy, 2),
            questions_solved=data["total_questions"],
            trend=trend
        ))
    
    return subjects


@router.get("/activity", response_model=List[ActivityItem])
async def get_recent_activity(
    limit: int = 5,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent activity (last N items, default 5).
    Returns test completions, questions solved, and topics reviewed.
    """
    user_id = current_user["user_id"]
    
    # Get recent test completions
    tests_result = supabase.table("tests")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "completed")\
        .order("completed_at", desc=True)\
        .limit(limit)\
        .execute()
    
    activities = []
    for test in tests_result.data:
        activities.append(ActivityItem(
            id=test.get("id", ""),
            type="test_completed",
            title=f"Completed: {test.get('title', 'Test')}",
            score=test.get("score"),
            timestamp=test.get("completed_at", datetime.utcnow().isoformat()),
            link=f"/tests/{test.get('id')}"
        ))
    
    # Sort by timestamp and limit to 5
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    return activities[:limit]


@router.get("/full", response_model=DashboardData)
async def get_full_dashboard_data(
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete Dashboard data including all sections.
    """
    user_id = current_user["user_id"]
    
    try:
        # Get all data
        metrics = await get_dashboard_metrics(current_user)
        streak = await get_streak_data(current_user)
        subjects = await get_subject_performance(current_user)
        activity = await get_recent_activity(5, current_user)
        
        # Get upcoming tests
        tests_result = supabase.table("tests")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("status", "upcoming")\
            .order("scheduled_at", desc=False)\
            .limit(5)\
            .execute()
        
        upcoming_tests = [
            UpcomingTest(
                test_id=t.get("id", ""),
                test_name=t.get("title", "Test"),
                test_type=t.get("type", "mock"),
                date=t.get("scheduled_at") or t.get("created_at") or datetime.utcnow().isoformat(),
                difficulty="medium"  # Default difficulty since it's not in the tests table
            )
            for t in tests_result.data
        ]
        
        # Generate recommendation (simplified: recommend weakest subject)
        weakest_subject = min(subjects, key=lambda x: x.accuracy_percentage) if subjects else None
        if weakest_subject:
            recommendation = Recommendation(
                topic_id=weakest_subject.subject_id,
                topic_name=weakest_subject.subject_name,
                reason=f"You scored {weakest_subject.accuracy_percentage}% - this is your weakest area",
                action=f"Practice 10 questions on {weakest_subject.subject_name}",
                difficulty="medium",
                estimated_time_minutes=15
            )
        else:
            recommendation = Recommendation(
                topic_id="general",
                topic_name="General Practice",
                reason="Keep practicing to improve your skills",
                action="Start a practice session",
                difficulty="medium",
                estimated_time_minutes=15
            )
        
        return DashboardData(
            user_id=user_id,
            current_streak=streak.current_streak,
            streak_milestone_reached=streak.streak_milestone_reached,
            key_metrics=metrics,
            recent_activity=activity,
            subject_performance=subjects,
            upcoming_tests=upcoming_tests,
            recommendation=recommendation,
            data_timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        print(f"Error in get_full_dashboard_data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")
