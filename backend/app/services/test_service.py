from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.database import supabase
from app.models.test import Question, Test, TestCreateRequest


async def create_test(
    user_id: str,
    title: str,
    test_type: str,
    questions: List[Dict[str, Any]],
    duration: int,
    subject: Optional[str] = None,
    scheduled_at: Optional[datetime] = None
) -> str:
    """
    Create a new test in the database.
    Returns the test ID.
    """
    test_data = {
        "user_id": user_id,
        "title": title,
        "type": test_type,
        "subject": subject,
        "status": "upcoming",
        "duration": duration,
        "questions": questions,
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    result = supabase.table("tests").insert(test_data).execute()
    
    if result.data:
        return result.data[0]["id"]
    else:
        raise Exception("Failed to create test")


async def generate_adaptive_test(
    user_id: str,
    num_questions: int = 20,
    focus_on_weak_areas: float = 0.7,
    include_strong_areas: bool = True
) -> List[Question]:
    """
    Generate an adaptive test based on user's performance.
    
    This queries the topic_mastery table to identify weak and strong areas,
    then selects questions accordingly.
    """
    # Get user's topic mastery data
    mastery_result = supabase.table("topic_mastery")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    if not mastery_result.data:
        # No mastery data, return random questions
        return await get_random_questions(num_questions)
    
    mastery_data = mastery_result.data
    
    # Categorize topics
    weak_topics = [m for m in mastery_data if m["mastery_score"] < 70]
    strong_topics = [m for m in mastery_data if m["mastery_score"] >= 70]
    
    # Calculate number of questions from each category
    num_weak = int(num_questions * focus_on_weak_areas)
    num_strong = num_questions - num_weak if include_strong_areas else 0
    
    # This is a placeholder - in a real implementation, you would:
    # 1. Have a questions table in the database
    # 2. Query questions based on topics
    # 3. Apply difficulty adjustments based on mastery scores
    
    # For now, return empty list (will be populated from mock data or question bank)
    return []


async def get_random_questions(num_questions: int) -> List[Question]:
    """
    Get random questions from the question bank.
    Placeholder for when you have a questions table.
    """
    # This would query your questions table
    # For now, return empty list
    return []


async def submit_test_attempts(
    test_id: str,
    user_id: str,
    attempts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Submit test attempts and calculate score.
    Also updates topic mastery based on performance.
    """
    # Insert test attempts
    attempt_records = [
        {
            "test_id": test_id,
            "user_id": user_id,
            "question_id": attempt["question_id"],
            "selected_answer": attempt.get("selected_answer"),
            "is_correct": attempt.get("is_correct", False),
            "time_spent": attempt.get("time_spent", 0),
            "marked_for_review": attempt.get("marked_for_review", False),
            "created_at": datetime.utcnow().isoformat()
        }
        for attempt in attempts
    ]
    
    supabase.table("test_attempts").insert(attempt_records).execute()
    
    # Calculate score
    total_questions = len(attempts)
    correct_answers = sum(1 for a in attempts if a.get("is_correct", False))
    score = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Update test status
    supabase.table("tests")\
        .update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "score": score,
            "max_score": 100
        })\
        .eq("id", test_id)\
        .execute()
    
    # Update topic mastery (would need to group by topic and update)
    await update_topic_mastery(user_id, attempts)
    
    return {
        "test_id": test_id,
        "score": score,
        "total_questions": total_questions,
        "correct_answers": correct_answers
    }


async def update_topic_mastery(user_id: str, attempts: List[Dict[str, Any]]):
    """
    Update topic mastery scores based on test performance.
    """
    # Group attempts by subject/topic
    topic_performance = {}
    
    for attempt in attempts:
        subject = attempt.get("subject", "unknown")
        topic = attempt.get("topic", "general")
        key = f"{subject}_{topic}"
        
        if key not in topic_performance:
            topic_performance[key] = {
                "subject": subject,
                "topic": topic,
                "correct": 0,
                "total": 0
            }
        
        topic_performance[key]["total"] += 1
        if attempt.get("is_correct"):
            topic_performance[key]["correct"] += 1
    
    # Update or insert topic mastery records
    for key, perf in topic_performance.items():
        mastery_score = (perf["correct"] / perf["total"] * 100) if perf["total"] > 0 else 0
        
        # Check if record exists
        existing = supabase.table("topic_mastery")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("subject", perf["subject"])\
            .eq("topic", perf["topic"])\
            .execute()
        
        if existing.data:
            # Update existing record
            old_score = existing.data[0]["mastery_score"]
            old_attempts = existing.data[0]["questions_attempted"]
            old_correct = existing.data[0]["questions_correct"]
            
            new_attempts = old_attempts + perf["total"]
            new_correct = old_correct + perf["correct"]
            new_score = (new_correct / new_attempts * 100) if new_attempts > 0 else 0
            
            supabase.table("topic_mastery")\
                .update({
                    "mastery_score": new_score,
                    "questions_attempted": new_attempts,
                    "questions_correct": new_correct,
                    "last_attempt_date": datetime.utcnow().isoformat()
                })\
                .eq("id", existing.data[0]["id"])\
                .execute()
        else:
            # Insert new record
            supabase.table("topic_mastery")\
                .insert({
                    "user_id": user_id,
                    "subject": perf["subject"],
                    "topic": perf["topic"],
                    "mastery_score": mastery_score,
                    "questions_attempted": perf["total"],
                    "questions_correct": perf["correct"],
                    "last_attempt_date": datetime.utcnow().isoformat()
                })\
                .execute()
