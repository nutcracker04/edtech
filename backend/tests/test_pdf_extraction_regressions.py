import importlib
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.services.pdf_extraction.database_writer import DatabaseWriter


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


if __name__ == "__main__":
    unittest.main()
