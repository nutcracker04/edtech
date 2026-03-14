"""
Legacy analysis models with backward compatibility adapters.

This module maintains backward compatibility with the old in-memory analysis models
while providing adapters to the new database-backed models in analytics.py.

DEPRECATED: Use models from analytics.py for new code.
This module is maintained for API backward compatibility only.

Requirements: 19.4, 19.6, 19.7
"""
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

# Import new database models
from app.models.analytics import (
    QuestionStats as DBQuestionStats,
    StudentTopicMastery as DBStudentTopicMastery,
    DailyActivity as DBDailyActivity,
    MasteryLevel
)


# ============================================================================
# Legacy Models (Deprecated - for backward compatibility only)
# ============================================================================

class PerformanceOverview(BaseModel):
    """Legacy performance overview model for backward compatibility."""
    accuracy_percentage: float
    questions_solved: int
    study_hours: float
    avg_time_per_question: float
    percentile_rank: Optional[float] = None

    @classmethod
    def from_db_analytics(
        cls,
        mastery_records: List[DBStudentTopicMastery],
        daily_activities: List[DBDailyActivity],
        percentile_rank: Optional[float] = None
    ) -> 'PerformanceOverview':
        """
        Convert database analytics models to legacy PerformanceOverview format.
        
        Args:
            mastery_records: List of student topic mastery records
            daily_activities: List of daily activity records
            percentile_rank: Optional percentile rank
        
        Returns:
            Legacy PerformanceOverview instance
        """
        # Calculate total questions and accuracy from mastery records
        total_questions = sum(m.questions_attempted for m in mastery_records)
        total_correct = sum(m.questions_correct for m in mastery_records)
        accuracy_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
        
        # Calculate study hours from daily activities
        total_minutes = sum(da.time_spent_minutes for da in daily_activities)
        study_hours = total_minutes / 60.0
        
        # Calculate average time per question
        avg_time_per_question = (total_minutes * 60 / total_questions) if total_questions > 0 else 0.0
        
        return cls(
            accuracy_percentage=round(accuracy_percentage, 2),
            questions_solved=total_questions,
            study_hours=round(study_hours, 2),
            avg_time_per_question=round(avg_time_per_question, 2),
            percentile_rank=percentile_rank
        )


class TrendDataPoint(BaseModel):
    """Legacy trend data point model for backward compatibility."""
    date: datetime
    accuracy: Optional[float] = None
    count: Optional[int] = None

    @classmethod
    def from_daily_activity(cls, daily_activity: DBDailyActivity, include_accuracy: bool = True) -> 'TrendDataPoint':
        """
        Convert database DailyActivity to legacy TrendDataPoint format.
        
        Args:
            daily_activity: Database daily activity model
            include_accuracy: Whether to include accuracy calculation
        
        Returns:
            Legacy TrendDataPoint instance
        """
        accuracy = None
        if include_accuracy and daily_activity.questions_attempted > 0:
            accuracy = (daily_activity.questions_correct / daily_activity.questions_attempted * 100)
        
        return cls(
            date=datetime.combine(daily_activity.activity_date, datetime.min.time()),
            accuracy=round(accuracy, 2) if accuracy is not None else None,
            count=daily_activity.questions_attempted
        )


class TopicData(BaseModel):
    """Legacy topic data model for backward compatibility."""
    topic_id: str
    topic_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal['up', 'down', 'flat']

    @classmethod
    def from_db_mastery(
        cls,
        mastery: DBStudentTopicMastery,
        topic_name: str = "Unknown Topic"
    ) -> 'TopicData':
        """
        Convert database StudentTopicMastery to legacy TopicData format.
        
        Args:
            mastery: Database student topic mastery model
            topic_name: Topic name (fetched from topics table)
        
        Returns:
            Legacy TopicData instance
        """
        # Determine trend based on mastery level
        trend_mapping = {
            MasteryLevel.NOT_STARTED: 'flat',
            MasteryLevel.LEARNING: 'down',
            MasteryLevel.DEVELOPING: 'flat',
            MasteryLevel.PROFICIENT: 'up',
            MasteryLevel.MASTERED: 'up'
        }
        
        return cls(
            topic_id=str(mastery.topic_id),
            topic_name=topic_name,
            accuracy_percentage=float(mastery.accuracy_pct),
            questions_solved=mastery.questions_attempted,
            trend=trend_mapping.get(mastery.mastery_level, 'flat')
        )


