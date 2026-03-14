"""
Dashboard Data Models
Pydantic models for Dashboard API responses

REFACTORED: This module now uses database models from analytics.py and test_engine.py
while maintaining backward compatibility for API responses.

Requirements: 19.5, 19.6, 19.7
"""

from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime, date
from decimal import Decimal

# Import new database models
from app.models.analytics import (
    QuestionStats,
    StudentTopicMastery,
    DailyActivity,
    MasteryLevel
)
from app.models.test_engine import (
    TestSession,
    TestPaper,
    SessionStatus
)


# ============================================================================
# LEGACY MODELS (Maintained for backward compatibility)
# ============================================================================
# These models are used by existing API endpoints and should not be removed.
# New code should use the database models from analytics.py and test_engine.py
# ============================================================================


class DashboardMetrics(BaseModel):
    """
    Legacy model for dashboard metrics.
    
    DEPRECATED: Use StudentTopicMastery and DailyActivity for new code.
    Maintained for backward compatibility with existing API responses.
    """
    accuracy_percentage: float
    questions_solved: int
    study_hours: float
    tests_completed: int

    @classmethod
    def from_db_analytics(
        cls,
        mastery_records: List[StudentTopicMastery],
        activity_records: List[DailyActivity],
        session_records: List[TestSession]
    ) -> 'DashboardMetrics':
        """
        Convert database analytics to legacy DashboardMetrics format.
        
        Args:
            mastery_records: List of StudentTopicMastery records
            activity_records: List of DailyActivity records
            session_records: List of TestSession records
            
        Returns:
            DashboardMetrics with aggregated data
        """
        # Calculate total questions and accuracy from mastery records
        total_questions = sum(m.questions_attempted for m in mastery_records)
        total_correct = sum(m.questions_correct for m in mastery_records)
        accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
        
        # Calculate study hours from activity records
        total_minutes = sum(a.time_spent_minutes for a in activity_records)
        study_hours = total_minutes / 60.0
        
        # Count completed tests
        completed_tests = len([s for s in session_records if s.status == SessionStatus.SUBMITTED])
        
        return cls(
            accuracy_percentage=round(accuracy, 2),
            questions_solved=total_questions,
            study_hours=round(study_hours, 2),
            tests_completed=completed_tests
        )


class StreakData(BaseModel):
    """
    Legacy model for streak data.
    
    DEPRECATED: Use DailyActivity for new code.
    Maintained for backward compatibility with existing API responses.
    """
    current_streak: int
    streak_milestone_reached: bool
    milestone_value: Optional[int] = None

    @classmethod
    def from_db_activity(cls, activity_records: List[DailyActivity]) -> 'StreakData':
        """
        Convert DailyActivity records to legacy StreakData format.
        
        Args:
            activity_records: List of DailyActivity records sorted by date descending
            
        Returns:
            StreakData with calculated streak
        """
        if not activity_records:
            return cls(current_streak=0, streak_milestone_reached=False)
        
        # Calculate current streak
        current_streak = 0
        today = date.today()
        
        for i, record in enumerate(activity_records):
            expected_date = today - (record.activity_date - today)
            
            if record.activity_date == today - (i * (today - today)) and record.questions_attempted > 0:
                current_streak += 1
            else:
                break
        
        # Check if milestone reached (7, 14, 30 days)
        milestone_reached = current_streak in [7, 14, 30]
        milestone_value = current_streak if milestone_reached else None
        
        return cls(
            current_streak=current_streak,
            streak_milestone_reached=milestone_reached,
            milestone_value=milestone_value
        )


