"""
FastAPI router for mastery tracking operations.

This module provides REST API endpoints for:
- Recording student performance on questions
- Getting mastery level for a student/concept
- Getting mastery history for a student
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from app.concept_graph.models import PerformanceRecord, DifficultyDNA
from app.concept_graph.mastery_tracker import MasteryTracker, MasteryRecord
from app.concept_graph.graph_manager import ConceptGraphManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mastery", tags=["mastery-tracking"])

# Initialize managers
mastery_tracker = MasteryTracker()
graph_manager = ConceptGraphManager()


# Request models
class PerformanceRecordRequest(BaseModel):
    """Request model for recording performance."""
    student_id: str = Field(..., description="Student identifier")
    concept_id: str = Field(..., description="Concept identifier")
    question_difficulty: DifficultyDNA = Field(..., description="Question difficulty DNA")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    time_taken_seconds: int = Field(..., gt=0, description="Time taken in seconds")


# Response models
class PerformanceResponse(BaseModel):
    """Response model for performance recording."""
    success: bool
    message: str


class MasteryLevelResponse(BaseModel):
    """Response model for mastery level query."""
    success: bool
    message: str
    student_id: str
    concept_id: str
    mastery_level: float
    is_mastered: bool
    threshold: float


class MasteryHistoryResponse(BaseModel):
    """Response model for mastery history query."""
    success: bool
    message: str
    student_id: str
    mastery_records: List[dict]
    count: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str
    message: str
    details: Optional[dict] = None


@router.post(
    "/performance",
    response_model=PerformanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record performance",
    description="Record a student's performance on a question for mastery tracking"
)
async def record_performance(request: PerformanceRecordRequest):
    """
    Record a student's performance on a question.
    
    This endpoint:
    1. Validates that the concept exists
    2. Creates a PerformanceRecord with the provided data
    3. Persists the record to the database
    4. Invalidates cached mastery data for the student/concept
    
    Args:
        request: Performance record data including student_id, concept_id,
                question_difficulty, is_correct, and time_taken_seconds
    
    Returns:
        PerformanceResponse confirming successful recording
        
    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If concept not found
        HTTPException 500: If database operation fails
        
    Requirements: 11.7
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
        
        # Create performance record
        performance_record = PerformanceRecord(
            student_id=request.student_id,
            concept_id=request.concept_id,
            question_difficulty=request.question_difficulty,
            is_correct=request.is_correct,
            time_taken_seconds=request.time_taken_seconds
        )
        
        # Record performance
        mastery_tracker.record_performance(performance_record)
        
        logger.info(
            f"Recorded performance for student {request.student_id} "
            f"on concept {request.concept_id}: "
            f"correct={request.is_correct}, time={request.time_taken_seconds}s"
        )
        
        return PerformanceResponse(
            success=True,
            message=f"Performance recorded successfully for concept '{concept.name}'"
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        logger.warning(f"Validation error recording performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "details": None
            }
        )
    
    except Exception as e:
        logger.error(f"Error recording performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DATABASE_ERROR",
                "message": "Failed to record performance",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{student_id}/{concept_id}",
    response_model=MasteryLevelResponse,
    summary="Get mastery level",
    description="Get the current mastery level for a student on a specific concept"
)
async def get_mastery_level(
    student_id: str,
    concept_id: str,
    threshold: float = 0.8
):
    """
    Get mastery level for a student on a specific concept.
    
    This endpoint:
    1. Validates that the concept exists
    2. Calculates the current mastery level (0.0 to 1.0)
    3. Determines if the concept is mastered based on threshold
    4. Returns mastery data
    
    The mastery level is calculated based on:
    - Weighted accuracy (recent attempts weighted higher)
    - Consistency bonus (reward consistent correct answers)
    - Difficulty bonus (reward mastery at higher difficulty)
    
    Args:
        student_id: Student identifier
        concept_id: Concept identifier
        threshold: Mastery threshold (default: 0.8)
    
    Returns:
        MasteryLevelResponse with mastery level and status
        
    Raises:
        HTTPException 400: If validation fails (e.g., invalid threshold)
        HTTPException 404: If concept not found
        HTTPException 500: If calculation fails
        
    Requirements: 11.7
    """
    try:
        # Validate threshold
        if threshold < 0.0 or threshold > 1.0:
            raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}")
        
        # Validate concept exists
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
        
        # Calculate mastery level
        mastery_level = mastery_tracker.calculate_mastery(student_id, concept_id)
        is_mastered = mastery_tracker.is_mastered(student_id, concept_id, threshold)
        
        logger.info(
            f"Retrieved mastery level for student {student_id}, "
            f"concept {concept_id}: {mastery_level:.3f} "
            f"(mastered={is_mastered}, threshold={threshold})"
        )
        
        return MasteryLevelResponse(
            success=True,
            message=f"Mastery level retrieved for concept '{concept.name}'",
            student_id=student_id,
            concept_id=concept_id,
            mastery_level=mastery_level,
            is_mastered=is_mastered,
            threshold=threshold
        )
    
    except HTTPException:
        raise
    
    except ValueError as e:
        logger.warning(f"Validation error getting mastery level: {e}")
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
            f"Error getting mastery level for student {student_id}, "
            f"concept {concept_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CALCULATION_ERROR",
                "message": "Failed to calculate mastery level",
                "details": {"error": str(e)}
            }
        )


@router.get(
    "/{student_id}/history",
    response_model=MasteryHistoryResponse,
    summary="Get mastery history",
    description="Get complete mastery history for a student across all attempted concepts"
)
async def get_mastery_history(student_id: str):
    """
    Get complete mastery history for a student.
    
    This endpoint:
    1. Retrieves all concepts the student has attempted
    2. Calculates current mastery level for each concept
    3. Returns list of mastery records with status
    
    Each mastery record includes:
    - Concept ID
    - Current mastery level (0.0 to 1.0)
    - Mastery status (mastered/not mastered)
    - Last update timestamp
    
    Args:
        student_id: Student identifier
    
    Returns:
        MasteryHistoryResponse with list of mastery records
        
    Raises:
        HTTPException 500: If retrieval fails
        
    Requirements: 11.7
    """
    try:
        logger.info(f"Retrieving mastery history for student {student_id}")
        
        # Get mastery history
        mastery_records = mastery_tracker.get_mastery_history(student_id)
        
        # Convert to dict format
        mastery_records_dict = [record.to_dict() for record in mastery_records]
        
        logger.info(
            f"Retrieved mastery history for student {student_id}: "
            f"{len(mastery_records)} concepts"
        )
        
        return MasteryHistoryResponse(
            success=True,
            message=f"Retrieved mastery history for {len(mastery_records)} concepts",
            student_id=student_id,
            mastery_records=mastery_records_dict,
            count=len(mastery_records)
        )
    
    except Exception as e:
        logger.error(f"Error getting mastery history for student {student_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "RETRIEVAL_ERROR",
                "message": "Failed to retrieve mastery history",
                "details": {"error": str(e)}
            }
        )
