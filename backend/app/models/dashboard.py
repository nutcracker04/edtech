"""
Dashboard Data Models
Pydantic models for Dashboard API responses
"""

from pydantic import BaseModel
from typing import List, Optional, Literal


class DashboardMetrics(BaseModel):
    accuracy_percentage: float
    questions_solved: int
    study_hours: float
    tests_completed: int


class StreakData(BaseModel):
    current_streak: int
    streak_milestone_reached: bool
    milestone_value: Optional[int] = None


class SubjectPerformance(BaseModel):
    subject_id: str
    subject_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal["up", "down", "flat"]


class ActivityItem(BaseModel):
    id: str
    type: Literal["test_completed", "questions_solved", "topic_reviewed"]
    title: str
    score: Optional[float] = None
    timestamp: str
    link: Optional[str] = None


class UpcomingTest(BaseModel):
    test_id: str
    test_name: str
    test_type: Literal["mock", "pyq", "topic", "adaptive", "full", "practice"]
    date: str
    difficulty: Literal["easy", "medium", "hard"]


class Recommendation(BaseModel):
    topic_id: str
    topic_name: str
    reason: str
    action: str
    difficulty: str
    estimated_time_minutes: int


class DashboardData(BaseModel):
    user_id: str
    current_streak: int
    streak_milestone_reached: bool
    key_metrics: DashboardMetrics
    recent_activity: List[ActivityItem]
    subject_performance: List[SubjectPerformance]
    upcoming_tests: List[UpcomingTest]
    recommendation: Recommendation
    data_timestamp: str
