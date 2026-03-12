"""
Data models for structured PDF question extraction.

This module defines all Pydantic models used throughout the extraction pipeline.
"""

from enum import Enum
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
from uuid import uuid4


class SectionType(str, Enum):
    """Types of sections in a textbook"""
    QUESTIONS = "questions"
    ANSWER_KEY = "answer_key"
    HINTS = "hints"
    EXPLANATIONS = "explanations"


class QuestionType(str, Enum):
    """Types of questions"""
    MCQ_SINGLE = "single_choice"
    MCQ_MULTIPLE = "multiple_choice"
    INTEGER = "integer"
    SUBJECTIVE = "subjective"
    NUMERICAL = "numerical"


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BookMetadata(BaseModel):
    """Metadata about the textbook being processed"""
    title: str = Field(..., min_length=1, description="Book title")
    subject: str = Field(..., description="Subject: Physics, Chemistry, or Mathematics")
    grade_level: str = Field(..., description="Grade level as string (1-12)")
    publisher: str = Field(..., description="Publisher name")
    edition: Optional[str] = Field(None, description="Edition information")
    isbn: Optional[str] = Field(None, description="ISBN number")

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject is one of the allowed values"""
        allowed = {"Physics", "Chemistry", "Mathematics"}
        if v not in allowed:
            raise ValueError(f"Subject must be one of {allowed}, got {v}")
        return v

    @field_validator("grade_level")
    @classmethod
    def validate_grade_level(cls, v: str) -> str:
        """Validate grade level is between 1 and 12"""
        try:
            grade = int(v)
            if not 1 <= grade <= 12:
                raise ValueError(f"Grade level must be between 1 and 12, got {grade}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Grade level must be a numeric string, got {v}")
            raise
        return v


class ImageReference(BaseModel):
    """Reference to an image in the document"""
    path: str = Field(..., description="Relative path to image file")
    alt_text: Optional[str] = Field(None, description="Alternative text for image")
    position: str = Field(..., description="Position: inline, above, or below")

    @field_validator("position")
    @classmethod
    def validate_position(cls, v: str) -> str:
        """Validate position is one of the allowed values"""
        allowed = {"inline", "above", "below"}
        if v not in allowed:
            raise ValueError(f"Position must be one of {allowed}, got {v}")
        return v


class Section(BaseModel):
    """A section within a topic"""
    section_type: SectionType = Field(..., description="Type of section")
    page_range: Tuple[int, int] = Field(..., description="Start and end page numbers")
    content: str = Field(..., description="Markdown content of the section")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")

    @field_validator("page_range")
    @classmethod
    def validate_page_range(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Validate page range has start <= end"""
        start, end = v
        if start > end:
            raise ValueError(f"Page range start ({start}) must be <= end ({end})")
        if start < 1:
            raise ValueError(f"Page numbers must be positive, got start={start}")
        return v


