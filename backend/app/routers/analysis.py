from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta

from app.utils.auth import get_current_user
from app.database import supabase

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/performance-trend")
async def get_performance_trend(
    subject: Optional[str] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get performance trend over time for visualizations.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    # Get test attempts over time
    query = supabase.table("test_attempts")\
        .select("*, tests!inner(created_at, subject)")\
        .eq("user_id", user_id)\
        .gte("created_at", start_date.isoformat())
    
    if subject:
        query = query.eq("tests.subject", subject)
    
    result = query.execute()
    
    # Group by date and calculate daily performance
    daily_performance = {}
    for attempt in result.data:
        date = attempt["created_at"][:10]  # Extract date
        
        if date not in daily_performance:
            daily_performance[date] = {
                "date": date,
                "total": 0,
                "correct": 0,
                "accuracy": 0
            }
        
        daily_performance[date]["total"] += 1
        if attempt["is_correct"]:
            daily_performance[date]["correct"] += 1
    
    # Calculate accuracy for each day
    for day in daily_performance.values():
        if day["total"] > 0:
            day["accuracy"] = round(day["correct"] / day["total"] * 100, 2)
    
    # Sort by date
    sorted_data = sorted(daily_performance.values(), key=lambda x: x["date"])
    
    return sorted_data


@router.get("/topic-breakdown")
async def get_topic_breakdown(
    subject: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed breakdown of performance by topic within a subject.
    For spider web visualization.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("subject", subject)\
        .execute()
    
    # Format for spider web chart
    topics_data = []
    for record in result.data:
        topics_data.append({
            "topic": record["topic"],
            "score": record["mastery_score"],
            "questions_attempted": record["questions_attempted"],
            "accuracy": (
                record["questions_correct"] / record["questions_attempted"] * 100
                if record["questions_attempted"] > 0 else 0
            ),
            "trend": record.get("trend")
        })
    
    return topics_data


@router.get("/weak-areas-analysis")
async def get_weak_areas_analysis(
    current_user: dict = Depends(get_current_user)
):
    """
    Detailed analysis of weak areas with recommendations.
    """
    user_id = current_user["user_id"]
    
    # Get weak topics
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .lt("mastery_score", 70)\
        .order("mastery_score", desc=False)\
        .limit(10)\
        .execute()
    
    weak_areas = []
    for record in result.data:
        # Generate recommendations based on mastery score
        if record["mastery_score"] < 40:
            priority = "high"
            recommendation = f"Start with basics of {record['topic']}. Focus on fundamental concepts."
        elif record["mastery_score"] < 55:
            priority = "high"
            recommendation = f"Review core concepts of {record['topic']} and practice regularly."
        else:
            priority = "medium"
            recommendation = f"Practice more problems on {record['topic']} to improve consistency."
        
        weak_areas.append({
            "subject": record["subject"],
            "topic": record["topic"],
            "mastery_score": record["mastery_score"],
            "questions_attempted": record["questions_attempted"],
            "accuracy": (
                record["questions_correct"] / record["questions_attempted"] * 100
                if record["questions_attempted"] > 0 else 0
            ),
            "priority": priority,
            "recommendation": recommendation,
            "last_attempt": record["last_attempt_date"]
        })
    
    return weak_areas


@router.get("/test-history")
async def get_test_history(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """
    Get test history for analysis and comparison.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    result = supabase.table("tests")\
        .select("*")\
        .eq("user_id", user_id)\
        .eq("status", "completed")\
        .gte("completed_at", start_date.isoformat())\
        .order("completed_at", desc=True)\
        .execute()
    
    # Format test history with statistics
    test_history = []
    for test in result.data:
        duration_minutes = test["duration"]
        actual_time = None
        
        if test["started_at"] and test["completed_at"]:
            start = datetime.fromisoformat(test["started_at"])
            end = datetime.fromisoformat(test["completed_at"])
            actual_time = int((end - start).total_seconds() / 60)
        
        test_history.append({
            "id": test["id"],
            "title": test["title"],
            "type": test["type"],
            "subject": test["subject"],
            "score": test["score"],
            "max_score": test["max_score"],
            "questions_count": len(test["questions"]),
            "allocated_time": duration_minutes,
            "actual_time": actual_time,
            "completed_at": test["completed_at"]
        })
    
    return test_history


@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """
    Get personalized study recommendations based on performance.
    """
    user_id = current_user["user_id"]
    
    # Get topic mastery data
    mastery_result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    recommendations = []
    
    # Analyze weak topics
    weak_topics = [t for t in mastery_result.data if t["mastery_score"] < 70]
    if weak_topics:
        most_weak = min(weak_topics, key=lambda x: x["mastery_score"])
        recommendations.append({
            "type": "focus",
            "priority": "high",
            "title": f"Focus on {most_weak['topic']}",
            "description": f"Your mastery in {most_weak['topic']} ({most_weak['subject']}) is at {most_weak['mastery_score']:.1f}%. This needs immediate attention.",
            "action_url": f"/practice?subject={most_weak['subject']}&topic={most_weak['topic']}"
        })
    
    # Check for topics with declining trend
    declining_topics = [t for t in mastery_result.data if t.get("trend") == "declining"]
    if declining_topics:
        recommendations.append({
            "type": "revision",
            "priority": "medium",
            "title": "Review declining topics",
            "description": f"You have {len(declining_topics)} topic(s) showing declining performance. Regular revision is recommended.",
            "action_url": "/revision-capsules"
        })
    
    # Check for inactive topics (not attempted recently)
    inactive_threshold = datetime.utcnow() - timedelta(days=7)
    inactive_topics = [
        t for t in mastery_result.data
        if datetime.fromisoformat(t["last_attempt_date"]) < inactive_threshold
    ]
    if inactive_topics and len(inactive_topics) > 3:
        recommendations.append({
            "type": "practice",
            "priority": "medium",
            "title": "Practice inactive topics",
            "description": f"You haven't practiced {len(inactive_topics)} topics in the last week. Regular practice helps retention.",
            "action_url": "/practice"
        })
    
    # Check for strong topics (motivational)
    strong_topics = [t for t in mastery_result.data if t["mastery_score"] >= 85]
    if strong_topics:
        recommendations.append({
            "type": "challenge",
            "priority": "low",
            "title": "Challenge yourself",
            "description": f"You have mastered {len(strong_topics)} topics! Try harder problems to push your limits.",
            "action_url": "/tests/create?difficulty=hard"
        })
    
    return recommendations


@router.get("/subject-comparison")
async def get_subject_comparison(
    current_user: dict = Depends(get_current_user)
):
    """
    Compare performance across subjects.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    # Group by subject
    subjects = {}
    for record in result.data:
        subject = record["subject"]
        if subject not in subjects:
            subjects[subject] = {
                "subject": subject,
                "topics": [],
                "average_mastery": 0,
                "total_questions": 0,
                "total_correct": 0,
                "weak_topics": 0,
                "strong_topics": 0
            }
        
        subjects[subject]["topics"].append(record)
        subjects[subject]["total_questions"] += record["questions_attempted"]
        subjects[subject]["total_correct"] += record["questions_correct"]
        
        if record["mastery_score"] < 70:
            subjects[subject]["weak_topics"] += 1
        elif record["mastery_score"] >= 85:
            subjects[subject]["strong_topics"] += 1
    
    # Calculate averages
    comparison = []
    for subject_data in subjects.values():
        if subject_data["topics"]:
            subject_data["average_mastery"] = round(
                sum(t["mastery_score"] for t in subject_data["topics"]) / len(subject_data["topics"]),
                2
            )
        
        if subject_data["total_questions"] > 0:
            subject_data["overall_accuracy"] = round(
                subject_data["total_correct"] / subject_data["total_questions"] * 100,
                2
            )
        else:
            subject_data["overall_accuracy"] = 0
        
        comparison.append(subject_data)
    
    return comparison
