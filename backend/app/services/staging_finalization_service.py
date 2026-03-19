"""
Finalize raw_questions into canonical questions/options/answers using Supabase client.

Replaces the legacy FinalizationService (async SQL) which did not match Supabase usage.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.models.admin import BulkOperationResult
from app.models.extraction import normalize_raw_options_value

logger = logging.getLogger(__name__)

_DB_ANSWER_TYPES = {
    "mcq_single",
    "mcq_multiple",
    "integer",
    "numerical",
    "subjective",
    "true_false",
    "fill_blank",
    "match",
}


def _parse_correct_labels(correct_answer: Optional[str]) -> Set[str]:
    if not correct_answer or not str(correct_answer).strip():
        return set()
    parts = [p.strip().upper() for p in re.split(r"[,;]", str(correct_answer)) if p.strip()]
    return set(parts)


def _difficulty_from_chapter_number(chapter_number: int) -> str:
    if chapter_number <= 3:
        return "easy"
    if chapter_number <= 6:
        return "medium"
    return "hard"


def _has_math(text: str) -> bool:
    return bool(re.search(r"\$.*?\$|\\\[.*?\\\]|\\\(.*?\\\)", text))


class StagingFinalizationService:
    def __init__(self, db_client):
        self.db = db_client

    def _resolve_canonical_book_id(self, job_book_id: UUID) -> Optional[UUID]:
        """Map extraction_books.id to curriculum books.id when needed."""
        rb = self.db.table("books").select("id").eq("id", str(job_book_id)).limit(1).execute()
        if rb.data:
            return job_book_id
        eb = (
            self.db.table("extraction_books")
            .select("title, subject, grade_level")
            .eq("id", str(job_book_id))
            .limit(1)
            .execute()
        )
        if not eb.data:
            return None
        row = eb.data[0]
        cb = (
            self.db.table("books")
            .select("id")
            .eq("title", row["title"])
            .eq("subject", row["subject"])
            .eq("grade_level", row["grade_level"])
            .limit(1)
            .execute()
        )
        if cb.data:
            return UUID(cb.data[0]["id"])
        logger.warning(
            "No canonical books row for extraction_book %s (%s); create a matching books row",
            job_book_id,
            row.get("title"),
        )
        return None

    def _match_ctx(self, needle: str, title: Optional[str], slug: Optional[str]) -> bool:
        if not needle or not needle.strip():
            return False
        n = needle.strip().lower()
        if title and title.strip().lower() == n:
            return True
        if slug and slug.strip().lower() == n:
            return True
        return False

    def _resolve_topic_ids(
        self, canonical_book_id: UUID, chapter_ctx: str, topic_ctx: str
    ) -> Optional[Tuple[UUID, UUID, UUID]]:
        chapters = (
            self.db.table("chapters")
            .select("*")
            .eq("book_id", str(canonical_book_id))
            .order("chapter_number")
            .execute()
        )
        chapter_id = None
        chapter_number = 1
        for ch in chapters.data or []:
            if self._match_ctx(chapter_ctx, ch.get("title"), ch.get("slug")):
                chapter_id = UUID(ch["id"])
                chapter_number = int(ch.get("chapter_number") or 1)
                break
        if not chapter_id:
            return None
        topics = (
            self.db.table("topics")
            .select("*")
            .eq("chapter_id", str(chapter_id))
            .order("topic_order")
            .execute()
        )
        topic_id = None
        for t in topics.data or []:
            if self._match_ctx(topic_ctx, t.get("title"), t.get("slug")):
                topic_id = UUID(t["id"])
                break
        if not topic_id:
            return None
        return canonical_book_id, chapter_id, topic_id

    def _infer_answer_type(self, opts: List[str], explicit: Optional[str]) -> str:
        if explicit:
            e = explicit.strip().lower()
            if e in _DB_ANSWER_TYPES:
                return e
        if len(opts) >= 2:
            return "mcq_single"
        return "integer"

    def finalize_raw_question(self, raw_question_id: UUID) -> Tuple[bool, Optional[str]]:
        rq = self.db.table("raw_questions").select("*").eq("id", str(raw_question_id)).execute()
        if not rq.data:
            return False, "Raw question not found"
        row = rq.data[0]
        if row.get("question_id"):
            return False, "Already approved / finalized"
        st = (row.get("processing_status") or "").lower()
        if st == "rejected":
            return False, "Question is rejected — reinstate before approving"
        if st not in ("pending", "error", "failed"):
            return False, f"Cannot approve from status '{st}'"

        job_row = self.db.table("extraction_jobs").select("book_id").eq("id", row["job_id"]).execute()
        if not job_row.data or not job_row.data[0].get("book_id"):
            return False, "Job has no book_id"
        job_book_id = UUID(job_row.data[0]["book_id"])

        canonical_book_id = self._resolve_canonical_book_id(job_book_id)
        if not canonical_book_id:
            return False, "Could not resolve curriculum book — add a matching row in books"

        chapter_ctx = (row.get("chapter_context") or "").strip()
        topic_ctx = (row.get("topic_context") or "").strip()
        if not chapter_ctx or not topic_ctx:
            return False, "chapter_context and topic_context are required"

        resolved = self._resolve_topic_ids(canonical_book_id, chapter_ctx, topic_ctx)
        if not resolved:
            return False, "Chapter/topic not found for this book — check titles/slugs against outline"
        book_id, chapter_id, topic_id = resolved

        opts = normalize_raw_options_value(row.get("options"))
        answer_type = self._infer_answer_type(opts, row.get("answer_type"))
        labels = _parse_correct_labels(row.get("correct_answer"))

        if answer_type in ("integer", "numerical", "subjective"):
            ca = (row.get("correct_answer") or "").strip()
            if not ca:
                return False, "correct_answer is required for this question type"
        else:
            if len(opts) < 2:
                return False, "At least two options are required for MCQ"
            if not labels:
                return False, "correct_answer is required (e.g. A or A,B)"

        ch = self.db.table("chapters").select("chapter_number").eq("id", str(chapter_id)).limit(1).execute()
        ch_num = int(ch.data[0]["chapter_number"]) if ch.data else 1
        difficulty = _difficulty_from_chapter_number(ch_num)

        qtext = (row.get("question_text") or "").strip()
        if not qtext:
            return False, "question_text is empty"

        raw_imgs = row.get("raw_images") or []
        raw_tbls = row.get("raw_tables") or []
        has_image = bool(raw_imgs)
        has_table = bool(raw_tbls)

        now = datetime.now(timezone.utc).isoformat()
        question_uuid = uuid4()
        qid_str = str(question_uuid)

        marks = row.get("marks")
        neg = row.get("negative_marks")
        bloom = row.get("bloom_level")

        question_data: Dict[str, Any] = {
            "id": qid_str,
            "question_number": (row.get("question_number") or "1").strip(),
            "question_text": qtext,
            "topic_id": str(topic_id),
            "chapter_id": str(chapter_id),
            "book_id": str(book_id),
            "sub_topic": row.get("sub_topic_context"),
            "answer_type": answer_type,
            "difficulty": difficulty,
            "page_number": row.get("page_number"),
            "has_image": has_image,
            "has_table": has_table,
            "has_math": _has_math(qtext),
            "marks": float(marks) if marks is not None else None,
            "negative_marks": float(neg) if neg is not None else None,
            "bloom_level": bloom,
            "raw_question_id": str(raw_question_id),
            "created_at": now,
            "updated_at": now,
        }

        try:
            self.db.table("questions").insert(question_data).execute()
        except Exception as e:
            logger.exception("Insert question failed")
            return False, f"Insert question failed: {e}"

        if answer_type not in ("integer", "numerical", "subjective"):
            for i, text in enumerate(opts):
                label = chr(65 + i)
                if ord(label) > 90:
                    break
                is_correct = label in labels
                try:
                    self.db.table("options").insert(
                        {
                            "id": str(uuid4()),
                            "question_id": qid_str,
                            "label": label,
                            "text": text,
                            "is_correct": is_correct,
                            "sort_order": i,
                            "created_at": now,
                        }
                    ).execute()
                except Exception as e:
                    logger.exception("Insert option failed")
                    return False, f"Insert option failed: {e}"

        if answer_type not in ("integer", "numerical", "subjective"):
            opt_rows = (
                self.db.table("options")
                .select("id, label")
                .eq("question_id", qid_str)
                .execute()
            )
            id_by_label = {r["label"]: r["id"] for r in (opt_rows.data or [])}
            correct_ids = [id_by_label[l] for l in sorted(labels) if l in id_by_label]
            try:
                self.db.table("answers").insert(
                    {
                        "id": str(uuid4()),
                        "question_id": qid_str,
                        "correct_answer": (row.get("correct_answer") or "").strip(),
                        "correct_option_ids": correct_ids,
                        "answer_source": "manual",
                        "page_number": row.get("page_number"),
                        "created_at": now,
                    }
                ).execute()
            except Exception as e:
                logger.exception("Insert answer failed")
                return False, f"Insert answer failed: {e}"
        else:
            try:
                self.db.table("answers").insert(
                    {
                        "id": str(uuid4()),
                        "question_id": qid_str,
                        "correct_answer": (row.get("correct_answer") or "").strip(),
                        "correct_option_ids": [],
                        "answer_source": "manual",
                        "page_number": row.get("page_number"),
                        "created_at": now,
                    }
                ).execute()
            except Exception as e:
                logger.exception("Insert answer failed")
                return False, f"Insert answer failed: {e}"

        for i, img in enumerate(raw_imgs if isinstance(raw_imgs, list) else []):
            if not isinstance(img, dict):
                continue
            path = img.get("path") or img.get("url") or img.get("storage_path") or ""
            if not path:
                continue
            try:
                self.db.table("question_images").insert(
                    {
                        "id": str(uuid4()),
                        "question_id": qid_str,
                        "storage_path": str(path)[:2048],
                        "alt_text": img.get("alt_text"),
                        "width_px": img.get("width_px") or img.get("width"),
                        "height_px": img.get("height_px") or img.get("height"),
                        "position_in_question": img.get("position", "question"),
                        "sort_order": i,
                        "created_at": now,
                    }
                ).execute()
            except Exception as e:
                logger.warning("Skip image insert: %s", e)

        for i, tbl in enumerate(raw_tbls if isinstance(raw_tbls, list) else []):
            if not isinstance(tbl, dict):
                continue
            headers = tbl.get("headers") or []
            rows_json = tbl.get("rows")
            if rows_json is None:
                rows_json = []
            try:
                self.db.table("question_tables").insert(
                    {
                        "id": str(uuid4()),
                        "question_id": qid_str,
                        "headers": headers,
                        "rows": rows_json,
                        "caption": tbl.get("caption"),
                        "sort_order": i,
                        "created_at": now,
                    }
                ).execute()
            except Exception as e:
                logger.warning("Skip table insert: %s", e)

        try:
            self.db.table("raw_questions").update(
                {
                    "question_id": qid_str,
                    "processing_status": "tagged",
                    "error_message": None,
                    "updated_at": now,
                }
            ).eq("id", str(raw_question_id)).execute()
        except Exception as e:
            logger.exception("Update raw_question failed")
            return False, f"Could not mark raw row finalized: {e}"

        return True, None

    def bulk_finalize_questions(self, question_ids: List[UUID]) -> BulkOperationResult:
        successful: List[UUID] = []
        failed: List[Dict[str, Any]] = []
        for qid in question_ids:
            ok, err = self.finalize_raw_question(qid)
            if ok:
                successful.append(qid)
            else:
                failed.append({"id": str(qid), "error": err or "Unknown error"})
        return BulkOperationResult(
            successful=successful,
            failed=failed,
            total=len(question_ids),
            success_count=len(successful),
            failure_count=len(failed),
        )
