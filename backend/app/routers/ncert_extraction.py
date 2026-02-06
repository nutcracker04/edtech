"""
FastAPI router for NCERT concept extraction operations.

This module provides REST API endpoints for:
- Extracting concepts from NCERT textbook content (text or image)
- Proposing difficulty DNA for extracted concepts
- Identifying prerequisite relationships
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import base64

from app.concept_graph.ncert_extractor import (
    NCERTExtractor,
    ExtractedConcept,
    ChapterExtraction
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extract", tags=["ncert-extraction"])

# Initialize extractor (without connection test to avoid rate limits on startup)
ncert_extractor = NCERTExtractor(test_connection=False)


# Request models
class NCERTExtractionRequest(BaseModel):
    """Request model for NCERT concept extraction."""
    textbook_content: str = Field(
        ...,
        description="NCERT textbook content (chapter or section text)",
        min_length=100
    )
    subject: str = Field(
        ...,
        description="Academic subject (e.g., mathematics, physics, chemistry)"
    )
    class_level: int = Field(
        ...,
        ge=8,
        le=12,
        description="Class level (8-12)"
    )
    chapter_name: Optional[str] = Field(
        default=None,
        description="Optional chapter name for metadata"
    )


# Response models
class ExtractedConceptResponse(BaseModel):
    """Response model for a single extracted concept."""
    name: str
    class_level: int
    keywords: List[str]
    description: str
    proposed_dna: Dict[str, Any]
    potential_prerequisites: List[str]
    chapter_context: Optional[str] = None


class NCERTExtractionResponse(BaseModel):
    """Response model for NCERT extraction operations."""
    success: bool
    message: str
    concepts: List[ExtractedConceptResponse]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str
    message: str
    details: Optional[dict] = None


@router.post(
    "/ncert",
    status_code=status.HTTP_200_OK,
    summary="Extract concepts from NCERT content",
    description="Extract mathematical concepts from NCERT textbook content (text or image) using AI analysis"
)
async def extract_ncert_concepts(
    subject: str = Form(..., description="Academic subject (e.g., mathematics, physics, chemistry)"),
    class_level: int = Form(..., ge=8, le=12, description="Class level (8-12)"),
    chapter_name: Optional[str] = Form(None, description="Optional chapter name for metadata"),
    textbook_content: Optional[str] = Form(None, description="Direct text content (if not uploading image)"),
    image_file: Optional[UploadFile] = File(None, description="Image file (PNG/JPG) to extract from")
):
    """
    Extract concepts from NCERT textbook content (text or image).
    
    This endpoint:
    1. Accepts direct text content OR image file (PNG/JPG) upload
    2. If image is provided, uses vision model for multimodal analysis
    3. Analyzes content using NVIDIA AI API with vision support
    4. Identifies concepts with metadata for the specified subject
    5. Proposes difficulty DNA encodings for each concept
    6. Identifies prerequisite relationships between concepts
    7. Returns structured extraction results for admin review
    
    The extracted concepts are NOT automatically added to the graph.
    Admins should review the extraction results and manually create
    concepts using the POST /api/concepts endpoint.
    
    Args:
        subject: Academic subject (e.g., mathematics, physics, chemistry)
        class_level: Class level (8-12)
        chapter_name: Optional chapter name for metadata
        textbook_content: Direct text content (if not uploading image)
        image_file: Image file (PNG/JPG) to extract from
    
    Returns:
        NCERTExtractionResponse with:
            - concepts: List of extracted concepts with proposed DNA
            - relationships: List of identified prerequisite relationships
            - metadata: Extraction metadata (counts, class level, subject, etc.)
        
    Raises:
        HTTPException 400: If validation fails or content is invalid
        HTTPException 500: If extraction fails
        
    Requirements: 11.8
    
    Example (text):
        Form data:
        - subject: "mathematics"
        - class_level: 8
        - chapter_name: "Rational Numbers"
        - textbook_content: "Chapter 1: Rational Numbers..."
    
    Example (image):
        Form data:
        - subject: "mathematics"
        - class_level: 8
        - chapter_name: "Rational Numbers"
        - textbook_content: "Extract concepts from this image"
        - image_file: <uploaded PNG/JPG file>
    """
    try:
        # Validate that at least one input is provided
        if not textbook_content and not image_file:
            raise ValueError("Either textbook_content or image_file must be provided")
        
        # Validate only one input type is provided
        if textbook_content and image_file:
            raise ValueError("Provide either textbook_content or image_file, not both")
        
        # Process input
        extracted_text = textbook_content
        image_b64 = None
        
        # Handle image file
        if image_file:
            logger.info(f"Processing image file: {image_file.filename}")
            try:
                image_bytes = await image_file.read()
                
                # Determine image format from filename
                filename_lower = image_file.filename.lower()
                if filename_lower.endswith('.jpg') or filename_lower.endswith('.jpeg'):
                    image_format = 'jpeg'
                elif filename_lower.endswith('.png'):
                    image_format = 'png'
                else:
                    raise ValueError("Image must be PNG or JPG format")
                
                image_b64 = base64.b64encode(image_bytes).decode()
                
                # Use a default prompt for image extraction
                if not extracted_text:
                    extracted_text = "Extract all mathematical concepts from this image"
                
                logger.info(f"Image encoded to base64 ({len(image_b64)} chars, format: {image_format})")
            except Exception as e:
                logger.error(f"Error processing image file: {e}")
                raise ValueError(f"Failed to process image file: {str(e)}")
        
        # Validate text content length (skip for images)
        if not image_b64 and len(extracted_text.strip()) < 100:
            raise ValueError("Text content must be at least 100 characters long")
        
        # Extract concepts
        source_type = 'image' if image_file else 'text'
        logger.info(
            f"Extracting concepts from NCERT Class {class_level} {subject} content "
            f"(chapter: {chapter_name or 'Unnamed'}, source: {source_type})"
        )
        
        # Extract concepts from chapter
        extraction = ncert_extractor.extract_from_chapter(
            chapter_text=extracted_text,
            subject=subject,
            class_level=class_level,
            chapter_name=chapter_name,
            image_b64=image_b64
        )
        
        # Convert ExtractedConcept objects to response format
        concept_responses = []
        for concept in extraction.concepts:
            concept_responses.append(
                ExtractedConceptResponse(
                    name=concept.name,
                    class_level=concept.class_level,
                    keywords=concept.keywords,
                    description=concept.description,
                    proposed_dna=concept.proposed_dna.to_dict(),
                    potential_prerequisites=concept.potential_prerequisites,
                    chapter_context=concept.chapter_context
                )
            )
        
        logger.info(
            f"Successfully extracted {len(concept_responses)} concepts "
            f"with {len(extraction.relationships)} relationships"
        )
        
        return NCERTExtractionResponse(
            success=True,
            message=(
                f"Extracted {len(concept_responses)} concepts from "
                f"Class {class_level} {subject} content"
            ),
            concepts=concept_responses,
            relationships=extraction.relationships,
            metadata=extraction.metadata
        )
    
    except ValueError as e:
        logger.warning(f"Validation error in NCERT extraction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error extracting NCERT concepts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EXTRACTION_ERROR",
                "message": "Failed to extract concepts from NCERT content",
                "details": {"error": str(e)}
            }
        )