class SubjectBreakdown(BaseModel):
    """Legacy subject breakdown model for backward compatibility."""
    subject_id: str
    subject_name: str
    accuracy_percentage: float
    questions_solved: int
    trend: Literal['up', 'down', 'flat']
    topics: List[TopicData]

    @classmethod
    def from_db_mastery_list(
        cls,
        subject_id: str,
        subject_name: str,
        mastery_records: List[DBStudentTopicMastery],
        topic_names: Dict[str, str] = None
    ) -> 'SubjectBreakdown':
        """
        Convert list of database StudentTopicMastery records to legacy SubjectBreakdown format.
        
        Args:
            subject_id: Subject ID
            subject_name: Subject name
            mastery_records: List of student topic mastery records for this subject
            topic_names: Dictionary mapping topic_id to topic_name
        
        Returns:
            Legacy SubjectBreakdown instance
        """
        topic_names = topic_names or {}
        
        # Calculate aggregate metrics
        total_questions = sum(m.questions_attempted for m in mastery_records)
        total_correct = sum(m.questions_correct for m in mastery_records)
        accuracy_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
        
        # Determine overall trend based on average mastery level
        mastery_scores = {
            MasteryLevel.NOT_STARTED: 0,
            MasteryLevel.LEARNING: 25,
            MasteryLevel.DEVELOPING: 50,
            MasteryLevel.PROFICIENT: 75,
            MasteryLevel.MASTERED: 100
        }
        avg_mastery = sum(mastery_scores.get(m.mastery_level, 0) for m in mastery_records) / len(mastery_records) if mastery_records else 0
        
        if avg_mastery >= 75:
            trend = 'up'
        elif avg_mastery >= 50:
            trend = 'flat'
        else:
            trend = 'down'
        
        # Convert topics
        topics = [
            TopicData.from_db_mastery(m, topic_names.get(str(m.topic_id), "Unknown Topic"))
            for m in mastery_records
        ]
        
        return cls(
            subject_id=subject_id,
            subject_name=subject_name,
            accuracy_percentage=round(accuracy_percentage, 2),
            questions_solved=total_questions,
            trend=trend,
            topics=topics
        )


class WeakArea(BaseModel):
    """Legacy weak area model for backward compatibility."""
    topic_id: str
    topic_name: str
    accuracy_percentage: float
    impact_score: float
    recommended_action: str

    @classmethod
    def from_db_mastery(
        cls,
        mastery: DBStudentTopicMastery,
        topic_name: str = "Unknown Topic"
    ) -> 'WeakArea':
        """
        Convert database StudentTopicMastery to legacy WeakArea format.
        
        Args:
            mastery: Database student topic mastery model
            topic_name: Topic name (fetched from topics table)
        
        Returns:
            Legacy WeakArea instance
        """
        accuracy = float(mastery.accuracy_pct)
        
        # Calculate impact score (combination of low accuracy and questions attempted)
        impact_score = (100 - accuracy) * (mastery.questions_attempted / 100)
        
        return cls(
            topic_id=str(mastery.topic_id),
            topic_name=topic_name,
            accuracy_percentage=accuracy,
            impact_score=round(impact_score, 2),
            recommended_action=f"Practice 10 questions on {topic_name}"
        )


