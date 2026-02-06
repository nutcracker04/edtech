"""
FastAPI router for concept graph operations.

This module provides REST API endpoints for:
- Creating and retrieving concepts
- Querying concepts with filters
- Creating relationships between concepts
- Getting prerequisites and dependents
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from app.concept_graph.models import (
    Concept,
    ConceptCreate,
    ConceptFilters,
    Relationship,
    RelationshipCreate,
    RelationshipType,
    Question,
    QuestionType,
)
from app.concept_graph.graph_manager import ConceptGraphManager
from app.concept_graph.prerequisite_validator import PrerequisiteValidator
from app.concept_graph.question_generator import QuestionGenerator
from app.concept_graph.persona_engine import PersonaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/concepts", tags=["concepts"])

# Initialize managers
graph_manager = ConceptGraphManager()
prerequisite_validator = PrerequisiteValidator(graph_manager)
question_generator = QuestionGenerator()
persona_engine = PersonaEngine()


# Response models
class ConceptResponse(BaseModel):
    """Response model for concept operations."""
    success: bool
    message: str
    concept: Optional[Concept] = None


class ConceptListResponse(BaseModel):
    """Response model for concept list operations."""
    success: bool
    message: str
    concepts: List[Concept]
    count: int


class RelationshipResponse(BaseModel):
    """Response model for relationship operations."""
    success: bool
    message: str
    relationship: Optional[Relationship] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str
    message: str
    details: Optional[dict] = None


@router.post(
    "",
    response_model=ConceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new concept",
    description="Create a new mathematical concept with difficulty DNA encoding"
)
async def create_concept(concept_create: ConceptCreate):
    """
    Create a new concept in the knowledge graph.
    
    Args:
        concept_create: Concept data including name, class level, keywords,
                       description, and difficulty DNA
    
    Returns:
        ConceptResponse with created concept
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If database operation fails
    """
    try:
        concept = graph_manager.create_concept(concept_create)
        logger.info(f"Created concept via API: {concept.id} - {concept.name}")
        
        return ConceptResponse(
            success=True,
            message=f"Concept '{concept.name}' created successfully",
            concept=concept
        )
    
    except ValueError as e:
        logger.warning(f"Validation error creating concept: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error creating concept: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to create concept",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{concept_id}",
    response_model=ConceptResponse,
    summary="Get concept by ID",
    description="Retrieve a concept by its unique identifier"
)
async def get_concept(concept_id: str):
    """
    Retrieve a concept by its unique identifier.
    
    Args:
        concept_id: Unique concept identifier (UUID)
    
    Returns:
        ConceptResponse with concept data
        
    Raises:
        HTTPException 404: If concept not found
        HTTPException 500: If database operation fails
    """
    try:
        concept = graph_manager.get_concept(concept_id)
        
        if concept is None:
            logger.warning(f"Concept not found: {concept_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found: {concept_id}",
                    "details": {"concept_id": concept_id}
                }
            )
        
        logger.debug(f"Retrieved concept via API: {concept_id}")
        
        return ConceptResponse(
            success=True,
            message="Concept retrieved successfully",
            concept=concept
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving concept {concept_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to retrieve concept",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "",
    response_model=ConceptListResponse,
    summary="Query concepts with filters",
    description="Query concepts by class level, keywords, or difficulty dimensions"
)
async def query_concepts(
    subject: Optional[str] = None,
    class_level: Optional[int] = None,
    keyword: Optional[str] = None,
    min_bloom_level: Optional[int] = None,
    max_bloom_level: Optional[int] = None,
    min_abstraction_level: Optional[int] = None,
    max_abstraction_level: Optional[int] = None,
    min_computational_complexity: Optional[int] = None,
    max_computational_complexity: Optional[int] = None,
    min_real_world_context: Optional[int] = None,
    max_real_world_context: Optional[int] = None,
    concept_integration: Optional[str] = None,
    problem_solving_approach: Optional[str] = None,
):
    """
    Query concepts with optional filters.
    
    All filters are optional. If no filters are provided, returns all concepts.
    
    Args:
        subject: Filter by subject (e.g., mathematics, physics)
        class_level: Filter by class level (8-12)
        keyword: Filter by keyword (fuzzy match)
        min_bloom_level: Minimum Bloom's level (1-6)
        max_bloom_level: Maximum Bloom's level (1-6)
        min_abstraction_level: Minimum abstraction level (1-5)
        max_abstraction_level: Maximum abstraction level (1-5)
        min_computational_complexity: Minimum computational complexity
        max_computational_complexity: Maximum computational complexity
        min_real_world_context: Minimum real-world context level (1-5)
        max_real_world_context: Maximum real-world context level (1-5)
        concept_integration: Filter by concept integration type
        problem_solving_approach: Filter by problem-solving approach
    
    Returns:
        ConceptListResponse with matching concepts
        
    Raises:
        HTTPException 400: If filter validation fails
        HTTPException 500: If database operation fails
    """
    try:
        # Build filters object
        filters = ConceptFilters(
            subject=subject,
            class_level=class_level,
            keyword=keyword,
            min_bloom_level=min_bloom_level,
            max_bloom_level=max_bloom_level,
            min_abstraction_level=min_abstraction_level,
            max_abstraction_level=max_abstraction_level,
            min_computational_complexity=min_computational_complexity,
            max_computational_complexity=max_computational_complexity,
            min_real_world_context=min_real_world_context,
            max_real_world_context=max_real_world_context,
            concept_integration=concept_integration,
            problem_solving_approach=problem_solving_approach,
        )
        
        concepts = graph_manager.query_concepts(filters)
        
        logger.info(f"Query returned {len(concepts)} concepts")
        
        return ConceptListResponse(
            success=True,
            message=f"Found {len(concepts)} matching concepts",
            concepts=concepts,
            count=len(concepts)
        )
    
    except ValueError as e:
        logger.warning(f"Validation error in query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error querying concepts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to query concepts",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/{concept_id}/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a relationship",
    description="Create a relationship between two concepts with cycle detection"
)
async def create_relationship(
    concept_id: str,
    relationship_create: RelationshipCreate
):
    """
    Create a relationship between two concepts.
    
    The source concept is specified in the URL path, and the target concept
    and relationship type are in the request body. Validates that the
    relationship won't create a cycle.
    
    Args:
        concept_id: Source concept ID (from URL path)
        relationship_create: Relationship data including target_id and relationship_type
    
    Returns:
        RelationshipResponse with created relationship
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If concepts not found
        HTTPException 409: If relationship would create a cycle
        HTTPException 500: If database operation fails
    """
    try:
        # Override source_id with the one from the URL path
        relationship_create.source_id = concept_id
        
        # Validate the relationship first
        validation_result = prerequisite_validator.validate_relationship(
            relationship_create.source_id,
            relationship_create.target_id
        )
        
        if not validation_result.is_valid:
            # Determine appropriate status code based on error type
            if "not found" in validation_result.message.lower():
                status_code = status.HTTP_404_NOT_FOUND
                error_code = "CONCEPT_NOT_FOUND"
            elif "cycle" in validation_result.message.lower():
                status_code = status.HTTP_409_CONFLICT
                error_code = "CYCLE_DETECTED"
            else:
                status_code = status.HTTP_400_BAD_REQUEST
                error_code = "VALIDATION_ERROR"
            
            logger.warning(f"Relationship validation failed: {validation_result.message}")
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error_code": error_code,
                    "message": validation_result.message,
                    "details": validation_result.details
                }
            )
        
        # Create the relationship
        relationship = graph_manager.create_relationship(
            relationship_create.source_id,
            relationship_create.target_id,
            relationship_create.relationship_type
        )
        
        logger.info(
            f"Created relationship via API: {relationship.source_id} "
            f"-> {relationship.target_id} ({relationship.relationship_type.value})"
        )
        
        return RelationshipResponse(
            success=True,
            message=f"Relationship created successfully",
            relationship=relationship
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        logger.warning(f"Validation error creating relationship: {e}")
        
        # Determine if it's a cycle error or other validation error
        if "cycle" in str(e).lower():
            status_code = status.HTTP_409_CONFLICT
            error_code = "CYCLE_DETECTED"
        elif "not found" in str(e).lower():
            status_code = status.HTTP_404_NOT_FOUND
            error_code = "CONCEPT_NOT_FOUND"
        else:
            status_code = status.HTTP_400_BAD_REQUEST
            error_code = "VALIDATION_ERROR"
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error creating relationship: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to create relationship",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{concept_id}/prerequisites",
    response_model=ConceptListResponse,
    summary="Get prerequisites",
    description="Get all prerequisite concepts for a given concept"
)
async def get_prerequisites(
    concept_id: str,
    recursive: bool = True,
    relationship_types: Optional[str] = None
):
    """
    Get all prerequisite concepts for a given concept.
    
    By default, includes both PREREQUISITE and BUILDS_UPON relationships
    and returns all transitive prerequisites.
    
    Args:
        concept_id: Concept ID to get prerequisites for
        recursive: If True, get all transitive prerequisites (default: True)
        relationship_types: Comma-separated list of relationship types to filter by.
                          Valid values: prerequisite, builds-upon, applies-to.
                          Defaults to "prerequisite,builds-upon" if not specified.
    
    Returns:
        ConceptListResponse with prerequisite concepts
        
    Raises:
        HTTPException 404: If concept not found
        HTTPException 400: If relationship types are invalid
        HTTPException 500: If database operation fails
    """
    try:
        # Verify concept exists
        concept = graph_manager.get_concept(concept_id)
        if concept is None:
            logger.warning(f"Concept not found: {concept_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found: {concept_id}",
                    "details": {"concept_id": concept_id}
                }
            )
        
        # Parse relationship types if provided
        rel_types = None
        if relationship_types:
            try:
                rel_type_strs = [rt.strip() for rt in relationship_types.split(",")]
                rel_types = [RelationshipType(rt) for rt in rel_type_strs]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_RELATIONSHIP_TYPE",
                        "message": f"Invalid relationship type: {e}",
                        "details": {"valid_types": [rt.value for rt in RelationshipType]}
                    }
                )
        
        # Get prerequisites
        prerequisites = graph_manager.get_prerequisites(
            concept_id,
            recursive=recursive,
            relationship_types=rel_types
        )
        
        logger.info(
            f"Retrieved {len(prerequisites)} prerequisites for concept {concept_id} "
            f"(recursive={recursive})"
        )
        
        return ConceptListResponse(
            success=True,
            message=f"Found {len(prerequisites)} prerequisite concepts",
            concepts=prerequisites,
            count=len(prerequisites)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting prerequisites for {concept_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to get prerequisites",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{concept_id}/dependents",
    response_model=ConceptListResponse,
    summary="Get dependents",
    description="Get all concepts that depend on this concept"
)
async def get_dependents(
    concept_id: str,
    relationship_types: Optional[str] = None
):
    """
    Get all concepts that depend on this concept (reverse prerequisites).
    
    By default, includes both PREREQUISITE and BUILDS_UPON relationships.
    
    Args:
        concept_id: Concept ID to get dependents for
        relationship_types: Comma-separated list of relationship types to filter by.
                          Valid values: prerequisite, builds-upon, applies-to.
                          Defaults to "prerequisite,builds-upon" if not specified.
    
    Returns:
        ConceptListResponse with dependent concepts
        
    Raises:
        HTTPException 404: If concept not found
        HTTPException 400: If relationship types are invalid
        HTTPException 500: If database operation fails
    """
    try:
        # Verify concept exists
        concept = graph_manager.get_concept(concept_id)
        if concept is None:
            logger.warning(f"Concept not found: {concept_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found: {concept_id}",
                    "details": {"concept_id": concept_id}
                }
            )
        
        # Parse relationship types if provided
        rel_types = None
        if relationship_types:
            try:
                rel_type_strs = [rt.strip() for rt in relationship_types.split(",")]
                rel_types = [RelationshipType(rt) for rt in rel_type_strs]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_RELATIONSHIP_TYPE",
                        "message": f"Invalid relationship type: {e}",
                        "details": {"valid_types": [rt.value for rt in RelationshipType]}
                    }
                )
        
        # Get dependents
        dependents = graph_manager.get_dependents(
            concept_id,
            relationship_types=rel_types
        )
        
        logger.info(f"Retrieved {len(dependents)} dependents for concept {concept_id}")
        
        return ConceptListResponse(
            success=True,
            message=f"Found {len(dependents)} dependent concepts",
            concepts=dependents,
            count=len(dependents)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error getting dependents for {concept_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to get dependents",
                "details": {"error": str(e)}
            }
        )



# In-memory storage for generated questions (for demo purposes)
# In production, this should be stored in a database
_questions_store = {}


# Question generation response models
class QuestionResponse(BaseModel):
    """Response model for question operations."""
    success: bool
    message: str
    question: Optional[Question] = None


class QuestionGenerateRequest(BaseModel):
    """Request model for question generation."""
    concept_id: str = Field(..., description="Concept ID to generate question for")
    class_level: int = Field(..., ge=8, le=13, description="Student class level (8-12, or 13 for JEE mode)")
    difficulty_adjustment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Difficulty adjustment factor (-1.0 to +1.0)"
    )
    question_type: QuestionType = Field(
        default=QuestionType.MCQ,
        description="Type of question to generate"
    )


@router.post(
    "/questions/generate",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate question for concept and persona",
    description="Generate an adaptive question for a concept tailored to student persona",
    tags=["questions"]
)
async def generate_question(request: QuestionGenerateRequest):
    """
    Generate a question for a concept adapted to student persona.
    
    This endpoint:
    1. Retrieves the concept by ID
    2. Loads the appropriate student persona for the class level
    3. Generates a question using NVIDIA AI API with persona constraints
    4. Validates the generated question against persona constraints
    5. Regenerates if constraints are violated (up to max attempts)
    
    Args:
        request: Question generation request with concept_id, class_level,
                difficulty_adjustment, and question_type
    
    Returns:
        QuestionResponse with generated question
        
    Raises:
        HTTPException 400: If validation fails or required inputs missing
        HTTPException 404: If concept or persona not found
        HTTPException 500: If generation fails after max attempts
        
    Requirements: 11.5
    """
    try:
        # Validate concept exists
        concept = graph_manager.get_concept(request.concept_id)
        if concept is None:
            logger.warning(f"Concept not found: {request.concept_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "CONCEPT_NOT_FOUND",
                    "message": f"Concept not found: {request.concept_id}",
                    "details": {"concept_id": request.concept_id}
                }
            )
        
        # Get persona for class level
        persona = persona_engine.get_persona(request.class_level)
        if persona is None:
            logger.warning(f"Persona not found for class level: {request.class_level}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PERSONA_NOT_FOUND",
                    "message": f"Persona not found for class level: {request.class_level}",
                    "details": {"class_level": request.class_level}
                }
            )
        
        # Generate question
        logger.info(
            f"Generating {request.question_type.value} question for concept {request.concept_id} "
            f"(class level {request.class_level}, adjustment {request.difficulty_adjustment})"
        )
        
        question = question_generator.generate_question(
            concept_id=request.concept_id,
            persona=persona,
            difficulty_adjustment=request.difficulty_adjustment,
            question_type=request.question_type
        )
        
        logger.info(f"Successfully generated question {question.id} for concept {request.concept_id}")
        
        # Store question in memory for retrieval
        _questions_store[question.id] = question
        
        return QuestionResponse(
            success=True,
            message=f"Question generated successfully for concept '{concept.name}'",
            question=question
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        logger.warning(f"Validation error generating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GENERATION_ERROR",
                "message": "Failed to generate question",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Get question by ID",
    description="Retrieve a generated question by its unique identifier",
    tags=["questions"]
)
async def get_question(question_id: str):
    """
    Retrieve a question by its unique identifier.
    
    Note: This is a simple in-memory implementation for demo purposes.
    In production, questions should be stored in a database.
    
    Args:
        question_id: Unique question identifier (UUID)
    
    Returns:
        QuestionResponse with question data
        
    Raises:
        HTTPException 404: If question not found
        HTTPException 500: If retrieval fails
        
    Requirements: 11.5
    """
    try:
        question = _questions_store.get(question_id)
        
        if question is None:
            logger.warning(f"Question not found: {question_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "QUESTION_NOT_FOUND",
                    "message": f"Question not found: {question_id}",
                    "details": {"question_id": question_id}
                }
            )
        
        logger.debug(f"Retrieved question via API: {question_id}")
        
        return QuestionResponse(
            success=True,
            message="Question retrieved successfully",
            question=question
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error retrieving question {question_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to retrieve question",
                "details": {"error": str(e)}
            }
        )





# Graph import/export response models
class GraphExportResponse(BaseModel):
    """Response model for graph export operations."""
    success: bool
    message: str
    data: Dict[str, Any]


class GraphImportRequest(BaseModel):
    """Request model for graph import operations."""
    concepts: List[Dict[str, Any]] = Field(..., description="List of concept dictionaries to import")
    relationships: List[Dict[str, Any]] = Field(..., description="List of relationship dictionaries to import")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata about the import")


class GraphImportResponse(BaseModel):
    """Response model for graph import operations."""
    success: bool
    message: str
    concepts_imported: int
    relationships_imported: int
    errors: List[str]


@router.get(
    "/graph/export",
    response_model=GraphExportResponse,
    summary="Export entire graph",
    description="Export the entire concept graph to JSON format for backup or transfer",
    tags=["graph"]
)
async def export_graph():
    """
    Export the entire concept graph to JSON format.
    
    This endpoint exports all concepts and relationships in the graph to a
    JSON-serializable format suitable for backup, versioning, or transfer.
    
    Returns:
        GraphExportResponse containing:
            - concepts: List of all concept dictionaries
            - relationships: List of all relationship dictionaries
            - metadata: Export metadata (timestamp, version, counts)
    
    Raises:
        HTTPException 500: If database operation fails
        
    Requirements: 11.1, 11.2
    """
    try:
        logger.info("Exporting entire concept graph")
        
        # Export graph using graph manager
        export_data = graph_manager.export_graph()
        
        logger.info(
            f"Successfully exported graph: {export_data['metadata']['concept_count']} concepts, "
            f"{export_data['metadata']['relationship_count']} relationships"
        )
        
        return GraphExportResponse(
            success=True,
            message=(
                f"Graph exported successfully: "
                f"{export_data['metadata']['concept_count']} concepts, "
                f"{export_data['metadata']['relationship_count']} relationships"
            ),
            data=export_data
        )
    
    except Exception as e:
        logger.error(f"Error exporting graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EXPORT_ERROR",
                "message": "Failed to export graph",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/graph/import",
    response_model=GraphImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import graph from JSON",
    description="Import concept graph data from JSON with validation",
    tags=["graph"]
)
async def import_graph(import_request: GraphImportRequest):
    """
    Import concept graph data from JSON format.
    
    This endpoint validates the imported data structure, checks for cycles,
    validates all concepts and relationships, and imports them into the database.
    The import is atomic - either all data is imported or none is.
    
    Args:
        import_request: Graph import request containing:
            - concepts: List of concept dictionaries
            - relationships: List of relationship dictionaries
            - metadata: Optional metadata
    
    Returns:
        GraphImportResponse with import results:
            - success: Boolean indicating success
            - concepts_imported: Number of concepts imported
            - relationships_imported: Number of relationships imported
            - errors: List of validation errors (if any)
    
    Raises:
        HTTPException 400: If validation fails or data contains cycles/invalid data
        HTTPException 500: If database operation fails
        
    Requirements: 11.1, 11.2
    """
    try:
        logger.info(
            f"Importing graph: {len(import_request.concepts)} concepts, "
            f"{len(import_request.relationships)} relationships"
        )
        
        # Build graph data dictionary
        graph_data = {
            "concepts": import_request.concepts,
            "relationships": import_request.relationships,
        }
        
        if import_request.metadata:
            graph_data["metadata"] = import_request.metadata
        
        # Import graph using graph manager
        result = graph_manager.import_graph(graph_data)
        
        logger.info(
            f"Successfully imported graph: {result['concepts_imported']} concepts, "
            f"{result['relationships_imported']} relationships"
        )
        
        return GraphImportResponse(
            success=result["success"],
            message=(
                f"Graph imported successfully: "
                f"{result['concepts_imported']} concepts, "
                f"{result['relationships_imported']} relationships"
            ),
            concepts_imported=result["concepts_imported"],
            relationships_imported=result["relationships_imported"],
            errors=result["errors"]
        )
    
    except ValueError as e:
        logger.warning(f"Validation error importing graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error importing graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "IMPORT_ERROR",
                "message": "Failed to import graph",
                "details": {"error": str(e)}
            }
        )
