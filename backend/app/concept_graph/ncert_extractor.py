"""
NCERT Concept Extractor for automated concept extraction from textbooks.

This module provides the NCERTExtractor class for:
- Extracting mathematical concepts from NCERT textbook images
- Proposing difficulty DNA encodings for extracted concepts
- Identifying prerequisite relationships between concepts

IMPROVEMENTS in this version:
- Image-based extraction using NVIDIA Mistral Large Vision model
- Robust JSON extraction with regex
- Better error handling and retry logic
- Improved prompting with examples
- API validation on initialization
- Better logging and error messages
"""

import logging
import re
import json
import base64
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError

from .models import (
    DifficultyDNA,
    ConceptIntegration,
    ProblemApproach,
    RelationshipType,
)
from .config import concept_graph_settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedConcept:
    """
    Represents a concept extracted from NCERT textbook content.
    
    Attributes:
        name: Concept name (concise, standard terminology)
        class_level: Class level (8-12)
        keywords: List of related terms
        description: Brief description (1-2 sentences)
        proposed_dna: Proposed difficulty DNA encoding
        potential_prerequisites: List of prerequisite concept names
        chapter_context: Optional chapter/section context
    """
    name: str
    class_level: int
    keywords: List[str]
    description: str
    proposed_dna: DifficultyDNA
    potential_prerequisites: List[str]
    chapter_context: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "class_level": self.class_level,
            "keywords": self.keywords,
            "description": self.description,
            "proposed_dna": self.proposed_dna.to_dict(),
            "potential_prerequisites": self.potential_prerequisites,
            "chapter_context": self.chapter_context
        }


@dataclass
class ChapterExtraction:
    """
    Represents the complete extraction from a chapter.
    
    Attributes:
        concepts: List of extracted concepts
        relationships: List of identified relationships
        metadata: Extraction metadata (chapter name, class level, etc.)
    """
    concepts: List[ExtractedConcept]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "concepts": [c.to_dict() for c in self.concepts],
            "relationships": self.relationships,
            "metadata": self.metadata
        }


