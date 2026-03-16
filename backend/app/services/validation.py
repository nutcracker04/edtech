"""
Validation Layer for Admin Operations

This module provides validation services for admin panel operations, including:
- Question update validation
- Finalization validation
- Hierarchy mapping validation
- Option validation

Requirements: 3.3, 3.4, 12.1, 12.2, 12.3, 12.4, 12.5
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime

from app.models.extraction import RawQuestion, ProcessingStatus
from app.models.admin import QuestionUpdateRequest, ValidationError


class ValidationResult:
    """
    Result of a validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors
    """
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[ValidationError]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, field: str, message: str, code: str = "validation_error") -> None:
        """Add a validation error."""
        self.errors.append(ValidationError(field=field, message=message, code=code))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "is_valid": self.is_valid,
            "errors": [{"field": e.field, "message": e.message, "code": e.code} for e in self.errors]
        }


class QuestionValidator:
    """
    Validator for raw question operations.
    
    Provides validation methods for:
    - Question updates
    - Finalization checks
    - Hierarchy mapping
    - Option validation
    
    Requirements: 3.3, 3.4, 12.1, 12.2, 12.3, 12.4, 12.5
    """
    
    @staticmethod
    def validate_update(updates: QuestionUpdateRequest) -> ValidationResult:
        """
        Validate a question update request.
        
        Checks:
        - question_text is not empty if provided
        - options has at least 2 items if provided
        - options are non-empty strings if provided
        
        Requirements: 3.3, 3.4
        
        Args:
            updates: The update request to validate
            
        Returns:
            ValidationResult with any validation errors
        """
        result = ValidationResult(is_valid=True)
        
        # Validate question_text
        if updates.question_text is not None:
            if not updates.question_text or not updates.question_text.strip():
                result.add_error(
                    field="question_text",
                    message="Question text cannot be empty",
                    code="empty_question_text"
                )
        
        # Validate options
        if updates.options is not None:
            if len(updates.options) < 2:
                result.add_error(
                    field="options",
                    message="At least 2 options are required",
                    code="insufficient_options"
                )
            
            for i, option in enumerate(updates.options):
                if not option or not isinstance(option, str) or not option.strip():
                    result.add_error(
                        field=f"options[{i}]",
                        message="Option text cannot be empty",
                        code="empty_option"
                    )
        
        result.is_valid = len(result.errors) == 0
        return result
    
    @staticmethod
    def validate_for_finalization(raw_question: RawQuestion) -> ValidationResult:
        """
        Validate a raw question before finalization.
        
        Checks:
        - question_text is not empty (Requirement 12.1)
        - at least 2 options exist (Requirement 12.2)
        - chapter_context is not null (Requirement 12.3)
        - topic_context is not null (Requirement 12.3)
        - question is not already finalized (Requirement 4.4)
        
        Requirements: 12.1, 12.2, 12.3, 4.4
        
        Args:
            raw_question: The raw question to validate
            
        Returns:
            ValidationResult with any validation errors
        """
        result = ValidationResult(is_valid=True)
        
        # Check if already finalized
        if raw_question.question_id is not None:
            result.add_error(
                field="question_id",
                message="Question has already been finalized",
                code="already_finalized"
            )
        
        # Check question_text
        if not raw_question.question_text or not raw_question.question_text.strip():
            result.add_error(
                field="question_text",
                message="Question text cannot be empty",
                code="empty_question_text"
            )
        
        # Check options
        if not raw_question.options or len(raw_question.options) < 2:
            result.add_error(
                field="options",
                message="At least 2 options are required for MCQ questions",
                code="insufficient_options"
            )
        
        for i, option in enumerate(raw_question.options or []):
            if not option or not isinstance(option, str) or not option.strip():
                result.add_error(
                    field=f"options[{i}]",
                    message="Option text cannot be empty",
                    code="empty_option"
                )
        
        # Check chapter_context
        if not raw_question.chapter_context or not raw_question.chapter_context.strip():
            result.add_error(
                field="chapter_context",
                message="Chapter context is required for finalization",
                code="missing_chapter_context"
            )
        
        # Check topic_context
        if not raw_question.topic_context or not raw_question.topic_context.strip():
            result.add_error(
                field="topic_context",
                message="Topic context is required for finalization",
                code="missing_topic_context"
            )
        
        result.is_valid = len(result.errors) == 0
        return result
    
    @staticmethod
    def validate_hierarchy_mapping(
        chapter_context: str,
        topic_context: str,
        book_id: UUID,
        chapters: List[Any],
        topics: List[Any]
    ) -> Tuple[bool, Optional[str], Optional[UUID], Optional[UUID]]:
        """
        Validate that chapter and topic contexts map to existing hierarchy records.
        
        Checks:
        - A chapter with matching title exists for the book (Requirement 12.4)
        - A topic with matching title exists in the chapter (Requirement 12.4)
        
        Requirements: 12.4, 12.5
        
        Args:
            chapter_context: Chapter name to find
            topic_context: Topic name to find
            book_id: Book ID for context
            chapters: List of available chapters
            topics: List of available topics
            
        Returns:
            Tuple of (is_valid, error_message, chapter_id, topic_id)
        """
        # Find matching chapter
        chapter_id = None
        for chapter in chapters:
            if chapter.get('title') == chapter_context or chapter.get('slug') == chapter_context:
                chapter_id = chapter.get('id')
                break
        
        if not chapter_id:
            return False, f"Chapter '{chapter_context}' not found in hierarchy", None, None
        
        # Find matching topic
        topic_id = None
        for topic in topics:
            if topic.get('chapter_id') == chapter_id:
                if topic.get('title') == topic_context or topic.get('slug') == topic_context:
                    topic_id = topic.get('id')
                    break
        
        if not topic_id:
            return False, f"Topic '{topic_context}' not found in chapter '{chapter_context}'", None, None
        
        return True, None, chapter_id, topic_id
    
    @staticmethod
    def validate_options(options: List[str], answer_type: Optional[str] = None) -> ValidationResult:
        """
        Validate question options.
        
        Checks:
        - At least 2 options exist
        - All options are non-empty strings
        - For MCQ, typically 2-6 options
        
        Requirements: 12.2
        
        Args:
            options: List of option texts
            answer_type: Optional answer type for additional validation
            
        Returns:
            ValidationResult with any validation errors
        """
        result = ValidationResult(is_valid=True)
        
        if not options or len(options) < 2:
            result.add_error(
                field="options",
                message="At least 2 options are required",
                code="insufficient_options"
            )
        
        if len(options) > 10:
            result.add_error(
                field="options",
                message="Too many options (maximum 10)",
                code="too_many_options"
            )
        
        for i, option in enumerate(options):
            if not option or not isinstance(option, str):
                result.add_error(
                    field=f"options[{i}]",
                    message="Option must be a non-empty string",
                    code="invalid_option"
                )
            elif not option.strip():
                result.add_error(
                    field=f"options[{i}]",
                    message="Option text cannot be empty",
                    code="empty_option"
                )
        
        result.is_valid = len(result.errors) == 0
        return result
    
    @staticmethod
    def validate_finalization_not_already_done(raw_question: RawQuestion) -> ValidationResult:
        """
        Validate that a question has not already been finalized.
        
        Requirements: 4.4
        
        Args:
            raw_question: The raw question to check
            
        Returns:
            ValidationResult with error if already finalized
        """
        result = ValidationResult(is_valid=True)
        
        if raw_question.question_id is not None:
            result.add_error(
                field="question_id",
                message="Cannot delete a question that has already been finalized",
                code="already_finalized"
            )
            result.is_valid = False
        
        return result