class AnalysisRecommendation(BaseModel):
    """Legacy analysis recommendation model for backward compatibility."""
    topic_id: str
    topic_name: str
    reason: str
    action: str
    difficulty: str
    estimated_time_minutes: int
    priority: Literal['high', 'medium', 'low']

    @classmethod
    def from_db_mastery(
        cls,
        mastery: DBStudentTopicMastery,
        topic_name: str = "Unknown Topic"
    ) -> 'AnalysisRecommendation':
        """
        Convert database StudentTopicMastery to legacy AnalysisRecommendation format.
        
        Args:
            mastery: Database student topic mastery model
            topic_name: Topic name (fetched from topics table)
        
        Returns:
            Legacy AnalysisRecommendation instance
        """
        accuracy = float(mastery.accuracy_pct)
        
        # Determine priority based on accuracy
        if accuracy < 40:
            priority = 'high'
            difficulty = 'easy'
        elif accuracy < 60:
            priority = 'high'
            difficulty = 'medium'
        else:
            priority = 'medium'
            difficulty = 'medium'
        
        return cls(
            topic_id=str(mastery.topic_id),
            topic_name=topic_name,
            reason=f"You scored {accuracy:.1f}% - this is a weak area",
            action=f"Practice 10 questions on {topic_name}",
            difficulty=difficulty,
            estimated_time_minutes=15,
            priority=priority
        )


class TrendData(BaseModel):
    """Legacy trend data model for backward compatibility."""
    accuracy_by_date: List[TrendDataPoint]
    questions_by_date: List[TrendDataPoint]

    @classmethod
    def from_db_daily_activities(cls, daily_activities: List[DBDailyActivity]) -> 'TrendData':
        """
        Convert list of database DailyActivity records to legacy TrendData format.
        
        Args:
            daily_activities: List of daily activity records
        
        Returns:
            Legacy TrendData instance
        """
        # Sort by date
        sorted_activities = sorted(daily_activities, key=lambda x: x.activity_date)
        
        accuracy_by_date = [
            TrendDataPoint.from_daily_activity(da, include_accuracy=True)
            for da in sorted_activities
        ]
        
        questions_by_date = [
            TrendDataPoint.from_daily_activity(da, include_accuracy=False)
            for da in sorted_activities
        ]
        
        return cls(
            accuracy_by_date=accuracy_by_date,
            questions_by_date=questions_by_date
        )


class AnalysisData(BaseModel):
    """Legacy analysis data model for backward compatibility."""
    user_id: str
    time_period: Literal['7d', '30d', '90d', 'all']
    performance_overview: PerformanceOverview
    subject_performance: List[SubjectBreakdown]
    trend_data: TrendData
    weak_areas: List[WeakArea]
    recommendations: List[AnalysisRecommendation]
    data_timestamp: datetime

    @classmethod
    def from_db_analytics(
        cls,
        user_id: UUID,
        time_period: Literal['7d', '30d', '90d', 'all'],
        mastery_records: List[DBStudentTopicMastery],
        daily_activities: List[DBDailyActivity],
        subject_grouping: Dict[str, List[DBStudentTopicMastery]],
        topic_names: Dict[str, str] = None,
        percentile_rank: Optional[float] = None
    ) -> 'AnalysisData':
        """
        Convert database analytics models to legacy AnalysisData format.
        
        Args:
            user_id: Student user ID
            time_period: Time period for analysis
            mastery_records: List of student topic mastery records
            daily_activities: List of daily activity records
            subject_grouping: Dictionary mapping subject_id to list of mastery records
            topic_names: Dictionary mapping topic_id to topic_name
            percentile_rank: Optional percentile rank
        
        Returns:
            Legacy AnalysisData instance
        """
        topic_names = topic_names or {}
        
        # Build performance overview
        performance_overview = PerformanceOverview.from_db_analytics(
            mastery_records,
            daily_activities,
            percentile_rank
        )
        
        # Build subject performance
        subject_performance = [
            SubjectBreakdown.from_db_mastery_list(
                subject_id,
                subject_id,  # Using subject_id as name for now
                records,
                topic_names
            )
            for subject_id, records in subject_grouping.items()
        ]
        
        # Build trend data
        trend_data = TrendData.from_db_daily_activities(daily_activities)
        
        # Build weak areas (topics with accuracy < 70%)
        weak_mastery = [m for m in mastery_records if float(m.accuracy_pct) < 70]
        weak_mastery.sort(key=lambda x: float(x.accuracy_pct))
        weak_areas = [
            WeakArea.from_db_mastery(m, topic_names.get(str(m.topic_id), "Unknown Topic"))
            for m in weak_mastery
        ]
        
        # Build recommendations (top 5 weak areas)
        recommendations = [
            AnalysisRecommendation.from_db_mastery(m, topic_names.get(str(m.topic_id), "Unknown Topic"))
            for m in weak_mastery[:5]
        ]
        
        return cls(
            user_id=str(user_id),
            time_period=time_period,
            performance_overview=performance_overview,
            subject_performance=subject_performance,
            trend_data=trend_data,
            weak_areas=weak_areas,
            recommendations=recommendations,
            data_timestamp=datetime.utcnow()
        )


