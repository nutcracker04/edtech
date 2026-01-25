from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class Option(BaseModel):
    id: str
    text: str


class Question(BaseModel):
    id: str
    question: str
    options: List[Option]
    correct_answer: str
    explanation: str
    difficulty: str  # 'easy', 'medium', 'hard'
    topic: str
    subject: str  # 'physics', 'chemistry', 'mathematics'
    grade_level: List[str]
    tags: Optional[List[str]] = []
    source: Optional[str] = None
    answer_type: str = "single_choice"  # 'single_choice', 'multiple_choice', 'integer', etc.


class Test(BaseModel):
    id: str
    user_id: str
    title: str
    type: str  # 'full', 'topic', 'practice', 'adaptive', 'uploaded'
    subject: Optional[str] = None
    status: str  # 'completed', 'in_progress', 'upcoming', 'paused'
    duration: int  # in minutes
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    questions: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class TestAttempt(BaseModel):
    id: str
    test_id: str
    user_id: str
    question_id: str
    selected_answer: Optional[str] = None
    is_correct: bool = False
    time_spent: int = 0  # in seconds
    marked_for_review: bool = False
    created_at: datetime


class TestCreateRequest(BaseModel):
    title: str
    type: str
    subject: Optional[str] = None
    duration: int
    number_of_questions: int = 20
    topics: Optional[List[str]] = None
    difficulty: Optional[str] = None


class TestSubmitRequest(BaseModel):
    test_id: str
    attempts: List[Dict[str, Any]]
