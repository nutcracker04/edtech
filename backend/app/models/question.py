from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal
import re


class QuestionType(str, Enum):
    """
    Enum for question answer types.
    """
    MCQ_SINGLE = "mcq_single"
    MCQ_MULTIPLE = "mcq_multiple"
    INTEGER = "integer"
    NUMERICAL = "numerical"
    SUBJECTIVE = "subjective"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    MATCH = "match"


class Difficulty(str, Enum):
    """
    Enum for question difficulty levels.
    """
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(BaseModel):
    """
    Represents a question in the question bank.
    
    Validation Rules:
    - answer_type must match QuestionType enum
    - difficulty must match Difficulty enum
    
    Computed Properties:
    - has_image: Checks if question_text contains image markdown
    - has_table: Checks if question_text contains table markdown
    - has_math: Checks if question_text contains LaTeX math delimiters
    """
    id: UUID
    question_number: str  # '1', '2a', 'Q5'
    question_text: str  # Markdown with LaTeX
    topic_id: UUID
    chapter_id: UUID  # Denormalized for query performance
    book_id: UUID  # Denormalized
    sub_topic: Optional[str] = None
    answer_type: QuestionType
    difficulty: Difficulty
    page_number: Optional[int] = None
    marks: Optional[Decimal] = None
    negative_marks: Optional[Decimal] = None
    bloom_level: Optional[str] = None
    raw_question_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('answer_type')
    @classmethod
    def validate_answer_type(cls, v: QuestionType) -> QuestionType:
        if not isinstance(v, QuestionType):
            raise ValueError(f'answer_type must be a valid QuestionType enum value')
        return v

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Difficulty) -> Difficulty:
        if not isinstance(v, Difficulty):
            raise ValueError(f'difficulty must be a valid Difficulty enum value')
        return v

    @computed_field
    @property
    def has_image(self) -> bool:
        """Check if question_text contains image markdown syntax."""
        return bool(re.search(r'!\[.*?\]\(.*?\)', self.question_text))

    @computed_field
    @property
    def has_table(self) -> bool:
        """Check if question_text contains table markdown syntax."""
        return bool(re.search(r'\|.*\|', self.question_text))

    @computed_field
    @property
    def has_math(self) -> bool:
        """Check if question_text contains LaTeX math delimiters."""
        # Check for inline math $...$ or display math $$...$$ or \[...\] or \(...\)
        return bool(re.search(r'\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)', self.question_text))

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'question_number': self.question_number,
            'question_text': self.question_text,
            'topic_id': str(self.topic_id),
            'chapter_id': str(self.chapter_id),
            'book_id': str(self.book_id),
            'sub_topic': self.sub_topic,
            'answer_type': self.answer_type.value,
            'difficulty': self.difficulty.value,
            'page_number': self.page_number,
            'has_image': self.has_image,
            'has_table': self.has_table,
            'has_math': self.has_math,
            'marks': str(self.marks) if self.marks else None,
            'negative_marks': str(self.negative_marks) if self.negative_marks else None,
            'bloom_level': self.bloom_level,
            'raw_question_id': str(self.raw_question_id) if self.raw_question_id else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Question':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'topic_id' in data and isinstance(data['topic_id'], str):
            data['topic_id'] = UUID(data['topic_id'])
        if 'chapter_id' in data and isinstance(data['chapter_id'], str):
            data['chapter_id'] = UUID(data['chapter_id'])
        if 'book_id' in data and isinstance(data['book_id'], str):
            data['book_id'] = UUID(data['book_id'])
        if 'raw_question_id' in data and data['raw_question_id'] and isinstance(data['raw_question_id'], str):
            data['raw_question_id'] = UUID(data['raw_question_id'])
        
        # Convert enum strings to enum objects
        if 'answer_type' in data and isinstance(data['answer_type'], str):
            data['answer_type'] = QuestionType(data['answer_type'])
        if 'difficulty' in data and isinstance(data['difficulty'], str):
            data['difficulty'] = Difficulty(data['difficulty'])
        
        # Convert decimal strings to Decimal objects
        if 'marks' in data and data['marks'] and isinstance(data['marks'], str):
            data['marks'] = Decimal(data['marks'])
        if 'negative_marks' in data and data['negative_marks'] and isinstance(data['negative_marks'], str):
            data['negative_marks'] = Decimal(data['negative_marks'])
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)


