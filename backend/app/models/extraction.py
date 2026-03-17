from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal


class ExtractionStage(str, Enum):
    """
    Enum for extraction job stages.
    """
    QUEUED = "queued"
    VALIDATION = "validation"
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStatus(str, Enum):
    """
    Enum for raw question processing status.
    """
    PENDING = "pending"
    TAGGED = "tagged"
    ERROR = "error"


class ExtractionJob(BaseModel):
    """
    Represents a PDF extraction job in the extraction pipeline.
    
    Validation Rules:
    - progress must be between 0.0 and 100.0
    - stage must match ExtractionStage enum
    
    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
    """
    model_config = {"from_attributes": True}
    
    id: UUID
    book_id: Optional[UUID] = None
    title: Optional[str] = None  # Admin-entered name for display in listing
    source_pdf_filename: str
    source_pdf_path: Optional[str] = None
    stage: ExtractionStage
    progress: Decimal  # 0.0 - 100.0
    total_pages: Optional[int] = None
    pages_processed: int = 0
    questions_extracted: int = 0
    success_rate: Optional[Decimal] = None
    error: Optional[str] = None
    manifest_path: Optional[str] = None
    extracted_path: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[Decimal] = None
    sarvam_job_ids: Optional[List[str]] = None  # JSONB
    created_at: datetime

    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 100:
            raise ValueError('progress must be between 0 and 100')
        return v

    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v: ExtractionStage) -> ExtractionStage:
        if not isinstance(v, ExtractionStage):
            raise ValueError('stage must be a valid ExtractionStage enum value')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'book_id': str(self.book_id) if self.book_id else None,
            'source_pdf_filename': self.source_pdf_filename,
            'source_pdf_path': self.source_pdf_path,
            'stage': self.stage.value,
            'progress': str(self.progress),
            'total_pages': self.total_pages,
            'pages_processed': self.pages_processed,
            'questions_extracted': self.questions_extracted,
            'success_rate': str(self.success_rate) if self.success_rate else None,
            'error': self.error,
            'manifest_path': self.manifest_path,
            'extracted_path': self.extracted_path,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time_seconds': str(self.processing_time_seconds) if self.processing_time_seconds else None,
            'sarvam_job_ids': self.sarvam_job_ids,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractionJob':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'book_id' in data and data['book_id'] and isinstance(data['book_id'], str):
            data['book_id'] = UUID(data['book_id'])
        
        # Convert enum strings to enum objects
        if 'stage' in data and isinstance(data['stage'], str):
            data['stage'] = ExtractionStage(data['stage'])
        
        # Convert decimal strings to Decimal objects
        if 'progress' in data and isinstance(data['progress'], str):
            data['progress'] = Decimal(data['progress'])
        if 'success_rate' in data and data['success_rate'] and isinstance(data['success_rate'], str):
            data['success_rate'] = Decimal(data['success_rate'])
        if 'processing_time_seconds' in data and data['processing_time_seconds'] and isinstance(data['processing_time_seconds'], str):
            data['processing_time_seconds'] = Decimal(data['processing_time_seconds'])
        
        # Convert ISO format strings back to datetime objects
        if 'started_at' in data and data['started_at'] and isinstance(data['started_at'], str):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if 'completed_at' in data and data['completed_at'] and isinstance(data['completed_at'], str):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class ExtractionPage(BaseModel):
    """
    Represents a page extracted from a PDF in the extraction pipeline.
    
    Validation Rules:
    - (job_id, page_num) must be unique (enforced at database level)
    
    Requirements: 7.2
    """
    id: UUID
    job_id: UUID
    page_num: int
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    created_at: datetime
    raw_json_path: Optional[str] = None
    block_count: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'job_id': str(self.job_id),
            'page_num': self.page_num,
            'image_width': self.image_width,
            'image_height': self.image_height,
            'created_at': self.created_at.isoformat(),
            'raw_json_path': self.raw_json_path,
            'block_count': self.block_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractionPage':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'job_id' in data and isinstance(data['job_id'], str):
            data['job_id'] = UUID(data['job_id'])
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)


