"""
StorageManager Service

This module provides the StorageManager class for handling Supabase storage operations
for images and PDFs.

Responsibilities:
- Upload question images to Supabase storage buckets
- Upload source PDFs to Supabase storage
- Generate storage paths following bucket structure
- Provide signed URLs for private images
- Handle retry logic for failed uploads with exponential backoff
- Fallback to local storage on upload failure
"""

import logging
import os
from pathlib import Path
from typing import Optional
from uuid import UUID

from supabase import Client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

logger = logging.getLogger(__name__)


class StorageUploadError(Exception):
    """Raised when image or PDF upload to Supabase storage fails after retries."""
    pass


class StorageManager:
    """
    Service for managing Supabase storage operations.
    
    This class handles uploading question images and source PDFs to Supabase storage,
    with automatic retry logic using tenacity library and fallback to local storage on failure.
    """
    
    # Storage bucket names
    QUESTION_IMAGES_BUCKET = "question-images"
    SOURCE_PDFS_BUCKET = "source-pdfs"
    EXTRACTION_ARTIFACTS_BUCKET = "extraction-artifacts"
    
    # Retry configuration
    MAX_RETRIES = 3
    
    # Signed URL expiration
    SIGNED_URL_EXPIRATION_SECONDS = 3600  # 1 hour
    
    # Local storage fallback directory
    LOCAL_STORAGE_DIR = Path("local_storage")
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the StorageManager.
        
        Args:
            supabase_client: Supabase client for storage operations
        """
        self.client = supabase_client
        
        # Ensure local storage directory exists
        self.LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        logger.info("StorageManager initialized")
    
    def _upload_to_supabase(
        self,
        bucket: str,
        storage_path: str,
        file_data: bytes,
        content_type: str
    ) -> None:
        """
        Internal method to upload file to Supabase storage with retry logic.
        
        This method uses tenacity to retry uploads with exponential backoff.
        It will retry up to MAX_RETRIES times (3 attempts total).
        
        Args:
            bucket: Supabase storage bucket name
            storage_path: Path within the bucket
            file_data: Raw file bytes
            content_type: MIME type of the file
        
        Raises:
            Exception: If upload fails (will be retried by tenacity)
        """
        @retry(
            stop=stop_after_attempt(self.MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True
        )
        def _do_upload():
            self.client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_data,
                file_options={"content-type": content_type}
            )
        
        _do_upload()
    
    def _save_to_local_storage(
        self,
        storage_path: str,
        file_data: bytes
    ) -> str:
        """
        Save file to local storage as fallback when Supabase upload fails.
        
        Args:
            storage_path: Original storage path (used to create local path structure)
            file_data: Raw file bytes
        
        Returns:
            Local storage path with 'local://' prefix
        """
        # Create local path maintaining the same structure
        local_path = self.LOCAL_STORAGE_DIR / storage_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file to local storage
        with open(local_path, 'wb') as f:
            f.write(file_data)
        
        # Return path with local:// prefix
        local_storage_path = f"local://{storage_path}"
        logger.info(f"Saved file to local storage: {local_storage_path}")
        
        return local_storage_path
    
    def upload_question_image(
        self,
        book_id: UUID,
        question_id: UUID,
        image_data: bytes,
        image_filename: str
    ) -> str:
        """
        Upload a question image to Supabase storage with retry and local fallback.
        
        This method uploads an image to the question-images bucket with the path format:
        {book_id}/{question_id}/{image_filename}
        
        The upload is retried up to MAX_RETRIES times (3 attempts) with exponential backoff
        using the tenacity library. If all retries fail, the image is stored locally with
        a 'local://' prefix and an error is logged.
        
        Algorithm:
        1. Construct storage path: {book_id}/{question_id}/{image_filename}
        2. Attempt upload to Supabase storage with tenacity retry logic
        3. If upload succeeds, return storage path
        4. If all retries fail, save to local storage with 'local://' prefix
        5. Log error and return local storage path
        
        Args:
            book_id: UUID of the book
            question_id: UUID of the question
            image_data: Raw image bytes
            image_filename: Original filename of the image
        
        Returns:
            Storage path in format: {book_id}/{question_id}/{image_filename}
            OR local path with 'local://' prefix if upload fails
        
        Preconditions:
            - book_id is a valid UUID
            - question_id is a valid UUID
            - image_data is non-empty bytes
            - image_filename is non-empty string
        
        Postconditions:
            - Image is uploaded to Supabase storage at the specified path, OR
            - Image is saved to local storage with 'local://' prefix
            - Returns storage path string (either Supabase or local)
        """
        # Construct storage path
        storage_path = f"{book_id}/{question_id}/{image_filename}"
        
        logger.info(f"Uploading question image to: {storage_path}")
        
        try:
            # Attempt upload with retry logic
            self._upload_to_supabase(
                bucket=self.QUESTION_IMAGES_BUCKET,
                storage_path=storage_path,
                file_data=image_data,
                content_type="image/png"  # Default to PNG, could be detected
            )
            
            logger.info(f"Successfully uploaded image to {storage_path}")
            return storage_path
            
        except (RetryError, Exception) as e:
            # All retries failed, fallback to local storage
            logger.error(
                f"Failed to upload image {storage_path} after {self.MAX_RETRIES} attempts: {e}. "
                f"Falling back to local storage."
            )
            
            # Save to local storage
            local_path = self._save_to_local_storage(storage_path, image_data)
            return local_path
    
    def upload_source_pdf(
        self,
        job_id: UUID,
        pdf_path: str,
        pdf_data: bytes
    ) -> str:
        """
        Upload a source PDF to Supabase storage with retry and local fallback.
        
        This method uploads a PDF file to the source-pdfs bucket with the path format:
        {job_id}/{filename}
        
        The upload is retried up to MAX_RETRIES times (3 attempts) with exponential backoff
        using the tenacity library. If all retries fail, the PDF is stored locally with
        a 'local://' prefix and an error is logged.
        
        Algorithm:
        1. Extract filename from pdf_path
        2. Construct storage path: {job_id}/{filename}
        3. Attempt upload to Supabase storage with tenacity retry logic
        4. If upload succeeds, return storage path
        5. If all retries fail, save to local storage with 'local://' prefix
        6. Log error and return local storage path
        
        Args:
            job_id: UUID of the extraction job
            pdf_path: Original path/filename of the PDF
            pdf_data: Raw PDF bytes
        
        Returns:
            Storage path in format: {job_id}/{filename}
            OR local path with 'local://' prefix if upload fails
        
        Preconditions:
            - job_id is a valid UUID
            - pdf_path is non-empty string
            - pdf_data is non-empty bytes
        
        Postconditions:
            - PDF is uploaded to Supabase storage at the specified path, OR
            - PDF is saved to local storage with 'local://' prefix
            - Returns storage path string (either Supabase or local)
        """
        # Extract filename from path
        filename = os.path.basename(pdf_path)
        
        # Construct storage path
        storage_path = f"{job_id}/{filename}"
        
        logger.info(f"Uploading source PDF to: {storage_path}")
        
        try:
            # Attempt upload with retry logic
            self._upload_to_supabase(
                bucket=self.SOURCE_PDFS_BUCKET,
                storage_path=storage_path,
                file_data=pdf_data,
                content_type="application/pdf"
            )
            
            logger.info(f"Successfully uploaded PDF to {storage_path}")
            return storage_path
            
        except (RetryError, Exception) as e:
            # All retries failed, fallback to local storage
            logger.error(
                f"Failed to upload PDF {storage_path} after {self.MAX_RETRIES} attempts: {e}. "
                f"Falling back to local storage."
            )
            
            # Save to local storage
            local_path = self._save_to_local_storage(storage_path, pdf_data)
            return local_path
    
    def upload_extraction_artifacts(
        self,
        job_id: str,
        extracted_dir_path: str,
    ) -> Optional[str]:
        """
        Upload extracted markdown and images to Supabase extraction-artifacts bucket.
        Stores combined.md and all image files. Returns Supabase storage path prefix.
        """
        import os
        from pathlib import Path
        
        extracted_dir = Path(extracted_dir_path)
        if not extracted_dir.exists():
            logger.error(f"Extraction dir not found: {extracted_dir_path}")
            return None
        
        prefix = f"{job_id}"
        uploaded_count = 0
        
        try:
            # Upload combined.md
            combined_path = extracted_dir / "combined.md"
            if combined_path.exists():
                content = combined_path.read_bytes()
                storage_path = f"{prefix}/combined.md"
                self._upload_to_supabase(
                    bucket=self.EXTRACTION_ARTIFACTS_BUCKET,
                    storage_path=storage_path,
                    file_data=content,
                    content_type="text/markdown",
                )
                uploaded_count += 1
                logger.info(f"Uploaded combined.md to {storage_path}")
            
            # Upload all images (png, jpg, etc.)
            image_suffixes = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".svg"}
            for file_path in extracted_dir.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in image_suffixes:
                    rel = file_path.relative_to(extracted_dir)
                    storage_path = f"{prefix}/{rel.as_posix()}"
                    content = file_path.read_bytes()
                    content_type = "image/png" if file_path.suffix.lower() == ".png" else "image/jpeg"
                    self._upload_to_supabase(
                        bucket=self.EXTRACTION_ARTIFACTS_BUCKET,
                        storage_path=storage_path,
                        file_data=content,
                        content_type=content_type,
                    )
                    uploaded_count += 1
            
            logger.info(f"Uploaded {uploaded_count} extraction artifacts for job {job_id}")
            return f"{prefix}/combined.md" if (extracted_dir / "combined.md").exists() else prefix
        except Exception as e:
            logger.error(f"Failed to upload extraction artifacts: {e}", exc_info=True)
            return None
    
    def get_extracted_content(
        self,
        storage_path: str,
        expiration_seconds: Optional[int] = None,
    ) -> Optional[str]:
        """
        Download extracted markdown content from Supabase storage.
        Returns file content as string, or None if not found.
        """
        try:
            response = self.client.storage.from_(self.EXTRACTION_ARTIFACTS_BUCKET).download(
                storage_path
            )
            if isinstance(response, bytes):
                return response.decode("utf-8", errors="replace")
            return str(response) if response else None
        except Exception as e:
            logger.error(f"Failed to get extracted content {storage_path}: {e}")
            return None
    
    def get_image_url(
        self,
        storage_path: str,
        expiration_seconds: Optional[int] = None
    ) -> str:
        """
        Generate a signed URL for a private image with expiration.
        
        This method creates a temporary signed URL that allows access to a private
        image in Supabase storage. The URL expires after the specified duration
        (default: 1 hour).
        
        Algorithm:
        1. Use Supabase storage client to create signed URL
        2. Set expiration time (default: SIGNED_URL_EXPIRATION_SECONDS)
        3. Return signed URL
        
        Args:
            storage_path: Path to the image in Supabase storage
            expiration_seconds: Optional custom expiration time in seconds
                               (default: SIGNED_URL_EXPIRATION_SECONDS = 3600)
        
        Returns:
            Signed URL string with expiration
        
        Raises:
            Exception: If signed URL generation fails
        
        Preconditions:
            - storage_path is non-empty string
            - storage_path exists in question-images bucket
        
        Postconditions:
            - Returns valid signed URL string
            - URL expires after expiration_seconds
        """
        if expiration_seconds is None:
            expiration_seconds = self.SIGNED_URL_EXPIRATION_SECONDS
        
        logger.info(f"Generating signed URL for {storage_path} with {expiration_seconds}s expiration")
        
        try:
            # Create signed URL
            response = self.client.storage.from_(self.QUESTION_IMAGES_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=expiration_seconds
            )
            
            # Extract URL from response
            signed_url = response.get("signedURL") or response.get("signedUrl")
            
            if not signed_url:
                raise ValueError(f"No signed URL in response: {response}")
            
            logger.info(f"Generated signed URL for {storage_path}")
            return signed_url
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {storage_path}: {e}", exc_info=True)
            raise
    
    def migrate_local_images(self) -> dict:
        """
        Migrate existing local images to Supabase storage.
        
        This method scans the question_images table for entries with storage_path
        starting with 'local://', reads the image files from local storage, uploads
        them to Supabase storage, and updates the storage_path in the database.
        
        Algorithm:
        1. Query question_images table for all rows with storage_path LIKE 'local://%'
        2. For each local image:
           a. Extract the local path (remove 'local://' prefix)
           b. Read image data from local storage
           c. Extract book_id and question_id from the path
           d. Upload to Supabase using upload_question_image()
           e. Update question_images.storage_path with new Supabase path
           f. Track success/failure counts
        3. Return MigrationResult with counts
        
        Returns:
            Dictionary with migration results:
            - images_migrated: Number of successfully migrated images
            - failed_count: Number of failed migrations
            - total_found: Total number of local images found
            - errors: List of error messages for failed migrations
        
        Preconditions:
            - Database connection is valid
            - Local storage directory exists
            - question_images table exists
        
        Postconditions:
            - All successfully migrated images have updated storage_path in database
            - Local image files remain unchanged (not deleted)
            - Returns migration statistics
        
        Requirements:
            - Requirement 17.1: Upload images to Supabase storage with correct path format
            - Requirement 17.2: Update question_images.storage_path with Supabase paths
        """
        logger.info("Starting local images migration to Supabase storage")
        
        images_migrated = 0
        failed_count = 0
        errors = []
        
        try:
            # Query for all local images
            response = self.client.table("question_images").select(
                "id, question_id, storage_path"
            ).like("storage_path", "local://%").execute()
            
            local_images = response.data if response.data else []
            total_found = len(local_images)
            
            logger.info(f"Found {total_found} local images to migrate")
            
            if total_found == 0:
                return {
                    "images_migrated": 0,
                    "failed_count": 0,
                    "total_found": 0,
                    "errors": []
                }
            
            # Process each local image
            for image_record in local_images:
                image_id = image_record["id"]
                question_id = image_record["question_id"]
                local_storage_path = image_record["storage_path"]
                
                try:
                    # Remove 'local://' prefix to get actual file path
                    local_path = local_storage_path.replace("local://", "")
                    
                    # Extract book_id and filename from path
                    # Path format: {book_id}/{question_id}/{filename}
                    path_parts = local_path.split('/')
                    if len(path_parts) < 3:
                        error_msg = f"Invalid path format: {local_path}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        failed_count += 1
                        continue
                    
                    full_local_path = self.LOCAL_STORAGE_DIR / local_path
                    
                    # Check if local file exists
                    if not full_local_path.exists():
                        error_msg = f"Local file not found: {full_local_path}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        failed_count += 1
                        continue
                    
                    # Read image data
                    with open(full_local_path, 'rb') as f:
                        image_data = f.read()
                    
                    book_id = UUID(path_parts[0])
                    filename = path_parts[-1]
                    
                    # Upload to Supabase storage
                    new_storage_path = self.upload_question_image(
                        book_id=book_id,
                        question_id=UUID(question_id),
                        image_data=image_data,
                        image_filename=filename
                    )
                    
                    # Check if upload succeeded (not a local:// path)
                    if new_storage_path.startswith("local://"):
                        error_msg = f"Upload failed for {local_path}, still using local storage"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                        failed_count += 1
                        continue
                    
                    # Update database with new storage path
                    self.client.table("question_images").update({
                        "storage_path": new_storage_path
                    }).eq("id", image_id).execute()
                    
                    images_migrated += 1
                    logger.info(f"Successfully migrated image {image_id}: {local_path} -> {new_storage_path}")
                    
                except Exception as e:
                    error_msg = f"Failed to migrate image {image_id} ({local_storage_path}): {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    failed_count += 1
            
            logger.info(
                f"Migration complete: {images_migrated} migrated, "
                f"{failed_count} failed out of {total_found} total"
            )
            
            return {
                "images_migrated": images_migrated,
                "failed_count": failed_count,
                "total_found": total_found,
                "errors": errors
            }
            
        except Exception as e:
            error_msg = f"Failed to query local images: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "images_migrated": 0,
                "failed_count": 0,
                "total_found": 0,
                "errors": [error_msg]
            }
