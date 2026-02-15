"""
Service for analyzing time-based test performance and journey tracking.
Provides insights into how students spend time on questions and navigate through tests.
"""

from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from app.database import supabase


async def save_navigation_log(
    test_id: UUID,
    user_id: str,
    navigation_entries: List[Dict[str, Any]]
) -> None:
    """Save question navigation log entries"""
    if not navigation_entries:
        return
    
    # Prepare entries for insertion
    entries = []
    for entry in navigation_entries:
        entries.append({
            "test_id": str(test_id),
            "user_id": user_id,
            "from_question_id": entry.get("from_question_id"),
            "to_question_id": entry.get("to_question_id"),
            "from_question_index": entry.get("from_question_index"),
            "to_question_index": entry.get("to_question_index"),
            "navigation_type": entry.get("navigation_type", "jump"),
            "time_on_previous_question": entry.get("time_on_previous_question", 0),
            "timestamp": entry.get("timestamp", datetime.utcnow().isoformat())
        })
    
    # Batch insert
    supabase.table("question_navigation_log").insert(entries).execute()


async def save_answer_changes(
    test_id: UUID,
    user_id: str,
    answer_changes: List[Dict[str, Any]]
) -> None:
    """Save answer change log entries"""
    if not answer_changes:
        return
    
    # Prepare entries for insertion
    entries = []
    for change in answer_changes:
        entries.append({
            "test_id": str(test_id),
            "user_id": user_id,
            "question_id": change.get("question_id"),
            "question_index": change.get("question_index"),
            "previous_answer": change.get("previous_answer"),
            "new_answer": change.get("new_answer"),
            "change_type": change.get("change_type", "modified"),
            "timestamp": change.get("timestamp", datetime.utcnow().isoformat())
        })
    
    # Batch insert
    supabase.table("answer_change_log").insert(entries).execute()


