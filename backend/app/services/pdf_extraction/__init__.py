"""
PDF Extraction Service

This module provides structured extraction of educational questions from textbook PDFs.
"""

from .models import (
    BookMetadata,
    DocumentStructure,
    Chapter,
    Topic,
    Section,
    RawQuestion,
    LinkedQuestion,
    TaggedQuestion,
    ImageReference,
    AnswerKey,
    Hint,
    Explanation,
    SectionType,
    QuestionType,
    DifficultyLevel,
)
from .document_processor import (
    DocumentProcessor,
    ProcessingResult,
    ProcessingStatus,
    ValidationResult,
    ProcessingStage,
)
from .relationship_linker import RelationshipLinker
from .config import PDFExtractionConfig, get_config
from .extraction_helpers import to_slug, parse_answer_key, normalize_question_number
from .extraction_pipeline import run_extraction_pipeline
from .database_writer import DatabaseWriter

__all__ = [
    "BookMetadata",
    "DocumentStructure",
    "Chapter",
    "Topic",
    "Section",
    "RawQuestion",
    "LinkedQuestion",
    "TaggedQuestion",
    "ImageReference",
    "AnswerKey",
    "Hint",
    "Explanation",
    "SectionType",
    "QuestionType",
    "DifficultyLevel",
    "DocumentProcessor",
    "ProcessingResult",
    "ProcessingStatus",
    "ValidationResult",
    "ProcessingStage",
    "RelationshipLinker",
    "PDFExtractionConfig",
    "get_config",
    "to_slug",
    "parse_answer_key",
    "normalize_question_number",
    "run_extraction_pipeline",
    "DatabaseWriter",
]
