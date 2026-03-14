from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from enum import Enum
from decimal import Decimal


class MasteryLevel(str, Enum):
    """
    Enum for student mastery levels.
    """
    NOT_STARTED = "not_started"
    LEARNING = "learning"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class QuestionStats(BaseModel):
    """
    Represents aggregated statistics for a question.
    
    Validation Rules:
    - accuracy_pct must be between 0 and 100
    - discrimination_index must be between -1 and 1
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    question_id: UUID  # Primary key
    total_attempts: int = 0
    correct_attempts: int = 0
    accuracy_pct: Decimal
    avg_time_seconds: Decimal
    skip_count: int = 0
    hint_use_count: int = 0
    explanation_view_count: int = 0
    most_common_wrong_answer: Optional[str] = None
    discrimination_index: Optional[Decimal] = None  # Psychometric measure
    updated_at: datetime

    @field_validator('accuracy_pct')
    @classmethod
    def validate_accuracy_pct(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError('accuracy_pct must be between 0 and 100')
        return v

    @field_validator('discrimination_index')
    @classmethod
    def validate_discrimination_index(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and (v < -1 or v > 1):
            raise ValueError('discrimination_index must be between -1 and 1')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'question_id': str(self.question_id),
            'total_attempts': self.total_attempts,
            'correct_attempts': self.correct_attempts,
            'accuracy_pct': str(self.accuracy_pct),
            'avg_time_seconds': str(self.avg_time_seconds),
            'skip_count': self.skip_count,
            'hint_use_count': self.hint_use_count,
            'explanation_view_count': self.explanation_view_count,
            'most_common_wrong_answer': self.most_common_wrong_answer,
            'discrimination_index': str(self.discrimination_index) if self.discrimination_index is not None else None,
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QuestionStats':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        # Convert decimal strings to Decimal objects
        if 'accuracy_pct' in data and isinstance(data['accuracy_pct'], str):
            data['accuracy_pct'] = Decimal(data['accuracy_pct'])
        if 'avg_time_seconds' in data and isinstance(data['avg_time_seconds'], str):
            data['avg_time_seconds'] = Decimal(data['avg_time_seconds'])
        if 'discrimination_index' in data and data['discrimination_index'] is not None and isinstance(data['discrimination_index'], str):
            data['discrimination_index'] = Decimal(data['discrimination_index'])
        
        # Convert ISO format strings back to datetime objects
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


class StudentTopicMastery(BaseModel):
    """
    Represents a student's mastery level for a specific topic.
    
    Validation Rules:
    - (student_id, topic_id) must be unique (enforced at database level)
    - accuracy_pct must be between 0 and 100
    - mastery_level must match MasteryLevel enum
    
    Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
    """
    id: UUID
    student_id: UUID
    topic_id: UUID
    chapter_id: UUID  # Denormalized
    book_id: UUID  # Denormalized
    questions_attempted: int = 0
    questions_correct: int = 0
    accuracy_pct: Decimal
    mastery_level: MasteryLevel
    last_attempted_at: Optional[datetime] = None
    streak_days: int = 0

    @field_validator('accuracy_pct')
    @classmethod
    def validate_accuracy_pct(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError('accuracy_pct must be between 0 and 100')
        return v

    @field_validator('mastery_level')
    @classmethod
    def validate_mastery_level(cls, v: MasteryLevel) -> MasteryLevel:
        if not isinstance(v, MasteryLevel):
            raise ValueError('mastery_level must be a valid MasteryLevel enum value')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'topic_id': str(self.topic_id),
            'chapter_id': str(self.chapter_id),
            'book_id': str(self.book_id),
            'questions_attempted': self.questions_attempted,
            'questions_correct': self.questions_correct,
            'accuracy_pct': str(self.accuracy_pct),
            'mastery_level': self.mastery_level.value,
            'last_attempted_at': self.last_attempted_at.isoformat() if self.last_attempted_at else None,
            'streak_days': self.streak_days,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'StudentTopicMastery':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'student_id' in data and isinstance(data['student_id'], str):
            data['student_id'] = UUID(data['student_id'])
        if 'topic_id' in data and isinstance(data['topic_id'], str):
            data['topic_id'] = UUID(data['topic_id'])
        if 'chapter_id' in data and isinstance(data['chapter_id'], str):
            data['chapter_id'] = UUID(data['chapter_id'])
        if 'book_id' in data and isinstance(data['book_id'], str):
            data['book_id'] = UUID(data['book_id'])
        
        # Convert enum strings to enum objects
        if 'mastery_level' in data and isinstance(data['mastery_level'], str):
            data['mastery_level'] = MasteryLevel(data['mastery_level'])
        
        # Convert decimal strings to Decimal objects
        if 'accuracy_pct' in data and isinstance(data['accuracy_pct'], str):
            data['accuracy_pct'] = Decimal(data['accuracy_pct'])
        
        # Convert ISO format strings back to datetime objects
        if 'last_attempted_at' in data and data['last_attempted_at'] and isinstance(data['last_attempted_at'], str):
            data['last_attempted_at'] = datetime.fromisoformat(data['last_attempted_at'])
        
        return cls(**data)


class DailyActivity(BaseModel):
    """
    Represents a student's daily activity summary.
    
    Validation Rules:
    - (student_id, activity_date) must be unique (enforced at database level)
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
    """
    id: UUID
    student_id: UUID
    activity_date: date
    sessions_count: int
    questions_attempted: int
    questions_correct: int
    time_spent_minutes: int

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'activity_date': self.activity_date.isoformat(),
            'sessions_count': self.sessions_count,
            'questions_attempted': self.questions_attempted,
            'questions_correct': self.questions_correct,
            'time_spent_minutes': self.time_spent_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DailyActivity':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'student_id' in data and isinstance(data['student_id'], str):
            data['student_id'] = UUID(data['student_id'])
        
        # Convert ISO format strings back to date objects
        if 'activity_date' in data and isinstance(data['activity_date'], str):
            data['activity_date'] = date.fromisoformat(data['activity_date'])
        
        return cls(**data)
