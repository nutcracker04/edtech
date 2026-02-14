"""
Analysis Page API endpoints
Provides data for the Analysis page including overview, trends, weak areas, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Literal
from datetime import datetime, timedelta

from app.utils.auth import get_current_user
from app.database import supabase
from app.models.analysis import (
    AnalysisData,
    PerformanceOverview,
    TrendDataPoint,
    TopicData,
    SubjectBreakdown,
    WeakArea,
    AnalysisRecommendation,
    TrendData,
)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def get_days_for_period(period: Literal['7d', '30d', '90d', 'all']) -> Optional[int]:
    """Convert time period to number of days"""
    mapping = {
        '7d': 7,
        '30d': 30,
        '90d': 90,
        'all': None
    }
    return mapping.get(period)


@router.get("/overview", response_model=PerformanceOverview)
async def get_performance_overview(
    time_period: Literal['7d', '30d', '90d', 'all'] = '30d',
    current_user: dict = Depends(get_current_user)
):
    """
    Get performance overview metrics for the Analysis page.
    Returns: accuracy, questions solved, study hours, average time per question
    """
    user_id = current_user["user_id"]
    days = get_days_for_period(time_period)
    
    # Get topic mastery data
    query = supabase.table("topic_mastery").select("*").eq("user_id", user_id)
    if days:
        start_date = (datetime.utcnow() - timedelta(days=days)).date()
        query = query.gte("last_attempt_date", start_date.isoformat())
    
    mastery_result = query.execute()
    
    # Get test attempts for time calculation
    query = supabase.table("test_attempts").select("*").eq("user_id", user_id)
    if days:
        start_date = (datetime.utcnow() - timedelta(days=days)).date()
        query = query.gte("created_at", start_date.isoformat())
    
    attempts_result = query.execute()
    
    # Calculate metrics
    total_questions = sum(t.get("questions_attempted", 0) for t in mastery_result.data)
    total_correct = sum(t.get("questions_correct", 0) for t in mastery_result.data)
    accuracy_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    # Calculate study hours from attempts
    total_time_seconds = sum(a.get("time_spent", 0) for a in attempts_result.data)
    study_hours = total_time_seconds / 3600
    
    # Calculate average time per question
    avg_time_per_question = (total_time_seconds / total_questions) if total_questions > 0 else 0
    
    return PerformanceOverview(
        accuracy_percentage=round(accuracy_percentage, 2),
        questions_solved=total_questions,
        study_hours=round(study_hours, 2),
        avg_time_per_question=round(avg_time_per_question, 2)
    )


@router.get("/trends", response_model=TrendData)
async def get_trend_data(
    time_period: Literal['7d', '30d', '90d', 'all'] = '30d',
    current_user: dict = Depends(get_current_user)
):
    """
    Get trend data for accuracy and question count over time.
    """
    user_id = current_user["user_id"]
    days = get_days_for_period(time_period)
    
    # Get test attempts
    query = supabase.table("test_attempts").select("*").eq("user_id", user_id)
    if days:
        start_date = (datetime.utcnow() - timedelta(days=days)).date()
        query = query.gte("created_at", start_date.isoformat())
    
    result = query.execute()
    
    # Group by date
    daily_data = {}
    for attempt in result.data:
        date_str = attempt["created_at"][:10]  # Extract date
        
        if date_str not in daily_data:
            daily_data[date_str] = {
                "date": date_str,
                "total": 0,
                "correct": 0,
                "accuracy": 0,
                "count": 0
            }
        
        daily_data[date_str]["total"] += 1
        daily_data[date_str]["count"] += 1
        if attempt.get("is_correct"):
            daily_data[date_str]["correct"] += 1
    
    # Calculate accuracy for each day
    for day in daily_data.values():
        if day["total"] > 0:
            day["accuracy"] = round(day["correct"] / day["total"] * 100, 2)
    
    # Sort by date
    sorted_dates = sorted(daily_data.keys())
    
    accuracy_by_date = [
        TrendDataPoint(
            date=datetime.fromisoformat(date).isoformat(),
            accuracy=daily_data[date]["accuracy"]
        )
        for date in sorted_dates
    ]
    
    questions_by_date = [
        TrendDataPoint(
            date=datetime.fromisoformat(date).isoformat(),
            count=daily_data[date]["count"]
        )
        for date in sorted_dates
    ]
    
    return TrendData(
        accuracy_by_date=accuracy_by_date,
        questions_by_date=questions_by_date
    )


@router.get("/weak-areas", response_model=List[WeakArea])
async def get_weak_areas(
    current_user: dict = Depends(get_current_user)
):
    """
    Get weak areas ranked by impact on overall score.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .lt("mastery_score", 70)\
        .order("mastery_score", desc=False)\
        .execute()
    
    weak_areas = []
    for record in result.data:
        # Calculate impact score (combination of low accuracy and questions attempted)
        accuracy = (record.get("questions_correct", 0) / record.get("questions_attempted", 1) * 100) if record.get("questions_attempted", 0) > 0 else 0
        impact_score = (100 - accuracy) * (record.get("questions_attempted", 0) / 100)
        
        weak_areas.append(WeakArea(
            topic_id=record.get("id", ""),
            topic_name=record.get("topic", ""),
            accuracy_percentage=round(accuracy, 2),
            impact_score=round(impact_score, 2),
            recommended_action=f"Practice 10 questions on {record.get('topic', '')}"
        ))
    
    # Sort by impact score
    weak_areas.sort(key=lambda x: x.impact_score, reverse=True)
    return weak_areas