class Option(BaseModel):
    """
    Represents an option for a multiple-choice question.
    
    Validation Rules:
    - label must be a single character A-Z
    """
    id: UUID
    question_id: UUID
    label: str  # 'A', 'B', 'C', 'D'
    text: str  # May contain LaTeX
    image_id: Optional[UUID] = None
    is_correct: Optional[bool] = None
    sort_order: int

    @field_validator('label')
    @classmethod
    def validate_label(cls, v: str) -> str:
        if not v or len(v) != 1 or not v.isalpha() or not v.isupper():
            raise ValueError('label must be a single uppercase character A-Z')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'question_id': str(self.question_id),
            'label': self.label,
            'text': self.text,
            'image_id': str(self.image_id) if self.image_id else None,
            'is_correct': self.is_correct,
            'sort_order': self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Option':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        if 'image_id' in data and data['image_id'] and isinstance(data['image_id'], str):
            data['image_id'] = UUID(data['image_id'])
        
        return cls(**data)


class Answer(BaseModel):
    """
    Represents the correct answer for a question.
    
    Validation Rules:
    - question_id must be unique (one answer per question)
    """
    id: UUID
    question_id: UUID
    correct_answer: str  # 'A' or 'A,C' or '3'
    correct_option_ids: Optional[List[UUID]] = None
    answer_source: str  # 'answer_key_section' | 'manual'
    page_number: Optional[int] = None
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'question_id': str(self.question_id),
            'correct_answer': self.correct_answer,
            'correct_option_ids': [str(oid) for oid in self.correct_option_ids] if self.correct_option_ids else None,
            'answer_source': self.answer_source,
            'page_number': self.page_number,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Answer':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        if 'correct_option_ids' in data and data['correct_option_ids']:
            data['correct_option_ids'] = [UUID(oid) if isinstance(oid, str) else oid for oid in data['correct_option_ids']]
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class QuestionImage(BaseModel):
    """
    Represents an image associated with a question.
    
    Validation Rules:
    - storage_path must be non-empty
    - position_in_question must be valid position value
    """
    id: UUID
    question_id: UUID
    storage_path: str  # Supabase storage path
    alt_text: Optional[str] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    position_in_question: str  # 'question' | 'option_a' | 'option_b' | 'option_c' | 'option_d' | 'explanation' | 'hint'
    sort_order: int
    created_at: datetime

    @field_validator('position_in_question')
    @classmethod
    def validate_position(cls, v: str) -> str:
        valid_positions = ['question', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'option_f', 'explanation', 'hint']
        if v not in valid_positions:
            raise ValueError(f'position_in_question must be one of {valid_positions}')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'question_id': str(self.question_id),
            'storage_path': self.storage_path,
            'alt_text': self.alt_text,
            'width_px': self.width_px,
            'height_px': self.height_px,
            'position_in_question': self.position_in_question,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QuestionImage':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class QuestionTable(BaseModel):
    """
    Represents a table associated with a question.
    
    Validation Rules:
    - headers must be a list of strings
    - rows must be a list of lists (JSONB in database)
    """
    id: UUID
    question_id: UUID
    headers: List[str]
    rows: List[List[str]]  # JSONB in database
    caption: Optional[str] = None
    sort_order: int

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'question_id': str(self.question_id),
            'headers': self.headers,
            'rows': self.rows,
            'caption': self.caption,
            'sort_order': self.sort_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QuestionTable':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        return cls(**data)


class QuestionTag(BaseModel):
    """
    Represents a tag associated with a question.
    
    Validation Rules:
    - (question_id, tag) must be unique
    - source must be 'auto' or 'manual'
    """
    question_id: UUID
    tag: str  # 'mcq', 'calculation', 'has-image', 'conceptual', 'numerical', 'diagram-based'
    source: str = "auto"  # 'auto' | 'manual'

    @field_validator('source')
    @classmethod
    def validate_source(cls, v: str) -> str:
        if v not in ['auto', 'manual']:
            raise ValueError("source must be 'auto' or 'manual'")
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'question_id': str(self.question_id),
            'tag': self.tag,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'QuestionTag':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'question_id' in data and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        return cls(**data)
