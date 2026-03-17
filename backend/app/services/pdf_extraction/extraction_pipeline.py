"""
Orchestrates the full book extraction pipeline: structure analysis, question extraction,
relationship linking, metadata tagging, and database writes.

Runs after DocumentProcessor completes PDF extraction. Reads combined.md, runs
StructureAnalyzer, QuestionExtractor, RelationshipLinker, MetadataTagger, and DatabaseWriter.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .database_writer import DatabaseWriter
from .extraction_helpers import normalize_question_number, parse_answer_key
from .metadata_tagger import DocumentContext, MetadataTagger
from .models import AnswerKey, BookMetadata
from .question_extractor import ExtractionContext, QuestionExtractor
from .relationship_linker import RelationshipLinker
from .structure_analyzer import StructureAnalyzer

logger = logging.getLogger(__name__)


def run_extraction_pipeline(
    job_id: str,
    extracted_path: str,
    manifest_path: str,
    metadata: BookMetadata,
    source_pdf_path: str = "",
    storage_root: Optional[Path] = None,
    total_pages: int = 0,
) -> int:
    """
    Run the full extraction pipeline after PDF extraction completes.

    Returns the number of questions successfully written to the database.
    """
    combined_path = Path(extracted_path) / "combined.md"
    if not combined_path.exists():
        logger.warning("combined.md not found at %s, skipping structured extraction", combined_path)
        return 0

    markdown_content = combined_path.read_text(encoding="utf-8", errors="ignore")
    if not markdown_content.strip():
        logger.warning("combined.md is empty, skipping structured extraction")
        return 0

    structure_analyzer = StructureAnalyzer()
    question_extractor = QuestionExtractor()
    relationship_linker = RelationshipLinker()
    metadata_tagger = MetadataTagger()
    db_writer = DatabaseWriter(storage_root=storage_root, job_id=job_id)

    questions_written = 0

    try:
        if db_writer.is_available():
            source_filename = Path(source_pdf_path).name if source_pdf_path else "source.pdf"
            db_writer.write_extraction_job(
                job_id=job_id,
                title=metadata.title or "",
                source_pdf_filename=source_filename,
                source_pdf_path=source_pdf_path or "",
                total_pages=total_pages,
                extracted_path=extracted_path,
                manifest_path=manifest_path,
            )
            db_writer.update_extraction_job(job_id, "extraction", progress=10)

        # 1. Analyze document structure
        structure = structure_analyzer.analyze_document(markdown_content, metadata)
        context = DocumentContext(structure)

        # 2. Phase 1: Write books, chapters, topics
        if db_writer.is_available():
            book_id = db_writer.write_phase1(
                job_id=job_id,
                metadata=metadata,
                structure=structure,
                isbn=metadata.isbn,
                source_pdf_path=source_pdf_path,
            )
            if not book_id:
                logger.warning("Phase 1 write failed, continuing without DB")

        # 3. Collect section content scoped to the chapter/topic where it belongs.
        raw_questions_by_topic: dict[tuple[str, str], list] = {}
        answer_keys_by_topic: dict[tuple[str, str], list[AnswerKey]] = {}
        hints_by_chapter: dict[str, list] = {}
        explanations_by_chapter: dict[str, list] = {}

        for chapter in structure.chapters:
            chapter_hints = []
            chapter_explanations = []

            if chapter.hints_section:
                chapter_hints = question_extractor.extract_hints(chapter.hints_section)
            if chapter.explanations_section:
                chapter_explanations = question_extractor.extract_explanations(
                    chapter.explanations_section,
                )

            hints_by_chapter[chapter.title] = chapter_hints
            explanations_by_chapter[chapter.title] = chapter_explanations

            for topic in chapter.topics:
                topic_key = (chapter.title, topic.title)
                if topic.questions_section:
                    ext_ctx = ExtractionContext(chapter, topic)
                    raw_questions = question_extractor.extract_questions(
                        topic.questions_section,
                        ext_ctx,
                    )
                    raw_questions_by_topic[topic_key] = raw_questions

                if topic.answer_key_section:
                    keys = question_extractor.extract_answer_keys(topic.answer_key_section)
                    topic_answer_map = {
                        normalize_question_number(ak.question_number): ak for ak in keys
                    }
                    parsed = parse_answer_key(topic.answer_key_section.content)
                    for qnum, answer in parsed.items():
                        normalized_qnum = normalize_question_number(qnum)
                        topic_answer_map[normalized_qnum] = AnswerKey(
                            question_number=normalized_qnum,
                            answer=answer.upper(),
                            page_number=topic.answer_key_section.page_range[0],
                        )
                    answer_keys_by_topic[topic_key] = list(topic_answer_map.values())
                else:
                    answer_keys_by_topic[topic_key] = []

        # 4. Link and write questions using topic-scoped answer keys.
        for (chapter_title, topic_title), raw_questions in raw_questions_by_topic.items():
            linked = relationship_linker.link_answers(
                raw_questions,
                answer_keys_by_topic.get((chapter_title, topic_title), []),
            )
            linked = relationship_linker.link_hints(
                linked,
                hints_by_chapter.get(chapter_title, []),
            )
            linked = relationship_linker.link_explanations(
                linked,
                explanations_by_chapter.get(chapter_title, []),
            )

            for linked_question in linked:
                try:
                    tagged = metadata_tagger.apply_metadata(linked_question, context)
                except ValueError as e:
                    logger.warning(
                        "Metadata tagging failed for question %s: %s",
                        linked_question.raw_question.question_number,
                        e,
                    )
                    continue

                raw = linked_question.raw_question

                if db_writer.is_available():
                    raw_id = db_writer.write_raw_question(job_id, raw)
                    q_id = db_writer.write_question(
                        tagged=tagged,
                        raw_question_id=raw_id,
                        job_id=job_id,
                        question_number=raw.question_number,
                        page_number=raw.page_number,
                    )
                    if q_id:
                        db_writer.write_answer(
                            question_id=q_id,
                            answer_text=linked_question.answer_key,
                            explanation_text=linked_question.explanation,
                            question_ref=f"{chapter_title} > {topic_title} > {raw.question_number}",
                        )
                        db_writer.write_hint(
                            question_id=q_id,
                            hint_text=linked_question.hint,
                            question_ref=f"{chapter_title} > {topic_title} > {raw.question_number}",
                        )
                        db_writer.write_explanation(
                            question_id=q_id,
                            explanation_text=linked_question.explanation,
                            question_ref=f"{chapter_title} > {topic_title} > {raw.question_number}",
                        )
                        questions_written += 1

        return questions_written

    except Exception as e:
        logger.error("Extraction pipeline failed: %s", e, exc_info=True)
        return questions_written
