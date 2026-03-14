from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class Book(BaseModel):
    """
    Represents a textbook in the hierarchy.
    
    Validation Rules:
    - grade_level must be in [7, 8, 9, 10]
    - subject must be in ['Chemistry', 'Physics', 'Mathematics']
    """
    id: UUID
    title: str
    subject: str  # 'Chemistry', 'Physics', 'Mathematics'
    grade_level: int  # 7, 8, 9, 10
    publisher: Optional[str] = None
    series: Optional[str] = None
    isbn: Optional[str] = None
    edition: Optional[str] = None
    language: str = "en"
    source_pdf_path: Optional[str] = None
    extraction_job_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    @field_validator('grade_level')
    @classmethod
    def validate_grade_level(cls, v: int) -> int:
        if v not in [7, 8, 9, 10]:
            raise ValueError('grade_level must be in [7, 8, 9, 10]')
        return v

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        valid_subjects = ['Chemistry', 'Physics', 'Mathematics']
        if v not in valid_subjects:
            raise ValueError(f'subject must be one of {valid_subjects}')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'title': self.title,
            'subject': self.subject,
            'grade_level': self.grade_level,
            'publisher': self.publisher,
            'series': self.series,
            'isbn': self.isbn,
            'edition': self.edition,
            'language': self.language,
            'source_pdf_path': self.source_pdf_path,
            'extraction_job_id': str(self.extraction_job_id) if self.extraction_job_id else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Book':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'extraction_job_id' in data and data['extraction_job_id'] and isinstance(data['extraction_job_id'], str):
            data['extraction_job_id'] = UUID(data['extraction_job_id'])
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class Chapter(BaseModel):
    """
    Represents a chapter within a book.
    
    Validation Rules:
    - chapter_number must be unique within book_id (enforced at database level)
    """
    id: UUID
    book_id: UUID
    chapter_number: int
    title: str
    slug: str  # URL-safe identifier
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'book_id': str(self.book_id),
            'chapter_number': self.chapter_number,
            'title': self.title,
            'slug': self.slug,
            'page_start': self.page_start,
            'page_end': self.page_end,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Chapter':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'book_id' in data and isinstance(data['book_id'], str):
            data['book_id'] = UUID(data['book_id'])
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class Topic(BaseModel):
    """
    Represents a topic within a chapter.
    
    Validation Rules:
    - slug must be unique within chapter_id (enforced at database level)
    """
    id: UUID
    chapter_id: UUID
    title: str
    slug: str  # Used as topic_id in MetadataTagger
    topic_order: int
    section_type: str  # 'questions' | 'hints' | 'explanations' | 'answer_key'
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    created_at: datetime

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'chapter_id': str(self.chapter_id),
            'title': self.title,
            'slug': self.slug,
            'topic_order': self.topic_order,
            'section_type': self.section_type,
            'page_start': self.page_start,
            'page_end': self.page_end,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Topic':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'chapter_id' in data and isinstance(data['chapter_id'], str):
            data['chapter_id'] = UUID(data['chapter_id'])
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)
