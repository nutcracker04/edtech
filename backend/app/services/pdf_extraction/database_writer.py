"""
DatabaseWriter for the book extraction pipeline.

Sits between MetadataTagger and the database. Receives TaggedQuestion objects and
executes all Phase 1 and Phase 2 inserts/updates per the implementation guide.

Uses Supabase Python client when configured. Gracefully no-ops when DB is unavailable.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

try:
    from app.database import get_supabase
    from app.database import MissingSupabaseConfigurationError
except ImportError:
    get_supabase = None
    MissingSupabaseConfigurationError = Exception

from .extraction_helpers import (
    extract_and_save_images,
    parse_answer_key,
    replace_images_in_text,
    to_slug,
    validate_answer,
)
from .models import (
    BookMetadata,
    Chapter,
    DocumentStructure,
    Explanation,
    Hint,
    LinkedQuestion,
    RawQuestion,
    SectionType,
    TaggedQuestion,
    Topic,
)

logger = logging.getLogger(__name__)

# Map QuestionType enum to answer_type column
ANSWER_TYPE_MAP = {
    "single_choice": "mcq_single",
    "multiple_choice": "mcq_multiple",
    "integer": "integer",
    "numerical": "numerical",
    "subjective": "subjective",
}


class DatabaseWriter:
    """
    Writes extraction results to the database.

    Phase 1: extraction_jobs, books, extraction_chapters, extraction_topics
    Phase 2: raw_questions, extraction_questions, extraction_options,
             question_images, question_tags, answers, hints, explanations
    """

    def __init__(
        self,
        storage_root: Optional[Path] = None,
        job_id: Optional[str] = None,
    ):
        self.storage_root = storage_root or Path("data/extracted_images")
        self.job_id = job_id
        self._supabase = None
        self._book_id: Optional[str] = None
        self._chapter_map: dict[str, str] = {}  # slug -> uuid
        self._topic_map: dict[tuple[str, str], str] = {}  # (chapter_slug, topic_slug) -> uuid

    def _get_client(self):
        if self._supabase is None and get_supabase:
            try:
                self._supabase = get_supabase()
            except MissingSupabaseConfigurationError:
                logger.warning("Supabase not configured, database writes skipped")
        return self._supabase

    def is_available(self) -> bool:
        return self._get_client() is not None

    def write_extraction_job(
        self,
        job_id: str,
        source_pdf_filename: str,
        source_pdf_path: str,
        total_pages: int = 0,
        extracted_path: str = "",
        manifest_path: str = "",
    ) -> Optional[str]:
        """Insert extraction_jobs row. Returns job_id."""
        client = self._get_client()
        if not client:
            return job_id

        try:
            data: dict[str, Any] = {
                "id": job_id,
                "source_pdf_filename": source_pdf_filename,
                "source_pdf_path": source_pdf_path,
                "stage": "queued",
                "progress": 0,
                "total_pages": total_pages,
                "pages_processed": 0,
                "questions_extracted": 0,
            }
            if extracted_path:
                data["extracted_path"] = extracted_path
            if manifest_path:
                data["manifest_path"] = manifest_path

            client.table("extraction_jobs").upsert(data, on_conflict="id").execute()
            self.job_id = job_id
            return job_id
        except Exception as e:
            logger.error("Failed to write extraction_job: %s", e)
            return None

    def update_extraction_job(
        self,
        job_id: str,
        stage: str,
        progress: Optional[float] = None,
        total_pages: Optional[int] = None,
        pages_processed: Optional[int] = None,
        questions_extracted: Optional[int] = None,
        error: Optional[str] = None,
        processing_time_seconds: Optional[float] = None,
        book_id: Optional[str] = None,
    ) -> None:
        """Update extraction_jobs row."""
        client = self._get_client()
        if not client:
            return

        updates: dict[str, Any] = {"stage": stage, "updated_at": datetime.now(timezone.utc).isoformat()}
        if progress is not None:
            updates["progress"] = progress
        if total_pages is not None:
            updates["total_pages"] = total_pages
        if pages_processed is not None:
            updates["pages_processed"] = pages_processed
        if questions_extracted is not None:
            updates["questions_extracted"] = questions_extracted
        if error is not None:
            updates["error"] = error
        if processing_time_seconds is not None:
            updates["processing_time_seconds"] = processing_time_seconds
        if stage == "completed":
            updates["completed_at"] = datetime.now(timezone.utc).isoformat()
        if book_id is not None:
            updates["book_id"] = book_id

        try:
            client.table("extraction_jobs").update(updates).eq("id", job_id).execute()
        except Exception as e:
            logger.error("Failed to update extraction_job: %s", e)

    def write_phase1(
        self,
        job_id: str,
        metadata: BookMetadata,
        structure: DocumentStructure,
        isbn: Optional[str] = None,
        source_pdf_path: str = "",
    ) -> Optional[str]:
        """
        Write Phase 1: books, extraction_chapters, extraction_topics.

        Flattens DocumentStructure into guide-style topics (one per section type).
        Returns book_id or None.
        """
        client = self._get_client()
        if not client:
            return None

        isbn = isbn or metadata.isbn
        grade = int(metadata.grade_level) if str(metadata.grade_level).isdigit() else 9

        try:
            # Upsert book
            book_data = {
                "title": metadata.title,
                "subject": metadata.subject,
                "grade_level": grade,
                "publisher": metadata.publisher or "",
                "series": None,
                "isbn": isbn,
                "edition": metadata.edition,
                "language": "en",
                "source_pdf_path": source_pdf_path,
                "extraction_job_id": job_id,
            }
            try:
                if isbn:
                    result = (
                        client.table("extraction_books")
                        .upsert(book_data, on_conflict="isbn")
                        .execute()
                    )
                else:
                    result = client.table("extraction_books").insert(book_data).execute()
                if result.data and len(result.data) > 0:
                    self._book_id = result.data[0]["id"]
            except Exception as ins_err:
                logger.warning("Book upsert/insert failed, trying select: %s", ins_err)
                sel = (
                    client.table("extraction_books")
                    .select("id")
                    .eq("title", metadata.title)
                    .eq("grade_level", grade)
                    .eq("subject", metadata.subject)
                    .limit(1)
                    .execute()
                )
                if sel.data:
                    self._book_id = sel.data[0]["id"]
                else:
                    raise

            if not self._book_id:
                logger.error("Failed to get book_id after upsert")
                return None

            # Update extraction_jobs with book_id
            self.update_extraction_job(job_id, "extraction", progress=50, book_id=self._book_id)

            # Write chapters and topics
            for chapter in structure.chapters:
                ch_slug = to_slug(chapter.title)
                ch_data = {
                    "book_id": self._book_id,
                    "chapter_number": chapter.chapter_number,
                    "title": chapter.title,
                    "slug": ch_slug,
                    "page_start": chapter.page_range[0],
                    "page_end": chapter.page_range[1],
                }
                ch_result = (
                    client.table("extraction_chapters")
                    .upsert(ch_data, on_conflict="book_id,chapter_number")
                    .execute()
                )
                chapter_uuid = ch_result.data[0]["id"] if ch_result.data else None
                if chapter_uuid:
                    self._chapter_map[ch_slug] = chapter_uuid

                # Flatten topics: each section becomes an extraction_topic
                topic_order = 0
                for topic in chapter.topics:
                    if topic.questions_section:
                        topic_order += 1
                        self._write_topic(
                            client,
                            chapter_uuid,
                            ch_slug,
                            topic,
                            topic.questions_section,
                            "questions",
                            topic_order,
                        )
                    if topic.answer_key_section:
                        topic_order += 1
                        self._write_topic(
                            client,
                            chapter_uuid,
                            ch_slug,
                            topic,
                            topic.answer_key_section,
                            "answer_key",
                            topic_order,
                        )
                if chapter.hints_section:
                    topic_order += 1
                    self._write_section_topic(
                        client,
                        chapter_uuid,
                        ch_slug,
                        chapter,
                        chapter.hints_section,
                        "hints",
                        topic_order,
                    )
                if chapter.explanations_section:
                    topic_order += 1
                    self._write_section_topic(
                        client,
                        chapter_uuid,
                        ch_slug,
                        chapter,
                        chapter.explanations_section,
                        "explanations",
                        topic_order,
                    )

            return self._book_id
        except Exception as e:
            logger.error("Phase 1 write failed: %s", e, exc_info=True)
            return None

    def _write_topic(
        self,
        client,
        chapter_id: str,
        chapter_slug: str,
        topic: Topic,
        section: Any,
        section_type: str,
        topic_order: int,
    ) -> None:
        title = topic.title
        slug = to_slug(title)
        data = {
            "chapter_id": chapter_id,
            "title": title,
            "slug": slug,
            "topic_order": topic_order,
            "section_type": section_type,
            "page_start": section.page_range[0],
            "page_end": section.page_range[1],
        }
        result = client.table("extraction_topics").upsert(data, on_conflict="chapter_id,slug").execute()
        if result.data:
            self._topic_map[(chapter_slug, slug)] = result.data[0]["id"]

    def _write_section_topic(
        self,
        client,
        chapter_id: str,
        chapter_slug: str,
        chapter: Chapter,
        section: Any,
        section_type: str,
        topic_order: int,
    ) -> None:
        title = "Hints" if section_type == "hints" else "Hints and Explanations"
        slug = to_slug(title)
        data = {
            "chapter_id": chapter_id,
            "title": title,
            "slug": slug,
            "topic_order": topic_order,
            "section_type": section_type,
            "page_start": section.page_range[0],
            "page_end": section.page_range[1],
        }
        result = client.table("extraction_topics").upsert(data, on_conflict="chapter_id,slug").execute()
        if result.data:
            self._topic_map[(chapter_slug, slug)] = result.data[0]["id"]

    def resolve_topic_id(self, chapter_slug: str, topic_slug: str) -> Optional[str]:
        """Resolve topic_id from chapter and topic slugs."""
        return self._topic_map.get((chapter_slug, topic_slug))

    def resolve_chapter_id(self, chapter_slug: str) -> Optional[str]:
        return self._chapter_map.get(chapter_slug)

    def write_raw_question(
        self,
        job_id: str,
        raw: RawQuestion,
    ) -> Optional[str]:
        """Insert raw_questions row. Returns raw_question_id."""
        client = self._get_client()
        if not client:
            return None

        try:
            data = {
                "job_id": job_id,
                "question_number": raw.question_number,
                "question_text": raw.question_text,
                "options": raw.options or [],
                "page_number": raw.page_number,
                "chapter_context": raw.chapter_context,
                "topic_context": raw.topic_context,
                "sub_topic_context": raw.sub_topic_context,
                "raw_images": [{"path": img.path, "alt": img.alt_text} for img in raw.images],
                "raw_tables": raw.tables,
                "processing_status": "pending",
            }
            result = client.table("raw_questions").insert(data).execute()
            return result.data[0]["id"] if result.data else None
        except Exception as e:
            logger.error("Failed to write raw_question: %s", e)
            return None

    def write_question(
        self,
        tagged: TaggedQuestion,
        raw_question_id: Optional[str],
        job_id: str,
        question_number: str = "",
        page_number: int = 1,
    ) -> Optional[str]:
        """
        Write extraction_questions, options, question_images, question_tags.

        Extracts base64 images, saves to storage, replaces in question_text.
        """
        client = self._get_client()
        if not client or not self._book_id:
            return None

        chapter_slug = to_slug(tagged.chapter)
        topic_slug = to_slug(tagged.topic)
        chapter_id = self.resolve_chapter_id(chapter_slug)
        topic_id = self.resolve_topic_id(chapter_slug, topic_slug)

        if not chapter_id or not topic_id:
            logger.warning(
                "Could not resolve chapter_id=%s or topic_id=%s for question %s",
                chapter_slug,
                topic_slug,
                tagged.question[:50],
            )
            return None

        question_text = tagged.question
        image_records: list[dict] = []

        # Extract and save images (upload to Supabase when available)
        question_id_pre = str(uuid4())
        storage_root = Path(self.storage_root)
        if storage_root.is_relative():
            storage_root = Path.cwd() / storage_root
        storage_manager = None
        if client:
            try:
                from app.services.storage_manager import StorageManager
                storage_manager = StorageManager(client)
            except Exception:
                pass
        image_records = extract_and_save_images(
            question_text,
            question_id_pre,
            self._book_id,
            storage_root,
            storage_manager=storage_manager,
        )
        if image_records:
            question_text = replace_images_in_text(question_text, list(image_records))

        answer_type = ANSWER_TYPE_MAP.get(
            tagged.answer_type.value if hasattr(tagged.answer_type, "value") else str(tagged.answer_type),
            "mcq_single",
        )

        try:
            q_data = {
                "id": question_id_pre,
                "question_number": question_number,
                "question_text": question_text,
                "topic_id": topic_id,
                "chapter_id": chapter_id,
                "book_id": self._book_id,
                "sub_topic": tagged.sub_topic,
                "answer_type": answer_type,
                "difficulty": tagged.difficulty.value if hasattr(tagged.difficulty, "value") else tagged.difficulty,
                "bloom_level": None,
                "page_number": page_number,
                "has_image": len(image_records) > 0,
                "has_table": bool(tagged.tables),
                "has_math": "$" in question_text or "\\(" in question_text,
                "raw_question_id": raw_question_id,
            }
            result = client.table("extraction_questions").insert(q_data).execute()
            question_id = result.data[0]["id"] if result.data else question_id_pre
            if not question_id:
                return None

            # Write options (A, B, C, D)
            labels = ["A", "B", "C", "D"]
            for i, opt in enumerate(tagged.options):
                opt_data = {
                    "question_id": question_id,
                    "label": labels[i] if i < len(labels) else chr(65 + i),
                    "text": opt.text if hasattr(opt, "text") else str(opt),
                    "is_correct": False,
                    "sort_order": i,
                }
                client.table("extraction_options").insert(opt_data).execute()

            # Write question_images
            for rec in image_records:
                img_data = {
                    "question_id": question_id,
                    "storage_path": rec["storage_path"],
                    "alt_text": rec.get("alt_text"),
                    "sort_order": rec["sort_order"],
                    "position_in_question": rec.get("position_in_question", "question"),
                }
                client.table("question_images").insert(img_data).execute()

            # Write question_tags
            for tag in tagged.tags:
                client.table("question_tags").insert(
                    {"question_id": question_id, "tag": tag, "source": "auto"}
                ).execute()

            return question_id
        except Exception as e:
            logger.error("Failed to write question: %s", e, exc_info=True)
            return None

    def write_answers(
        self,
        answer_key_map: dict[str, str],
        question_id_map: dict[str, str],
        explanation_map: Optional[dict[str, str]] = None,
    ) -> None:
        """
        Write extraction_answers and update options.is_correct.

        answer_key_map: {question_number: answer_letter}
        question_id_map: {question_number: extraction_questions.id}
        """
        client = self._get_client()
        if not client:
            return

        explanation_map = explanation_map or {}
        for qnum, answer_letter in answer_key_map.items():
            question_id = question_id_map.get(qnum)
            if not question_id:
                continue
            expl_text = explanation_map.get(qnum)
            answer, source = validate_answer(answer_letter, expl_text)
            if source == "conflict":
                logger.warning("Answer conflict for question %s: key=%s vs explanation", qnum, answer_letter)

            try:
                client.table("extraction_answers").upsert(
                    {
                        "question_id": question_id,
                        "correct_answer": answer.lower(),
                        "correct_option_ids": [],
                        "answer_source": source,
                        "page_number": None,
                    },
                    on_conflict="question_id",
                ).execute()

                # Update options SET is_correct = true WHERE label = answer
                opts = (
                    client.table("extraction_options")
                    .select("id")
                    .eq("question_id", question_id)
                    .eq("label", answer.upper())
                    .execute()
                )
                if opts.data:
                    client.table("extraction_options").update(
                        {"is_correct": True}
                    ).eq("id", opts.data[0]["id"]).execute()
            except Exception as e:
                logger.error("Failed to write answer for question %s: %s", qnum, e)

    def write_hints(
        self,
        hint_map: dict[str, str],
        question_id_map: dict[str, str],
    ) -> None:
        """Write extraction_hints. hint_map: {question_number: hint_text}."""
        client = self._get_client()
        if not client:
            return
        for qnum, hint_text in hint_map.items():
            question_id = question_id_map.get(qnum)
            if not question_id or not hint_text:
                continue
            try:
                client.table("extraction_hints").upsert(
                    {
                        "question_id": question_id,
                        "hint_text": hint_text,
                        "sort_order": 0,
                    },
                    on_conflict="question_id",
                ).execute()
            except Exception as e:
                logger.error("Failed to write hint for question %s: %s", qnum, e)

    def write_explanations(
        self,
        explanation_map: dict[str, str],
        question_id_map: dict[str, str],
    ) -> None:
        """Write extraction_explanations. explanation_map: {question_number: explanation_text}."""
        client = self._get_client()
        if not client:
            return
        for qnum, explanation_text in explanation_map.items():
            question_id = question_id_map.get(qnum)
            if not question_id or not explanation_text:
                continue
            try:
                client.table("extraction_explanations").upsert(
                    {
                        "question_id": question_id,
                        "explanation_text": explanation_text,
                    },
                    on_conflict="question_id",
                ).execute()
            except Exception as e:
                logger.error("Failed to write explanation for question %s: %s", qnum, e)
