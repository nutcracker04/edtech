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
]
