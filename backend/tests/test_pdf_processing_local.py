import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.routers import pdf_processing
from app.services.pdf_extraction.config import PDFExtractionConfig
from app.services.pdf_extraction.document_processor import (
    DocumentProcessor,
    ProcessingArtifacts,
    ProcessingResult,
    ProcessingStage,
    ProcessingStatus,
    ValidationResult,
)
from app.services.pdf_extraction.models import BookMetadata


class FakeProcessor:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self._jobs = {}
        self._results = {}

    def queue_job(self, job_id: str) -> None:
        now = time.time()
        self._jobs[job_id] = ProcessingStatus(
            job_id=job_id,
            current_stage=ProcessingStage.QUEUED,
            progress=0.0,
            started_at=now,
            updated_at=now,
        )

    def process_pdf(self, pdf_path: str, metadata: BookMetadata, job_id: str | None = None):
        assert job_id is not None

        output_dir = self.storage_root / job_id
        extracted_dir = output_dir / "extracted"
        images_dir = extracted_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        markdown_rel = "extracted/book.md"
        image_rel = "extracted/images/page-1.png"

        (output_dir / markdown_rel).write_text("# Extracted book\n\nSample content", encoding="utf-8")
        (output_dir / image_rel).write_bytes(b"fake-image")

        manifest_path = output_dir / "manifest.json"
        manifest_payload = {
            "job_id": job_id,
            "metadata": metadata.model_dump(),
            "source_pdf_path": str(Path(pdf_path).resolve()),
            "output_dir": str(output_dir),
            "extracted_path": str(extracted_dir),
            "markdown_files": [markdown_rel],
            "image_files": [image_rel],
            "other_files": [],
            "preview": "Sample content",
        }
        manifest_path.write_text(json.dumps(manifest_payload), encoding="utf-8")

        self._jobs[job_id].current_stage = ProcessingStage.COMPLETED
        self._jobs[job_id].progress = 100.0
        self._jobs[job_id].is_complete = True
        self._jobs[job_id].updated_at = time.time()

        artifacts = ProcessingArtifacts(
            source_pdf_path=str(Path(pdf_path).resolve()),
            output_dir=str(output_dir),
            extracted_path=str(extracted_dir),
            manifest_path=str(manifest_path),
            markdown_files=[markdown_rel],
            image_files=[image_rel],
            other_files=[],
            preview="Sample content",
            metadata=metadata.model_dump(),
        )
        result = ProcessingResult(
            success=True,
            job_id=job_id,
            processing_time_seconds=0.01,
            extracted_path=str(extracted_dir),
            artifacts=artifacts,
            success_rate=100.0,
        )
        self._results[job_id] = result
        return result

    def get_processing_status(self, job_id: str):
        return self._jobs.get(job_id)

    def get_result(self, job_id: str):
        return self._results.get(job_id)

    def validate_pdf_structure(self, pdf_path: str):
        return ValidationResult(is_valid=True, confidence=1.0, chapter_count=0, errors=[])


class PdfProcessingRouterLocalTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_root = Path(self.temp_dir.name) / "data"
        self.fake_processor = FakeProcessor(self.data_root / "extracted_images")

        self.original_data_root = pdf_processing.DATA_ROOT
        self.original_processor = pdf_processing.processor

        pdf_processing.DATA_ROOT = self.data_root
        pdf_processing.processor = self.fake_processor

        app = FastAPI()
        app.include_router(pdf_processing.router)
        self.client = TestClient(app)

    def tearDown(self):
        pdf_processing.DATA_ROOT = self.original_data_root
        pdf_processing.processor = self.original_processor
        self.temp_dir.cleanup()

    def test_upload_status_and_result_store_local_artifacts(self):
        response = self.client.post(
            "/api/pdf/upload",
            data={
                "title": "Local Book",
                "subject": "Physics",
                "grade_level": "11",
                "publisher": "Local Publisher",
            },
            files={
                "file": ("book.pdf", b"%PDF-1.4\nfake pdf body", "application/pdf"),
            },
        )

        self.assertEqual(response.status_code, 202, response.text)
        payload = response.json()
        job_id = payload["job_id"]

        saved_pdf = self.data_root / "uploads" / f"{job_id}.pdf"
        self.assertTrue(saved_pdf.exists())

        status_response = self.client.get(f"/api/pdf/status/{job_id}")
        self.assertEqual(status_response.status_code, 200, status_response.text)
        self.assertEqual(status_response.json()["status"], "completed")

        result_response = self.client.get(f"/api/pdf/result/{job_id}")
        self.assertEqual(result_response.status_code, 200, result_response.text)
        result_payload = result_response.json()

        self.assertEqual(result_payload["status"], "completed")
        self.assertEqual(result_payload["statistics"]["markdown_file_count"], 1)
        self.assertEqual(result_payload["statistics"]["image_file_count"], 1)
        self.assertTrue(result_payload["artifacts"]["manifest_path"].endswith("manifest.json"))

        output_dir = Path(result_payload["artifacts"]["output_dir"])
        manifest_path = Path(result_payload["artifacts"]["manifest_path"])
        image_rel = result_payload["artifacts"]["image_files"][0]
        markdown_rel = result_payload["artifacts"]["markdown_files"][0]

        self.assertTrue(output_dir.exists())
        self.assertTrue(manifest_path.exists())
        self.assertTrue((output_dir / image_rel).exists())
        self.assertTrue((output_dir / markdown_rel).exists())