class ExtractionBlock(BaseModel):
    """
    Represents a block extracted from a page in the extraction pipeline.
    
    Validation Rules:
    - confidence must be between 0.0 and 1.0
    
    Requirements: 7.3
    """
    id: UUID  # Same as Sarvam block_id
    page_id: UUID
    job_id: UUID
    block_index: int
    layout_tag: str  # 'headline' | 'paragraph' | 'image' | 'table'
    confidence: Decimal
    reading_order: Optional[int] = None
    text: Optional[str] = None
    x1: Optional[Decimal] = None
    y1: Optional[Decimal] = None
    x2: Optional[Decimal] = None
    y2: Optional[Decimal] = None
    raw_block: Dict[str, Any]  # JSONB

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: Decimal) -> Decimal:
        if v < 0 or v > 1:
            raise ValueError('confidence must be between 0 and 1')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'page_id': str(self.page_id),
            'job_id': str(self.job_id),
            'block_index': self.block_index,
            'layout_tag': self.layout_tag,
            'confidence': str(self.confidence),
            'reading_order': self.reading_order,
            'text': self.text,
            'x1': str(self.x1) if self.x1 is not None else None,
            'y1': str(self.y1) if self.y1 is not None else None,
            'x2': str(self.x2) if self.x2 is not None else None,
            'y2': str(self.y2) if self.y2 is not None else None,
            'raw_block': self.raw_block,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ExtractionBlock':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'page_id' in data and isinstance(data['page_id'], str):
            data['page_id'] = UUID(data['page_id'])
        if 'job_id' in data and isinstance(data['job_id'], str):
            data['job_id'] = UUID(data['job_id'])
        
        # Convert decimal strings to Decimal objects
        if 'confidence' in data and isinstance(data['confidence'], str):
            data['confidence'] = Decimal(data['confidence'])
        if 'x1' in data and data['x1'] is not None and isinstance(data['x1'], str):
            data['x1'] = Decimal(data['x1'])
        if 'y1' in data and data['y1'] is not None and isinstance(data['y1'], str):
            data['y1'] = Decimal(data['y1'])
        if 'x2' in data and data['x2'] is not None and isinstance(data['x2'], str):
            data['x2'] = Decimal(data['x2'])
        if 'y2' in data and data['y2'] is not None and isinstance(data['y2'], str):
            data['y2'] = Decimal(data['y2'])
        
        return cls(**data)


class RawQuestion(BaseModel):
    """
    Represents a raw extracted question before tagging with metadata.
    
    Validation Rules:
    - processing_status must match ProcessingStatus enum
    
    Requirements: 8.1, 8.2, 8.3, 8.4
    """
    id: UUID
    job_id: UUID
    question_number: str
    question_text: str
    options: List[str]  # JSONB
    page_number: Optional[int] = None
    chapter_context: Optional[str] = None
    topic_context: Optional[str] = None
    sub_topic_context: Optional[str] = None
    raw_images: Optional[List[Dict[str, Any]]] = None  # JSONB
    raw_tables: Optional[List[Dict[str, Any]]] = None  # JSONB
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    question_id: Optional[UUID] = None  # Set after tagging
    created_at: datetime

    @field_validator('processing_status')
    @classmethod
    def validate_processing_status(cls, v: ProcessingStatus) -> ProcessingStatus:
        if not isinstance(v, ProcessingStatus):
            raise ValueError('processing_status must be a valid ProcessingStatus enum value')
        return v

    def to_dict(self) -> dict:
        """Convert model to dictionary for serialization."""
        return {
            'id': str(self.id),
            'job_id': str(self.job_id),
            'question_number': self.question_number,
            'question_text': self.question_text,
            'options': self.options,
            'page_number': self.page_number,
            'chapter_context': self.chapter_context,
            'topic_context': self.topic_context,
            'sub_topic_context': self.sub_topic_context,
            'raw_images': self.raw_images,
            'raw_tables': self.raw_tables,
            'processing_status': self.processing_status.value,
            'error_message': self.error_message,
            'question_id': str(self.question_id) if self.question_id else None,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RawQuestion':
        """Create model from dictionary."""
        # Convert string UUIDs back to UUID objects
        if 'id' in data and isinstance(data['id'], str):
            data['id'] = UUID(data['id'])
        if 'job_id' in data and isinstance(data['job_id'], str):
            data['job_id'] = UUID(data['job_id'])
        if 'question_id' in data and data['question_id'] and isinstance(data['question_id'], str):
            data['question_id'] = UUID(data['question_id'])
        
        # Convert enum strings to enum objects
        if 'processing_status' in data and isinstance(data['processing_status'], str):
            data['processing_status'] = ProcessingStatus(data['processing_status'])
        
        # Convert ISO format strings back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return cls(**data)
