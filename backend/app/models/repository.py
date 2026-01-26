from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class Subject(SubjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChapterBase(BaseModel):
    subject_id: UUID
    name: str
    description: Optional[str] = None
    order_index: int = 0

class ChapterCreate(ChapterBase):
    pass

class Chapter(ChapterBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TopicBase(BaseModel):
    chapter_id: UUID
    name: str
    description: Optional[str] = None
    order_index: int = 0

class TopicCreate(TopicBase):
    pass

class Topic(TopicBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RepositoryQuestionBase(BaseModel):
    subject_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None
    topic_id: Optional[UUID] = None
    question_text: str
    options: List[Dict[str, str]] = Field(default_factory=list)
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty_level: Optional[str] = None
    source_paper_id: Optional[UUID] = None
    is_tagged: bool = False
    image_url: Optional[str] = None

class RepositoryQuestionCreate(RepositoryQuestionBase):
    pass

class RepositoryQuestion(RepositoryQuestionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionTagRequest(BaseModel):
    subject_id: UUID
    chapter_id: UUID
    topic_id: UUID
    difficulty_level: Optional[str] = None
