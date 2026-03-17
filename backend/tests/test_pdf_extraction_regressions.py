import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

from app.services.pdf_extraction.database_writer import DatabaseWriter
from app.services.pdf_extraction.models import (
    AnswerKey,
    BookMetadata,
    Chapter,
    DifficultyLevel,
    DocumentStructure,
    LinkedQuestion,
    Option,
    QuestionType,
    RawQuestion,
    Section,
    SectionType,
    TaggedQuestion,
    Topic,
)


class _FakeTable:
    def __init__(self, name: str, inserts: dict[str, list[dict]]):
        self.name = name
        self.inserts = inserts
        self._record = None

    def insert(self, record: dict):
        self._record = record
        self.inserts.setdefault(self.name, []).append(record)
        return self

    def execute(self):
        return SimpleNamespace(data=[self._record] if self._record is not None else [])


class _FakeSupabaseClient:
    def __init__(self):
        self.inserts: dict[str, list[dict]] = {}

    def table(self, name: str) -> _FakeTable:
        return _FakeTable(name, self.inserts)


class DatabaseWriterRegressionTests(unittest.TestCase):
    def test_resolve_storage_root_makes_relative_paths_absolute(self):
        writer = DatabaseWriter(storage_root=Path("data/extracted_images"))

        resolved = writer._resolve_storage_root()

        self.assertTrue(resolved.is_absolute())
        self.assertEqual(resolved, Path.cwd() / "data/extracted_images")


class DocumentProcessorRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document_processor_module = importlib.import_module(
            "app.services.pdf_extraction.document_processor"
        )
        cls.DocumentProcessor = cls.document_processor_module.DocumentProcessor

    def test_normalize_block_id_preserves_existing_uuid(self):
        existing_uuid = str(uuid4())

        normalized = self.DocumentProcessor._normalize_block_id(
            job_id=str(uuid4()),
            page_num=1,
            block_index=0,
            block={"block_id": existing_uuid},
        )

        self.assertEqual(normalized, existing_uuid)

    def test_write_extraction_pages_and_blocks_uses_uuid_safe_ids(self):
        processor = self.DocumentProcessor.__new__(self.DocumentProcessor)
        processor.supabase_client = _FakeSupabaseClient()

        source_block_id = "20260317_1ed48231-eed0-4dd0-8f5b-0dcd025f4256_1_block_000"
        job_id = str(uuid4())
        processor._write_extraction_pages_and_blocks(
            job_id=job_id,
            page_num=1,
            page_data={
                "image_width": 100,
                "image_height": 200,
                "blocks": [
                    {
                        "block_id": source_block_id,
                        "layout_tag": "paragraph",
                        "confidence": 0.95,
                        "reading_order": 1,
                        "text": "Example text",
                    }
                ],
            },
        )

        block_records = processor.supabase_client.inserts["extraction_blocks"]
        self.assertEqual(len(block_records), 1)

        stored_block = block_records[0]
        UUID(stored_block["id"])
        self.assertEqual(stored_block["job_id"], job_id)
        self.assertEqual(stored_block["raw_block"]["source_block_id"], source_block_id)
        self.assertEqual(stored_block["raw_block"]["block_id"], stored_block["id"])


class QuestionExtractorRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.question_extractor_module = importlib.import_module(
            "app.services.pdf_extraction.question_extractor"
        )
        cls.QuestionExtractor = cls.question_extractor_module.QuestionExtractor

    def test_clean_answer_text_extracts_option_label_from_explanation(self):
        extractor = self.QuestionExtractor.__new__(self.QuestionExtractor)

        cleaned = extractor._clean_answer_text(
            "76 cm of Hg therefore 19 cm Hg = 25323 Pascal. Hence, the correct option is (c)."
        )

        self.assertEqual(cleaned, "C")


class TaggedQuestionRegressionTests(unittest.TestCase):
    def test_mcq_validator_accepts_embedded_option_label(self):
        tagged = TaggedQuestion(
            question="What is correct?",
            options=[
                Option(text="Alpha", label="A"),
                Option(text="Beta", label="B"),
                Option(text="Gamma", label="C"),
                Option(text="Delta", label="D"),
            ],
            correct_answer="Hence, the correct option is (c).",
            explanation=None,
            hint=None,
            difficulty=DifficultyLevel.MEDIUM,
            topic="Topic",
            topic_id="topic-1",
            chapter="Chapter",
            chapter_id="chapter-1",
            subject="Chemistry",
            subject_id="subject-1",
            grade_level=["10"],
            tags=[],
            source="Book",
            answer_type=QuestionType.MCQ_SINGLE,
            images=[],
            tables=[],
            sub_topic=None,
        )

        self.assertEqual(tagged.correct_answer, "C")


class ExtractionPipelineRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pipeline_module = importlib.import_module(
            "app.services.pdf_extraction.extraction_pipeline"
        )

    def test_pipeline_links_answers_per_topic_instead_of_global_pool(self):
        metadata = BookMetadata(
            title="Book",
            subject="Chemistry",
            grade_level="10",
            publisher="Publisher",
        )
        structure = DocumentStructure(
            chapters=[
                Chapter(
                    chapter_number=1,
                    title="Chapter 1",
                    page_range=(1, 5),
                    topics=[
                        Topic(
                            title="Topic A",
                            page_range=(1, 2),
                            sub_topics=[],
                            questions_section=Section(
                                section_type=SectionType.QUESTIONS,
                                page_range=(1, 1),
                                content="topic-a-questions",
                                confidence=0.9,
                            ),
                            answer_key_section=Section(
                                section_type=SectionType.ANSWER_KEY,
                                page_range=(1, 1),
                                content="topic-a-answers",
                                confidence=0.9,
                            ),
                        ),
                        Topic(
                            title="Topic B",
                            page_range=(3, 4),
                            sub_topics=[],
                            questions_section=Section(
                                section_type=SectionType.QUESTIONS,
                                page_range=(3, 3),
                                content="topic-b-questions",
                                confidence=0.9,
                            ),
                            answer_key_section=Section(
                                section_type=SectionType.ANSWER_KEY,
                                page_range=(3, 3),
                                content="topic-b-answers",
                                confidence=0.9,
                            ),
                        ),
                    ],
                )
            ],
            metadata=metadata,
            total_pages=5,
            structure_confidence=0.9,
        )

        class FakeStructureAnalyzer:
            def analyze_document(self, markdown_content, incoming_metadata):
                return structure

        class FakeQuestionExtractor:
            def extract_questions(self, section, context):
                return [
                    RawQuestion(
                        question_number="1",
                        question_text=f"Question for {context.topic.title}",
                        options=["Alpha", "Beta", "Gamma", "Delta"],
                        images=[],
                        tables=[],
                        page_number=section.page_range[0],
                        chapter_context=context.chapter.title,
                        topic_context=context.topic.title,
                        sub_topic_context=None,
                    )
                ]

            def extract_answer_keys(self, section):
                answer = "A" if section.content == "topic-a-answers" else "B"
                return [AnswerKey(question_number="1", answer=answer, page_number=section.page_range[0])]

            def extract_hints(self, section):
                return []

            def extract_explanations(self, section):
                return []

        class FakeRelationshipLinker:
            def __init__(self):
                self.answer_link_inputs = []

            def link_answers(self, questions, answer_keys):
                self.answer_link_inputs.append([answer.answer for answer in answer_keys])
                answer = answer_keys[0].answer if answer_keys else None
                return [
                    LinkedQuestion(
                        raw_question=question,
                        answer_key=answer,
                        hint=None,
                        explanation=None,
                        link_confidence={"answer": 1.0},
                    )
                    for question in questions
                ]

            def link_hints(self, questions, hints):
                return questions

            def link_explanations(self, questions, explanations):
                return questions

        class FakeMetadataTagger:
            def apply_metadata(self, linked_question, context):
                return SimpleNamespace()

        class FakeDatabaseWriter:
            def __init__(self, storage_root=None, job_id=None):
                self.storage_root = storage_root
                self.job_id = job_id

            def is_available(self):
                return False

        fake_linker = FakeRelationshipLinker()

        with tempfile.TemporaryDirectory() as tmpdir:
            extracted_path = Path(tmpdir)
            (extracted_path / "combined.md").write_text("# extracted", encoding="utf-8")

            with (
                patch.object(self.pipeline_module, "StructureAnalyzer", return_value=FakeStructureAnalyzer()),
                patch.object(self.pipeline_module, "QuestionExtractor", return_value=FakeQuestionExtractor()),
                patch.object(self.pipeline_module, "RelationshipLinker", return_value=fake_linker),
                patch.object(self.pipeline_module, "MetadataTagger", return_value=FakeMetadataTagger()),
                patch.object(self.pipeline_module, "DatabaseWriter", FakeDatabaseWriter),
            ):
                questions_written = self.pipeline_module.run_extraction_pipeline(
                    job_id=str(uuid4()),
                    extracted_path=str(extracted_path),
                    manifest_path=str(extracted_path / "manifest.json"),
                    metadata=metadata,
                )

        self.assertEqual(questions_written, 0)
        self.assertEqual(fake_linker.answer_link_inputs, [["A"], ["B"]])


if __name__ == "__main__":
    unittest.main()
