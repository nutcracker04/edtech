"""
Legacy test models with backward compatibility adapters.

This module maintains backward compatibility with the old in-memory test models
while providing adapters to the new database-backed models in test_engine.py.

DEPRECATED: Use models from test_engine.py for new code.
This module is maintained for API backward compatibility only.

Requirements: 19.1, 19.6, 19.7
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# Import new database models
from app.models.test_engine import (
    TestPaper as DBTestPaper,
    TestPaperQuestion as DBTestPaperQuestion,
    TestSession as DBTestSession,
    Attempt as DBAttempt,
    PaperType,
    SessionStatus
)
from app.models.question import Question as DBQuestion, Option as DBOption


# ============================================================================
# Legacy Models (Deprecated - for backward compatibility only)
# ============================================================================

class Option(BaseModel):
    """Legacy option model for backward compatibility."""
    id: str
    text: str

    @classmethod
    def from_db_option(cls, db_option: DBOption) -> 'Option':
        """Convert database Option to legacy Option format."""
        return cls(
            id=str(db_option.id),
            text=db_option.text
        )

    def to_db_option(self, question_id: UUID, label: str, sort_order: int) -> DBOption:
        """Convert legacy Option to database Option format."""
        return DBOption(
            id=UUID(self.id) if self.id else None,
            question_id=question_id,
            label=label,
            text=self.text,
            is_correct=None,  # Set separately
            sort_order=sort_order
        )


class Question(BaseModel):
    """Legacy question model for backward compatibility."""
    id: str
    question: str
    options: List[Option]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: Optional[str] = None  # 'easy', 'medium', 'hard'
    topic: Optional[str] = None
    topic_id: Optional[str] = None
    chapter: Optional[str] = None
    chapter_id: Optional[str] = None
    subject: Optional[str] = None  # 'physics', 'chemistry', 'mathematics'
    subject_id: Optional[str] = None
    grade_level: Optional[List[str]] = None
    tags: Optional[List[str]] = []
    source: Optional[str] = None
    answer_type: str = "single_choice"  # 'single_choice', 'multiple_choice', 'integer', etc.

    @classmethod
    def from_db_question(cls, db_question: DBQuestion, options: List[DBOption] = None, 
                        correct_answer: str = None) -> 'Question':
        """
        Convert database Question to legacy Question format.
        
        Args:
            db_question: Database question model
            options: List of database options (if available)
            correct_answer: Correct answer string (if available)
        """
        legacy_options = []
        if options:
            legacy_options = [Option.from_db_option(opt) for opt in options]
        
        return cls(
            id=str(db_question.id),
            question=db_question.question_text,
            options=legacy_options,
            correct_answer=correct_answer or "",
            explanation=None,  # Fetch from explanations table if needed
            difficulty=db_question.difficulty.value if db_question.difficulty else None,
            topic=None,  # Fetch from topics table if needed
            topic_id=str(db_question.topic_id) if db_question.topic_id else None,
            chapter=None,  # Fetch from chapters table if needed
            chapter_id=str(db_question.chapter_id) if db_question.chapter_id else None,
            subject=db_question.sub_topic,  # Using sub_topic as subject for now
            subject_id=str(db_question.book_id) if db_question.book_id else None,
            grade_level=[],
            tags=[],  # Fetch from question_tags table if needed
            source=None,
            answer_type=db_question.answer_type.value if db_question.answer_type else "single_choice"
        )


class Test(BaseModel):
    """Legacy test model for backward compatibility."""
    id: str
    user_id: str
    title: str
    type: str  # 'full', 'topic', 'practice', 'adaptive'
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

    @classmethod
    def from_db_test_paper(cls, test_paper: DBTestPaper, test_session: DBTestSession = None,
                          questions: List[Dict[str, Any]] = None) -> 'Test':
        """
        Convert database TestPaper and TestSession to legacy Test format.
        
        Args:
            test_paper: Database test paper model
            test_session: Database test session model (if available)
            questions: List of question dictionaries (if available)
        """
        # Map paper_type to legacy test type
        type_mapping = {
            PaperType.CHAPTER_TEST: "topic",
            PaperType.FULL_SYLLABUS: "full",
            PaperType.TOPIC_TEST: "topic",
            PaperType.CUSTOM: "practice"
        }
        
        # Map session status to legacy status
        status = "upcoming"
        started_at = None
        completed_at = None
        score = None
        max_score = float(test_paper.total_marks)
        
        if test_session:
            status_mapping = {
                SessionStatus.IN_PROGRESS: "in_progress",
                SessionStatus.SUBMITTED: "completed",
                SessionStatus.TIMED_OUT: "completed",
                SessionStatus.ABANDONED: "paused"
            }
            status = status_mapping.get(test_session.status, "upcoming")
            started_at = test_session.started_at
            completed_at = test_session.submitted_at
            score = float(test_session.total_marks_obtained) if test_session.total_marks_obtained else None
        
        return cls(
            id=str(test_paper.id),
            user_id=str(test_session.student_id) if test_session else str(test_paper.created_by),
            title=test_paper.title,
            type=type_mapping.get(test_paper.paper_type, "practice"),
            subject=test_paper.subject,
            status=status,
            duration=test_paper.duration_minutes,
            scheduled_at=None,
            started_at=started_at,
            completed_at=completed_at,
            score=score,
            max_score=max_score,
            questions=questions or [],
            created_at=test_paper.created_at,
            updated_at=test_paper.created_at  # Using created_at as updated_at
        )

    def to_db_test_paper(self) -> DBTestPaper:
        """Convert legacy Test to database TestPaper format."""
        # Map legacy test type to paper_type
        type_mapping = {
            "full": PaperType.FULL_SYLLABUS,
            "topic": PaperType.TOPIC_TEST,
            "practice": PaperType.CUSTOM,
            "adaptive": PaperType.CUSTOM
        }
        
        return DBTestPaper(
            id=UUID(self.id) if self.id else None,
            title=self.title,
            description=None,
            book_id=None,
            chapter_id=None,
            subject=self.subject,
            grade_level=None,
            total_marks=Decimal(str(self.max_score)) if self.max_score else Decimal("0"),
            duration_minutes=self.duration,
            is_published=True,
            created_by=UUID(self.user_id),
            paper_type=type_mapping.get(self.type, PaperType.CUSTOM),
            negative_marking_scheme=None,
            created_at=self.created_at
        )


class TestAttempt(BaseModel):
    """Legacy test attempt model for backward compatibility."""
    id: str
    test_id: str
    user_id: str
    question_id: str
    selected_answer: Optional[str] = None
    is_correct: bool = False
    time_spent: int = 0  # in seconds
    marked_for_review: bool = False
    created_at: datetime
    # Enhanced time tracking fields
    question_order: Optional[int] = None
    first_viewed_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None
    view_count: int = 1
    answer_changed_count: int = 0

    @classmethod
    def from_db_attempt(cls, db_attempt: DBAttempt, test_id: str = None, 
                       user_id: str = None) -> 'TestAttempt':
        """
        Convert database Attempt to legacy TestAttempt format.
        
        Args:
            db_attempt: Database attempt model
            test_id: Test ID (if not available from db_attempt)
            user_id: User ID (if not available from db_attempt)
        """
        return cls(
            id=str(db_attempt.id),
            test_id=test_id or str(db_attempt.session_id),
            user_id=user_id or "",  # Need to fetch from session
            question_id=str(db_attempt.question_id),
            selected_answer=db_attempt.student_answer,
            is_correct=db_attempt.is_correct or False,
            time_spent=db_attempt.time_spent_seconds or 0,
            marked_for_review=db_attempt.flagged,
            created_at=db_attempt.created_at,
            question_order=None,
            first_viewed_at=None,
            last_viewed_at=None,
            view_count=1,
            answer_changed_count=0
        )

    def to_db_attempt(self, session_id: UUID, test_paper_question_id: UUID) -> DBAttempt:
        """Convert legacy TestAttempt to database Attempt format."""
        return DBAttempt(
            id=UUID(self.id) if self.id else None,
            session_id=session_id,
            question_id=UUID(self.question_id),
            test_paper_question_id=test_paper_question_id,
            student_answer=self.selected_answer,
            selected_option_ids=None,  # Parse from selected_answer if needed
            is_correct=self.is_correct,
            is_attempted=self.selected_answer is not None,
            marks_awarded=None,  # Calculate based on is_correct
            time_spent_seconds=self.time_spent,
            hint_used=False,
            explanation_viewed=False,
            flagged=self.marked_for_review,
            created_at=self.created_at
        )


class QuestionNavigation(BaseModel):
    """Tracks navigation between questions during test"""
    id: Optional[str] = None
    test_id: str
    user_id: str
    from_question_id: Optional[str] = None
    to_question_id: str
    from_question_index: Optional[int] = None
    to_question_index: int
    navigation_type: str  # 'next', 'previous', 'jump', 'review', 'initial'
    time_on_previous_question: Optional[int] = None  # seconds
    timestamp: datetime


class AnswerChange(BaseModel):
    """Tracks answer changes for analysis"""
    id: Optional[str] = None
    test_id: str
    user_id: str
    question_id: str
    question_index: int
    previous_answer: Optional[str] = None
    new_answer: Optional[str] = None
    change_type: str  # 'initial', 'modified', 'cleared'
    timestamp: datetime


# ============================================================================
# Request/Response Models
# ============================================================================

class TestCreateRequest(BaseModel):
    """Request model for creating a test."""
    title: str
    type: str
    source: str = "repository"  # 'repository' or 'pyq'
    subject: Optional[str] = None
    duration: int
    number_of_questions: int = 20
    topics: Optional[List[str]] = None
    topic_ids: Optional[List[str]] = None
    chapter_ids: Optional[List[str]] = None
    subject_id: Optional[str] = None
    difficulty: Optional[str] = None


class TestSubmitRequest(BaseModel):
    """Request model for submitting a test."""
    test_id: UUID
    attempts: List[Dict[str, Any]]
    navigation_log: Optional[List[Dict[str, Any]]] = []
    answer_changes: Optional[List[Dict[str, Any]]] = []


class TestTimeAnalysisRequest(BaseModel):
    """Request for time-based test analysis"""
    test_id: UUID


# ============================================================================
# Backward Compatibility Helper Functions
# ============================================================================

def convert_test_paper_to_legacy_format(
    test_paper: DBTestPaper,
    test_session: Optional[DBTestSession] = None,
    questions: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Convert database TestPaper to legacy API response format.
    
    This function ensures API backward compatibility by converting
    new database models to the format expected by existing API clients.
    
    Args:
        test_paper: Database test paper model
        test_session: Optional test session model
        questions: Optional list of question dictionaries
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_test = Test.from_db_test_paper(test_paper, test_session, questions)
    return legacy_test.model_dump()


def convert_attempt_to_legacy_format(
    db_attempt: DBAttempt,
    test_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert database Attempt to legacy API response format.
    
    Args:
        db_attempt: Database attempt model
        test_id: Optional test ID
        user_id: Optional user ID
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_attempt = TestAttempt.from_db_attempt(db_attempt, test_id, user_id)
    return legacy_attempt.model_dump()


def convert_question_to_legacy_format(
    db_question: DBQuestion,
    options: Optional[List[DBOption]] = None,
    correct_answer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert database Question to legacy API response format.
    
    Args:
        db_question: Database question model
        options: Optional list of database options
        correct_answer: Optional correct answer string
    
    Returns:
        Dictionary in legacy API format
    """
    legacy_question = Question.from_db_question(db_question, options, correct_answer)
    return legacy_question.model_dump()