# ============================================================================
# Backward Compatibility Helper Functions
# ============================================================================

def convert_question_stats_to_legacy_format(db_stats: DBQuestionStats) -> Dict[str, Any]:
    """
    Convert database QuestionStats to legacy API response format.
    
    This function ensures API backward compatibility by converting
    new database models to the format expected by existing API clients.
    
    Args:
        db_stats: Database question stats model
    
    Returns:
        Dictionary in legacy API format
    """
    return {
        'question_id': str(db_stats.question_id),
        'total_attempts': db_stats.total_attempts,
        'correct_attempts': db_stats.correct_attempts,
        'accuracy_percentage': float(db_stats.accuracy_pct),
        'avg_time_seconds': float(db_stats.avg_time_seconds),
        'skip_count': db_stats.skip_count,
        'hint_use_count': db_stats.hint_use_count,
        'explanation_view_count': db_stats.explanation_view_count,
        'most_common_wrong_answer': db_stats.most_common_wrong_answer,
        'discrimination_index': float(db_stats.discrimination_index) if db_stats.discrimination_index else None,
        'updated_at': db_stats.updated_at.isoformat()
    }


def convert_mastery_to_legacy_format(
    db_mastery: DBStudentTopicMastery,
    topic_name: str = "Unknown Topic"
) -> Dict[str, Any]:
    """
    Convert database StudentTopicMastery to legacy API response format.
    
    Args:
        db_mastery: Database student topic mastery model
        topic_name: Topic name (fetched from topics table)
    
    Returns:
        Dictionary in legacy API format
    """
    return {
        'id': str(db_mastery.id),
        'student_id': str(db_mastery.student_id),
        'topic_id': str(db_mastery.topic_id),
        'topic_name': topic_name,
        'chapter_id': str(db_mastery.chapter_id),
        'book_id': str(db_mastery.book_id),
        'questions_attempted': db_mastery.questions_attempted,
        'questions_correct': db_mastery.questions_correct,
        'accuracy_percentage': float(db_mastery.accuracy_pct),
        'mastery_level': db_mastery.mastery_level.value,
        'last_attempted_at': db_mastery.last_attempted_at.isoformat() if db_mastery.last_attempted_at else None,
        'streak_days': db_mastery.streak_days
    }


