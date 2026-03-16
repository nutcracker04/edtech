"""
Finalization Service Layer

This module provides the business logic for finalizing raw questions into the main question repository.
It handles:
- Metadata mapping from raw question contexts to hierarchy IDs
- Answer type determination based on options format
- Difficulty level determination using heuristics
- Auto-detection of tags (has-image, has-table, has-math, mcq, numerical)
- Single question finalization with transaction management
- Bulk finalization with all-or-nothing semantics

Requirements: 5.1-5.10, 6.1-6.8, 9.1-9.4, 12.6-12.7, 14.6
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
import logging
import re

from app.models.extraction import RawQuestion, ProcessingStatus
from app.models.question import Question, QuestionType, Difficulty, Option, QuestionImage, QuestionTable, QuestionTag
from app.models.hierarchy import Book, Chapter, Topic
from app.models.admin import BulkOperationResult
from app.services.validation import QuestionValidator, ValidationResult

logger = logging.getLogger(__name__)


class FinalizationService:
    """
    Service for finalizing raw questions into the main question repository.
    
    Handles:
    - Metadata mapping from contexts to hierarchy IDs
    - Answer type and difficulty determination
    - Tag generation and auto-detection
    - Single and bulk finalization with transaction management
    
    Requirements: 5.1-5.10, 6.1-6.8, 9.1-9.4, 12.6-12.7, 14.6
    """
    
    def __init__(self, db_client):
        """
        Initialize the finalization service.
        
        Args:
            db_client: Database client for executing queries
        """
        self.db = db_client
        self.validator = QuestionValidator()
    
    async def finalize_question(self, raw_question_id: UUID) -> Tuple[bool, Optional[Question], Optional[str]]:
        """
        Finalize a single raw question into the main repository.
        
        Process:
        1. Fetch raw question
        2. Validate for finalization
        3. Begin transaction
        4. Map metadata (chapter_id, topic_id, book_id)
        5. Determine answer type and difficulty
        6. Generate tags
        7. Create question record
        8. Create option records
        9. Create image records if raw_images exist
        10. Create table records if raw_tables exist
        11. Create tag records
        12. Update raw_question with question_id and status='tagged'
        13. Commit transaction
        
        On error:
        - Rollback transaction
        - Update raw_question with status='error' and error_message
        
        Requirements: 5.1-5.10, 12.6-12.7, 14.6
        
        Args:
            raw_question_id: ID of the raw question to finalize
            
        Returns:
            Tuple of (success: bool, question: Optional[Question], error: Optional[str])
        """
        try:
            # Fetch raw question
            raw_question = await self._fetch_raw_question(raw_question_id)
            if not raw_question:
                error_msg = f"Raw question {raw_question_id} not found"
                logger.error(error_msg)
                return False, None, error_msg
            
            # Validate for finalization
            validation_result = self.validator.validate_for_finalization(raw_question)
            if not validation_result.is_valid:
                error_msg = "; ".join([e.message for e in validation_result.errors])
                logger.warning(f"Validation failed for raw question {raw_question_id}: {error_msg}")
                await self._update_raw_question_error(raw_question_id, error_msg)
                return False, None, error_msg
            
            # Begin transaction
            async with self.db.transaction():
                # Map metadata
                metadata = await self._map_metadata(raw_question)
                if not metadata:
                    error_msg = "Failed to map metadata from contexts"
                    logger.error(f"Metadata mapping failed for raw question {raw_question_id}")
                    await self._update_raw_question_error(raw_question_id, error_msg)
                    return False, None, error_msg
                
                # Determine answer type
                answer_type = self._determine_answer_type(raw_question.options)
                
                # Determine difficulty
                difficulty = await self._determine_difficulty(
                    metadata.get('chapter_id'),
                    metadata.get('topic_id')
                )
                
                # Generate tags
                tags = self._generate_tags(
                    raw_question.question_text,
                    bool(raw_question.raw_images),
                    bool(raw_question.raw_tables),
                    answer_type
                )
                
                # Create question record
                question_id = uuid4()
                question = Question(
                    id=question_id,
                    question_number=raw_question.question_number,
                    question_text=raw_question.question_text,
                    topic_id=metadata['topic_id'],
                    chapter_id=metadata['chapter_id'],
                    book_id=metadata['book_id'],
                    sub_topic=raw_question.sub_topic_context,
                    answer_type=answer_type,
                    difficulty=difficulty,
                    page_number=raw_question.page_number,
                    raw_question_id=raw_question_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                await self._insert_question(question)
                
                # Create option records
                for i, option_text in enumerate(raw_question.options):
                    option = Option(
                        id=uuid4(),
                        question_id=question_id,
                        label=chr(65 + i),  # A, B, C, D, ...
                        text=option_text,
                        sort_order=i
                    )
                    await self._insert_option(option)
                
                # Create image records if raw_images exist
                if raw_question.raw_images:
                    for i, image_data in enumerate(raw_question.raw_images):
                        question_image = QuestionImage(
                            id=uuid4(),
                            question_id=question_id,
                            storage_path=image_data.get('path', ''),
                            alt_text=image_data.get('alt_text'),
                            width_px=image_data.get('width'),
                            height_px=image_data.get('height'),
                            position_in_question=image_data.get('position', 'question'),
                            sort_order=i,
                            created_at=datetime.utcnow()
                        )
                        await self._insert_question_image(question_image)
                
                # Create table records if raw_tables exist
                if raw_question.raw_tables:
                    for i, table_data in enumerate(raw_question.raw_tables):
                        question_table = QuestionTable(
                            id=uuid4(),
                            question_id=question_id,
                            headers=table_data.get('headers', []),
                            rows=table_data.get('rows', []),
                            caption=table_data.get('caption'),
                            sort_order=i
                        )
                        await self._insert_question_table(question_table)
                
                # Create tag records
                for tag in tags:
                    question_tag = QuestionTag(
                        question_id=question_id,
                        tag=tag,
                        source='auto'
                    )
                    await self._insert_question_tag(question_tag)
                
                # Update raw_question with question_id and status='tagged'
                await self._update_raw_question_finalized(raw_question_id, question_id)
            
            logger.info(f"Successfully finalized raw question {raw_question_id} to question {question_id}")
            return True, question, None
        
        except Exception as e:
            error_msg = f"Finalization failed: {str(e)}"
            logger.error(f"Error finalizing raw question {raw_question_id}: {error_msg}", exc_info=True)
            await self._update_raw_question_error(raw_question_id, error_msg)
            return False, None, error_msg
    
    async def bulk_finalize_questions(self, raw_question_ids: List[UUID]) -> BulkOperationResult:
        """
        Finalize multiple raw questions in a single bulk operation.
        
        Process:
        - For each question, attempt finalization
        - Collect successful and failed operations
        - Use database transaction for all-or-nothing semantics
        - Return detailed result with success/failure counts
        
        Requirements: 9.1, 9.2, 9.3, 9.4
        
        Args:
            raw_question_ids: List of raw question IDs to finalize
            
        Returns:
            BulkOperationResult with successful/failed operations
        """
        successful = []
        failed = []
        
        try:
            # Begin transaction for all-or-nothing semantics
            async with self.db.transaction():
                for raw_question_id in raw_question_ids:
                    success, question, error = await self.finalize_question(raw_question_id)
                    
                    if success:
                        successful.append(raw_question_id)
                    else:
                        failed.append({
                            'id': str(raw_question_id),
                            'error': error or 'Unknown error'
                        })
        
        except Exception as e:
            # On transaction error, all operations failed
            error_msg = f"Bulk finalization transaction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            failed = [{'id': str(qid), 'error': error_msg} for qid in raw_question_ids]
        
        result = BulkOperationResult(
            successful=successful,
            failed=failed,
            total=len(raw_question_ids),
            success_count=len(successful),
            failure_count=len(failed)
        )
        
        logger.info(f"Bulk finalization completed: {len(successful)} successful, {len(failed)} failed")
        return result
    
    async def _map_metadata(self, raw_question: RawQuestion) -> Optional[Dict[str, UUID]]:
        """
        Map raw question contexts to hierarchy IDs.
        
        Resolves:
        - chapter_context -> chapter_id
        - topic_context -> topic_id
        - book_id from extraction job
        
        Requirements: 5.4, 6.4, 6.5
        
        Args:
            raw_question: The raw question with context information
            
        Returns:
            Dict with chapter_id, topic_id, book_id or None if mapping fails
        """
        try:
            # Fetch extraction job to get book_id
            job = await self._fetch_extraction_job(raw_question.job_id)
            if not job or not job.book_id:
                logger.error(f"Extraction job {raw_question.job_id} not found or has no book_id")
                return None
            
            book_id = job.book_id
            
            # Fetch chapters for the book
            chapters = await self._fetch_chapters_for_book(book_id)
            
            # Find matching chapter
            chapter_id = None
            for chapter in chapters:
                if chapter.title == raw_question.chapter_context or chapter.slug == raw_question.chapter_context:
                    chapter_id = chapter.id
                    break
            
            if not chapter_id:
                logger.error(f"Chapter '{raw_question.chapter_context}' not found for book {book_id}")
                return None
            
            # Fetch topics for the chapter
            topics = await self._fetch_topics_for_chapter(chapter_id)
            
            # Find matching topic
            topic_id = None
            for topic in topics:
                if topic.title == raw_question.topic_context or topic.slug == raw_question.topic_context:
                    topic_id = topic.id
                    break
            
            if not topic_id:
                logger.error(f"Topic '{raw_question.topic_context}' not found in chapter {chapter_id}")
                return None
            
            return {
                'chapter_id': chapter_id,
                'topic_id': topic_id,
                'book_id': book_id
            }
        
        except Exception as e:
            logger.error(f"Error mapping metadata: {str(e)}", exc_info=True)
            return None
    
    def _determine_answer_type(self, options: List[str]) -> QuestionType:
        """
        Determine answer type based on options format.
        
        Logic:
        - If options list exists and has 2+ items -> MCQ_SINGLE (default for extracted questions)
        - Could be extended to detect other types based on question text patterns
        
        Requirements: 6.1
        
        Args:
            options: List of option texts
            
        Returns:
            QuestionType enum value
        """
        if options and len(options) >= 2:
            return QuestionType.MCQ_SINGLE
        
        return QuestionType.MCQ_SINGLE
    
    async def _determine_difficulty(self, chapter_id: UUID, topic_id: UUID) -> Difficulty:
        """
        Determine difficulty level using chapter/topic heuristics.
        
        Heuristics:
        - Early chapters (1-3) -> EASY
        - Middle chapters (4-6) -> MEDIUM
        - Later chapters (7+) -> HARD
        - Can be overridden by topic-specific rules
        
        Requirements: 6.2
        
        Args:
            chapter_id: Chapter ID for context
            topic_id: Topic ID for context
            
        Returns:
            Difficulty enum value
        """
        try:
            chapter = await self._fetch_chapter(chapter_id)
            if not chapter:
                return Difficulty.MEDIUM
            
            # Use chapter number as heuristic
            if chapter.chapter_number <= 3:
                return Difficulty.EASY
            elif chapter.chapter_number <= 6:
                return Difficulty.MEDIUM
            else:
                return Difficulty.HARD
        
        except Exception as e:
            logger.warning(f"Error determining difficulty: {str(e)}")
            return Difficulty.MEDIUM
    
    def _generate_tags(
        self,
        question_text: str,
        has_images: bool,
        has_tables: bool,
        answer_type: QuestionType
    ) -> List[str]:
        """
        Generate auto-detected tags for a question.
        
        Auto-detects:
        - has-image: If raw_images exist (Requirement 6.7)
        - has-table: If raw_tables exist (Requirement 6.8)
        - has-math: If LaTeX math notation detected (Requirement 6.6)
        - mcq: If answer_type is MCQ (Requirement 6.3)
        - numerical: If question contains numerical patterns (Requirement 6.3)
        
        Requirements: 6.3, 6.6, 6.7, 6.8
        
        Args:
            question_text: The question text to analyze
            has_images: Whether question has images
            has_tables: Whether question has tables
            answer_type: The determined answer type
            
        Returns:
            List of tag strings
        """
        tags = []
        
        # Check for images
        if has_images:
            tags.append('has-image')
        
        # Check for tables
        if has_tables:
            tags.append('has-table')
        
        # Check for LaTeX math notation
        if self._has_math_notation(question_text):
            tags.append('has-math')
        
        # Check for MCQ
        if answer_type in [QuestionType.MCQ_SINGLE, QuestionType.MCQ_MULTIPLE]:
            tags.append('mcq')
        
        # Check for numerical content
        if self._has_numerical_content(question_text):
            tags.append('numerical')
        
        return tags
    
    def _has_math_notation(self, text: str) -> bool:
        """
        Check if text contains LaTeX math notation.
        
        Detects:
        - Inline math: $...$
        - Display math: $$...$$
        - LaTeX delimiters: \[...\] or \(...\)
        
        Args:
            text: Text to check
            
        Returns:
            True if math notation found
        """
        # Check for inline math $...$
        if re.search(r'\$[^\$]+\$', text):
            return True
        
        # Check for display math $$...$$
        if re.search(r'\$\$[^\$]+\$\$', text):
            return True
        
        # Check for LaTeX delimiters \[...\]
        if re.search(r'\\\[[^\]]+\\\]', text):
            return True
        
        # Check for LaTeX delimiters \(...\)
        if re.search(r'\\\([^\)]+\\\)', text):
            return True
        
        return False
    
    def _has_numerical_content(self, text: str) -> bool:
        """
        Check if text contains numerical content.
        
        Detects:
        - Decimal numbers: 3.14, 0.5
        - Integers: 100, 42
        - Percentages: 50%
        - Fractions: 1/2, 3/4
        
        Args:
            text: Text to check
            
        Returns:
            True if numerical content found
        """
        # Check for decimal numbers
        if re.search(r'\d+\.\d+', text):
            return True
        
        # Check for percentages
        if re.search(r'\d+%', text):
            return True
        
        # Check for fractions
        if re.search(r'\d+/\d+', text):
            return True
        
        # Check for large integers (more than 2 digits)
        if re.search(r'\b\d{3,}\b', text):
            return True
        
        return False
    
    # Database helper methods
    
    async def _fetch_raw_question(self, raw_question_id: UUID) -> Optional[RawQuestion]:
        """Fetch a raw question from the database."""
        try:
            result = await self.db.execute(
                "SELECT * FROM raw_question WHERE id = %s",
                (str(raw_question_id),)
            )
            if result:
                return self._map_raw_question_row(result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching raw question {raw_question_id}: {str(e)}")
            return None
    
    async def _fetch_extraction_job(self, job_id: UUID) -> Optional[Any]:
        """Fetch an extraction job from the database."""
        try:
            result = await self.db.execute(
                "SELECT * FROM extraction_job WHERE id = %s",
                (str(job_id),)
            )
            if result:
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error fetching extraction job {job_id}: {str(e)}")
            return None
    
    async def _fetch_chapters_for_book(self, book_id: UUID) -> List[Chapter]:
        """Fetch all chapters for a book."""
        try:
            result = await self.db.execute(
                "SELECT * FROM chapter WHERE book_id = %s ORDER BY chapter_number",
                (str(book_id),)
            )
            return [self._map_chapter_row(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error fetching chapters for book {book_id}: {str(e)}")
            return []
    
    async def _fetch_topics_for_chapter(self, chapter_id: UUID) -> List[Topic]:
        """Fetch all topics for a chapter."""
        try:
            result = await self.db.execute(
                "SELECT * FROM topic WHERE chapter_id = %s ORDER BY topic_order",
                (str(chapter_id),)
            )
            return [self._map_topic_row(row) for row in result] if result else []
        except Exception as e:
            logger.error(f"Error fetching topics for chapter {chapter_id}: {str(e)}")
            return []
    
    async def _fetch_chapter(self, chapter_id: UUID) -> Optional[Chapter]:
        """Fetch a chapter from the database."""
        try:
            result = await self.db.execute(
                "SELECT * FROM chapter WHERE id = %s",
                (str(chapter_id),)
            )
            if result:
                return self._map_chapter_row(result[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching chapter {chapter_id}: {str(e)}")
            return None
    
    async def _insert_question(self, question: Question) -> None:
        """Insert a question into the database."""
        try:
            await self.db.execute(
                """INSERT INTO question 
                (id, question_number, question_text, topic_id, chapter_id, book_id, 
                 sub_topic, answer_type, difficulty, page_number, raw_question_id, 
                 created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (str(question.id), question.question_number, question.question_text,
                 str(question.topic_id), str(question.chapter_id), str(question.book_id),
                 question.sub_topic, question.answer_type.value, question.difficulty.value,
                 question.page_number, str(question.raw_question_id),
                 question.created_at, question.updated_at)
            )
        except Exception as e:
            logger.error(f"Error inserting question: {str(e)}")
            raise
    
    async def _insert_option(self, option: Option) -> None:
        """Insert an option into the database."""
        try:
            await self.db.execute(
                """INSERT INTO option (id, question_id, label, text, sort_order)
                VALUES (%s, %s, %s, %s, %s)""",
                (str(option.id), str(option.question_id), option.label, option.text, option.sort_order)
            )
        except Exception as e:
            logger.error(f"Error inserting option: {str(e)}")
            raise
    
    async def _insert_question_image(self, image: QuestionImage) -> None:
        """Insert a question image into the database."""
        try:
            await self.db.execute(
                """INSERT INTO question_image 
                (id, question_id, storage_path, alt_text, width_px, height_px, 
                 position_in_question, sort_order, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (str(image.id), str(image.question_id), image.storage_path, image.alt_text,
                 image.width_px, image.height_px, image.position_in_question, image.sort_order,
                 image.created_at)
            )
        except Exception as e:
            logger.error(f"Error inserting question image: {str(e)}")
            raise
    
    async def _insert_question_table(self, table: QuestionTable) -> None:
        """Insert a question table into the database."""
        try:
            await self.db.execute(
                """INSERT INTO question_table (id, question_id, headers, rows, caption, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (str(table.id), str(table.question_id), table.headers, table.rows, table.caption, table.sort_order)
            )
        except Exception as e:
            logger.error(f"Error inserting question table: {str(e)}")
            raise
    
    async def _insert_question_tag(self, tag: QuestionTag) -> None:
        """Insert a question tag into the database."""
        try:
            await self.db.execute(
                """INSERT INTO question_tag (question_id, tag, source)
                VALUES (%s, %s, %s)""",
                (str(tag.question_id), tag.tag, tag.source)
            )
        except Exception as e:
            logger.error(f"Error inserting question tag: {str(e)}")
            raise
    
    async def _update_raw_question_finalized(self, raw_question_id: UUID, question_id: UUID) -> None:
        """Update raw question with finalized question_id and status='tagged'."""
        try:
            await self.db.execute(
                """UPDATE raw_question 
                SET question_id = %s, processing_status = %s, updated_at = %s
                WHERE id = %s""",
                (str(question_id), ProcessingStatus.TAGGED.value, datetime.utcnow(), str(raw_question_id))
            )
        except Exception as e:
            logger.error(f"Error updating raw question {raw_question_id}: {str(e)}")
            raise
    
    async def _update_raw_question_error(self, raw_question_id: UUID, error_message: str) -> None:
        """Update raw question with error status and message."""
        try:
            await self.db.execute(
                """UPDATE raw_question 
                SET processing_status = %s, error_message = %s, updated_at = %s
                WHERE id = %s""",
                (ProcessingStatus.ERROR.value, error_message, datetime.utcnow(), str(raw_question_id))
            )
        except Exception as e:
            logger.error(f"Error updating raw question error status {raw_question_id}: {str(e)}")
    
    # Row mapping helpers
    
    def _map_raw_question_row(self, row: Dict[str, Any]) -> RawQuestion:
        """Map database row to RawQuestion model."""
        return RawQuestion(
            id=UUID(row['id']),
            job_id=UUID(row['job_id']),
            question_number=row['question_number'],
            question_text=row['question_text'],
            options=row['options'],
            page_number=row.get('page_number'),
            chapter_context=row.get('chapter_context'),
            topic_context=row.get('topic_context'),
            sub_topic_context=row.get('sub_topic_context'),
            raw_images=row.get('raw_images'),
            raw_tables=row.get('raw_tables'),
            processing_status=ProcessingStatus(row['processing_status']),
            error_message=row.get('error_message'),
            question_id=UUID(row['question_id']) if row.get('question_id') else None,
            created_at=row['created_at']
        )
    
    def _map_chapter_row(self, row: Dict[str, Any]) -> Chapter:
        """Map database row to Chapter model."""
        return Chapter(
            id=UUID(row['id']),
            book_id=UUID(row['book_id']),
            chapter_number=row['chapter_number'],
            title=row['title'],
            slug=row['slug'],
            page_start=row.get('page_start'),
            page_end=row.get('page_end'),
            created_at=row['created_at']
        )
    
    def _map_topic_row(self, row: Dict[str, Any]) -> Topic:
        """Map database row to Topic model."""
        return Topic(
            id=UUID(row['id']),
            chapter_id=UUID(row['chapter_id']),
            title=row['title'],
            slug=row['slug'],
            topic_order=row['topic_order'],
            section_type=row['section_type'],
            page_start=row.get('page_start'),
            page_end=row.get('page_end'),
            created_at=row['created_at']
        )