class DocumentProcessorLocalManifestTest(unittest.TestCase):
    def test_process_pdf_writes_manifest_and_collects_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir) / "local-extractions"
            uploads_root = Path(temp_dir) / "uploads"
            uploads_root.mkdir(parents=True, exist_ok=True)

            pdf_path = uploads_root / "book.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\nlocal test pdf")

            config = PDFExtractionConfig(
                sarvam_api_key="test-key",
                image_storage_path=str(storage_root),
                max_retries=1,
            )
            metadata = BookMetadata(
                title="Test Book",
                subject="Physics",
                grade_level="11",
                publisher="Test Publisher",
            )

            with patch("app.services.pdf_extraction.document_processor.SarvamAI"):
                processor = DocumentProcessor(config=config)

            def fake_extract(pdf_path_arg: str, job_id_arg: str) -> str:
                extracted_dir = storage_root / job_id_arg / "extracted"
                figures_dir = extracted_dir / "figures"
                figures_dir.mkdir(parents=True, exist_ok=True)
                (extracted_dir / "content.md").write_text("## Chapter 1\n\nExtracted text", encoding="utf-8")
                (figures_dir / "figure-1.png").write_bytes(b"png")
                (storage_root / job_id_arg / "raw-output.zip").write_bytes(b"zip")
                return str(extracted_dir)

            processor._extract_pdf_content = fake_extract  # type: ignore[method-assign]

            result = processor.process_pdf(str(pdf_path), metadata, job_id="job-123")

            self.assertTrue(result.success)
            self.assertIsNotNone(result.artifacts)
            assert result.artifacts is not None

            self.assertEqual(result.artifacts.markdown_files, ["extracted/content.md"])
            self.assertEqual(result.artifacts.image_files, ["extracted/figures/figure-1.png"])
            self.assertIn("raw-output.zip", result.artifacts.other_files)
            self.assertTrue(Path(result.artifacts.manifest_path).exists())

            manifest = json.loads(Path(result.artifacts.manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest["metadata"]["title"], "Test Book")
            self.assertEqual(manifest["markdown_files"], ["extracted/content.md"])

    def test_process_pdf_splits_large_books_into_chunked_extractions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_root = Path(temp_dir) / "local-extractions"
            uploads_root = Path(temp_dir) / "uploads"
            uploads_root.mkdir(parents=True, exist_ok=True)

            pdf_path = uploads_root / "large-book.pdf"
            writer = PdfWriter()
            for _ in range(12):
                writer.add_blank_page(width=72, height=72)
            with pdf_path.open("wb") as file_handle:
                writer.write(file_handle)

            config = PDFExtractionConfig(
                sarvam_api_key="test-key",
                image_storage_path=str(storage_root),
                max_retries=1,
                max_pages_per_job=10,
            )
            metadata = BookMetadata(
                title="Large Test Book",
                subject="Physics",
                grade_level="11",
                publisher="Test Publisher",
            )

            with patch("app.services.pdf_extraction.document_processor.SarvamAI"):
                processor = DocumentProcessor(config=config)

            extracted_chunks = []

            def fake_extract_single(
                pdf_path: str,
                job_output_dir: Path,
                extract_destination: Path,
                archive_prefix: str,
            ) -> None:
                chunk_index = len(extracted_chunks) + 1
                extract_destination.mkdir(parents=True, exist_ok=True)
                (extract_destination / f"content-{chunk_index}.md").write_text(
                    f"Chunk {chunk_index} content",
                    encoding="utf-8",
                )
                (extract_destination / f"image-{chunk_index}.png").write_bytes(b"png")
                (job_output_dir / f"{archive_prefix}_output.zip").write_bytes(b"zip")
                extracted_chunks.append(Path(pdf_path))

            processor._extract_single_pdf = fake_extract_single  # type: ignore[method-assign]

            result = processor.process_pdf(str(pdf_path), metadata, job_id="job-large")

            self.assertTrue(result.success)
            self.assertEqual(len(extracted_chunks), 2)
            self.assertEqual(
                [path.name for path in extracted_chunks],
                [
                    "chunk_001_pages_0001_0010.pdf",
                    "chunk_002_pages_0011_0012.pdf",
                ],
            )

            assert result.artifacts is not None
            self.assertIn("extracted/combined.md", result.artifacts.markdown_files)
            self.assertIn("extracted/chunk_001/content-1.md", result.artifacts.markdown_files)
            self.assertIn("extracted/chunk_002/content-2.md", result.artifacts.markdown_files)

            combined_markdown = (
                Path(result.artifacts.output_dir) / "extracted" / "combined.md"
            ).read_text(encoding="utf-8")
            self.assertIn("Chunk 1 content", combined_markdown)
            self.assertIn("Chunk 2 content", combined_markdown)


if __name__ == "__main__":
    unittest.main()