def convert_daily_activity_to_legacy_format(db_activity: DBDailyActivity) -> Dict[str, Any]:
    """
    Convert database DailyActivity to legacy API response format.
    
    Args:
        db_activity: Database daily activity model
    
    Returns:
        Dictionary in legacy API format
    """
    return {
        'id': str(db_activity.id),
        'student_id': str(db_activity.student_id),
        'activity_date': db_activity.activity_date.isoformat(),
        'sessions_count': db_activity.sessions_count,
        'questions_attempted': db_activity.questions_attempted,
        'questions_correct': db_activity.questions_correct,
        'time_spent_minutes': db_activity.time_spent_minutes,
        'accuracy_percentage': (db_activity.questions_correct / db_activity.questions_attempted * 100) if db_activity.questions_attempted > 0 else 0.0
    }


def convert_performance_overview_to_legacy_format(
    mastery_records: List[DBStudentTopicMastery],
    daily_activities: List[DBDailyActivity],
    percentile_rank: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convert database analytics to legacy PerformanceOverview API format.
    
    Args:
        mastery_records: List of student topic mastery records
        daily_activities: List of daily activity records
        percentile_rank: Optional percentile rank
    
    Returns:
        Dictionary in legacy API format
    """
    overview = PerformanceOverview.from_db_analytics(
        mastery_records,
        daily_activities,
        percentile_rank
    )
    return overview.model_dump()


def convert_trend_data_to_legacy_format(daily_activities: List[DBDailyActivity]) -> Dict[str, Any]:
    """
    Convert database DailyActivity records to legacy TrendData API format.
    
    Args:
        daily_activities: List of daily activity records
    
    Returns:
        Dictionary in legacy API format
    """
    trend_data = TrendData.from_db_daily_activities(daily_activities)
    return trend_data.model_dump()


def convert_weak_areas_to_legacy_format(
    mastery_records: List[DBStudentTopicMastery],
    topic_names: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Convert database StudentTopicMastery records to legacy WeakArea API format.
    
    Args:
        mastery_records: List of student topic mastery records (filtered for weak areas)
        topic_names: Dictionary mapping topic_id to topic_name
    
    Returns:
        List of dictionaries in legacy API format
    """
    topic_names = topic_names or {}
    weak_areas = [
        WeakArea.from_db_mastery(m, topic_names.get(str(m.topic_id), "Unknown Topic"))
        for m in mastery_records
    ]
    return [wa.model_dump() for wa in weak_areas]


def convert_recommendations_to_legacy_format(
    mastery_records: List[DBStudentTopicMastery],
    topic_names: Dict[str, str] = None
) -> List[Dict[str, Any]]:
    """
    Convert database StudentTopicMastery records to legacy AnalysisRecommendation API format.
    
    Args:
        mastery_records: List of student topic mastery records (filtered for weak areas)
        topic_names: Dictionary mapping topic_id to topic_name
    
    Returns:
        List of dictionaries in legacy API format
    """
    topic_names = topic_names or {}
    recommendations = [
        AnalysisRecommendation.from_db_mastery(m, topic_names.get(str(m.topic_id), "Unknown Topic"))
        for m in mastery_records
    ]
    return [rec.model_dump() for rec in recommendations]


def convert_full_analysis_to_legacy_format(
    user_id: UUID,
    time_period: Literal['7d', '30d', '90d', 'all'],
    mastery_records: List[DBStudentTopicMastery],
    daily_activities: List[DBDailyActivity],
    subject_grouping: Dict[str, List[DBStudentTopicMastery]],
    topic_names: Dict[str, str] = None,
    percentile_rank: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convert database analytics to legacy AnalysisData API format.
    
    Args:
        user_id: Student user ID
        time_period: Time period for analysis
        mastery_records: List of student topic mastery records
        daily_activities: List of daily activity records
        subject_grouping: Dictionary mapping subject_id to list of mastery records
        topic_names: Dictionary mapping topic_id to topic_name
        percentile_rank: Optional percentile rank
    
    Returns:
        Dictionary in legacy API format
    """
    analysis_data = AnalysisData.from_db_analytics(
        user_id,
        time_period,
        mastery_records,
        daily_activities,
        subject_grouping,
        topic_names,
        percentile_rank
    )
    return analysis_data.model_dump()
