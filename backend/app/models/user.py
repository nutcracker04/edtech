"""
Legacy user models with backward compatibility adapters.

This module maintains backward compatibility with the old in-memory user models
while providing adapters to Supabase Auth and new database-backed analytics models.

DEPRECATED: Use Supabase Auth directly for user management and models from 
analytics.py for user-related data. This module is maintained for API backward 
compatibility only.

Requirements: 19.3, 19.6, 19.7
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

# Import new database models for user-related data
from app.models.analytics import (
    StudentTopicMastery as DBStudentTopicMastery,
    DailyActivity as DBDailyActivity,
    MasteryLevel
)


# ============================================================================
# Legacy Models (Deprecated - for backward compatibility only)
# ============================================================================

class UserProfile(BaseModel):
    """
    Legacy user profile model for backward compatibility.
    
    DEPRECATED: Use Supabase Auth user object directly.
    This model maps to Supabase Auth user with user_metadata.
    """
    id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    grade: str  # '9', '10', '11', '12'
    syllabus: str  # 'cbse', 'icse', 'state'
    target_exam: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_supabase_user(cls, supabase_user: Dict[str, Any]) -> 'UserProfile':
        """
        Convert Supabase Auth user object to legacy UserProfile format.
        
        Args:
            supabase_user: Supabase Auth user object (dict format)
        
        Returns:
            Legacy UserProfile instance
        
        Example supabase_user structure:
        {
            "id": "uuid",
            "email": "user@example.com",
            "user_metadata": {
                "name": "John Doe",
                "phone": "+1234567890",
                "grade": "10",
                "syllabus": "cbse",
                "target_exam": "JEE"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        """
        user_metadata = supabase_user.get('user_metadata', {})
        
        return cls(
            id=str(supabase_user['id']),
            email=supabase_user['email'],
            name=user_metadata.get('name', ''),
            phone=user_metadata.get('phone'),
            grade=user_metadata.get('grade', '10'),
            syllabus=user_metadata.get('syllabus', 'cbse'),
            target_exam=user_metadata.get('target_exam', ''),
            created_at=datetime.fromisoformat(supabase_user['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(supabase_user.get('updated_at', supabase_user['created_at']).replace('Z', '+00:00'))
        )

    def to_supabase_metadata(self) -> Dict[str, Any]:
        """
        Convert UserProfile to Supabase user_metadata format.
        
        Returns:
            Dictionary suitable for Supabase Auth user_metadata field
        """
        return {
            "name": self.name,
            "phone": self.phone,
            "grade": self.grade,
            "syllabus": self.syllabus,
            "target_exam": self.target_exam
        }


class UserPreferences(BaseModel):
    """
    Legacy user preferences model for backward compatibility.
    
    DEPRECATED: Store preferences in Supabase Auth user_metadata or 
    a dedicated user_preferences table.
    """
    id: str
    user_id: str
    daily_goal: int = 20
    focus_subjects: List[str] = []
    difficulty_level: str = "adaptive"
    notifications_enabled: bool = True
    daily_reminders: bool = True
    dark_mode: bool = False
    created_at: datetime
    updated_at: datetime

    @field_validator('daily_goal')
    @classmethod
    def validate_daily_goal(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError('daily_goal must be between 1 and 100')
        return v

    @field_validator('difficulty_level')
    @classmethod
    def validate_difficulty_level(cls, v: str) -> str:
        valid_levels = ['easy', 'medium', 'hard', 'adaptive']
        if v not in valid_levels:
            raise ValueError(f'difficulty_level must be one of {valid_levels}')
        return v

    @classmethod
    def from_supabase_metadata(cls, user_id: str, user_metadata: Dict[str, Any]) -> 'UserPreferences':
        """
        Convert Supabase user_metadata to legacy UserPreferences format.
        
        Args:
            user_id: User ID
            user_metadata: Supabase Auth user_metadata dictionary
        
        Returns:
            Legacy UserPreferences instance
        """
        preferences = user_metadata.get('preferences', {})
        
        return cls(
            id=user_id,  # Using user_id as preferences id
            user_id=user_id,
            daily_goal=preferences.get('daily_goal', 20),
            focus_subjects=preferences.get('focus_subjects', []),
            difficulty_level=preferences.get('difficulty_level', 'adaptive'),
            notifications_enabled=preferences.get('notifications_enabled', True),
            daily_reminders=preferences.get('daily_reminders', True),
            dark_mode=preferences.get('dark_mode', False),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def to_supabase_metadata(self) -> Dict[str, Any]:
        """
        Convert UserPreferences to Supabase user_metadata format.
        
        Returns:
            Dictionary suitable for Supabase Auth user_metadata.preferences field
        """
        return {
            "preferences": {
                "daily_goal": self.daily_goal,
                "focus_subjects": self.focus_subjects,
                "difficulty_level": self.difficulty_level,
                "notifications_enabled": self.notifications_enabled,
                "daily_reminders": self.daily_reminders,
                "dark_mode": self.dark_mode
            }
        }


# ============================================================================
# User Analytics Models (Adapters to new database models)
# ============================================================================

class UserTopicProgress(BaseModel):
    """
    Legacy user topic progress model for backward compatibility.
    Maps to StudentTopicMastery from analytics.py.
    """
    topic_id: str
    topic_name: Optional[str] = None
    chapter_id: str
    chapter_name: Optional[str] = None
    subject: Optional[str] = None
    questions_attempted: int
    questions_correct: int
    accuracy: float  # Percentage (0-100)
    mastery_level: str  # 'not_started', 'learning', 'developing', 'proficient', 'mastered'
    last_attempted: Optional[datetime] = None
    streak_days: int = 0

    @classmethod
    def from_db_mastery(cls, db_mastery: DBStudentTopicMastery, 
                       topic_name: Optional[str] = None,
                       chapter_name: Optional[str] = None,
                       subject: Optional[str] = None) -> 'UserTopicProgress':
        """
        Convert database StudentTopicMastery to legacy UserTopicProgress format.
        
        Args:
            db_mastery: Database student topic mastery model
            topic_name: Optional topic name (fetch from topics table if needed)
            chapter_name: Optional chapter name (fetch from chapters table if needed)
            subject: Optional subject name (fetch from books table if needed)
        
        Returns:
            Legacy UserTopicProgress instance
        """
        return cls(
            topic_id=str(db_mastery.topic_id),
            topic_name=topic_name,
            chapter_id=str(db_mastery.chapter_id),
            chapter_name=chapter_name,
            subject=subject,
            questions_attempted=db_mastery.questions_attempted,
            questions_correct=db_mastery.questions_correct,
            accuracy=float(db_mastery.accuracy_pct),
            mastery_level=db_mastery.mastery_level.value,
            last_attempted=db_mastery.last_attempted_at,
            streak_days=db_mastery.streak_days
        )


class UserDailyStats(BaseModel):
    """
    Legacy user daily stats model for backward compatibility.
    Maps to DailyActivity from analytics.py.
    """
    date: date
    sessions_count: int
    questions_attempted: int
    questions_correct: int
    time_spent_minutes: int
    accuracy: float  # Percentage (0-100)

    @classmethod
    def from_db_activity(cls, db_activity: DBDailyActivity) -> 'UserDailyStats':
        """
        Convert database DailyActivity to legacy UserDailyStats format.
        
        Args:
            db_activity: Database daily activity model
        
        Returns:
            Legacy UserDailyStats instance
        """
        # Calculate accuracy percentage
        accuracy = 0.0
        if db_activity.questions_attempted > 0:
            accuracy = (db_activity.questions_correct / db_activity.questions_attempted) * 100
        
        return cls(
            date=db_activity.activity_date,
            sessions_count=db_activity.sessions_count,
            questions_attempted=db_activity.questions_attempted,
            questions_correct=db_activity.questions_correct,
            time_spent_minutes=db_activity.time_spent_minutes,
            accuracy=accuracy
        )


class UserPerformanceSummary(BaseModel):
    """
    Aggregated user performance summary combining multiple data sources.
    """
    user_id: str
    total_questions_attempted: int
    total_questions_correct: int
    overall_accuracy: float  # Percentage (0-100)
    total_time_spent_minutes: int
    total_sessions: int
    current_streak_days: int
    topics_mastered: int
    topics_in_progress: int
    topics_not_started: int
    last_activity_date: Optional[date] = None

    @classmethod
    def from_analytics_data(
        cls,
        user_id: str,
        daily_activities: List[DBDailyActivity],
        topic_masteries: List[DBStudentTopicMastery]
    ) -> 'UserPerformanceSummary':
        """
        Create performance summary from analytics data.
        
        Args:
            user_id: User ID
            daily_activities: List of daily activity records
            topic_masteries: List of topic mastery records
        
        Returns:
            UserPerformanceSummary instance
        """
        # Aggregate daily activities
        total_questions_attempted = sum(da.questions_attempted for da in daily_activities)
        total_questions_correct = sum(da.questions_correct for da in daily_activities)
        total_time_spent_minutes = sum(da.time_spent_minutes for da in daily_activities)
        total_sessions = sum(da.sessions_count for da in daily_activities)
        
        # Calculate overall accuracy
        overall_accuracy = 0.0
        if total_questions_attempted > 0:
            overall_accuracy = (total_questions_correct / total_questions_attempted) * 100
        
        # Calculate streak (consecutive days with activity)
        current_streak_days = 0
        if daily_activities:
            sorted_activities = sorted(daily_activities, key=lambda x: x.activity_date, reverse=True)
            last_activity_date = sorted_activities[0].activity_date
            
            # Count consecutive days from today backwards
            current_date = date.today()
            for activity in sorted_activities:
                if activity.activity_date == current_date:
                    current_streak_days += 1
                    current_date = current_date.replace(day=current_date.day - 1)
                else:
                    break
        else:
            last_activity_date = None
        
        # Count topics by mastery level
        topics_mastered = sum(1 for tm in topic_masteries if tm.mastery_level == MasteryLevel.MASTERED)
        topics_in_progress = sum(1 for tm in topic_masteries if tm.mastery_level in [
            MasteryLevel.LEARNING, MasteryLevel.DEVELOPING, MasteryLevel.PROFICIENT
        ])
        topics_not_started = sum(1 for tm in topic_masteries if tm.mastery_level == MasteryLevel.NOT_STARTED)
        
        return cls(
            user_id=user_id,
            total_questions_attempted=total_questions_attempted,
            total_questions_correct=total_questions_correct,
            overall_accuracy=overall_accuracy,
            total_time_spent_minutes=total_time_spent_minutes,
            total_sessions=total_sessions,
            current_streak_days=current_streak_days,
            topics_mastered=topics_mastered,
            topics_in_progress=topics_in_progress,
            topics_not_started=topics_not_started,
            last_activity_date=last_activity_date
        )


# ============================================================================
# Backward Compatibility Helper Functions
# ============================================================================

def convert_supabase_user_to_profile(supabase_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Supabase Auth user to legacy UserProfile API format.
    
    This function ensures API backward compatibility by converting
    Supabase Auth user objects to the format expected by existing API clients.
    
    Args:
        supabase_user: Supabase Auth user object (dict format)
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_profile = UserProfile.from_supabase_user(supabase_user)
    return legacy_profile.model_dump()


def convert_supabase_metadata_to_preferences(
    user_id: str,
    user_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert Supabase user_metadata to legacy UserPreferences API format.
    
    Args:
        user_id: User ID
        user_metadata: Supabase Auth user_metadata dictionary
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_preferences = UserPreferences.from_supabase_metadata(user_id, user_metadata)
    return legacy_preferences.model_dump()


def convert_mastery_to_topic_progress(
    db_mastery: DBStudentTopicMastery,
    topic_name: Optional[str] = None,
    chapter_name: Optional[str] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert database StudentTopicMastery to legacy UserTopicProgress API format.
    
    Args:
        db_mastery: Database student topic mastery model
        topic_name: Optional topic name
        chapter_name: Optional chapter name
        subject: Optional subject name
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_progress = UserTopicProgress.from_db_mastery(
        db_mastery, topic_name, chapter_name, subject
    )
    return legacy_progress.model_dump()


def convert_activity_to_daily_stats(db_activity: DBDailyActivity) -> Dict[str, Any]:
    """
    Convert database DailyActivity to legacy UserDailyStats API format.
    
    Args:
        db_activity: Database daily activity model
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_stats = UserDailyStats.from_db_activity(db_activity)
    return legacy_stats.model_dump()


def create_performance_summary(
    user_id: str,
    daily_activities: List[DBDailyActivity],
    topic_masteries: List[DBStudentTopicMastery]
) -> Dict[str, Any]:
    """
    Create user performance summary from analytics data.
    
    Args:
        user_id: User ID
        daily_activities: List of daily activity records
        topic_masteries: List of topic mastery records
    
    Returns:
        Dictionary with performance summary
    """
    summary = UserPerformanceSummary.from_analytics_data(
        user_id, daily_activities, topic_masteries
    )
    return summary.model_dump()


def update_user_profile_in_supabase(
    supabase_client,
    user_id: str,
    profile_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update user profile in Supabase Auth user_metadata.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to update
        profile_data: Profile data dictionary (name, phone, grade, syllabus, target_exam)
    
    Returns:
        Updated user object in legacy format
    
    Example:
        updated_user = update_user_profile_in_supabase(
            supabase,
            "user-uuid",
            {"name": "John Doe", "grade": "10", "syllabus": "cbse"}
        )
    """
    # Update user metadata in Supabase Auth
    response = supabase_client.auth.admin.update_user_by_id(
        user_id,
        {"user_metadata": profile_data}
    )
    
    # Convert to legacy format
    return convert_supabase_user_to_profile(response.user.__dict__)


def update_user_preferences_in_supabase(
    supabase_client,
    user_id: str,
    preferences_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update user preferences in Supabase Auth user_metadata.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID to update
        preferences_data: Preferences data dictionary
    
    Returns:
        Updated preferences in legacy format
    
    Example:
        updated_prefs = update_user_preferences_in_supabase(
            supabase,
            "user-uuid",
            {"daily_goal": 30, "dark_mode": True}
        )
    """
    # Get current user metadata
    user = supabase_client.auth.admin.get_user_by_id(user_id)
    current_metadata = user.user.user_metadata or {}
    
    # Merge preferences
    current_metadata['preferences'] = {
        **current_metadata.get('preferences', {}),
        **preferences_data
    }
    
    # Update user metadata
    response = supabase_client.auth.admin.update_user_by_id(
        user_id,
        {"user_metadata": current_metadata}
    )
    
    # Convert to legacy format
    return convert_supabase_metadata_to_preferences(
        user_id,
        response.user.user_metadata
    )


def get_user_topic_progress_list(
    supabase_client,
    user_id: str,
    include_names: bool = True
) -> List[Dict[str, Any]]:
    """
    Get user's topic progress list from StudentTopicMastery table.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        include_names: Whether to fetch topic/chapter/subject names
    
    Returns:
        List of topic progress dictionaries in legacy format
    """
    # Query student_topic_mastery table
    response = supabase_client.table('student_topic_mastery') \
        .select('*') \
        .eq('student_id', user_id) \
        .execute()
    
    progress_list = []
    for row in response.data:
        # Convert to StudentTopicMastery model
        db_mastery = DBStudentTopicMastery.from_dict(row)
        
        # Optionally fetch names
        topic_name = None
        chapter_name = None
        subject = None
        
        if include_names:
            # Fetch topic name
            topic_response = supabase_client.table('topics') \
                .select('title') \
                .eq('id', str(db_mastery.topic_id)) \
                .single() \
                .execute()
            if topic_response.data:
                topic_name = topic_response.data['title']
            
            # Fetch chapter name
            chapter_response = supabase_client.table('chapters') \
                .select('title') \
                .eq('id', str(db_mastery.chapter_id)) \
                .single() \
                .execute()
            if chapter_response.data:
                chapter_name = chapter_response.data['title']
            
            # Fetch subject from book
            book_response = supabase_client.table('books') \
                .select('subject') \
                .eq('id', str(db_mastery.book_id)) \
                .single() \
                .execute()
            if book_response.data:
                subject = book_response.data['subject']
        
        # Convert to legacy format
        progress_dict = convert_mastery_to_topic_progress(
            db_mastery, topic_name, chapter_name, subject
        )
        progress_list.append(progress_dict)
    
    return progress_list


def get_user_daily_stats_list(
    supabase_client,
    user_id: str,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get user's daily stats for the last N days from DailyActivity table.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
        days: Number of days to fetch (default 30)
    
    Returns:
        List of daily stats dictionaries in legacy format
    """
    # Calculate start date
    start_date = date.today().replace(day=date.today().day - days)
    
    # Query daily_activity table
    response = supabase_client.table('daily_activity') \
        .select('*') \
        .eq('student_id', user_id) \
        .gte('activity_date', start_date.isoformat()) \
        .order('activity_date', desc=True) \
        .execute()
    
    stats_list = []
    for row in response.data:
        # Convert to DailyActivity model
        db_activity = DBDailyActivity.from_dict(row)
        
        # Convert to legacy format
        stats_dict = convert_activity_to_daily_stats(db_activity)
        stats_list.append(stats_dict)
    
    return stats_list


def get_user_performance_summary(
    supabase_client,
    user_id: str
) -> Dict[str, Any]:
    """
    Get comprehensive user performance summary.
    
    Args:
        supabase_client: Supabase client instance
        user_id: User ID
    
    Returns:
        Performance summary dictionary
    """
    # Fetch all daily activities
    daily_response = supabase_client.table('daily_activity') \
        .select('*') \
        .eq('student_id', user_id) \
        .execute()
    
    daily_activities = [DBDailyActivity.from_dict(row) for row in daily_response.data]
    
    # Fetch all topic masteries
    mastery_response = supabase_client.table('student_topic_mastery') \
        .select('*') \
        .eq('student_id', user_id) \
        .execute()
    
    topic_masteries = [DBStudentTopicMastery.from_dict(row) for row in mastery_response.data]
    
    # Create summary
    return create_performance_summary(user_id, daily_activities, topic_masteries)
