"""
FastAPI router for learning pathway operations.

This module provides REST API endpoints for:
- Getting learning pathways for students
- Getting next recommended concepts
- Generating progressive question series
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.concept_graph.models import Concept, Question, QuestionType
from app.concept_graph.learning_pathway_generator import (
    LearningPathwayGenerator,
    LearningPathway
)
from app.concept_graph.graph_manager import ConceptGraphManager
from app.concept_graph.prerequisite_validator import PrerequisiteValidator
from app.concept_graph.mastery_tracker import MasteryTracker
from app.concept_graph.question_generator import QuestionGenerator
from app.concept_graph.persona_engine import PersonaEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pathways", tags=["learning-pathways"])

# Initialize managers
graph_manager = ConceptGraphManager()
prerequisite_validator = PrerequisiteValidator(graph_manager)
mastery_tracker = MasteryTracker()
pathway_generator = LearningPathwayGenerator(
    graph_manager=graph_manager,
    prerequisite_validator=prerequisite_validator,
    mastery_tracker=mastery_tracker
)
question_generator = QuestionGenerator()
persona_engine = PersonaEngine()


# Response models
class PathwayResponse(BaseModel):
    """Response model for learning pathway operations."""
    success: bool
    message: str
    pathway: Optional[dict] = None


class NextConceptsResponse(BaseModel):
    """Response model for next concept recommendations."""
    success: bool
    message: str
    concepts: List[Concept]
    count: int


class QuestionSeriesRequest(BaseModel):
    """Request model for question series generation."""
    concept_id: str = Field(..., description="Concept ID to generate questions for")
    count: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    question_type: QuestionType = Field(
        default=QuestionType.MCQ,
        description="Type of questions to generate"
    )


class QuestionSeriesResponse(BaseModel):
    """Response model for question series generation."""
    success: bool
    message: str
    questions: List[Question]
    count: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str
    message: str
    details: Optional[dict] = None


@router.get(
    "/{student_id}",
    response_model=PathwayResponse,
    summary="Get learning pathway for student",
    description="Generate a progressive learning pathway from student's current level to target level"
)
async def get_learning_pathway(
    student_id: str,
    target_class_level: int = 12
):
    """
    Get learning pathway for a student.
    
    This endpoint:
    1. Retrieves student's mastered concepts from mastery tracker
    2. Infers current class level from mastered concepts
    3. Generates pathway from current to target level
    4. Orders concepts by prerequisite dependencies and difficulty
    5. Returns structured learning pathway
    
    Args:
        student_id: Student identifier
        target_class_level: Target class level (8-12, default: 12)
    
    Returns:
        PathwayResponse with learning pathway data
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If pathway generation fails
        
    Requirements: 11.6
    """
    try:
        # Validate target_class_level
        if target_class_level < 8 or target_class_level > 12:
            raise ValueError(f"target_class_level must be between 8 and 12, got {target_class_level}")
        
        logger.info(
            f"Generating learning pathway for student {student_id} "
            f"(target level: {target_class_level})"
        )
        
        # Generate pathway
        pathway = pathway_generator.generate_pathway(
            student_id=student_id,
            target_class_level=target_class_level
        )
        
        logger.info(
            f"Generated pathway with {pathway.total_concepts} concepts "
            f"for student {student_id}"
        )
        
        return PathwayResponse(
            success=True,
            message=(
                f"Generated learning pathway with {pathway.total_concepts} concepts "
                f"(current level: {pathway.current_level}, target level: {pathway.target_level})"
            ),
            pathway=pathway.to_dict()
        )
    
    except ValueError as e:
        logger.warning(f"Validation error generating pathway: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error generating pathway for student {student_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "PATHWAY_GENERATION_ERROR",
                "message": "Failed to generate learning pathway",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{student_id}/next",
    response_model=NextConceptsResponse,
    summary="Get next recommended concepts",
    description="Get next recommended concepts based on mastery and prerequisites"
)
async def get_next_concepts(
    student_id: str,
    count: int = 5
):
    """
    Get next recommended concepts for a student.
    
    This endpoint:
    1. Retrieves student's mastered concepts
    2. Finds concepts with all prerequisites satisfied
    3. Filters out already mastered concepts
    4. Orders by difficulty progression
    5. Returns top N concepts
    
    Args:
        student_id: Student identifier
        count: Number of concepts to return (1-20, default: 5)
    
    Returns:
        NextConceptsResponse with recommended concepts
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If recommendation fails
        
    Requirements: 11.6
    """
    try:
        # Validate count
        if count < 1 or count > 20:
            raise ValueError(f"count must be between 1 and 20, got {count}")
        
        logger.info(
            f"Getting next {count} recommended concepts for student {student_id}"
        )
        
        # Get next concepts
        next_concepts = pathway_generator.get_next_concepts(
            student_id=student_id,
            count=count
        )
        
        logger.info(
            f"Recommended {len(next_concepts)} concepts for student {student_id}"
        )
        
        return NextConceptsResponse(
            success=True,
            message=f"Found {len(next_concepts)} recommended concepts",
            concepts=next_concepts,
            count=len(next_concepts)
        )
    
    except ValueError as e:
        logger.warning(f"Validation error getting next concepts: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting next concepts for student {student_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "RECOMMENDATION_ERROR",
                "message": "Failed to get next recommended concepts",
                "details": {"error": str(e)}
            }
        )


@router.post(
    "/{student_id}/questions",
    response_model=QuestionSeriesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate question series",
    description="Generate a progressive series of questions for a concept"
)
async def generate_question_series(
    student_id: str,
    request: QuestionSeriesRequest
):
    """
    Generate a progressive series of questions for a concept.
    
    This endpoint:
    1. Validates the concept exists
    2. Retrieves student's mastery data for the concept
    3. Infers student's current class level
    4. Generates a series of questions with progressive difficulty
    5. Each question is calibrated to student's persona
    
    Args:
        student_id: Student identifier
        request: Question series request with concept_id, count, and question_type
    
    Returns:
        QuestionSeriesResponse with generated questions
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If concept or persona not found
        HTTPException 500: If generation fails
        
    Requirements: 11.6
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
        
        # Get student's mastered concepts to infer level
        mastered_concepts = pathway_generator._get_mastered_concepts(student_id)
        current_level = pathway_generator._infer_current_level(mastered_concepts)
        
        # Get persona for student's level
        persona = persona_engine.get_persona(current_level)
        if persona is None:
            logger.warning(f"Persona not found for class level: {current_level}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "PERSONA_NOT_FOUND",
                    "message": f"Persona not found for class level: {current_level}",
                    "details": {"class_level": current_level}
                }
            )
        
        logger.info(
            f"Generating {request.count} {request.question_type.value} questions "
            f"for concept {request.concept_id} (student {student_id}, level {current_level})"
        )
        
        # Generate progressive series of questions
        questions = []
        for i in range(request.count):
            # Progressive difficulty adjustment: start at -0.3, end at +0.3
            # This creates a smooth progression from easier to harder
            difficulty_adjustment = -0.3 + (0.6 * i / max(request.count - 1, 1))
            
            try:
                question = question_generator.generate_question(
                    concept_id=request.concept_id,
                    persona=persona,
                    difficulty_adjustment=difficulty_adjustment,
                    question_type=request.question_type
                )
                questions.append(question)
                
            except Exception as e:
                logger.warning(
                    f"Failed to generate question {i+1}/{request.count} "
                    f"for concept {request.concept_id}: {e}"
                )
                # Continue generating remaining questions even if one fails
                continue
        
        if not questions:
            raise ValueError("Failed to generate any questions")
        
        logger.info(
            f"Successfully generated {len(questions)} questions "
            f"for concept {request.concept_id}"
        )
        
        return QuestionSeriesResponse(
            success=True,
            message=(
                f"Generated {len(questions)} progressive questions "
                f"for concept '{concept.name}'"
            ),
            questions=questions,
            count=len(questions)
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        logger.warning(f"Validation error generating question series: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(
            f"Error generating question series for student {student_id}, "
            f"concept {request.concept_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GENERATION_ERROR",
                "message": "Failed to generate question series",
                "details": {"error": str(e)}
            }
        )