async def get_test_time_breakdown(test_id: UUID, user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive time breakdown for a test.
    Returns time spent per question, subject, and topic.
    """
    # Get test attempts with time data
    attempts_result = supabase.table("test_attempts")\
        .select("*")\
        .eq("test_id", str(test_id))\
        .eq("user_id", user_id)\
        .execute()
    
    attempts = attempts_result.data
    
    if not attempts:
        return {
            "total_time": 0,
            "questions": [],
            "subject_breakdown": [],
            "topic_breakdown": []
        }
    
    # Get question details
    question_ids = [a["question_id"] for a in attempts]
    questions_result = supabase.table("repository_questions")\
        .select("id, question_text, subject_id, topic_id, chapter_id")\
        .in_("id", question_ids)\
        .execute()
    
    question_map = {q["id"]: q for q in questions_result.data}
    
    # Get subject, topic, and chapter names
    subject_ids = list(set([q.get("subject_id") for q in questions_result.data if q.get("subject_id")]))
    topic_ids = list(set([q.get("topic_id") for q in questions_result.data if q.get("topic_id")]))
    chapter_ids = list(set([q.get("chapter_id") for q in questions_result.data if q.get("chapter_id")]))
    
    subjects_result = supabase.table("subjects").select("id, name").in_("id", subject_ids).execute()
    topics_result = supabase.table("topics").select("id, name").in_("id", topic_ids).execute()
    chapters_result = supabase.table("chapters").select("id, name").in_("id", chapter_ids).execute()
    
    subject_map = {s["id"]: s["name"] for s in subjects_result.data}
    topic_map = {t["id"]: t["name"] for t in topics_result.data}
    chapter_map = {c["id"]: c["name"] for c in chapters_result.data}
    
    # Build question-wise breakdown
    total_time = 0
    question_breakdown = []
    subject_time = {}
    topic_time = {}
    
    for attempt in attempts:
        question = question_map.get(attempt["question_id"])
        if not question:
            continue
        
        time_spent = attempt.get("time_spent", 0)
        total_time += time_spent
        
        subject_id = question.get("subject_id")
        topic_id = question.get("topic_id")
        chapter_id = question.get("chapter_id")
        
        subject_name = subject_map.get(subject_id, "Unknown")
        topic_name = topic_map.get(topic_id, "Unknown")
        chapter_name = chapter_map.get(chapter_id, "Unknown")
        
        # Track subject time
        if subject_name not in subject_time:
            subject_time[subject_name] = {
                "total_time": 0,
                "question_count": 0,
                "correct_count": 0
            }
        subject_time[subject_name]["total_time"] += time_spent
        subject_time[subject_name]["question_count"] += 1
        if attempt.get("is_correct"):
            subject_time[subject_name]["correct_count"] += 1
        
        # Track topic time
        if topic_name not in topic_time:
            topic_time[topic_name] = {
                "total_time": 0,
                "question_count": 0,
                "subject": subject_name,
                "chapter": chapter_name
            }
        topic_time[topic_name]["total_time"] += time_spent
        topic_time[topic_name]["question_count"] += 1
        
        question_breakdown.append({
            "question_id": attempt["question_id"],
            "question_order": attempt.get("question_order", 0),
            "time_spent": time_spent,
            "is_correct": attempt.get("is_correct", False),
            "marked_for_review": attempt.get("marked_for_review", False),
            "view_count": attempt.get("view_count", 1),
            "answer_changed_count": attempt.get("answer_changed_count", 0),
            "subject": subject_name,
            "topic": topic_name,
            "chapter": chapter_name,
            "first_viewed_at": attempt.get("first_viewed_at"),
            "last_viewed_at": attempt.get("last_viewed_at")
        })
    
    # Sort by question order
    question_breakdown.sort(key=lambda x: x["question_order"])
    
    # Build subject breakdown
    subject_breakdown = [
        {
            "subject": subject,
            "total_time": data["total_time"],
            "avg_time_per_question": data["total_time"] / data["question_count"] if data["question_count"] > 0 else 0,
            "question_count": data["question_count"],
            "correct_count": data["correct_count"],
            "accuracy": (data["correct_count"] / data["question_count"] * 100) if data["question_count"] > 0 else 0,
            "time_percentage": (data["total_time"] / total_time * 100) if total_time > 0 else 0
        }
        for subject, data in subject_time.items()
    ]
    
    # Build topic breakdown
    topic_breakdown = [
        {
            "topic": topic,
            "subject": data["subject"],
            "chapter": data["chapter"],
            "total_time": data["total_time"],
            "avg_time_per_question": data["total_time"] / data["question_count"] if data["question_count"] > 0 else 0,
            "question_count": data["question_count"],
            "time_percentage": (data["total_time"] / total_time * 100) if total_time > 0 else 0
        }
        for topic, data in topic_time.items()
    ]
    
    return {
        "total_time": total_time,
        "avg_time_per_question": total_time / len(attempts) if attempts else 0,
        "questions": question_breakdown,
        "subject_breakdown": subject_breakdown,
        "topic_breakdown": topic_breakdown
    }


async def get_test_journey_analysis(test_id: UUID, user_id: str) -> Dict[str, Any]:
    """
    Analyze the test-taking journey including navigation patterns.
    Shows how the student moved through the test.
    """
    # Get navigation log
    nav_result = supabase.table("question_navigation_log")\
        .select("*")\
        .eq("test_id", str(test_id))\
        .eq("user_id", user_id)\
        .order("timestamp")\
        .execute()
    
    navigation_log = nav_result.data
    
    # Get answer changes
    changes_result = supabase.table("answer_change_log")\
        .select("*")\
        .eq("test_id", str(test_id))\
        .eq("user_id", user_id)\
        .order("timestamp")\
        .execute()
    
    answer_changes = changes_result.data
    
    # Analyze navigation patterns
    navigation_patterns = {
        "total_navigations": len(navigation_log),
        "next_clicks": sum(1 for n in navigation_log if n.get("navigation_type") == "next"),
        "previous_clicks": sum(1 for n in navigation_log if n.get("navigation_type") == "previous"),
        "jumps": sum(1 for n in navigation_log if n.get("navigation_type") == "jump"),
        "review_navigations": sum(1 for n in navigation_log if n.get("navigation_type") == "review")
    }
    
    # Analyze answer changes
    answer_change_stats = {
        "total_changes": len(answer_changes),
        "initial_answers": sum(1 for c in answer_changes if c.get("change_type") == "initial"),
        "modifications": sum(1 for c in answer_changes if c.get("change_type") == "modified"),
        "cleared_answers": sum(1 for c in answer_changes if c.get("change_type") == "cleared")
    }
    
    # Build timeline
    timeline = []
    for nav in navigation_log:
        timeline.append({
            "type": "navigation",
            "timestamp": nav.get("timestamp"),
            "from_index": nav.get("from_question_index"),
            "to_index": nav.get("to_question_index"),
            "navigation_type": nav.get("navigation_type"),
            "time_on_previous": nav.get("time_on_previous_question", 0)
        })
    
    for change in answer_changes:
        timeline.append({
            "type": "answer_change",
            "timestamp": change.get("timestamp"),
            "question_index": change.get("question_index"),
            "change_type": change.get("change_type"),
            "previous_answer": change.get("previous_answer"),
            "new_answer": change.get("new_answer")
        })
    
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    
    return {
        "navigation_patterns": navigation_patterns,
        "answer_change_stats": answer_change_stats,
        "timeline": timeline,
        "navigation_log": navigation_log,
        "answer_changes": answer_changes
    }


async def get_question_difficulty_by_time(test_id: UUID, user_id: str) -> List[Dict[str, Any]]:
    """
    Identify questions that took unusually long or short time.
    Helps identify difficult questions or areas of strength.
    """
    time_breakdown = await get_test_time_breakdown(test_id, user_id)
    
    questions = time_breakdown["questions"]
    if not questions:
        return []
    
    # Calculate average time
    avg_time = time_breakdown["avg_time_per_question"]
    
    # Categorize questions by time spent
    categorized = []
    for q in questions:
        time_spent = q["time_spent"]
        time_ratio = time_spent / avg_time if avg_time > 0 else 1
        
        if time_ratio > 1.5:
            category = "very_slow"
            insight = "Spent significantly more time than average"
        elif time_ratio > 1.2:
            category = "slow"
            insight = "Spent more time than average"
        elif time_ratio < 0.5:
            category = "very_fast"
            insight = "Answered very quickly"
        elif time_ratio < 0.8:
            category = "fast"
            insight = "Answered faster than average"
        else:
            category = "normal"
            insight = "Normal time spent"
        
        categorized.append({
            **q,
            "time_category": category,
            "time_ratio": time_ratio,
            "insight": insight,
            "avg_time": avg_time
        })
    
    return categorized


async def get_subject_time_efficiency(test_id: UUID, user_id: str) -> Dict[str, Any]:
    """
    Analyze time efficiency per subject.
    Shows which subjects take more time and their accuracy correlation.
    """
    time_breakdown = await get_test_time_breakdown(test_id, user_id)
    
    subject_breakdown = time_breakdown["subject_breakdown"]
    
    # Add efficiency metrics
    for subject in subject_breakdown:
        # Efficiency = accuracy / (time_percentage / 100)
        # Higher efficiency means better accuracy with less time
        time_pct = subject["time_percentage"] / 100 if subject["time_percentage"] > 0 else 1
        subject["efficiency_score"] = subject["accuracy"] / time_pct if time_pct > 0 else 0
        
        # Time per correct answer
        subject["time_per_correct"] = (
            subject["total_time"] / subject["correct_count"]
            if subject["correct_count"] > 0 else 0
        )
    
    # Sort by efficiency
    subject_breakdown.sort(key=lambda x: x["efficiency_score"], reverse=True)
    
    return {
        "subjects": subject_breakdown,
        "most_efficient": subject_breakdown[0] if subject_breakdown else None,
        "least_efficient": subject_breakdown[-1] if subject_breakdown else None
    }
