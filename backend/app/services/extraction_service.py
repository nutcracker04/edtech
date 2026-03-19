"""
Extraction Service Layer

This module provides the business logic for extraction management operations, including:
- Listing extraction jobs with filtering, sorting, and pagination
- Retrieving job details with statistics and hierarchy
- Managing raw questions (list, update, delete, search)
- Bulk operations (delete, finalize)
- Statistics calculation

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""

from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
import logging

from app.models.extraction import ExtractionJob, RawQuestion, ExtractionStage, ProcessingStatus
from app.models.question import Question
from app.models.hierarchy import Book, Chapter, Topic
from app.models.admin import (
    JobListFilters,
    JobListSort,
    PaginationParams,
    QuestionUpdateRequest,
    QuestionFilters,
    ExtractionJobDetail,
    ChapterWithTopics,
    JobStatistics,
    BulkOperationResult,
    RawQuestionResponse,
    ManualRawQuestionItem,
)
from app.services.validation import QuestionValidator, ValidationResult

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Service layer for extraction management operations.
    
    Provides methods for:
    - Listing and filtering extraction jobs
    - Retrieving job details with statistics
    - Managing raw questions (CRUD operations)
    - Bulk operations
    - Statistics calculation
    - Full-text search
    
    Requirements: 1.1-1.5, 2.1-2.5, 3.1-3.2, 4.1-4.4, 10.1-10.5, 11.1-11.7
    """
    
    def __init__(self, db_client):
        """
        Initialize the extraction service.
        
        Args:
            db_client: Database client for executing queries
        """
        self.db = db_client
        self.validator = QuestionValidator()
    
    def list_jobs(
        self,
        filters: Optional[JobListFilters] = None,
        sort: Optional[JobListSort] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[ExtractionJob], int]:
        """
        List extraction jobs with filtering, sorting, and pagination.
        
        Supports:
        - Filtering by stage and grade_level (Requirements 1.3, 1.4)
        - Sorting by created_at, completed_at, questions_extracted (Requirement 1.5)
        - Pagination with configurable page size (Requirement 1.1)
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 15.1, 15.2
        
        Args:
            filters: Optional filters to apply
            sort: Optional sort configuration
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (list of extraction jobs, total count)
        """
        if filters is None:
            filters = JobListFilters()
        if sort is None:
            sort = JobListSort(field="created_at", order="desc")
        if pagination is None:
            pagination = PaginationParams()
        
        try:
            # Build query using Supabase client
            query = self.db.table("extraction_jobs").select("*")
            
            # Apply filters
            if filters.stage:
                query = query.eq("stage", filters.stage.value)
            
            if filters.grade_level:
                query = query.eq("grade_level", filters.grade_level)
            
            # Apply sorting
            sort_field = sort.field
            ascending = sort.order.lower() == "asc"
            query = query.order(sort_field, desc=not ascending)
            
            # Apply pagination
            offset = (pagination.page - 1) * pagination.page_size
            query = query.range(offset, offset + pagination.page_size - 1)
            
            # Execute query
            result = query.execute()
            jobs = [ExtractionJob(**row) for row in result.data] if result.data else []
            
            # Get total count
            count_query = self.db.table("extraction_jobs").select("*", count="exact")
            
            if filters.stage:
                count_query = count_query.eq("stage", filters.stage.value)
            
            if filters.grade_level:
                count_query = count_query.eq("grade_level", filters.grade_level)
            
            count_result = count_query.execute()
            total = count_result.count if count_result.count is not None else 0
            
            return jobs, total
        except Exception as e:
            logger.error(f"Error listing extraction jobs: {str(e)}")
            raise
    
    async def get_job_details(self, job_id: UUID) -> Optional[ExtractionJobDetail]:
        """
        Get detailed information about a specific extraction job.
        
        Returns:
        - Job metadata
        - Associated book information
        - Hierarchical structure (chapters and topics)
        - Aggregate statistics
        
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
        
        Args:
            job_id: ID of the extraction job
            
        Returns:
            ExtractionJobDetail or None if job not found
        """
        try:
            # Get job using Supabase client
            job_result = self.db.table("extraction_jobs").select("*").eq("id", str(job_id)).execute()
            if not job_result.data:
                return None
            
            job = ExtractionJob(**job_result.data[0])
            
            # Get book and hierarchy (extraction_books may not exist if migration 011/015 not applied)
            book = None
            hierarchy = []
            if job.book_id:
                try:
                    book_result = self.db.table("extraction_books").select("*").eq("id", str(job.book_id)).execute()
                    if book_result.data:
                        book = Book(**book_result.data[0])

                    chapters_result = self.db.table("extraction_chapters").select("*").eq("book_id", str(job.book_id)).order("chapter_number").execute()
                    for chapter_row in (chapters_result.data or []):
                        chapter = Chapter(**chapter_row)
                        topics_result = self.db.table("extraction_topics").select("*").eq("chapter_id", str(chapter.id)).order("topic_order").execute()
                        topics = [Topic(**row) for row in (topics_result.data or [])]
                        hierarchy.append(ChapterWithTopics(chapter=chapter, topics=topics))
                except Exception as hierarchy_exc:
                    logger.warning("Could not fetch book/hierarchy (tables may be missing): %s", hierarchy_exc)

                if book is None:
                    try:
                        canon = self.db.table("books").select("*").eq("id", str(job.book_id)).execute()
                        if canon.data:
                            book = Book(**canon.data[0])
                    except Exception as canon_exc:
                        logger.warning("Could not fetch canonical book: %s", canon_exc)

                if not hierarchy:
                    try:
                        chapters_result = self.db.table("chapters").select("*").eq("book_id", str(job.book_id)).order("chapter_number").execute()
                        for chapter_row in (chapters_result.data or []):
                            chapter = Chapter(**chapter_row)
                            topics_result = self.db.table("topics").select("*").eq("chapter_id", str(chapter.id)).order("topic_order").execute()
                            topics = [Topic(**row) for row in (topics_result.data or [])]
                            hierarchy.append(ChapterWithTopics(chapter=chapter, topics=topics))
                    except Exception as ch_exc:
                        logger.warning("Could not fetch canonical chapters/topics: %s", ch_exc)
            
            # Get statistics
            statistics = await self.get_job_statistics(job_id)
            
            return ExtractionJobDetail(
                job=job,
                book=book,
                hierarchy=hierarchy,
                statistics=statistics
            )
        except Exception as e:
            logger.error(f"Error getting job details for {job_id}: {str(e)}")
            raise
    
    async def list_questions(
        self,
        job_id: UUID,
        filters: Optional[QuestionFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[RawQuestion], int]:
        """
        List raw questions for a job with filtering and pagination.
        
        Supports:
        - Filtering by processing_status (Requirement 11.2)
        - Filtering by chapter_context (Requirement 11.3)
        - Filtering by topic_context (Requirement 11.4)
        - Filtering by page_number range (Requirement 11.5)
        - Full-text search on question_text (Requirement 11.1)
        - Combined filters with AND logic (Requirement 11.6)
        - Pagination (Requirement 11.7)
        
        Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 2.2
        
        Args:
            job_id: ID of the extraction job
            filters: Optional filters to apply
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (list of raw questions, total count)
        """
        if filters is None:
            filters = QuestionFilters()
        if pagination is None:
            pagination = PaginationParams()
        
        try:
            # Build query using Supabase client
            query = self.db.table("raw_questions").select("*").eq("job_id", str(job_id))
            
            # Apply filters
            if filters.processing_status:
                query = query.eq("processing_status", filters.processing_status.value)
            
            if filters.chapter_context:
                query = query.eq("chapter_context", filters.chapter_context)
            
            if filters.topic_context:
                query = query.eq("topic_context", filters.topic_context)
            
            if filters.page_number_min is not None:
                query = query.gte("page_number", filters.page_number_min)
            
            if filters.page_number_max is not None:
                query = query.lte("page_number", filters.page_number_max)
            
            # Note: Full-text search would require a different approach with Supabase
            # For now, we'll use a simple text search if search_query is provided
            if filters.search_query:
                query = query.ilike("question_text", f"%{filters.search_query}%")
            
            # Apply sorting
            query = query.order("created_at", desc=True)
            
            # Apply pagination
            offset = (pagination.page - 1) * pagination.page_size
            query = query.range(offset, offset + pagination.page_size - 1)
            
            # Execute query
            result = query.execute()
            questions = [RawQuestion(**row) for row in result.data] if result.data else []
            
            # Get total count
            count_query = self.db.table("raw_questions").select("*", count="exact").eq("job_id", str(job_id))
            
            if filters.processing_status:
                count_query = count_query.eq("processing_status", filters.processing_status.value)
            
            if filters.chapter_context:
                count_query = count_query.eq("chapter_context", filters.chapter_context)
            
            if filters.topic_context:
                count_query = count_query.eq("topic_context", filters.topic_context)
            
            if filters.page_number_min is not None:
                count_query = count_query.gte("page_number", filters.page_number_min)
            
            if filters.page_number_max is not None:
                count_query = count_query.lte("page_number", filters.page_number_max)
            
            if filters.search_query:
                count_query = count_query.ilike("question_text", f"%{filters.search_query}%")
            
            count_result = count_query.execute()
            total = count_result.count if count_result.count is not None else 0
            
            return questions, total
        except Exception as e:
            logger.error(f"Error listing questions for job {job_id}: {str(e)}")
            raise
    
    async def update_question(
        self,
        question_id: UUID,
        updates: QuestionUpdateRequest
    ) -> Optional[RawQuestion]:
        """
        Update a raw question with validation.
        
        Validates:
        - question_text is not empty (Requirement 3.3)
        - options is a non-empty list (Requirement 3.4)
        - Updates updated_at timestamp (Requirement 3.5)
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        
        Args:
            question_id: ID of the question to update
            updates: Update request with new values
            
        Returns:
            Updated RawQuestion or None if not found
            
        Raises:
            ValueError: If validation fails
        """
        # Validate updates
        validation_result = self.validator.validate_update(updates)
        if not validation_result.is_valid:
            error_messages = "; ".join([e.message for e in validation_result.errors])
            raise ValueError(f"Validation failed: {error_messages}")
        
        try:
            # Get current question using Supabase table API
            current_result = self.db.table("raw_questions").select("*").eq("id", str(question_id)).execute()
            if not current_result.data:
                return None
            
            current_question = RawQuestion(**current_result.data[0])
            
            # Build update payload
            update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
            if updates.question_text is not None:
                update_data["question_text"] = updates.question_text
            if updates.options is not None:
                update_data["options"] = updates.options
            if updates.chapter_context is not None:
                update_data["chapter_context"] = updates.chapter_context
            if updates.topic_context is not None:
                update_data["topic_context"] = updates.topic_context
            if updates.sub_topic_context is not None:
                update_data["sub_topic_context"] = updates.sub_topic_context
            if updates.page_number is not None:
                update_data["page_number"] = updates.page_number
            
            if len(update_data) <= 1:  # Only updated_at
                return current_question
            
            result = self.db.table("raw_questions").update(update_data).eq("id", str(question_id)).execute()
            if result.data and len(result.data) > 0:
                return RawQuestion(**result.data[0])
            
            return None
        except Exception as e:
            logger.error(f"Error updating question {question_id}: {str(e)}")
            raise
    
    async def delete_question(self, question_id: UUID) -> bool:
        """
        Delete a raw question.
        
        Validates:
        - Question is not already finalized (Requirement 4.4)
        - Deletes associated raw_images and raw_tables (Requirement 4.3)
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        
        Args:
            question_id: ID of the question to delete
            
        Returns:
            True if deleted, False if not found or already finalized
            
        Raises:
            ValueError: If question is already finalized
        """
        try:
            # Get question using Supabase table API
            result = self.db.table("raw_questions").select("*").eq("id", str(question_id)).execute()
            if not result.data:
                return False
            
            question = RawQuestion(**result.data[0])
            
            # Check if already finalized
            if question.question_id is not None:
                raise ValueError("Cannot delete a question that has already been finalized")
            
            # Delete using Supabase table API
            self.db.table("raw_questions").delete().eq("id", str(question_id)).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting question {question_id}: {str(e)}")
            raise
    
    async def bulk_delete_questions(self, question_ids: List[UUID]) -> BulkOperationResult:
        """
        Delete multiple raw questions.
        
        Validates:
        - None of the questions are already finalized (Requirement 9.6)
        - Returns detailed status for each question (Requirement 9.4)
        
        Requirements: 9.5, 9.6, 9.2, 9.3, 9.4
        
        Args:
            question_ids: List of question IDs to delete
            
        Returns:
            BulkOperationResult with successful and failed operations
        """
        successful = []
        failed = []
        
        try:
            for question_id in question_ids:
                try:
                    # Get question using Supabase table API
                    result = self.db.table("raw_questions").select("*").eq("id", str(question_id)).execute()
                    
                    if not result.data:
                        failed.append({
                            "id": str(question_id),
                            "error": "Question not found"
                        })
                        continue
                    
                    question = RawQuestion(**result.data[0])
                    
                    # Check if already finalized
                    if question.question_id is not None:
                        failed.append({
                            "id": str(question_id),
                            "error": "Cannot delete finalized question"
                        })
                        continue
                    
                    # Delete question using Supabase table API
                    self.db.table("raw_questions").delete().eq("id", str(question_id)).execute()
                    
                    successful.append(question_id)
                except Exception as e:
                    failed.append({
                        "id": str(question_id),
                        "error": str(e)
                    })
            
            return BulkOperationResult(
                successful=successful,
                failed=failed,
                total=len(question_ids),
                success_count=len(successful),
                failure_count=len(failed)
            )
        except Exception as e:
            logger.error(f"Error in bulk delete: {str(e)}")
            raise
    
    async def get_job_statistics(self, job_id: UUID) -> JobStatistics:
        """
        Calculate aggregate statistics for an extraction job.
        
        Calculates:
        - total_questions_extracted (Requirement 10.1)
        - questions_by_status (Requirement 10.2)
        - questions_by_chapter (Requirement 10.3)
        - finalization_rate (Requirement 10.4)
        - average_questions_per_page (Requirement 10.5)
        
        Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
        
        Args:
            job_id: ID of the extraction job
            
        Returns:
            JobStatistics with calculated values
        """
        try:
            job_id_str = str(job_id)
            
            # Get all raw questions for this job to compute stats
            questions_result = self.db.table("raw_questions").select(
                "processing_status", "chapter_context", "question_id"
            ).eq("job_id", job_id_str).execute()
            
            questions = questions_result.data or []
            total_questions = len(questions)
            
            questions_by_status: Dict[str, int] = {}
            for q in questions:
                status = q.get("processing_status") or "pending"
                questions_by_status[status] = questions_by_status.get(status, 0) + 1
            
            questions_by_chapter: Dict[str, int] = {}
            for q in questions:
                ch = q.get("chapter_context")
                if ch:
                    questions_by_chapter[ch] = questions_by_chapter.get(ch, 0) + 1
            
            finalized_count = sum(1 for q in questions if q.get("question_id"))
            finalization_rate = Decimal(0)
            if total_questions > 0:
                finalization_rate = Decimal(finalized_count) / Decimal(total_questions) * Decimal(100)
            
            # Get job for total_pages
            job_result = self.db.table("extraction_jobs").select("total_pages").eq("id", job_id_str).execute()
            total_pages = 1
            if job_result.data and job_result.data[0].get("total_pages"):
                total_pages = job_result.data[0]["total_pages"]
            
            average_questions_per_page = Decimal(0)
            if total_pages > 0:
                average_questions_per_page = Decimal(total_questions) / Decimal(total_pages)
            
            return JobStatistics(
                total_questions=total_questions,
                questions_by_status=questions_by_status,
                questions_by_chapter=questions_by_chapter,
                finalization_rate=finalization_rate,
                average_questions_per_page=average_questions_per_page
            )
        except Exception as e:
            logger.error(f"Error calculating statistics for job {job_id}: {str(e)}")
            return JobStatistics()
    
    async def delete_job(self, job_id: UUID) -> bool:
        """
        Delete an extraction job and all associated data.
        
        Deletes:
        - Extraction job record
        - All raw questions (cascade)
        - All extraction pages (cascade)
        - All extraction blocks (cascade)
        
        Args:
            job_id: ID of the extraction job to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Check if job exists
            job_result = self.db.table("extraction_jobs").select("*").eq("id", str(job_id)).execute()
            if not job_result.data:
                return False
            
            # Delete the job (cascade will handle related records)
            delete_result = self.db.table("extraction_jobs").delete().eq("id", str(job_id)).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            raise
    
    async def search_questions(
        self,
        job_id: UUID,
        query: str,
        filters: Optional[QuestionFilters] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Tuple[List[RawQuestion], int]:
        """
        Search raw questions with full-text search and filters.
        
        Performs full-text search on question_text and applies additional filters.
        
        Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
        
        Args:
            job_id: ID of the extraction job
            query: Full-text search query
            filters: Optional additional filters
            pagination: Optional pagination parameters
            
        Returns:
            Tuple of (list of matching questions, total count)
        """
        if filters is None:
            filters = QuestionFilters()
        if pagination is None:
            pagination = PaginationParams()
        
        # Add search query to filters
        filters.search_query = query
        
        # Use list_questions with search filter
        return await self.list_questions(job_id, filters, pagination)

    def list_books_for_manual_import(self) -> List[Dict[str, Any]]:
        """Books available to attach a manual import job (extraction_books preferred, else canonical books)."""
        try:
            r = self.db.table("extraction_books").select("id, title, subject, grade_level").order("title").execute()
            if r.data:
                return r.data
        except Exception as e:
            logger.warning("extraction_books list failed: %s", e)
        try:
            r = self.db.table("books").select("id, title, subject, grade_level").order("title").execute()
            return r.data or []
        except Exception as e:
            logger.error("books list failed: %s", e)
            raise

    def get_book_outline_for_import(self, book_id: UUID) -> Dict[str, Any]:
        """Chapter/topic titles for JSON hints (matches finalization mapping by title or slug)."""
        chapters_out: List[Dict[str, Any]] = []
        try:
            ch = self.db.table("extraction_chapters").select("*").eq("book_id", str(book_id)).order("chapter_number").execute()
            if ch.data:
                for chapter_row in ch.data:
                    cid = chapter_row["id"]
                    topics_result = self.db.table("extraction_topics").select("title, slug").eq("chapter_id", str(cid)).order("topic_order").execute()
                    chapters_out.append({
                        "title": chapter_row.get("title"),
                        "slug": chapter_row.get("slug"),
                        "topics": [{"title": t.get("title"), "slug": t.get("slug")} for t in (topics_result.data or [])],
                    })
                return {"source": "extraction_books", "chapters": chapters_out}
        except Exception as e:
            logger.warning("extraction outline failed: %s", e)

        try:
            ch = self.db.table("chapters").select("*").eq("book_id", str(book_id)).order("chapter_number").execute()
            for chapter_row in ch.data or []:
                cid = chapter_row["id"]
                topics_result = self.db.table("topics").select("title, slug").eq("chapter_id", str(cid)).order("topic_order").execute()
                chapters_out.append({
                    "title": chapter_row.get("title"),
                    "slug": chapter_row.get("slug"),
                    "topics": [{"title": t.get("title"), "slug": t.get("slug")} for t in (topics_result.data or [])],
                })
            return {"source": "books", "chapters": chapters_out}
        except Exception as e:
            logger.error("canonical outline failed: %s", e)
            raise

    def assert_book_exists_for_import(self, book_id: UUID) -> None:
        try:
            r1 = self.db.table("extraction_books").select("id").eq("id", str(book_id)).limit(1).execute()
            if r1.data:
                return
        except Exception:
            pass
        r2 = self.db.table("books").select("id").eq("id", str(book_id)).limit(1).execute()
        if r2.data:
            return
        raise ValueError(f"No book found with id {book_id}")

    async def create_manual_import_job(
        self,
        book_id: UUID,
        job_title: Optional[str],
        items: List[ManualRawQuestionItem],
    ) -> Tuple[UUID, int]:
        """
        Insert extraction_jobs (completed) and raw_questions without PDF processing.
        """
        self.assert_book_exists_for_import(book_id)

        job_uuid = uuid4()
        job_id_str = str(job_uuid)
        now = datetime.now(timezone.utc).isoformat()

        job_row: Dict[str, Any] = {
            "id": job_id_str,
            "book_id": str(book_id),
            "source_pdf_filename": "manual-import",
            "source_pdf_path": "manual://import",
            "stage": ExtractionStage.COMPLETED.value,
            "progress": 100,
            "pages_processed": 0,
            "questions_extracted": len(items),
            "started_at": now,
            "completed_at": now,
            "created_at": now,
        }
        if job_title:
            job_row["title"] = job_title

        self.db.table("extraction_jobs").insert(job_row).execute()

        batch: List[Dict[str, Any]] = []
        batch_size = 50
        for item in items:
            page_num = item.page_number if item.page_number is not None else 1
            batch.append({
                "id": str(uuid4()),
                "job_id": job_id_str,
                "question_number": item.question_number.strip(),
                "question_text": item.question_text.strip(),
                "options": list(item.options or []),
                "page_number": page_num,
                "chapter_context": item.chapter_context,
                "topic_context": item.topic_context,
                "sub_topic_context": item.sub_topic_context,
                "raw_images": item.raw_images if item.raw_images is not None else [],
                "raw_tables": item.raw_tables if item.raw_tables is not None else [],
                "processing_status": ProcessingStatus.PENDING.value,
                "created_at": now,
            })
            if len(batch) >= batch_size:
                self.db.table("raw_questions").insert(batch).execute()
                batch = []
        if batch:
            self.db.table("raw_questions").insert(batch).execute()

        return job_uuid, len(items)
