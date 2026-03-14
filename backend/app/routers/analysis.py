from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from app.utils.auth import get_current_user
from app.database import supabase
from app.utils.normalization import normalize_subject
from app.services.analytics_aggregator import AnalyticsAggregator

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize AnalyticsAggregator
analytics_aggregator = AnalyticsAggregator(supabase)


@router.get("/performance-trend")
async def get_performance_trend(
    subject: Optional[str] = None,
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """
    Get performance trend over time for visualizations.
    Uses new attempts and test_sessions tables.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    # Get attempts over time with test session and test paper joins
    query = supabase.table("attempts")\
        .select("*, test_sessions!inner(student_id, test_papers!inner(subject)), created_at")\
        .eq("test_sessions.student_id", user_id)\
        .gte("created_at", start_date.isoformat())
    
    if subject:
        query = query.eq("test_sessions.test_papers.subject", normalize_subject(subject))
    
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
        if attempt.get("is_correct"):
            daily_performance[date]["correct"] += 1
    
    # Calculate accuracy for each day
    for day in daily_performance.values():
        if day["total"] > 0:
            day["accuracy"] = round(day["correct"] / day["total"] * 100, 2)
    
    # Sort by date
    sorted_data = sorted(daily_performance.values(), key=lambda x: x["date"])
    
    return sorted_data

@router.get("/hierarchy")
async def get_subject_hierarchy():
    """
    Get full subject -> chapter -> topic hierarchy for selection.
    Uses new books, chapters, topics tables.
    """
    # Get books (subjects)
    books = supabase.table("books").select("id, title, subject").execute().data
    chapters = supabase.table("chapters").select("id, title, book_id").execute().data
    topics = supabase.table("topics").select("id, title, chapter_id").execute().data
    
    hierarchy = []
    
    for book in books:
        book_node = {
            "id": book["id"],
            "name": f"{book['subject']} - {book['title']}",
            "subject": book["subject"],
            "chapters": []
        }
        
        # Find chapters for this book
        book_chapters = [c for c in chapters if c["book_id"] == book["id"]]
        
        for chap in book_chapters:
            chap_node = {
                "id": chap["id"],
                "name": chap["title"],
                "topics": []
            }
            
            # Find topics for this chapter
            chap_topics = [t for t in topics if t["chapter_id"] == chap["id"]]
            
            for top in chap_topics:
                chap_node["topics"].append({
                    "id": top["id"],
                    "name": top["title"]
                })
                
            book_node["chapters"].append(chap_node)
            
        hierarchy.append(book_node)
        
    return hierarchy
@router.get("/topic-breakdown")
async def get_topic_breakdown(
    subject: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed breakdown of performance by topic within a subject.
    Uses new student_topic_mastery table.
    For spider web visualization.
    """
    user_id = current_user["user_id"]
    
    # Query student_topic_mastery with topic and book joins
    query = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)
    
    if subject:
        # Filter by subject through books join
        query = query.eq("books.subject", normalize_subject(subject))

    result = query.execute()
    
    # Format for spider web chart
    topics_data = []
    for record in result.data:
        topic = record.get("topics", {})
        topics_data.append({
            "topic": topic.get("title", "Unknown"),
            "score": float(record.get("accuracy_pct", 0)),
            "questions_attempted": record.get("questions_attempted", 0),
            "accuracy": float(record.get("accuracy_pct", 0)),
            "mastery_level": record.get("mastery_level", "not_started")
        })
    
    return topics_data


