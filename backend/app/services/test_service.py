from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import random
from app.database import supabase
from app.models.test import Question, Test, TestCreateRequest
from app.utils.normalization import normalize_subject

async def create_test(
    user_id: str,
    title: str,
    test_type: str,
    questions: List[Dict[str, Any]],
    duration: int,
    subject: Optional[str] = None,
    subject_id: Optional[str] = None,
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
        # "subject_id": subject_id, # Removed as column doesn't exist
        "status": "upcoming",
        "duration": duration,
        "questions": questions,
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # If subject_id is provided but subject name is missing, try to resolve it
    if subject_id and not subject:
        try:
            sub_res = supabase.table("subjects").select("name").eq("id", subject_id).execute()
            if sub_res.data:
                subject = sub_res.data[0]["name"]
        except Exception:
            pass
            
    # Normalize subject for DB constraints
    test_data["subject"] = normalize_subject(subject) if subject else None
    
    result = supabase.table("tests").insert(test_data).execute()
    
    if result.data:
        return result.data[0]["id"]
    else:
        raise Exception("Failed to create test")

async def generate_test(
    user_id: str,
    num_questions: int = 20,
    subject_id: Optional[str] = None,
    chapter_ids: Optional[List[str]] = None,
    topic_ids: Optional[List[str]] = None,
    difficulty: Optional[str] = None
) -> List[Question]:
    """
    Generate a standard test based on filters.
    """
    query = supabase.table("repository_questions").select("*").eq("is_tagged", True)
    
    if subject_id:
        query = query.eq("subject_id", subject_id)
        
    if chapter_ids:
        # Supabase 'in' filter for array check
        query = query.in_("chapter_id", chapter_ids)
        
    if topic_ids:
        query = query.in_("topic_id", topic_ids)
        
    if difficulty:
        query = query.eq("difficulty_level", difficulty)
        
    # Execute query
    result = query.execute()
    all_questions = result.data
    
    if not all_questions:
        return []
        
    # Randomly select questions
    selected_data = random.sample(all_questions, min(len(all_questions), num_questions))
    
    return [await _map_repo_question(q) for q in selected_data]

async def generate_adaptive_test(
    user_id: str,
    num_questions: int = 20,
    focus_on_weak_areas: float = 0.7,
    subject_id: Optional[str] = None
) -> List[Question]:
    """
    Generate an adaptive test based on user's topic mastery.
    """
    # 1. Get User's Mastery
    mastery_query = supabase.table("topic_mastery").select("*").eq("user_id", user_id)
    if subject_id:
        # topic_mastery uses subject name, not ID. Resolve ID to name.
        try:
            sub_res = supabase.table("subjects").select("name").eq("id", subject_id).execute()
            if sub_res.data:
                subject_name = sub_res.data[0]["name"]
                mastery_query = mastery_query.eq("subject", subject_name)
        except Exception:
            # Fallback or just ignore if valid subject not found
            pass
    
    mastery_result = mastery_query.execute()
    mastery_data = mastery_result.data
    
    weak_topics = []
    strong_topics = []
    
    if mastery_data:
        # Filter by weak (< 70%) and strong (>= 70%)
        # Using topic names or IDs depending on what's stored. Current topic_mastery uses topic names.
        # We need to map these back to IDs to query repository_questions.
        # This is a bit complex without clear ID mapping. 
        # Ideally, we should fetch topic IDs for these names.
        
        # Strategy: Get all topics from DB to map Names -> IDs
        topics_lookup = await _get_topics_lookup()
        
        for m in mastery_data:
            t_id = topics_lookup.get(m["topic"])
            if t_id:
                if m["mastery_score"] < 70:
                    weak_topics.append(t_id)
                else:
                    strong_topics.append(t_id)
    
    # 2. Determine Question Distribution
    num_weak = int(num_questions * focus_on_weak_areas)
    num_other = num_questions - num_weak
    
    selected_questions = []
    
    # 3. Fetch Weak Area Questions
    if weak_topics:
        weak_q_result = supabase.table("repository_questions")\
            .select("*")\
            .in_("topic_id", weak_topics)\
            .execute()
        
        if weak_q_result.data:
            count = min(len(weak_q_result.data), num_weak)
            selected_questions.extend(random.sample(weak_q_result.data, count))
            
    # 4. Fetch Other/Random Questions (if needed to fill up)
    remaining_slots = num_questions - len(selected_questions)
    if remaining_slots > 0:
        # Fetch generic questions, potentially filtering out already selected IDs
        query = supabase.table("repository_questions").select("*").eq("is_tagged", True)
        if subject_id:
            query = query.eq("subject_id", subject_id)
            
        random_result = query.execute()
        if random_result.data:
            # Filter out already selected
            existing_ids = {q["id"] for q in selected_questions}
            pool = [q for q in random_result.data if q["id"] not in existing_ids]
            
            count = min(len(pool), remaining_slots)
            selected_questions.extend(random.sample(pool, count))
            
    return [await _map_repo_question(q) for q in selected_questions]

async def submit_test_attempts(
    test_id: str,
    user_id: str,
    attempts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Submit test attempts, calculate score (+4 correct, -1 incorrect).
    Updates topic mastery and test status.
    """
    # 1. Fetch Request to validate correct answers
    # We need the correct answers. We can get them from the attempts if trusted (not secure), 
    # OR we can re-fetch questions from DB. 
    # For this implementation, let's assume we trust the 'is_correct' flag passed from frontend 
    # (which checked against the Question object it received). 
    # SECURITY NOTE: In production, backend should re-calculate is_correct.
    # Let's re-calculate for robustness.
    
    question_ids = [a["question_id"] for a in attempts]
    
    # Fetch original questions to get correct answers and metadata (topic/chapter)
    # Note: If questions can be deleted, this might break. Assuming soft delete or stability.
    q_result = supabase.table("repository_questions").select("*").in_("id", question_ids).execute()
    question_map = {q["id"]: q for q in q_result.data} if q_result.data else {}
    
    processed_attempts = []
    total_score = 0
    correct_count = 0
    total_time = 0
    
    for attempt in attempts:
        q_id = attempt["question_id"]
        original_q = question_map.get(q_id)
        
        if not original_q:
            continue
            
        selected = attempt.get("selected_answer")
        is_correct = False
        score_change = 0
        
        if selected:
            if selected == original_q["correct_answer"]:
                is_correct = True
                score_change = 4
                correct_count += 1
            else:
                is_correct = False
                score_change = -1
        else:
            # Unattempted
            score_change = 0
            
        total_score += score_change
        time_spent = attempt.get("time_spent", 0)
        total_time += time_spent
        
        processed_attempts.append({
            "test_id": str(test_id),
            "user_id": user_id,
            "question_id": q_id,
            "selected_answer": selected,
            "is_correct": is_correct,
            "time_spent": time_spent,
            "marked_for_review": attempt.get("marked_for_review", False),
            "created_at": datetime.utcnow().isoformat()
        })

    # 2. Insert Attempts
    if processed_attempts:
        supabase.table("test_attempts").insert(processed_attempts).execute()
    
    # 3. Update Test Status
    supabase.table("tests").update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "score": total_score,
        "max_score": len(attempts) * 4, # Max possible
    }).eq("id", str(test_id)).execute()
    
    # 4. Update Analysis (Topic Mastery)
    await update_mastery_stats(user_id, processed_attempts, question_map)
    
    return {
        "test_id": str(test_id),
        "score": total_score,
        "max_score": len(attempts) * 4,
        "total_questions": len(attempts),
        "correct_answers": correct_count
    }

async def update_mastery_stats(user_id: str, attempts: List[Dict], question_map: Dict):
    """
    Update topic_mastery table. 
    Aggregates stats at topic level.
    """
    # Group by topic ID
    topic_aggregates = {}
    
    for att in attempts:
        q = question_map.get(att["question_id"])
        # Ensure we have a valid question and topic_id
        if not q or not q.get("topic_id"):
            continue
            
        t_id = str(q["topic_id"])
        
        if t_id not in topic_aggregates:
            topic_aggregates[t_id] = {
                "total": 0,
                "correct": 0,
                "subject_id": q.get("subject_id"), 
            }
        
        stats = topic_aggregates[t_id]
        stats["total"] += 1
        if att["is_correct"]:
            stats["correct"] += 1

    if not topic_aggregates:
        return

    topic_ids = list(topic_aggregates.keys())
    
    # Fetch Metadata (Names)
    metadata = {}
    if topic_ids:
        # Topics table has chapter_id, not subject_id. Need to join through chapters.
        t_res = supabase.table("topics").select("id, name, chapter_id").in_("id", topic_ids).execute()
        
        # Get chapter IDs to fetch subject IDs
        chapter_ids = {r["chapter_id"] for r in t_res.data if r.get("chapter_id")}
        c_res = supabase.table("chapters").select("id, subject_id").in_("id", list(chapter_ids)).execute()
        chapter_to_subject = {c["id"]: c["subject_id"] for c in c_res.data}
        
        # Get subject IDs to fetch names
        subj_ids = set(chapter_to_subject.values())
        s_res = supabase.table("subjects").select("id, name").in_("id", list(subj_ids)).execute()
        subj_map = {s["id"]: s["name"] for s in s_res.data}
        
        for t in t_res.data:
            chapter_id = t.get("chapter_id")
            subject_id = chapter_to_subject.get(chapter_id)
            s_name = subj_map.get(subject_id, "Unknown")
            metadata[t["id"]] = {
                "topic_name": t["name"],
                "subject_name": s_name
            }

    for t_id, stats in topic_aggregates.items():
        meta = metadata.get(t_id)
        if not meta:
            continue
            
        topic_name = meta["topic_name"]
        subject_name = normalize_subject(meta["subject_name"])
        
        # Check existing mastery
        existing = supabase.table("topic_mastery").select("*")\
            .eq("user_id", user_id)\
            .eq("topic", topic_name)\
            .eq("subject", subject_name)\
            .execute()
            
        if existing.data:
            # Update
            row = existing.data[0]
            old_total = row["questions_attempted"]
            old_correct = row["questions_correct"]
            
            new_total = old_total + stats["total"]
            new_correct = old_correct + stats["correct"]
            new_score = (new_correct / new_total * 100) if new_total > 0 else 0
            
            # Simple Trend Logic
            batch_score = (stats["correct"] / stats["total"] * 100)
            trend = "stable"
            if batch_score > row["mastery_score"] + 5:
                trend = "improving"
            elif batch_score < row["mastery_score"] - 5:
                trend = "declining"
                
            supabase.table("topic_mastery").update({
                "mastery_score": new_score,
                "questions_attempted": new_total,
                "questions_correct": new_correct,
                "trend": trend,
                "last_attempt_date": datetime.utcnow().isoformat()
            }).eq("id", row["id"]).execute()
        else:
            # Insert
            score = (stats["correct"] / stats["total"] * 100)
            supabase.table("topic_mastery").insert({
                "user_id": user_id,
                "subject": subject_name,
                "topic": topic_name,
                "mastery_score": score,
                "questions_attempted": stats["total"],
                "questions_correct": stats["correct"],
                "trend": "stable",
                "last_attempt_date": datetime.utcnow().isoformat()
            }).execute()

async def _map_repo_question(repo_q: Dict) -> Question:
    """
    Map DB row to Pydantic Model.
    Fetches Names for IDs.
    """
    # Fetch names for IDs - Optimization: Cache this or do joins.
    # For now, simplistic single fetches or just returning IDs.
    # Frontend might need names.
    
    # To keep it fast, we return IDs in the optional fields.
    # The frontend can resolve IDs if it has the metadata loaded, 
    # OR we do a join in `generate_test`. 
    # Supabase join: .select("*, topics(name), chapters(name), subjects(name)")
    
    # Let's assume we can get names if we update the query.
    
    # For basic implementation:
    options = []
    if repo_q.get("options"):
        # repo_options is list of dicts or similar. 
        # Model expects List[Option(id, text)]
        for idx, opt in enumerate(repo_q["options"]):
            # handle different structures
            if isinstance(opt, str):
                options.append({"id": str(idx), "text": opt})
            elif isinstance(opt, dict):
                options.append({"id": opt.get("id", str(idx)), "text": opt.get("text", "")})

    return Question(
        id=repo_q["id"],
        question=repo_q["question_text"],
        options=options,
        correct_answer=repo_q["correct_answer"] or "",
        explanation=repo_q.get("explanation") or "",
        difficulty=repo_q.get("difficulty_level") or "medium",
        topic_id=repo_q.get("topic_id"),
        chapter_id=repo_q.get("chapter_id"),
        subject_id=repo_q.get("subject_id"),
        # We fill names if we had them. For now, empty or IDs.
        topic=repo_q.get("topic_id"), 
        chapter=repo_q.get("chapter_id"),
        subject=repo_q.get("subject_id"),
        grade_level=[], # schema default
        answer_type="single_choice" # default
    )

async def _get_topics_lookup():
    """Helper to map Topic Name -> ID"""
    res = supabase.table("topics").select("id, name").execute()
    return {r["name"]: r["id"] for r in res.data}
