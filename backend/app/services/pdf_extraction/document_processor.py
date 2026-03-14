"""
DocumentProcessor orchestration component for local PDF extraction.

This implementation keeps the local flow deliberately simple:
- validate the uploaded PDF
- send it to Sarvam Document Intelligence
- download the extracted markdown/images locally
- write a manifest that points to all generated artifacts

That gives a reliable local setup for verifying extraction before migrating the
storage layer to Supabase later.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
import zipfile
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter
from sarvamai import SarvamAI

try:
    from .config import PDFExtractionConfig, get_config
    from .models import BookMetadata
except ImportError:
    from config import PDFExtractionConfig, get_config
    from models import BookMetadata

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class ProcessingStage(str, Enum):
    """Stages of the local extraction flow."""

    QUEUED = "queued"
    VALIDATION = "validation"
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationResult(BaseModel):
    """Result of PDF validation."""

    is_valid: bool = Field(..., description="Whether PDF is valid for processing")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation confidence score")
    chapter_count: int = Field(default=0, ge=0, description="Number of detected chapters")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class ProcessingStatus(BaseModel):
    """Status of an extraction job."""

    job_id: str = Field(..., description="Unique job identifier")
    current_stage: ProcessingStage = Field(..., description="Current processing stage")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    is_complete: bool = Field(default=False, description="Whether processing is complete")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: float = Field(..., description="Timestamp when job started")
    updated_at: float = Field(..., description="Timestamp of last update")
    current_chapter: Optional[str] = Field(None, description="Reserved for future structured extraction")
    current_topic: Optional[str] = Field(None, description="Reserved for future structured extraction")
    questions_extracted: int = Field(default=0, description="Reserved for future structured extraction")


class ProcessingArtifacts(BaseModel):
    """Artifacts generated for a local extraction job."""

    source_pdf_path: str = Field(..., description="Absolute path of the saved source PDF")
    output_dir: str = Field(..., description="Absolute path of the job output directory")
    extracted_path: str = Field(..., description="Absolute path of the extracted output directory")
    manifest_path: str = Field(..., description="Absolute path of the local manifest JSON")
    markdown_files: List[str] = Field(default_factory=list, description="Relative markdown files inside output_dir")
    image_files: List[str] = Field(default_factory=list, description="Relative image files inside output_dir")
    other_files: List[str] = Field(default_factory=list, description="Relative non-image, non-markdown files")
    preview: Optional[str] = Field(None, description="Preview of extracted markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Book metadata used for this extraction")


class ProcessingResult(BaseModel):
    """Result of a completed extraction job."""

    success: bool = Field(..., description="Whether processing succeeded")
    job_id: str = Field(..., description="Job identifier")
    questions_written: int = Field(default=0, ge=0, description="Reserved for future database writes")
    success_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Local extraction success rate")
    failed_links: int = Field(default=0, ge=0, description="Reserved for future structured linking")
    processing_time_seconds: float = Field(default=0.0, ge=0.0, description="Total processing time")
    error: Optional[str] = Field(None, description="Error message if failed")
    extracted_path: Optional[str] = Field(None, description="Absolute path to extracted content")
    artifacts: Optional[ProcessingArtifacts] = Field(None, description="Local extraction artifacts")
    resumed_from_checkpoint: bool = Field(default=False, description="Unused in local mode")


class DocumentProcessor:
    """Run local PDF extraction and persist the generated artifacts on disk."""

    def __init__(self, config: Optional[PDFExtractionConfig] = None, supabase_client=None):
        self.config = config or get_config()
        self.client = SarvamAI(api_subscription_key=self.config.sarvam_api_key)
        self.storage_root = self._resolve_storage_path(self.config.image_storage_path)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self._jobs: Dict[str, ProcessingStatus] = {}
        self._results: Dict[str, ProcessingResult] = {}
        self._progress_callbacks: Dict[str, Callable[[ProcessingStatus], None]] = {}
        self.supabase_client = supabase_client  # Optional Supabase client for database integration

        logger.info("DocumentProcessor initialized for local extraction at %s", self.storage_root)

    def queue_job(self, job_id: str) -> None:
        """Create a queued job entry so status polling works immediately after upload."""

        now = time.time()
        self._jobs[job_id] = ProcessingStatus(
            job_id=job_id,
            current_stage=ProcessingStage.QUEUED,
            progress=0.0,
            is_complete=False,
            started_at=now,
            updated_at=now,
        )
        
        # Create extraction_jobs record in database if Supabase client is available
        if self.supabase_client:
            self._create_extraction_job_record(job_id)

    def process_pdf(
        self,
        pdf_path: str,
        metadata: BookMetadata,
        async_mode: bool = False,
        job_id: Optional[str] = None,
    ) -> ProcessingResult:
        """
        Extract a PDF locally and persist markdown/images/manifest on disk.
        """

        del async_mode  # Kept for compatibility with the previous call signature.

        if job_id is None:
            job_id = str(uuid4())

        source_pdf_path = Path(pdf_path).resolve()
        start_time = self._jobs.get(job_id).started_at if job_id in self._jobs else time.time()

        if job_id not in self._jobs:
            self.queue_job(job_id)
        
        # Update extraction_jobs with source PDF filename
        if self.supabase_client:
            try:
                self.supabase_client.table("extraction_jobs").update({
                    "source_pdf_filename": source_pdf_path.name,
                    "source_pdf_path": str(source_pdf_path)
                }).eq("id", job_id).execute()
            except Exception as e:
                logger.error(f"Failed to update source_pdf_filename: {e}")

        logger.info("Starting local PDF extraction job %s for %s", job_id, source_pdf_path)

        try:
            self._update_job_status(job_id, ProcessingStage.VALIDATION, 5.0)
            self._update_extraction_job_stage(job_id, ProcessingStage.VALIDATION, 5.0)
            
            validation = self.validate_pdf_structure(str(source_pdf_path))
            if not validation.is_valid:
                raise ValueError(", ".join(validation.errors) or "PDF validation failed")

            self._update_job_status(job_id, ProcessingStage.UPLOAD, 20.0)
            self._update_extraction_job_stage(job_id, ProcessingStage.UPLOAD, 20.0)
            
            # Get total pages for database tracking
            total_pages = self._get_pdf_page_count(str(source_pdf_path))
            self._update_extraction_job_stage(job_id, ProcessingStage.UPLOAD, 20.0, total_pages=total_pages)
            
            extracted_path = self._extract_pdf_content(str(source_pdf_path), job_id)

            self._update_job_status(job_id, ProcessingStage.EXTRACTION, 85.0)
            self._update_extraction_job_stage(job_id, ProcessingStage.EXTRACTION, 85.0)
            
            artifacts = self._collect_artifacts(
                job_id=job_id,
                metadata=metadata,
                source_pdf_path=source_pdf_path,
                extracted_path=Path(extracted_path),
            )

            self._update_job_status(job_id, ProcessingStage.COMPLETED, 100.0)
            self._update_extraction_job_stage(job_id, ProcessingStage.COMPLETED, 100.0)

            result = ProcessingResult(
                success=True,
                job_id=job_id,
                questions_written=0,
                success_rate=100.0,
                failed_links=0,
                processing_time_seconds=time.time() - start_time,
                extracted_path=artifacts.extracted_path,
                artifacts=artifacts,
            )
            self._results[job_id] = result
            return result

        except Exception as exc:
            logger.error("Job %s failed: %s", job_id, exc, exc_info=True)
            self._update_job_status(job_id, ProcessingStage.FAILED, None, error=str(exc))
            self._update_extraction_job_stage(job_id, ProcessingStage.FAILED, 0.0, error=str(exc))

            result = ProcessingResult(
                success=False,
                job_id=job_id,
                processing_time_seconds=time.time() - start_time,
                error=str(exc),
            )
            self._results[job_id] = result
            return result

    def validate_pdf_structure(self, pdf_path: str) -> ValidationResult:
        """Perform lightweight local validation before calling the extractor."""

        path = Path(pdf_path).resolve()
        errors: List[str] = []
        warnings: List[str] = []

        if not path.exists():
            errors.append("File does not exist")
        elif path.suffix.lower() != ".pdf":
            errors.append("File must have a .pdf extension")

        if not errors and path.stat().st_size == 0:
            errors.append("PDF file is empty")

        max_bytes = self.config.max_pdf_size_mb * 1024 * 1024
        if not errors and path.stat().st_size > max_bytes:
            errors.append(
                f"PDF exceeds maximum size of {self.config.max_pdf_size_mb}MB "
                f"({path.stat().st_size / 1024 / 1024:.2f}MB)"
            )

        if not errors:
            with path.open("rb") as file_handle:
                header = file_handle.read(4)
            if header != b"%PDF":
                errors.append("File content does not look like a valid PDF")

        if not errors and path.stat().st_size > max_bytes * 0.8:
            warnings.append("PDF is large and extraction may take longer than usual")

        return ValidationResult(
            is_valid=not errors,
            confidence=1.0 if not errors else 0.0,
            chapter_count=0,
            errors=errors,
            warnings=warnings,
        )

    def get_processing_status(self, job_id: str) -> Optional[ProcessingStatus]:
        return self._jobs.get(job_id)

    def get_result(self, job_id: str) -> Optional[ProcessingResult]:
        return self._results.get(job_id)

    def register_progress_callback(
        self,
        job_id: str,
        callback: Callable[[ProcessingStatus], None],
    ) -> None:
        self._progress_callbacks[job_id] = callback

    def unregister_progress_callback(self, job_id: str) -> None:
        self._progress_callbacks.pop(job_id, None)

    def _resolve_storage_path(self, configured_path: str) -> Path:
        storage_path = Path(configured_path)
        if storage_path.is_absolute():
            return storage_path
        return (PROJECT_ROOT / storage_path).resolve()

    def _extract_pdf_content(self, pdf_path: str, job_id: str) -> str:
        """
        Call Sarvam Document Intelligence and download the full extraction bundle.

        Sarvam currently limits each extraction request to 10 pages, so large PDFs
        are split into chunks and processed sequentially. Their outputs are stored
        under a single job directory for local inspection.
        """

        job_output_dir = self.storage_root / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        extracted_dir = job_output_dir / "extracted"
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)

        total_pages = self._get_pdf_page_count(pdf_path)
        max_pages_per_job = max(1, self.config.max_pages_per_job)

        if total_pages <= max_pages_per_job:
            self._extract_single_pdf(
                pdf_path=pdf_path,
                job_output_dir=job_output_dir,
                extract_destination=extracted_dir,
                archive_prefix="full_document",
            )
            return str(extracted_dir)

        chunk_dir = job_output_dir / "chunks"
        chunk_paths = self._split_pdf_into_chunks(pdf_path, chunk_dir, max_pages_per_job)

        logger.info(
            "PDF %s has %s pages; splitting into %s chunk(s) of up to %s pages",
            pdf_path,
            total_pages,
            len(chunk_paths),
            max_pages_per_job,
        )

        for index, chunk_path in enumerate(chunk_paths, start=1):
            chunk_name = f"chunk_{index:03d}"
            chunk_extract_dir = extracted_dir / chunk_name
            chunk_extract_dir.mkdir(parents=True, exist_ok=True)

            progress = 20.0 + (index / len(chunk_paths)) * 65.0
            self._update_job_status(
                job_id,
                ProcessingStage.EXTRACTION,
                progress,
                current_chapter=f"Chunk {index}/{len(chunk_paths)}",
                current_topic=f"Pages {self._chunk_page_label(chunk_path)}",
            )

            self._extract_single_pdf(
                pdf_path=str(chunk_path),
                job_output_dir=job_output_dir,
                extract_destination=chunk_extract_dir,
                archive_prefix=chunk_name,
            )

        self._build_combined_markdown(extracted_dir)
        return str(extracted_dir)

    def _get_pdf_page_count(self, pdf_path: str) -> int:
        reader = PdfReader(pdf_path)
        return len(reader.pages)

    def _split_pdf_into_chunks(
        self,
        pdf_path: str,
        chunk_dir: Path,
        max_pages_per_job: int,
    ) -> List[Path]:
        reader = PdfReader(pdf_path)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        chunk_paths: List[Path] = []
        total_pages = len(reader.pages)

        for start_page in range(0, total_pages, max_pages_per_job):
            end_page = min(start_page + max_pages_per_job, total_pages)
            writer = PdfWriter()

            for page_index in range(start_page, end_page):
                writer.add_page(reader.pages[page_index])

            chunk_number = len(chunk_paths) + 1
            chunk_path = chunk_dir / (
                f"chunk_{chunk_number:03d}_pages_{start_page + 1:04d}_{end_page:04d}.pdf"
            )
            with chunk_path.open("wb") as file_handle:
                writer.write(file_handle)
            chunk_paths.append(chunk_path)

        return chunk_paths

    def _extract_single_pdf(
        self,
        pdf_path: str,
        job_output_dir: Path,
        extract_destination: Path,
        archive_prefix: str,
    ) -> None:
        retry_count = 0
        last_error: Optional[Exception] = None

        while retry_count < self.config.max_retries:
            try:
                extraction_job = self.client.document_intelligence.create_job(
                    language="en-IN",
                    output_format="md",
                )
                extraction_job.upload_file(pdf_path)
                extraction_job.start()

                status = extraction_job.wait_until_complete(poll_interval=5.0)
                job_state = (
                    getattr(status, "job_state", None)
                    or getattr(status, "state", None)
                    or ""
                )

                if job_state not in {"Completed", "PartiallyCompleted"}:
                    raise RuntimeError(f"Document Intelligence job ended with state: {job_state}")

                try:
                    metrics = extraction_job.get_page_metrics()
                    if metrics:
                        logger.info("Extraction metrics for %s: %s", archive_prefix, metrics)
                except Exception:
                    logger.debug("Page metrics were not available for %s", archive_prefix)

                zip_name = f"{archive_prefix}_{getattr(extraction_job, 'job_id', 'output')}.zip"
                zip_path = job_output_dir / zip_name
                extraction_job.download_output(str(zip_path))

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_destination)

                return

            except Exception as exc:
                last_error = exc
                retry_count += 1
                should_retry = retry_count < self.config.max_retries and not self._is_non_retryable_error(exc)

                if not should_retry:
                    break

                delay = self.config.retry_delay_seconds * (2 ** (retry_count - 1))
                logger.warning(
                    "Extraction attempt %s/%s failed for %s: %s. Retrying in %ss",
                    retry_count,
                    self.config.max_retries,
                    archive_prefix,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise RuntimeError(
            f"PDF extraction failed after {retry_count} attempt(s): {last_error}"
        )

    def _is_non_retryable_error(self, exc: Exception) -> bool:
        error_text = str(exc).lower()
        return "status_code: 400" in error_text or "invalid_request_error" in error_text

    def _chunk_page_label(self, chunk_path: Path) -> str:
        stem_parts = chunk_path.stem.split("_")
        if len(stem_parts) >= 5:
            return f"{int(stem_parts[-2])}-{int(stem_parts[-1])}"
        return chunk_path.stem

    def _build_combined_markdown(self, extracted_dir: Path) -> None:
        markdown_files = sorted(
            path for path in extracted_dir.rglob("*.md") if path.name != "combined.md"
        )
        if not markdown_files:
            return

        combined_parts = []
        for markdown_path in markdown_files:
            relative_path = markdown_path.relative_to(extracted_dir)
            content = markdown_path.read_text(encoding="utf-8", errors="ignore").strip()
            combined_parts.append(f"<!-- Source: {relative_path} -->\n\n{content}")

        (extracted_dir / "combined.md").write_text(
            "\n\n".join(part for part in combined_parts if part.strip()),
            encoding="utf-8",
        )

    def _collect_artifacts(
        self,
        job_id: str,
        metadata: BookMetadata,
        source_pdf_path: Path,
        extracted_path: Path,
    ) -> ProcessingArtifacts:
        output_dir = self.storage_root / job_id
        all_files = sorted(path for path in output_dir.rglob("*") if path.is_file())

        markdown_suffixes = {".md"}
        image_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}

        markdown_files = [
            str(path.relative_to(output_dir))
            for path in all_files
            if path.suffix.lower() in markdown_suffixes
        ]
        image_files = [
            str(path.relative_to(output_dir))
            for path in all_files
            if path.suffix.lower() in image_suffixes
        ]
        other_files = [
            str(path.relative_to(output_dir))
            for path in all_files
            if path.suffix.lower() not in markdown_suffixes | image_suffixes
        ]

        preview = None
        if markdown_files:
            preview_path = output_dir / markdown_files[0]
            preview = preview_path.read_text(encoding="utf-8", errors="ignore")[:2000]

        manifest_path = output_dir / "manifest.json"
        manifest = {
            "job_id": job_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata.model_dump(),
            "source_pdf_path": str(source_pdf_path),
            "output_dir": str(output_dir),
            "extracted_path": str(extracted_path),
            "markdown_files": markdown_files,
            "image_files": image_files,
            "other_files": other_files,
            "preview": preview,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        return ProcessingArtifacts(
            source_pdf_path=str(source_pdf_path),
            output_dir=str(output_dir),
            extracted_path=str(extracted_path),
            manifest_path=str(manifest_path),
            markdown_files=markdown_files,
            image_files=image_files,
            other_files=other_files,
            preview=preview,
            metadata=metadata.model_dump(),
        )

    def _update_job_status(
        self,
        job_id: str,
        stage: ProcessingStage,
        progress: Optional[float],
        error: Optional[str] = None,
        current_chapter: Optional[str] = None,
        current_topic: Optional[str] = None,
        questions_extracted: Optional[int] = None,
    ) -> None:
        if job_id not in self._jobs:
            self.queue_job(job_id)

        status = self._jobs[job_id]
        status.current_stage = stage

        if progress is not None:
            status.progress = progress
        if error is not None:
            status.error = error
        if current_chapter is not None:
            status.current_chapter = current_chapter
        if current_topic is not None:
            status.current_topic = current_topic
        if questions_extracted is not None:
            status.questions_extracted = questions_extracted

        status.is_complete = stage in {ProcessingStage.COMPLETED, ProcessingStage.FAILED}
        status.updated_at = time.time()

        callback = self._progress_callbacks.get(job_id)
        if callback:
            try:
                callback(status)
            except Exception as exc:
                logger.error("Progress callback failed for %s: %s", job_id, exc)

    def get_error_summary(self) -> Dict[str, Any]:
        failed_jobs = [
            {"job_id": job_id, "error": result.error}
            for job_id, result in self._results.items()
            if not result.success
        ]
        return {
            "failed_jobs": len(failed_jobs),
            "jobs": failed_jobs,
        }
    
    def _create_extraction_job_record(self, job_id: str) -> None:
        """
        Create extraction_jobs record in database.
        
        Requirements: 7.1, 23.1
        """
        try:
            from datetime import datetime, timezone
            from uuid import UUID
            
            job_data = {
                "id": job_id,
                "source_pdf_filename": "unknown",  # Will be updated in process_pdf
                "stage": ProcessingStage.QUEUED.value,
                "progress": 0.0,
                "pages_processed": 0,
                "questions_extracted": 0,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase_client.table("extraction_jobs").insert(job_data).execute()
            logger.info(f"Created extraction_jobs record for job_id={job_id}")
            
        except Exception as e:
            logger.error(f"Failed to create extraction_jobs record: {e}", exc_info=True)
    
    def _update_extraction_job_stage(
        self,
        job_id: str,
        stage: ProcessingStage,
        progress: float,
        error: Optional[str] = None,
        total_pages: Optional[int] = None,
        pages_processed: Optional[int] = None,
        questions_extracted: Optional[int] = None
    ) -> None:
        """
        Update extraction_jobs record with current stage and progress.
        
        Requirements: 7.1, 23.5
        """
        if not self.supabase_client:
            return
        
        try:
            from datetime import datetime, timezone
            
            update_data = {
                "stage": stage.value,
                "progress": progress,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if error:
                update_data["error"] = error
            
            if total_pages is not None:
                update_data["total_pages"] = total_pages
            
            if pages_processed is not None:
                update_data["pages_processed"] = pages_processed
            
            if questions_extracted is not None:
                update_data["questions_extracted"] = questions_extracted
            
            # Set completed_at and processing_time_seconds when completed or failed
            if stage in [ProcessingStage.COMPLETED, ProcessingStage.FAILED]:
                update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
                
                # Calculate processing time
                job_record = self.supabase_client.table("extraction_jobs").select("started_at").eq("id", job_id).execute()
                if job_record.data and len(job_record.data) > 0:
                    started_at_str = job_record.data[0]["started_at"]
                    if started_at_str:
                        started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                        completed_at = datetime.now(timezone.utc)
                        processing_time = (completed_at - started_at).total_seconds()
                        update_data["processing_time_seconds"] = processing_time
            
            self.supabase_client.table("extraction_jobs").update(update_data).eq("id", job_id).execute()
            logger.debug(f"Updated extraction_jobs record: job_id={job_id}, stage={stage.value}, progress={progress}")
            
        except Exception as e:
            logger.error(f"Failed to update extraction_jobs record: {e}", exc_info=True)
    
    def _write_extraction_pages_and_blocks(
        self,
        job_id: str,
        page_num: int,
        page_data: Dict[str, Any]
    ) -> None:
        """
        Write extraction_pages and extraction_blocks to database.
        
        Requirements: 7.2, 7.3, 23.2
        """
        if not self.supabase_client:
            return
        
        try:
            from datetime import datetime, timezone
            from uuid import uuid4
            from decimal import Decimal
            
            # Create extraction_pages record
            page_id = str(uuid4())
            page_record = {
                "id": page_id,
                "job_id": job_id,
                "page_num": page_num,
                "image_width": page_data.get("image_width"),
                "image_height": page_data.get("image_height"),
                "raw_json_path": page_data.get("raw_json_path"),
                "block_count": len(page_data.get("blocks", [])),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase_client.table("extraction_pages").insert(page_record).execute()
            logger.debug(f"Created extraction_pages record: page_id={page_id}, page_num={page_num}")
            
            # Create extraction_blocks records
            blocks = page_data.get("blocks", [])
            for block_index, block in enumerate(blocks):
                block_id = block.get("block_id", str(uuid4()))
                block_record = {
                    "id": block_id,
                    "page_id": page_id,
                    "job_id": job_id,
                    "block_index": block_index,
                    "layout_tag": block.get("layout_tag", "paragraph"),
                    "confidence": float(block.get("confidence", 0.0)),
                    "reading_order": block.get("reading_order"),
                    "text": block.get("text"),
                    "x1": float(block.get("x1")) if block.get("x1") is not None else None,
                    "y1": float(block.get("y1")) if block.get("y1") is not None else None,
                    "x2": float(block.get("x2")) if block.get("x2") is not None else None,
                    "y2": float(block.get("y2")) if block.get("y2") is not None else None,
                    "raw_block": block
                }
                
                self.supabase_client.table("extraction_blocks").insert(block_record).execute()
            
            logger.debug(f"Created {len(blocks)} extraction_blocks records for page {page_num}")
            
        except Exception as e:
            logger.error(f"Failed to write extraction_pages/blocks: {e}", exc_info=True)