@router.get("/weak-areas-analysis")
async def get_weak_areas_analysis(
    current_user: dict = Depends(get_current_user)
):
    """
    Detailed analysis of weak areas with recommendations.
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    # Get weak topics (accuracy < 70%)
    result = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)\
        .lt("accuracy_pct", 70)\
        .order("accuracy_pct", desc=False)\
        .limit(10)\
        .execute()
    
    weak_areas = []
    for record in result.data:
        topic = record.get("topics", {})
        book = record.get("books", {})
        accuracy = float(record.get("accuracy_pct", 0))
        
        # Generate recommendations based on accuracy
        if accuracy < 40:
            priority = "high"
            recommendation = f"Start with basics of {topic.get('title', 'this topic')}. Focus on fundamental concepts."
        elif accuracy < 55:
            priority = "high"
            recommendation = f"Review core concepts of {topic.get('title', 'this topic')} and practice regularly."
        else:
            priority = "medium"
            recommendation = f"Practice more problems on {topic.get('title', 'this topic')} to improve consistency."
        
        weak_areas.append({
            "subject": book.get("subject", "Unknown"),
            "topic": topic.get("title", "Unknown"),
            "mastery_score": accuracy,
            "questions_attempted": record.get("questions_attempted", 0),
            "accuracy": accuracy,
            "priority": priority,
            "recommendation": recommendation,
            "last_attempt": record.get("last_attempted_at")
        })
    
    return weak_areas


@router.get("/test-history")
async def get_test_history(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """
    Get test history for analysis and comparison.
    Uses new test_sessions and test_papers tables.
    """
    user_id = current_user["user_id"]
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    result = supabase.table("test_sessions")\
        .select("*, test_papers!inner(*)")\
        .eq("student_id", user_id)\
        .eq("status", "submitted")\
        .gte("submitted_at", start_date.isoformat())\
        .order("submitted_at", desc=True)\
        .execute()
    
    # Format test history with statistics
    test_history = []
    for session in result.data:
        test_paper = session.get("test_papers", {})
        duration_minutes = test_paper.get("duration_minutes", 0)
        actual_time = None
        
        if session.get("started_at") and session.get("submitted_at"):
            start = datetime.fromisoformat(session["started_at"])
            end = datetime.fromisoformat(session["submitted_at"])
            actual_time = int((end - start).total_seconds() / 60)
        
        # Get question count
        questions_result = supabase.table("test_paper_questions")\
            .select("id")\
            .eq("test_paper_id", test_paper.get("id"))\
            .execute()
        
        test_history.append({
            "id": session.get("id"),
            "title": test_paper.get("title", ""),
            "type": test_paper.get("paper_type", "custom"),
            "subject": test_paper.get("subject"),
            "score": float(session.get("total_marks_obtained", 0)),
            "max_score": float(test_paper.get("total_marks", 0)),
            "questions_count": len(questions_result.data),
            "allocated_time": duration_minutes,
            "actual_time": actual_time,
            "completed_at": session.get("submitted_at")
        })
    
    return test_history


@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """
    Get personalized study recommendations based on performance.
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    # Get topic mastery data with topic and book joins
    mastery_result = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)\
        .execute()
    
    recommendations = []
    
    # Analyze weak topics (accuracy < 70%)
    weak_topics = [t for t in mastery_result.data if float(t.get("accuracy_pct", 0)) < 70]
    if weak_topics:
        most_weak = min(weak_topics, key=lambda x: float(x.get("accuracy_pct", 0)))
        topic = most_weak.get("topics", {})
        book = most_weak.get("books", {})
        recommendations.append({
            "type": "focus",
            "priority": "high",
            "title": f"Focus on {topic.get('title', 'this topic')}",
            "description": f"Your mastery in {topic.get('title', 'this topic')} ({book.get('subject', 'Unknown')}) is at {float(most_weak.get('accuracy_pct', 0)):.1f}%. This needs immediate attention.",
            "action_url": f"/practice?subject={book.get('subject')}&topic={topic.get('title')}"
        })
    
    # Check for inactive topics (not attempted recently)
    inactive_threshold = datetime.now(timezone.utc) - timedelta(days=7)
    inactive_topics = []
    
    for t in mastery_result.data:
        if t.get("last_attempted_at"):
            try:
                last_attempt = datetime.fromisoformat(t["last_attempted_at"])
                if last_attempt.tzinfo is None:
                    last_attempt = last_attempt.replace(tzinfo=timezone.utc)
                
                if last_attempt < inactive_threshold:
                    inactive_topics.append(t)
            except (ValueError, TypeError):
                continue
    
    if inactive_topics and len(inactive_topics) > 3:
        recommendations.append({
            "type": "practice",
            "priority": "medium",
            "title": "Practice inactive topics",
            "description": f"You haven't practiced {len(inactive_topics)} topics in the last week. Regular practice helps retention.",
            "action_url": "/practice"
        })
    
    # Check for strong topics (motivational) - accuracy >= 85%
    strong_topics = [t for t in mastery_result.data if float(t.get("accuracy_pct", 0)) >= 85]
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
    Uses new student_topic_mastery table.
    """
    user_id = current_user["user_id"]
    
    result = supabase.table("student_topic_mastery")\
        .select("*, topics!inner(title), books!inner(subject)")\
        .eq("student_id", user_id)\
        .execute()
    
    # Group by subject
    subjects = {}
    for record in result.data:
        book = record.get("books", {})
        subject = book.get("subject", "Unknown")
        
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
        subjects[subject]["total_questions"] += record.get("questions_attempted", 0)
        subjects[subject]["total_correct"] += record.get("questions_correct", 0)
        
        accuracy = float(record.get("accuracy_pct", 0))
        if accuracy < 70:
            subjects[subject]["weak_topics"] += 1
        elif accuracy >= 85:
            subjects[subject]["strong_topics"] += 1
    
    # Calculate averages
    comparison = []
    for subject_data in subjects.values():
        if subject_data["topics"]:
            subject_data["average_mastery"] = round(
                sum(float(t.get("accuracy_pct", 0)) for t in subject_data["topics"]) / len(subject_data["topics"]),
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