class SubjectPerformance(BaseModel):
    """
    Legacy model for subject performance.
    
    DEPRECATED: Use StudentTopicMastery for new code.
    Maintained for backward compatibility with existing API responses.
    """
    subject_id: str
    subject_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal["up", "down", "flat"]

    @classmethod
    def from_db_mastery(
        cls,
        subject_id: str,
        subject_name: str,
        mastery_records: List[StudentTopicMastery]
    ) -> 'SubjectPerformance':
        """
        Convert StudentTopicMastery records to legacy SubjectPerformance format.
        
        Args:
            subject_id: Subject identifier
            subject_name: Subject name
            mastery_records: List of StudentTopicMastery records for this subject
            
        Returns:
            SubjectPerformance with aggregated data
        """
        # Aggregate questions across all topics in subject
        total_questions = sum(m.questions_attempted for m in mastery_records)
        total_correct = sum(m.questions_correct for m in mastery_records)
        accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
        
        # Determine trend based on average mastery level
        if mastery_records:
            mastery_scores = {
                MasteryLevel.NOT_STARTED: 0,
                MasteryLevel.LEARNING: 25,
                MasteryLevel.DEVELOPING: 50,
                MasteryLevel.PROFICIENT: 75,
                MasteryLevel.MASTERED: 100
            }
            avg_mastery = sum(mastery_scores[m.mastery_level] for m in mastery_records) / len(mastery_records)
            
            if avg_mastery >= 75:
                trend = "up"
            elif avg_mastery >= 50:
                trend = "flat"
            else:
                trend = "down"
        else:
            trend = "flat"
        
        return cls(
            subject_id=subject_id,
            subject_name=subject_name,
            accuracy_percentage=round(accuracy, 2),
            questions_solved=total_questions,
            trend=trend
        )


class ActivityItem(BaseModel):
    """
    Legacy model for activity items.
    
    DEPRECATED: Use TestSession for new code.
    Maintained for backward compatibility with existing API responses.
    """
    id: str
    type: Literal["test_completed", "questions_solved", "topic_reviewed"]
    title: str
    score: Optional[float] = None
    timestamp: str
    link: Optional[str] = None

    @classmethod
    def from_db_session(cls, session: TestSession, paper: TestPaper) -> 'ActivityItem':
        """
        Convert TestSession to legacy ActivityItem format.
        
        Args:
            session: TestSession record
            paper: TestPaper record
            
        Returns:
            ActivityItem for test completion
        """
        return cls(
            id=str(session.id),
            type="test_completed",
            title=f"Completed: {paper.title}",
            score=float(session.percentage) if session.percentage else None,
            timestamp=session.submitted_at.isoformat() if session.submitted_at else session.created_at.isoformat(),
            link=f"/tests/{session.id}"
        )


class UpcomingTest(BaseModel):
    """
    Legacy model for upcoming tests.
    
    DEPRECATED: Use TestPaper and TestSession for new code.
    Maintained for backward compatibility with existing API responses.
    """
    test_id: str
    test_name: str
    test_type: Literal["mock", "pyq", "topic", "adaptive", "full", "practice"]
    date: str
    difficulty: Literal["easy", "medium", "hard"]

    @classmethod
    def from_db_paper(cls, paper: TestPaper, scheduled_date: Optional[datetime] = None) -> 'UpcomingTest':
        """
        Convert TestPaper to legacy UpcomingTest format.
        
        Args:
            paper: TestPaper record
            scheduled_date: Optional scheduled date
            
        Returns:
            UpcomingTest for the paper
        """
        # Map paper_type to legacy test_type
        type_mapping = {
            "chapter_test": "topic",
            "full_syllabus": "full",
            "topic_test": "topic",
            "custom": "practice"
        }
        
        return cls(
            test_id=str(paper.id),
            test_name=paper.title,
            test_type=type_mapping.get(paper.paper_type.value, "practice"),
            date=(scheduled_date or paper.created_at).isoformat(),
            difficulty="medium"  # Default difficulty
        )


