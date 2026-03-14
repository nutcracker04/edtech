from .user import (
    UserProfile,
    UserPreferences,
    UserTopicProgress,
    UserDailyStats,
    UserPerformanceSummary,
    convert_supabase_user_to_profile,
    convert_supabase_metadata_to_preferences,
    convert_mastery_to_topic_progress,
    convert_activity_to_daily_stats,
    create_performance_summary,
    update_user_profile_in_supabase,
    update_user_preferences_in_supabase,
    get_user_topic_progress_list,
    get_user_daily_stats_list,
    get_user_performance_summary,
)
# Legacy models for backward compatibility
from .test import (
    Test, 
    TestAttempt, 
    Question,
    Option,
    TestCreateRequest,
    TestSubmitRequest,
    QuestionNavigation,
    AnswerChange,
    convert_test_paper_to_legacy_format,
    convert_attempt_to_legacy_format,
    convert_question_to_legacy_format,
)
# Dashboard models and helpers
from .dashboard import (
    DashboardMetrics,
    StreakData,
    SubjectPerformance,
    ActivityItem,
    UpcomingTest,
    Recommendation,
    DashboardData,
    convert_metrics_to_legacy_format,
    convert_streak_to_legacy_format,
    convert_subject_performance_to_legacy_format,
    convert_activity_to_legacy_format,
    convert_upcoming_test_to_legacy_format,
    convert_recommendation_to_legacy_format,
)
# New database models
from .test_engine import (
    TestPaper,
    TestPaperQuestion,
    TestSession,
    Attempt,
    PaperType,
    SessionStatus,
)
from .hierarchy import Book, Chapter, Topic
from .extraction import (
    ExtractionJob,
    ExtractionStage,
    ExtractionPage,
    ExtractionBlock,
    RawQuestion,
    ProcessingStatus,
)
from .question import (
    Question as DBQuestion,
    QuestionType,
    Difficulty,
    Option as DBOption,
    Answer,
    QuestionImage,
    QuestionTable,
    QuestionTag,
)
from .analytics import (
    QuestionStats,
    StudentTopicMastery,
    MasteryLevel,
    DailyActivity,
)

__all__ = [
    # User models
    "UserProfile",
    "UserPreferences",
    "UserTopicProgress",
    "UserDailyStats",
    "UserPerformanceSummary",
    # User helper functions
    "convert_supabase_user_to_profile",
    "convert_supabase_metadata_to_preferences",
    "convert_mastery_to_topic_progress",
    "convert_activity_to_daily_stats",
    "create_performance_summary",
    "update_user_profile_in_supabase",
    "update_user_preferences_in_supabase",
    "get_user_topic_progress_list",
    "get_user_daily_stats_list",
    "get_user_performance_summary",
    # Legacy test models (deprecated)
    "Test",
    "TestAttempt",
    "Question",
    "Option",
    "TestCreateRequest",
    "TestSubmitRequest",
    "QuestionNavigation",
    "AnswerChange",
    # Backward compatibility helpers
    "convert_test_paper_to_legacy_format",
    "convert_attempt_to_legacy_format",
    "convert_question_to_legacy_format",
    # Dashboard models
    "DashboardMetrics",
    "StreakData",
    "SubjectPerformance",
    "ActivityItem",
    "UpcomingTest",
    "Recommendation",
    "DashboardData",
    # Dashboard helper functions
    "convert_metrics_to_legacy_format",
    "convert_streak_to_legacy_format",
    "convert_subject_performance_to_legacy_format",
    "convert_activity_to_legacy_format",
    "convert_upcoming_test_to_legacy_format",
    "convert_recommendation_to_legacy_format",
    # New database models
    "TestPaper",
    "TestPaperQuestion",
    "TestSession",
    "Attempt",
    "PaperType",
    "SessionStatus",
    # Hierarchy models
    "Book",
    "Chapter",
    "Topic",
    # Extraction models
    "ExtractionJob",
    "ExtractionStage",
    "ExtractionPage",
    "ExtractionBlock",
    "RawQuestion",
    "ProcessingStatus",
    # Question models
    "DBQuestion",
    "QuestionType",
    "Difficulty",
    "DBOption",
    "Answer",
    "QuestionImage",
    "QuestionTable",
    "QuestionTag",
    # Analytics models
    "QuestionStats",
    "StudentTopicMastery",
    "MasteryLevel",
    "DailyActivity",
]
