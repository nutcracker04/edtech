from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal


class PaperType(str, Enum):
    """
    Enum for test paper types.
    """
    CHAPTER_TEST = "chapter_test"
    FULL_SYLLABUS = "full_syllabus"
    TOPIC_TEST = "topic_test"
    CUSTOM = "custom"


class SessionStatus(str, Enum):
    """
    Enum for test session status.
    """
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    TIMED_OUT = "timed_out"
    ABANDONED = "abandoned"


class TestPaper(BaseModel):
    """
    Represents a test paper created from the question bank.
    
    Validation Rules:
    - duration_minutes must be positive
    - total_marks must be positive
    - paper_type must match PaperType enum
    
    Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
    """
    id: UUID
    title: str
    description: Optional[str] = None
    book_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    total_marks: Decimal
    duration_minutes: int
    is_published: bool = False
    created_by: UUID  # Teacher/admin user
    paper_type: PaperType = PaperType.CHAPTER_TEST
    negative_marking_scheme: Optional[Dict[str, Decimal]] = None  # JSONB
    created_at: datetime

    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v <= 0:
            raise ValueError('duration_minutes must be positive')
        return v

    @field_validator('total_marks')
    @classmethod
    def validate_total_marks(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('total_marks must be positive')
        return v

    @field_validator('paper_type')
    @classmethod
    def validate_paper_type(cls, v: PaperType) -> PaperType:
        if not isinstance(v, PaperType):
            raise ValueError('paper_type must be a valid PaperType enum value')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'book_id': str(self.book_id) if self.book_id else None,
            'chapter_id': str(self.chapter_id) if self.chapter_id else None,
            'subject': self.subject,
            'grade_level': self.grade_level,
            'total_marks': str(self.total_marks),
            'duration_minutes': self.duration_minutes,
            'is_published': self.is_published,
            'created_by': str(self.created_by),
            'paper_type': self.paper_type.value,
            'negative_marking_scheme': {k: str(v) for k, v in self.negative_marking_scheme.items()} if self.negative_marking_scheme else None,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TestPaper':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'book_id' in data and data['book_id'] and isinstance(data['book_id'], str):
            data['book_id'] = UUID(data['book_id'])
        if 'chapter_id' in data and data['chapter_id'] and isinstance(data['chapter_id'], str):
            data['chapter_id'] = UUID(data['chapter_id'])
        if 'created_by' in data and isinstance(data['created_by'], str):
            data['created_by'] = UUID(data['created_by'])
        
        # Convert enum strings to enum objects
        if 'paper_type' in data and isinstance(data['paper_type'], str):
            data['paper_type'] = PaperType(data['paper_type'])
        
        # Convert decimal strings to Decimal objects
        if 'total_marks' in data and isinstance(data['total_marks'], str):
            data['total_marks'] = Decimal(data['total_marks'])
        if 'negative_marking_scheme' in data and data['negative_marking_scheme']:
            data['negative_marking_scheme'] = {k: Decimal(v) if isinstance(v, str) else v for k, v in data['negative_marking_scheme'].items()}
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class TestPaperQuestion(BaseModel):
    """
    Represents a question in a test paper.
    
    Validation Rules:
    - (test_paper_id, question_id) must be unique (enforced at database level)
    
    Requirements: 9.4
    """
    id: UUID
    test_paper_id: UUID
    question_id: UUID
    sort_order: int
    marks: Decimal
    negative_marks: Decimal = Decimal("0")
    section_label: Optional[str] = None  # 'Section A', 'Section B'

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'test_paper_id': str(self.test_paper_id),
            'question_id': str(self.question_id),
            'sort_order': self.sort_order,
            'marks': str(self.marks),
            'negative_marks': str(self.negative_marks),
            'section_label': self.section_label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TestPaperQuestion':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'test_paper_id' in data and isinstance(data['test_paper_id'], str):
            data['test_paper_id'] = UUID(data['test_paper_id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        # Convert decimal strings to Decimal objects
        if 'marks' in data and isinstance(data['marks'], str):
            data['marks'] = Decimal(data['marks'])
        if 'negative_marks' in data and isinstance(data['negative_marks'], str):
            data['negative_marks'] = Decimal(data['negative_marks'])
        
        return cls(**data)


class TestSession(BaseModel):
    """
    Represents a student's test session.
    
    Validation Rules:
    - submitted_at must be after started_at
    - status must match SessionStatus enum
    
    Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
    """
    id: UUID
    test_paper_id: UUID
    student_id: UUID
    started_at: datetime
    submitted_at: Optional[datetime] = None
    time_taken_seconds: Optional[int] = None
    status: SessionStatus
    total_marks_obtained: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    rank: Optional[int] = None
    is_practice: bool = False
    created_at: datetime

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: SessionStatus) -> SessionStatus:
        if not isinstance(v, SessionStatus):
            raise ValueError('status must be a valid SessionStatus enum value')
        return v

    @model_validator(mode='after')
    def validate_submitted_at(self):
        """Validate that submitted_at is after started_at."""
        if self.submitted_at is not None and self.submitted_at < self.started_at:
            raise ValueError('submitted_at must be after started_at')
        return self

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'test_paper_id': str(self.test_paper_id),
            'student_id': str(self.student_id),
            'started_at': self.started_at.isoformat(),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'time_taken_seconds': self.time_taken_seconds,
            'status': self.status.value,
            'total_marks_obtained': str(self.total_marks_obtained) if self.total_marks_obtained is not None else None,
            'percentage': str(self.percentage) if self.percentage is not None else None,
            'rank': self.rank,
            'is_practice': self.is_practice,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TestSession':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'test_paper_id' in data and isinstance(data['test_paper_id'], str):
            data['test_paper_id'] = UUID(data['test_paper_id'])
        if 'student_id' in data and isinstance(data['student_id'], str):
            data['student_id'] = UUID(data['student_id'])
        
        # Convert enum strings to enum objects
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = SessionStatus(data['status'])
        
        # Convert decimal strings to Decimal objects
        if 'total_marks_obtained' in data and data['total_marks_obtained'] is not None and isinstance(data['total_marks_obtained'], str):
            data['total_marks_obtained'] = Decimal(data['total_marks_obtained'])
        if 'percentage' in data and data['percentage'] is not None and isinstance(data['percentage'], str):
            data['percentage'] = Decimal(data['percentage'])
        
        # Convert ISO format strings back to datetime objects
        if 'started_at' in data and isinstance(data['started_at'], str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'submitted_at' in data and data['submitted_at'] and isinstance(data['submitted_at'], str):
            data['submitted_at'] = datetime.fromisoformat(data['submitted_at'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class Attempt(BaseModel):
    """
    Represents a student's attempt at a question in a test session.
    
    Validation Rules:
    - (session_id, question_id) must be unique (enforced at database level)
    
    Requirements: 11.1, 11.2, 11.3, 11.4
    """
    id: UUID
    session_id: UUID
    question_id: UUID
    test_paper_question_id: UUID
    student_answer: Optional[str] = None
    selected_option_ids: Optional[List[UUID]] = None
    is_correct: Optional[bool] = None
    is_attempted: bool = False
    marks_awarded: Optional[Decimal] = None
    time_spent_seconds: Optional[int] = None
    hint_used: bool = False
    explanation_viewed: bool = False
    flagged: bool = False
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'question_id': str(self.question_id),
            'test_paper_question_id': str(self.test_paper_question_id),
            'student_answer': self.student_answer,
            'selected_option_ids': [str(oid) for oid in self.selected_option_ids] if self.selected_option_ids else None,
            'is_correct': self.is_correct,
            'is_attempted': self.is_attempted,
            'marks_awarded': str(self.marks_awarded) if self.marks_awarded is not None else None,
            'time_spent_seconds': self.time_spent_seconds,
            'hint_used': self.hint_used,
            'explanation_viewed': self.explanation_viewed,
            'flagged': self.flagged,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Attempt':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'session_id' in data and isinstance(data['session_id'], str):
            data['session_id'] = UUID(data['session_id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        if 'test_paper_question_id' in data and isinstance(data['test_paper_question_id'], str):
            data['test_paper_question_id'] = UUID(data['test_paper_question_id'])
        if 'selected_option_ids' in data and data['selected_option_ids']:
            data['selected_option_ids'] = [UUID(oid) if isinstance(oid, str) else oid for oid in data['selected_option_ids']]
        
        # Convert decimal strings to Decimal objects
        if 'marks_awarded' in data and data['marks_awarded'] is not None and isinstance(data['marks_awarded'], str):
            data['marks_awarded'] = Decimal(data['marks_awarded'])
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