class Topic(BaseModel):
    """A topic within a chapter"""
    title: str = Field(..., min_length=1, description="Topic title")
    page_range: Tuple[int, int] = Field(..., description="Start and end page numbers")
    sub_topics: List[str] = Field(default_factory=list, description="List of sub-topic titles")
    questions_section: Optional[Section] = Field(None, description="Questions section")
    answer_key_section: Optional[Section] = Field(None, description="Answer key section")

    @field_validator("page_range")
    @classmethod
    def validate_page_range(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Validate page range has start <= end"""
        start, end = v
        if start > end:
            raise ValueError(f"Page range start ({start}) must be <= end ({end})")
        if start < 1:
            raise ValueError(f"Page numbers must be positive, got start={start}")
        return v


class Chapter(BaseModel):
    """A chapter in the textbook"""
    chapter_number: int = Field(..., gt=0, description="Chapter number (must be positive)")
    title: str = Field(..., min_length=1, description="Chapter title")
    page_range: Tuple[int, int] = Field(..., description="Start and end page numbers")
    topics: List[Topic] = Field(..., min_length=1, description="List of topics in chapter")
    hints_section: Optional[Section] = Field(None, description="Chapter-level hints section")
    explanations_section: Optional[Section] = Field(None, description="Chapter-level explanations section")

    @field_validator("page_range")
    @classmethod
    def validate_page_range(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Validate page range has start <= end"""
        start, end = v
        if start > end:
            raise ValueError(f"Page range start ({start}) must be <= end ({end})")
        if start < 1:
            raise ValueError(f"Page numbers must be positive, got start={start}")
        return v


class DocumentStructure(BaseModel):
    """Complete hierarchical structure of the document"""
    chapters: List[Chapter] = Field(..., min_length=1, description="List of chapters")
    metadata: BookMetadata = Field(..., description="Book metadata")
    total_pages: int = Field(..., gt=0, description="Total number of pages")
    structure_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall structure confidence")

    @field_validator("structure_confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate structure confidence is >= 0.7 for processing"""
        if v < 0.7:
            raise ValueError(f"Structure confidence ({v}) must be >= 0.7 for processing")
        return v


class RawQuestion(BaseModel):
    """A question extracted from the document before linking"""
    question_number: str = Field(..., min_length=1, description="Question number (e.g., '1', '2.a', 'Q15')")
    question_text: str = Field(..., min_length=1, description="Question text with formatting")
    options: Optional[List[str]] = Field(None, description="MCQ options if applicable")
    images: List[ImageReference] = Field(default_factory=list, description="Referenced images")
    tables: List[str] = Field(default_factory=list, description="Markdown tables")
    page_number: int = Field(..., gt=0, description="Page number where question appears")
    chapter_context: str = Field(..., description="Chapter title")
    topic_context: str = Field(..., description="Topic title")
    sub_topic_context: Optional[str] = Field(None, description="Sub-topic title if applicable")


class AnswerKey(BaseModel):
    """Answer key for a question"""
    question_number: str = Field(..., min_length=1, description="Question number")
    answer: str = Field(..., min_length=1, description="Answer text")
    page_number: int = Field(..., gt=0, description="Page number where answer appears")


class Hint(BaseModel):
    """Hint for a question"""
    question_number: str = Field(..., min_length=1, description="Question number")
    hint_text: str = Field(..., min_length=1, description="Hint text")
    page_number: int = Field(..., gt=0, description="Page number where hint appears")


class Explanation(BaseModel):
    """Detailed explanation for a question"""
    question_number: str = Field(..., min_length=1, description="Question number")
    explanation_text: str = Field(..., min_length=1, description="Explanation text")
    images: List[ImageReference] = Field(default_factory=list, description="Images in explanation")
    page_number: int = Field(..., gt=0, description="Page number where explanation appears")


class LinkedQuestion(BaseModel):
    """Question with linked answer, hint, and explanation"""
    raw_question: RawQuestion = Field(..., description="Original question data")
    answer_key: Optional[str] = Field(None, description="Linked answer")
    hint: Optional[str] = Field(None, description="Linked hint")
    explanation: Optional[str] = Field(None, description="Linked explanation")
    link_confidence: Dict[str, float] = Field(
        default_factory=dict,
        description="Confidence scores for each link (answer, hint, explanation)"
    )

    @field_validator("link_confidence")
    @classmethod
    def validate_confidence_scores(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate all confidence scores are between 0.0 and 1.0"""
        for key, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Confidence score for {key} must be between 0.0 and 1.0, got {score}")
        return v

    @model_validator(mode="after")
    def validate_mcq_has_answer(self) -> "LinkedQuestion":
        """Validate MCQ questions have answer keys"""
        if self.raw_question.options is not None and self.answer_key is None:
            raise ValueError(
                f"MCQ question {self.raw_question.question_number} must have an answer_key"
            )
        return self


class Option(BaseModel):
    """An option for a multiple choice question"""
    text: str = Field(..., min_length=1, description="Option text")
    label: str = Field(..., description="Option label (A, B, C, D, etc.)")


class TaggedQuestion(BaseModel):
    """Fully processed question with all metadata and tags"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique question ID")
    question: str = Field(..., min_length=1, description="Question text")
    options: List[Option] = Field(default_factory=list, description="MCQ options")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: Optional[str] = Field(None, description="Explanation text")
    hint: Optional[str] = Field(None, description="Hint text")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    topic: str = Field(..., description="Topic name")
    topic_id: str = Field(..., description="Topic ID")
    chapter: str = Field(..., description="Chapter name")
    chapter_id: str = Field(..., description="Chapter ID")
    subject: str = Field(..., description="Subject name")
    subject_id: str = Field(..., description="Subject ID")
    grade_level: List[str] = Field(..., min_length=1, description="Grade levels")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    source: str = Field(..., description="Book title")
    answer_type: QuestionType = Field(..., description="Type of answer expected")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    tables: List[str] = Field(default_factory=list, description="Markdown tables")
    sub_topic: Optional[str] = Field(None, description="Sub-topic if applicable")

    @model_validator(mode="after")
    def validate_mcq_answer(self) -> "TaggedQuestion":
        """Validate MCQ correct answer matches one of the options"""
        if self.answer_type in [QuestionType.MCQ_SINGLE, QuestionType.MCQ_MULTIPLE]:
            if not self.options:
                raise ValueError("MCQ questions must have options")
            option_texts = [opt.text for opt in self.options]
            if self.correct_answer not in option_texts:
                raise ValueError(
                    f"Correct answer '{self.correct_answer}' must match one of the options"
                )
        return self
