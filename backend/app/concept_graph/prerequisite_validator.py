"""
Prerequisite Validator for validating concept prerequisites and student readiness.

This module provides the PrerequisiteValidator class which handles:
- Validating prerequisite relationships (cycle detection)
- Getting prerequisites with recursive traversal (BFS)
- Getting dependents for reverse prerequisite queries
- Checking student readiness for concepts
- Getting unmet prerequisites for students
"""

from typing import List, Optional, Set
from dataclasses import dataclass
import logging

from .models import Concept, RelationshipType
from .graph_manager import ConceptGraphManager

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    message: str
    details: Optional[dict] = None


@dataclass
class ReadinessResult:
    """Result of a student readiness check."""
    is_ready: bool
    message: str
    unmet_prerequisites: List[Concept]


class PrerequisiteValidator:
    """
    Validator for prerequisite relationships and student readiness.
    
    This class wraps ConceptGraphManager to provide specialized methods
    for prerequisite validation, readiness checking, and prerequisite queries.
    """
    
    def __init__(self, graph_manager: Optional[ConceptGraphManager] = None):
        """
        Initialize the PrerequisiteValidator.
        
        Args:
            graph_manager: Optional ConceptGraphManager instance. If not provided,
                          a new instance will be created.
        """
        self.graph_manager = graph_manager or ConceptGraphManager()
    
    def validate_relationship(
        self,
        source_id: str,
        target_id: str
    ) -> ValidationResult:
        """
        Validate that adding a prerequisite relationship won't create cycles.
        
        Uses cycle detection to ensure the graph remains acyclic. A cycle would
        occur if there's already a path from target to source.
        
        Args:
            source_id: Source concept ID for proposed relationship
            target_id: Target concept ID for proposed relationship
            
        Returns:
            ValidationResult indicating if the relationship is valid
        """
        # Check if both concepts exist
        source = self.graph_manager.get_concept(source_id)
        if source is None:
            return ValidationResult(
                is_valid=False,
                message=f"Source concept not found: {source_id}",
                details={"source_id": source_id}
            )
        
        target = self.graph_manager.get_concept(target_id)
        if target is None:
            return ValidationResult(
                is_valid=False,
                message=f"Target concept not found: {target_id}",
                details={"target_id": target_id}
            )
        
        # Check for cycles
        would_create_cycle = self.detect_cycle(source_id, target_id)
        
        if would_create_cycle:
            return ValidationResult(
                is_valid=False,
                message=(
                    f"Cannot create relationship: would create a cycle. "
                    f"A path already exists from {target_id} ({target.name}) "
                    f"to {source_id} ({source.name})"
                ),
                details={
                    "source_id": source_id,
                    "target_id": target_id,
                    "source_name": source.name,
                    "target_name": target.name
                }
            )
        
        return ValidationResult(
            is_valid=True,
            message="Relationship is valid and will not create a cycle",
            details={
                "source_id": source_id,
                "target_id": target_id,
                "source_name": source.name,
                "target_name": target.name
            }
        )
    
    def detect_cycle(self, source_id: str, target_id: str) -> bool:
        """
        Detect if adding an edge from source to target would create a cycle.
        
        This method delegates to the ConceptGraphManager's cycle detection
        implementation, which uses depth-first search to check if there's
        already a path from target to source.
        
        Args:
            source_id: Source concept ID for proposed edge
            target_id: Target concept ID for proposed edge
            
        Returns:
            True if adding the edge would create a cycle, False otherwise
        """
        return self.graph_manager.detect_cycle(source_id, target_id)
    
    def get_prerequisites(
        self,
        concept_id: str,
        recursive: bool = True,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Concept]:
        """
        Get all prerequisite concepts for a given concept.
        
        By default, includes both PREREQUISITE and BUILDS_UPON relationships.
        Can be filtered to specific relationship types.
        
        Uses breadth-first search (BFS) to traverse the prerequisite graph.
        
        Args:
            concept_id: Concept ID to get prerequisites for
            recursive: If True, get all transitive prerequisites (default: True)
            relationship_types: Optional list of relationship types to filter by.
                              Defaults to [PREREQUISITE, BUILDS_UPON] if not specified.
            
        Returns:
            List of prerequisite concepts
        """
        return self.graph_manager.get_prerequisites(concept_id, recursive, relationship_types)
    
    def get_dependents(
        self,
        concept_id: str,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Concept]:
        """
        Get all concepts that depend on this concept (reverse prerequisites).
        
        By default, includes both PREREQUISITE and BUILDS_UPON relationships.
        Can be filtered to specific relationship types.
        
        This returns all concepts that have the given concept as a prerequisite,
        either directly or through BUILDS_UPON relationships.
        
        Args:
            concept_id: Concept ID to get dependents for
            relationship_types: Optional list of relationship types to filter by.
                              Defaults to [PREREQUISITE, BUILDS_UPON] if not specified.
            
        Returns:
            List of dependent concepts
        """
        return self.graph_manager.get_dependents(concept_id, relationship_types)
    
    def check_readiness(
        self,
        student_id: str,
        concept_id: str,
        mastered_concepts: Set[str]
    ) -> ReadinessResult:
        """
        Check if a student has mastered all prerequisites for a concept.
        
        Args:
            student_id: Student identifier
            concept_id: Concept ID to check readiness for
            mastered_concepts: Set of concept IDs that the student has mastered
            
        Returns:
            ReadinessResult indicating if student is ready and listing unmet prerequisites
        """
        # Get the concept
        concept = self.graph_manager.get_concept(concept_id)
        if concept is None:
            return ReadinessResult(
                is_ready=False,
                message=f"Concept not found: {concept_id}",
                unmet_prerequisites=[]
            )
        
        # Get all prerequisites (recursive)
        prerequisites = self.get_prerequisites(concept_id, recursive=True)
        
        # Check which prerequisites are not mastered
        unmet = []
        for prereq in prerequisites:
            if prereq.id not in mastered_concepts:
                unmet.append(prereq)
        
        if unmet:
            unmet_names = [p.name for p in unmet]
            return ReadinessResult(
                is_ready=False,
                message=(
                    f"Student {student_id} is not ready for '{concept.name}'. "
                    f"Unmet prerequisites: {', '.join(unmet_names)}"
                ),
                unmet_prerequisites=unmet
            )
        
        return ReadinessResult(
            is_ready=True,
            message=f"Student {student_id} is ready for '{concept.name}'",
            unmet_prerequisites=[]
        )
    
    def get_unmet_prerequisites(
        self,
        student_id: str,
        concept_id: str,
        mastered_concepts: Set[str]
    ) -> List[Concept]:
        """
        Get list of unmet prerequisite concepts for a student.
        
        Args:
            student_id: Student identifier
            concept_id: Concept ID to check prerequisites for
            mastered_concepts: Set of concept IDs that the student has mastered
            
        Returns:
            List of unmet prerequisite concepts
        """
        readiness = self.check_readiness(student_id, concept_id, mastered_concepts)
        return readiness.unmet_prerequisites