class NCERTExtractor:
    """
    Extractor for mathematical concepts from NCERT textbooks using NVIDIA AI API.
    
    Handles:
    - AI-powered concept extraction from textbook images
    - Difficulty DNA proposal for extracted concepts
    - Prerequisite relationship identification
    """
    
    def __init__(self, test_connection: bool = False):
        """
        Initialize the NCERTExtractor with API validation.
        
        Args:
            test_connection: Whether to test API connection on init (default: False)
                           Set to True only when explicitly testing
        
        Raises:
            ValueError: If API key is not configured
        """
        if not concept_graph_settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA API key not configured. Set CONCEPT_GRAPH_NVIDIA_API_KEY "
                "environment variable or add to .env file"
            )
        
        self.api_key = concept_graph_settings.nvidia_api_key
        self.invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
        self.model = "mistralai/mistral-large-3-675b-instruct-2512"
        self.temperature = 0.15
        self.max_tokens = 2048
        
        # Only test API connectivity if explicitly requested
        if test_connection:
            logger.info("Testing NVIDIA API connection...")
            try:
                self._test_api_connection()
                logger.info("NVIDIA API connection verified successfully")
            except Exception as e:
                logger.warning(f"API connection test failed (this is OK during startup): {e}")
        else:
            logger.info("NVIDIA API initialized (connection will be tested on first use)")
    
    def _test_api_connection(self):
        """
        Test API connection with a simple request.
        
        Raises:
            Exception: If connection test fails
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
                "temperature": self.temperature,
                "stream": False
            }
            response = requests.post(self.invoke_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            logger.debug(f"API test successful")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit hit during connection test - this is OK, API key is valid")
                return  # Don't raise on rate limit during test
            logger.error(f"API connection test failed: {e}")
            raise
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=30),  # Longer waits for rate limits
        reraise=True
    )
    def _call_api_with_retry(self, prompt: str, image_b64: Optional[str] = None) -> str:
        """
        Call NVIDIA API with automatic retry on transient failures.
        
        Args:
            prompt: The prompt to send to the API
            image_b64: Optional base64-encoded image for vision analysis
            
        Returns:
            Full response text from the API
            
        Raises:
            Exception: If all retry attempts fail
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # Build message content according to NVIDIA API format
            if image_b64:
                # For images, use the structured format with type and image_url
                content = [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        }
                    }
                ]
            else:
                # For text-only, use simple string
                content = prompt
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 1.00,
                "stream": False
            }
            
            response = requests.post(self.invoke_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            full_response = result["choices"][0]["message"]["content"]
            
            if not full_response:
                raise ValueError("API returned empty response")
            
            return full_response
            
        except requests.exceptions.HTTPError as e:
            # Log detailed error information
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            
            if e.response.status_code == 429:
                logger.warning(f"Rate limit hit (429), will retry with exponential backoff")
            else:
                logger.warning(f"API call failed with status {e.response.status_code}: {error_detail}")
            raise
        except Exception as e:
            # Log and re-raise for retry mechanism
            logger.warning(f"API call failed: {e}")
            raise
    
    def _extract_json_from_response(self, response: str) -> dict:
        """
        Robustly extract JSON from AI response.
        
        Handles:
        - Markdown code blocks anywhere in response
        - Text before/after JSON
        - Multiple JSON objects (takes first valid one)
        
        Args:
            response: Raw response text from AI
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Try to find JSON object or array
        # This regex matches balanced braces/brackets
        json_pattern = r'(\{(?:[^{}]|(?:\{(?:[^{}]|(?:\{[^{}]*\}))*\}))*\})'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        # Try each potential JSON match
        for match in matches:
            try:
                data = json.loads(match)
                # Validate structure
                if isinstance(data, dict) and 'concepts' in data:
                    return data
                elif isinstance(data, list):
                    return {'concepts': data}
            except json.JSONDecodeError:
                continue
        
        # If no valid JSON found in matches, try parsing the whole response
        try:
            data = json.loads(response.strip())
            if isinstance(data, dict) and 'concepts' in data:
                return data
            elif isinstance(data, list):
                return {'concepts': data}
        except json.JSONDecodeError:
            pass
        
        # If still no valid JSON, raise error with helpful message
        logger.error(f"Failed to extract JSON from response. First 500 chars: {response[:500]}")
        raise json.JSONDecodeError(
            "No valid JSON found in response. The AI may have returned explanatory text instead of JSON.",
            response,
            0
        )
    
    def extract_concepts(
        self,
        textbook_content: str,
        subject: str,
        class_level: int,
        image_b64: Optional[str] = None
    ) -> List[ExtractedConcept]:
        """
        Extract concepts from NCERT textbook content or image.
        
        Uses NVIDIA AI API to analyze textbook content and identify concepts
        with their metadata and proposed difficulty encodings.
        
        Args:
            textbook_content: NCERT textbook content (chapter or section text)
            subject: Academic subject (e.g., "mathematics", "physics")
            class_level: Class level (8-12)
            image_b64: Optional base64-encoded image for vision analysis
            
        Returns:
            List of ExtractedConcept objects
            
        Raises:
            ValueError: If class_level is invalid or content is empty
            Exception: If extraction fails after all retries
            
        Requirements: 4.1, 4.2
        """
        # Validate inputs
        if not textbook_content or not textbook_content.strip():
            raise ValueError("textbook_content cannot be empty")
        
        if class_level < 8 or class_level > 12:
            raise ValueError(f"class_level must be between 8 and 12, got {class_level}")
        
        logger.info(
            f"Extracting concepts from NCERT Class {class_level} {subject} content "
            f"({len(textbook_content)} characters, image: {bool(image_b64)})"
        )
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(textbook_content, subject, class_level)
        
        concepts = []
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Extraction attempt {attempt + 1}/{max_attempts}")
                
                # Call API with retry mechanism
                full_response = self._call_api_with_retry(prompt, image_b64)
                logger.debug(f"Got response ({len(full_response)} chars)")
                
                # Extract and parse JSON
                extraction_data = self._extract_json_from_response(full_response)
                logger.debug(f"Parsed JSON with {len(extraction_data.get('concepts', []))} concepts")
                
                # Convert to ExtractedConcept objects
                for concept_data in extraction_data.get("concepts", []):
                    try:
                        concept = self._parse_extracted_concept(concept_data, class_level)
                        concepts.append(concept)
                    except Exception as e:
                        logger.warning(f"Failed to parse concept: {e}. Data: {concept_data}")
                        # Continue with other concepts
                
                if concepts:
                    logger.info(f"Successfully extracted {len(concepts)} concepts")
                    return concepts
                else:
                    logger.warning(f"Attempt {attempt + 1}: No valid concepts extracted")
                    
            except RetryError as e:
                logger.warning(f"Attempt {attempt + 1}: API calls failed after retries: {e}")
                if attempt == max_attempts - 1:
                    raise Exception(
                        f"API calls failed after {max_attempts} attempts with retries. "
                        "This could be due to:\n"
                        "1. API timeout or rate limiting\n"
                        "2. Content too complex\n"
                        "3. Network issues\n"
                        "Try reducing the content size or waiting a few minutes."
                    )
            
            except json.JSONDecodeError as e:
                logger.warning(f"Attempt {attempt + 1}: JSON parsing failed: {e}")
                if attempt == max_attempts - 1:
                    raise Exception(
                        f"Failed to extract valid JSON after {max_attempts} attempts. "
                        "The AI model may not be following the JSON format instructions. "
                        "Try:\n"
                        "1. Simplifying the content\n"
                        "2. Using a different AI model\n"
                        "3. Checking the prompt template"
                    )
            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Extraction failed: {e}")
                if attempt == max_attempts - 1:
                    raise Exception(
                        f"Concept extraction failed after {max_attempts} attempts: {e}"
                    )
        
        # If we get here, all attempts failed but no exception was raised
        raise Exception(f"Failed to extract any concepts after {max_attempts} attempts")
    
    def propose_difficulty_dna(self, concept: ExtractedConcept) -> DifficultyDNA:
        """
        Propose difficulty DNA encoding for an extracted concept.
        
        The DNA is already proposed during extraction, so this method
        returns the existing proposed DNA. Can be overridden for
        custom DNA proposal logic.
        
        Args:
            concept: Extracted concept
            
        Returns:
            Proposed DifficultyDNA
            
        Requirements: 4.3
        """
        return concept.proposed_dna
    
    def identify_prerequisites(
        self,
        concepts: List[ExtractedConcept]
    ) -> List[Dict[str, Any]]:
        """
        Identify prerequisite relationships between extracted concepts.
        
        Analyzes the potential_prerequisites field of each concept and
        creates relationship mappings.
        
        Args:
            concepts: List of extracted concepts
            
        Returns:
            List of relationship dictionaries with source, target, and type
            
        Requirements: 4.4
        """
        relationships = []
        
        # Create a mapping of concept names to concepts (case-insensitive)
        concept_map = {c.name.lower(): c for c in concepts}
        
        for concept in concepts:
            for prereq_name in concept.potential_prerequisites:
                prereq_name_lower = prereq_name.lower().strip()
                
                # Check if prerequisite exists in extracted concepts
                if prereq_name_lower in concept_map:
                    relationships.append({
                        "source_name": concept.name,
                        "target_name": concept_map[prereq_name_lower].name,
                        "relationship_type": RelationshipType.PREREQUISITE.value,
                        "confidence": "high"  # High confidence for same-chapter prerequisites
                    })
                else:
                    # Prerequisite might be from another chapter
                    relationships.append({
                        "source_name": concept.name,
                        "target_name": prereq_name,
                        "relationship_type": RelationshipType.PREREQUISITE.value,
                        "confidence": "medium"  # Medium confidence for cross-chapter prerequisites
                    })
        
        logger.info(f"Identified {len(relationships)} prerequisite relationships")
        return relationships
    
    def extract_from_chapter(
        self,
        chapter_text: str,
        subject: str,
        class_level: int,
        chapter_name: Optional[str] = None,
        image_b64: Optional[str] = None
    ) -> ChapterExtraction:
        """
        Extract concepts from a chapter with automatic chunking for large content.
        
        Args:
            chapter_text: Chapter text content
            subject: Academic subject
            class_level: Class level (8-12)
            chapter_name: Optional chapter name
            image_b64: Optional base64-encoded image for vision analysis
            
        Returns:
            ChapterExtraction with all concepts and relationships
        """
        # If image is provided, process with image (no chunking for images)
        if image_b64:
            return self._extract_single_chunk(chapter_text, subject, class_level, chapter_name, image_b64)
        
        # Check content length and chunk if necessary
        max_chars = 3000  # Larger chunks for better context
        
        if len(chapter_text) <= max_chars:
            # Small enough to process in one go
            return self._extract_single_chunk(chapter_text, subject, class_level, chapter_name)
        
        # Large content - need to chunk with overlap
        logger.info(
            f"Content large ({len(chapter_text)} chars), "
            f"chunking into pieces with overlap"
        )
        
        # Split into chunks with overlap for context preservation
        chunks = self._chunk_text_with_overlap(chapter_text, max_chars, overlap=500)
        logger.info(f"Split into {len(chunks)} overlapping chunks")
        
        # Extract from each chunk
        all_concepts = []
        all_relationships = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            try:
                extraction = self._extract_single_chunk(
                    chunk, 
                    subject, 
                    class_level, 
                    f"{chapter_name} (Part {i+1})" if chapter_name else None
                )
                all_concepts.extend(extraction.concepts)
                all_relationships.extend(extraction.relationships)
                logger.info(
                    f"Chunk {i+1}: extracted {len(extraction.concepts)} concepts, "
                    f"{len(extraction.relationships)} relationships"
                )
            except Exception as e:
                logger.warning(f"Failed to extract from chunk {i+1}: {e}")
                # Continue with other chunks rather than failing completely
                continue
        
        # Deduplicate concepts by name (case-insensitive)
        unique_concepts = {}
        for concept in all_concepts:
            name_key = concept.name.lower()
            if name_key not in unique_concepts:
                unique_concepts[name_key] = concept
            else:
                # Merge keywords if duplicate found
                existing = unique_concepts[name_key]
                existing.keywords = list(set(existing.keywords + concept.keywords))
        
        final_concepts = list(unique_concepts.values())
        
        # Deduplicate relationships
        unique_relationships = []
        seen_rels = set()
        for rel in all_relationships:
            rel_key = (rel['source_name'].lower(), rel['target_name'].lower(), rel['relationship_type'])
            if rel_key not in seen_rels:
                unique_relationships.append(rel)
                seen_rels.add(rel_key)
        
        # Build metadata
        metadata = {
            "subject": subject,
            "class_level": class_level,
            "chapter_name": chapter_name,
            "concept_count": len(final_concepts),
            "relationship_count": len(unique_relationships),
            "chunks_processed": len(chunks),
            "extraction_method": "chunked" if len(chunks) > 1 else "single",
            "original_length": len(chapter_text)
        }
        
        logger.info(
            f"Chapter extraction complete: {len(final_concepts)} unique concepts, "
            f"{len(unique_relationships)} unique relationships"
        )
        
        return ChapterExtraction(
            concepts=final_concepts,
            relationships=unique_relationships,
            metadata=metadata
        )
    
    def _chunk_text_with_overlap(
        self, 
        text: str, 
        max_chars: int = 3000, 
        overlap: int = 500
    ) -> List[str]:
        """
        Split text into overlapping chunks to preserve context.
        
        Args:
            text: Text to chunk
            max_chars: Maximum characters per chunk
            overlap: Character overlap between chunks
            
        Returns:
            List of text chunks with overlap
        """
        # Split by paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # If adding this paragraph exceeds max, save current chunk
            if current_length + para_length > max_chars and current_chunk:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap from previous chunk
                if len(chunk_text) > overlap:
                    # Find paragraphs that fit in the overlap
                    overlap_paras = []
                    overlap_length = 0
                    for p in reversed(current_chunk):
                        if overlap_length + len(p) <= overlap:
                            overlap_paras.insert(0, p)
                            overlap_length += len(p)
                        else:
                            break
                    
                    current_chunk = overlap_paras + [para]
                    current_length = sum(len(p) for p in current_chunk)
                else:
                    current_chunk = [para]
                    current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _extract_single_chunk(
        self,
        chapter_text: str,
        subject: str,
        class_level: int,
        chapter_name: Optional[str] = None,
        image_b64: Optional[str] = None
    ) -> ChapterExtraction:
        """
        Extract all concepts from a single chapter chunk.
        
        Convenience method that extracts concepts and identifies relationships
        in a single call.
        
        Args:
            chapter_text: Chapter text content
            subject: Academic subject
            class_level: Class level (8-12)
            chapter_name: Optional chapter name for metadata
            image_b64: Optional base64-encoded image for vision analysis
            
        Returns:
            ChapterExtraction with concepts, relationships, and metadata
            
        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        logger.debug(
            f"Extracting from chunk: {chapter_name or 'Unnamed'} "
            f"(Class {class_level} {subject}, {len(chapter_text)} chars, image: {bool(image_b64)})"
        )
        
        # Extract concepts
        concepts = self.extract_concepts(chapter_text, subject, class_level, image_b64)
        
        # Identify relationships
        relationships = self.identify_prerequisites(concepts)
        
        # Build metadata
        metadata = {
            "class_level": class_level,
            "chapter_name": chapter_name,
            "concept_count": len(concepts),
            "relationship_count": len(relationships),
            "chunk_length": len(chapter_text)
        }
        
        return ChapterExtraction(
            concepts=concepts,
            relationships=relationships,
            metadata=metadata
        )
    
    def _build_extraction_prompt(
        self,
        textbook_content: str,
        subject: str,
        class_level: int
    ) -> str:
        """
        Build NVIDIA AI API prompt for concept extraction.
        
        Includes examples and strong formatting instructions to ensure JSON output.
        """
        # Example for the model to follow
        example_json = {
            "concepts": [
                {
                    "name": "Quadratic Equations",
                    "keywords": ["algebra", "quadratic", "polynomial", "roots", "factorization"],
                    "description": "Equations of the form ax² + bx + c = 0 and methods to solve them including factorization, completing the square, and the quadratic formula.",
                    "difficulty_dna": {
                        "bloom_level": 3,
                        "abstraction_level": 2,
                        "computational_complexity": 5,
                        "concept_integration": "single",
                        "real_world_context": 3,
                        "problem_solving_approach": "multi-step"
                    },
                    "potential_prerequisites": ["Linear Equations", "Factorization", "Basic Algebra"]
                }
            ]
        }
        
        prompt = f"""You are a curriculum analyzer specializing in NCERT textbooks.

CRITICAL INSTRUCTION: You MUST respond with ONLY valid JSON. Do not include:
- Any explanatory text before or after the JSON
- Markdown code blocks or formatting
- Comments or notes
- Just pure, valid JSON

TASK: Extract {subject} concepts from this NCERT Class {class_level} textbook content.

For each concept, provide:
1. name: Concise, standard {subject} terminology
2. keywords: 5-10 related {subject} terms
3. description: 1-2 sentences explaining the concept clearly
4. difficulty_dna: Contains 6 required dimensions (see below)
5. potential_prerequisites: List of concept names that should be learned first

DIFFICULTY DNA DIMENSIONS (all required):
- bloom_level (1-6): 1=Remember, 2=Understand, 3=Apply, 4=Analyze, 5=Evaluate, 6=Create
- abstraction_level (1-5): 1=very concrete, 5=highly abstract
- computational_complexity: positive integer (number of computational steps)
- concept_integration: must be "single", "multi-concept", or "cross-subject"
- real_world_context (1-5): 1=pure theory, 5=highly practical
- problem_solving_approach: must be "direct-application", "multi-step", "proof-based", or "exploratory"

EXAMPLE OUTPUT (your response should follow this exact structure):
{json.dumps(example_json, indent=2)}

TEXTBOOK CONTENT TO ANALYZE:
{textbook_content[:3500]}

YOUR JSON RESPONSE (remember: JSON only, no other text):"""
        
        return prompt
    
    def _parse_extracted_concept(
        self,
        concept_data: dict,
        class_level: int
    ) -> ExtractedConcept:
        """
        Parse concept data from NVIDIA AI API response into ExtractedConcept.
        
        Args:
            concept_data: Dictionary with concept data from AI
            class_level: Class level for the concept
            
        Returns:
            ExtractedConcept object
            
        Raises:
            KeyError: If required fields are missing
            ValueError: If field values are invalid
        """
        try:
            # Parse difficulty DNA
            dna_data = concept_data["difficulty_dna"]
            difficulty_dna = DifficultyDNA(
                bloom_level=int(dna_data["bloom_level"]),
                abstraction_level=int(dna_data["abstraction_level"]),
                computational_complexity=int(dna_data["computational_complexity"]),
                concept_integration=ConceptIntegration(dna_data["concept_integration"]),
                real_world_context=int(dna_data["real_world_context"]),
                problem_solving_approach=ProblemApproach(dna_data["problem_solving_approach"])
            )
            
            # Create ExtractedConcept
            return ExtractedConcept(
                name=str(concept_data["name"]).strip(),
                class_level=class_level,
                keywords=[str(k).strip() for k in concept_data["keywords"]],
                description=str(concept_data["description"]).strip(),
                proposed_dna=difficulty_dna,
                potential_prerequisites=[
                    str(p).strip() 
                    for p in concept_data.get("potential_prerequisites", [])
                ],
                chapter_context=None
            )
        except KeyError as e:
            raise KeyError(f"Missing required field in concept data: {e}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid value in concept data: {e}")