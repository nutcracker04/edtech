"""
Analysis page data models and schemas
"""

from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


class PerformanceOverview(BaseModel):
    accuracy_percentage: float
    questions_solved: int
    study_hours: float
    avg_time_per_question: float
    percentile_rank: Optional[float] = None


class TrendDataPoint(BaseModel):
    date: datetime
    accuracy: Optional[float] = None
    count: Optional[int] = None


class TopicData(BaseModel):
    topic_id: str
    topic_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal['up', 'down', 'flat']


class SubjectBreakdown(BaseModel):
    subject_id: str
    subject_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal['up', 'down', 'flat']
    topics: List[TopicData]


class WeakArea(BaseModel):
    topic_id: str
    topic_name: str
    accuracy_percentage: float
    impact_score: float
    recommended_action: str


class AnalysisRecommendation(BaseModel):
    topic_id: str
    topic_name: str
    reason: str
    action: str
    difficulty: str
    estimated_time_minutes: int
    priority: Literal['high', 'medium', 'low']


class TrendData(BaseModel):
    accuracy_by_date: List[TrendDataPoint]
    questions_by_date: List[TrendDataPoint]


class AnalysisData(BaseModel):
    user_id: str
    time_period: Literal['7d', '30d', '90d', 'all']
    performance_overview: PerformanceOverview
    subject_performance: List[SubjectBreakdown]
    trend_data: TrendData
    weak_areas: List[WeakArea]
    recommendations: List[AnalysisRecommendation]
    data_timestamp: datetime
