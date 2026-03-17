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
from .extraction_helpers import normalize_question_number, parse_answer_key, to_slug
from .metadata_tagger import DocumentContext, MetadataTagger
from .models import BookMetadata, DocumentStructure
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

        # 3. Collect answer keys, hints, explanations from all sections
        all_answer_keys: list = []
        all_hints: list = []
        all_explanations: list = []
        raw_questions_by_topic: dict[tuple[str, str], list] = {}
        answer_key_map: dict[str, str] = {}
        hint_map: dict[str, str] = {}
        explanation_map: dict[str, str] = {}

        for chapter in structure.chapters:
            for topic in chapter.topics:
                if topic.questions_section:
                    ext_ctx = ExtractionContext(chapter, topic)
                    raw_questions = question_extractor.extract_questions(
                        topic.questions_section,
                        ext_ctx,
                    )
                    raw_questions_by_topic[(chapter.title, topic.title)] = raw_questions

                if topic.answer_key_section:
                    keys = question_extractor.extract_answer_keys(topic.answer_key_section)
                    all_answer_keys.extend(keys)
                    for ak in keys:
                        answer_key_map[ak.question_number] = ak.answer

            if chapter.hints_section:
                hints = question_extractor.extract_hints(chapter.hints_section)
                all_hints.extend(hints)
                for h in hints:
                    hint_map[h.question_number] = h.hint_text
            if chapter.explanations_section:
                explanations = question_extractor.extract_explanations(
                    chapter.explanations_section,
                )
                all_explanations.extend(explanations)
                for ex in explanations:
                    explanation_map[ex.question_number] = ex.explanation_text

        # 4. Link answers, hints, explanations for each topic's questions
        all_linked: list = []
        for (_, _), raw_questions in raw_questions_by_topic.items():
            linked = relationship_linker.link_answers(raw_questions, all_answer_keys)
            linked = relationship_linker.link_hints(linked, all_hints)
            linked = relationship_linker.link_explanations(linked, all_explanations)
            all_linked.extend(linked)

        # 5. Supplement answer_key_map from parse_answer_key for any missing
        for chapter in structure.chapters:
            for topic in chapter.topics:
                if topic.answer_key_section:
                    parsed = parse_answer_key(topic.answer_key_section.content)
                    for k, v in parsed.items():
                        if k not in answer_key_map:
                            answer_key_map[k] = v

        # 6. Apply metadata and write to DB
        question_id_map: dict[str, str] = {}
        for linked in all_linked:
            try:
                tagged = metadata_tagger.apply_metadata(linked, context)
            except ValueError as e:
                logger.warning("Metadata tagging failed for question %s: %s", linked.raw_question.question_number, e)
                continue

            raw = linked.raw_question
            qnum = normalize_question_number(raw.question_number)

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
                    question_id_map[qnum] = q_id
                    questions_written += 1

        # 7. Write answers, hints, explanations
        if db_writer.is_available() and question_id_map:
            db_writer.write_answers(
                answer_key_map=answer_key_map,
                question_id_map=question_id_map,
                explanation_map=explanation_map,
            )
            db_writer.write_hints(hint_map=hint_map, question_id_map=question_id_map)
            db_writer.write_explanations(
                explanation_map=explanation_map,
                question_id_map=question_id_map,
            )

        return questions_written

    except Exception as e:
        logger.error("Extraction pipeline failed: %s", e, exc_info=True)
        return questions_written