class Recommendation(BaseModel):
    """
    Legacy model for recommendations.
    
    DEPRECATED: Use StudentTopicMastery for new code.
    Maintained for backward compatibility with existing API responses.
    """
    topic_id: str
    topic_name: str
    reason: str
    action: str
    difficulty: str
    estimated_time_minutes: int

    @classmethod
    def from_db_mastery(cls, mastery: StudentTopicMastery, topic_name: str) -> 'Recommendation':
        """
        Convert StudentTopicMastery to legacy Recommendation format.
        
        Args:
            mastery: StudentTopicMastery record
            topic_name: Topic name
            
        Returns:
            Recommendation for the topic
        """
        accuracy = float(mastery.accuracy_pct)
        
        # Determine difficulty and priority based on accuracy
        if accuracy < 40:
            difficulty = "easy"
            reason = f"You scored {accuracy:.1f}% - start with easier questions"
        elif accuracy < 60:
            difficulty = "medium"
            reason = f"You scored {accuracy:.1f}% - practice more to improve"
        else:
            difficulty = "medium"
            reason = f"You scored {accuracy:.1f}% - keep practicing to master this topic"
        
        return cls(
            topic_id=str(mastery.topic_id),
            topic_name=topic_name,
            reason=reason,
            action=f"Practice 10 questions on {topic_name}",
            difficulty=difficulty,
            estimated_time_minutes=15
        )


class DashboardData(BaseModel):
    """
    Legacy model for complete dashboard data.
    
    DEPRECATED: Use database models directly for new code.
    Maintained for backward compatibility with existing API responses.
    """
    user_id: str
    current_streak: int
    streak_milestone_reached: bool
    key_metrics: DashboardMetrics
    recent_activity: List[ActivityItem]
    subject_performance: List[SubjectPerformance]
    upcoming_tests: List[UpcomingTest]
    recommendation: Recommendation
    data_timestamp: str


# ============================================================================
# BACKWARD COMPATIBILITY HELPER FUNCTIONS
# ============================================================================
# These functions convert database models to legacy API response formats
# ============================================================================


def convert_metrics_to_legacy_format(
    mastery_records: List[StudentTopicMastery],
    activity_records: List[DailyActivity],
    session_records: List[TestSession]
) -> DashboardMetrics:
    """
    Convert database analytics to legacy DashboardMetrics format.
    
    Args:
        mastery_records: List of StudentTopicMastery records
        activity_records: List of DailyActivity records
        session_records: List of TestSession records
        
    Returns:
        DashboardMetrics with aggregated data
    """
    return DashboardMetrics.from_db_analytics(mastery_records, activity_records, session_records)


def convert_streak_to_legacy_format(activity_records: List[DailyActivity]) -> StreakData:
    """
    Convert DailyActivity records to legacy StreakData format.
    
    Args:
        activity_records: List of DailyActivity records sorted by date descending
        
    Returns:
        StreakData with calculated streak
    """
    return StreakData.from_db_activity(activity_records)


def convert_subject_performance_to_legacy_format(
    subject_id: str,
    subject_name: str,
    mastery_records: List[StudentTopicMastery]
) -> SubjectPerformance:
    """
    Convert StudentTopicMastery records to legacy SubjectPerformance format.
    
    Args:
        subject_id: Subject identifier
        subject_name: Subject name
        mastery_records: List of StudentTopicMastery records for this subject
        
    Returns:
        SubjectPerformance with aggregated data
    """
    return SubjectPerformance.from_db_mastery(subject_id, subject_name, mastery_records)


def convert_activity_to_legacy_format(
    session: TestSession,
    paper: TestPaper
) -> ActivityItem:
    """
    Convert TestSession to legacy ActivityItem format.
    
    Args:
        session: TestSession record
        paper: TestPaper record
        
    Returns:
        ActivityItem for test completion
    """
    return ActivityItem.from_db_session(session, paper)


def convert_upcoming_test_to_legacy_format(
    paper: TestPaper,
    scheduled_date: Optional[datetime] = None
) -> UpcomingTest:
    """
    Convert TestPaper to legacy UpcomingTest format.
    
    Args:
        paper: TestPaper record
        scheduled_date: Optional scheduled date
        
    Returns:
        UpcomingTest for the paper
    """
    return UpcomingTest.from_db_paper(paper, scheduled_date)


def convert_recommendation_to_legacy_format(
    mastery: StudentTopicMastery,
    topic_name: str
) -> Recommendation:
    """
    Convert StudentTopicMastery to legacy Recommendation format.
    
    Args:
        mastery: StudentTopicMastery record
        topic_name: Topic name
        
    Returns:
        Recommendation for the topic
    """
    return Recommendation.from_db_mastery(mastery, topic_name)