@router.get("/subjects", response_model=List[SubjectBreakdown])
async def get_subject_breakdown(
    current_user: dict = Depends(get_current_user)
):
    """
    Get subject-wise breakdown with nested topics.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Group by subject
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
            }
        
        subject_data[subject_id]["topics"].append(record)
        subject_data[subject_id]["total_questions"] += record.get("questions_attempted", 0)
        subject_data[subject_id]["total_correct"] += record.get("questions_correct", 0)
    
    # Build subject breakdowns
    breakdowns = []
    for subject_id, data in subject_data.items():
        accuracy = (data["total_correct"] / data["total_questions"] * 100) if data["total_questions"] > 0 else 0
        
        # Determine trend
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
        
        # Build topic data
        topics = [
            TopicData(
                topic_id=t.get("id", ""),
                topic_name=t.get("topic", ""),
                accuracy_percentage=round((t.get("questions_correct", 0) / t.get("questions_attempted", 1) * 100) if t.get("questions_attempted", 0) > 0 else 0, 2),
                questions_solved=t.get("questions_attempted", 0),
                trend="up" if t.get("mastery_score", 0) >= 80 else ("flat" if t.get("mastery_score", 0) >= 60 else "down")
            )
            for t in data["topics"]
        ]
        
        breakdowns.append(SubjectBreakdown(
            subject_id=subject_id,
            subject_name=data["subject_name"],
            accuracy_percentage=round(accuracy, 2),
            questions_solved=data["total_questions"],
            trend=trend,
            topics=topics
        ))
    
    return breakdowns


@router.get("/recommendations", response_model=List[AnalysisRecommendation])
async def get_analysis_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """
    Get personalized recommendations based on weak areas and learning patterns.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    recommendations = []
    
    # Get weak topics
    weak_topics = [t for t in result.data if t.get("mastery_score", 0) < 70]
    weak_topics.sort(key=lambda x: x.get("mastery_score", 0))
    
    for topic in weak_topics[:5]:  # Top 5 weak areas
        accuracy = (topic.get("questions_correct", 0) / topic.get("questions_attempted", 1) * 100) if topic.get("questions_attempted", 0) > 0 else 0
        
        if accuracy < 40:
            priority = "high"
        elif accuracy < 60:
            priority = "high"
        else:
            priority = "medium"
        
        recommendations.append(AnalysisRecommendation(
            topic_id=topic.get("id", ""),
            topic_name=topic.get("topic", ""),
            reason=f"You scored {accuracy:.1f}% - this is your weakest area",
            action=f"Practice 10 questions on {topic.get('topic', '')}",
            difficulty="medium",
            estimated_time_minutes=15,
            priority=priority
        ))
    
    return recommendations


@router.get("/full", response_model=AnalysisData)
async def get_full_analysis_data(
    time_period: Literal['7d', '30d', '90d', 'all'] = '30d',
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete Analysis page data.
    """
    user_id = current_user["user_id"]
    
    # Get all data
    overview = await get_performance_overview(time_period, current_user)
    trends = await get_trend_data(time_period, current_user)
    weak_areas = await get_weak_areas(current_user)
    subjects = await get_subject_breakdown(current_user)
    recommendations = await get_analysis_recommendations(current_user)
    
    return AnalysisData(
        user_id=user_id,
        time_period=time_period,
        performance_overview=overview,
        subject_performance=subjects,
        trend_data=trends,
        weak_areas=weak_areas,
        recommendations=recommendations,
        data_timestamp=datetime.utcnow().isoformat()
    )
