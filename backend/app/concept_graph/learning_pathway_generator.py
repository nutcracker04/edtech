"""
Learning Pathway Generator for creating progressive learning sequences.

This module provides:
- Learning pathway generation based on prerequisites and mastery
- Next concept recommendations with mastery filtering
- Progressive question series generation
- Pathway adaptation based on performance trends
"""

from typing import List, Optional, Set
from dataclasses import dataclass
import logging

from .models import Concept, Question, DifficultyDNA
from .graph_manager import ConceptGraphManager
from .prerequisite_validator import PrerequisiteValidator
from .mastery_tracker import MasteryTracker

logger = logging.getLogger(__name__)


@dataclass
class LearningPathway:
    """
    A progressive learning pathway for a student.
    
    Attributes:
        student_id: Student identifier
        concepts: Ordered list of concepts in the pathway
        current_level: Student's current class level
        target_level: Target class level
        total_concepts: Total number of concepts in pathway
        mastered_count: Number of concepts already mastered
    """
    student_id: str
    concepts: List[Concept]
    current_level: int
    target_level: int
    total_concepts: int
    mastered_count: int
    
    def to_dict(self) -> dict:
        """Convert LearningPathway to dictionary format."""
        return {
            "student_id": self.student_id,
            "concepts": [c.to_dict() for c in self.concepts],
            "current_level": self.current_level,
            "target_level": self.target_level,
            "total_concepts": self.total_concepts,
            "mastered_count": self.mastered_count
        }


class LearningPathwayGenerator:
    """
    Generate progressive learning pathways based on prerequisites and mastery.
    
    This class manages:
    - Generating learning pathways from current to target level
    - Recommending next concepts based on prerequisite satisfaction
    - Generating progressive question series for concepts
    - Adapting pathways based on performance trends
    """
    
    def __init__(
        self,
        graph_manager: Optional[ConceptGraphManager] = None,
        prerequisite_validator: Optional[PrerequisiteValidator] = None,
        mastery_tracker: Optional[MasteryTracker] = None
    ):
        """
        Initialize the LearningPathwayGenerator.
        
        Args:
            graph_manager: Optional ConceptGraphManager instance
            prerequisite_validator: Optional PrerequisiteValidator instance
            mastery_tracker: Optional MasteryTracker instance
        """
        self.graph_manager = graph_manager or ConceptGraphManager()
        self.prerequisite_validator = prerequisite_validator or PrerequisiteValidator(self.graph_manager)
        self.mastery_tracker = mastery_tracker or MasteryTracker()
    
    def generate_pathway(
        self,
        student_id: str,
        target_class_level: int,
        mastered_concepts: Optional[Set[str]] = None
    ) -> LearningPathway:
        """
        Generate a learning pathway for student to reach target level.
        
        This method:
        1. Determines student's current level from mastered concepts
        2. Queries all concepts from current to target level
        3. Filters to concepts with satisfied prerequisites
        4. Orders concepts by difficulty progression
        5. Returns structured learning pathway
        
        Args:
            student_id: Student identifier
            target_class_level: Target class level (8-12)
            mastered_concepts: Optional set of mastered concept IDs.
                              If None, will be retrieved from mastery tracker.
            
        Returns:
            LearningPathway with ordered concept sequence
            
        Raises:
            ValueError: If target_class_level is invalid
        """
        if target_class_level < 8 or target_class_level > 12:
            raise ValueError(f"Invalid target class level: {target_class_level}. Must be 8-12.")
        
        # Get mastered concepts if not provided
        if mastered_concepts is None:
            mastered_concepts = self._get_mastered_concepts(student_id)
        
        # Infer current level from mastered concepts
        current_level = self._infer_current_level(mastered_concepts)
        
        logger.info(
            f"Generating pathway for student {student_id}: "
            f"current_level={current_level}, target_level={target_class_level}, "
            f"mastered_count={len(mastered_concepts)}"
        )
        
        # Get all concepts from current to target level
        candidate_concepts = self._get_concepts_in_range(current_level, target_class_level)
        
        # Filter to concepts with satisfied prerequisites
        available_concepts = self._filter_by_prerequisites(
            candidate_concepts,
            mastered_concepts
        )
        
        # Sort by difficulty progression
        ordered_concepts = self._sort_by_difficulty_progression(available_concepts)
        
        pathway = LearningPathway(
            student_id=student_id,
            concepts=ordered_concepts,
            current_level=current_level,
            target_level=target_class_level,
            total_concepts=len(ordered_concepts),
            mastered_count=len(mastered_concepts)
        )
        
        logger.info(
            f"Generated pathway with {len(ordered_concepts)} concepts "
            f"for student {student_id}"
        )
        
        return pathway
    
    def get_next_concepts(
        self,
        student_id: str,
        count: int = 5,
        mastered_concepts: Optional[Set[str]] = None
    ) -> List[Concept]:
        """
        Get next recommended concepts based on mastery and prerequisites.
        
        This method:
        1. Gets mastered concepts for the student
        2. Finds concepts with all prerequisites satisfied
        3. Filters out already mastered concepts
        4. Orders by difficulty progression
        5. Returns top N concepts
        
        Args:
            student_id: Student identifier
            count: Number of concepts to return (default: 5)
            mastered_concepts: Optional set of mastered concept IDs.
                              If None, will be retrieved from mastery tracker.
            
        Returns:
            List of next recommended concepts (up to count)
        """
        # Get mastered concepts if not provided
        if mastered_concepts is None:
            mastered_concepts = self._get_mastered_concepts(student_id)
        
        # Infer current level
        current_level = self._infer_current_level(mastered_concepts)
        
        # Get concepts at current level and one level above
        candidate_concepts = self._get_concepts_in_range(
            current_level,
            min(current_level + 1, 12)
        )
        
        # Filter to concepts with satisfied prerequisites
        available_concepts = self._filter_by_prerequisites(
            candidate_concepts,
            mastered_concepts
        )
        
        # Filter out already mastered concepts
        unmastered_concepts = [
            c for c in available_concepts
            if c.id not in mastered_concepts
        ]
        
        # Sort by difficulty progression
        ordered_concepts = self._sort_by_difficulty_progression(unmastered_concepts)
        
        # Return top N concepts
        next_concepts = ordered_concepts[:count]
        
        logger.info(
            f"Recommended {len(next_concepts)} next concepts for student {student_id}"
        )
        
        return next_concepts
    
    def _get_mastered_concepts(self, student_id: str) -> Set[str]:
        """
        Get set of mastered concept IDs for a student.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Set of concept IDs that are mastered
        """
        mastery_history = self.mastery_tracker.get_mastery_history(student_id)
        mastered = {
            record.concept_id
            for record in mastery_history
            if record.is_mastered
        }
        
        logger.debug(f"Student {student_id} has mastered {len(mastered)} concepts")
        return mastered
    
    def _infer_current_level(self, mastered_concepts: Set[str]) -> int:
        """
        Infer student's current class level from mastered concepts.
        
        Algorithm:
        1. If no concepts mastered, return Class 8 (starting level)
        2. Get all mastered concept details
        3. Find highest class level among mastered concepts
        4. Return that level (student is at the level of their highest mastery)
        
        Args:
            mastered_concepts: Set of mastered concept IDs
            
        Returns:
            Inferred class level (8-12)
        """
        if not mastered_concepts:
            return 8  # Starting level
        
        # Get concept details for mastered concepts
        max_level = 8
        for concept_id in mastered_concepts:
            concept = self.graph_manager.get_concept(concept_id)
            if concept and concept.class_level > max_level:
                max_level = concept.class_level
        
        logger.debug(f"Inferred current level: {max_level}")
        return max_level
    
    def _get_concepts_in_range(
        self,
        min_level: int,
        max_level: int
    ) -> List[Concept]:
        """
        Get all concepts within a class level range.
        
        Args:
            min_level: Minimum class level (inclusive)
            max_level: Maximum class level (inclusive)
            
        Returns:
            List of concepts in the range
        """
        from .models import ConceptFilters
        
        all_concepts = []
        for level in range(min_level, max_level + 1):
            filters = ConceptFilters(class_level=level)
            concepts = self.graph_manager.query_concepts(filters)
            all_concepts.extend(concepts)
        
        logger.debug(
            f"Found {len(all_concepts)} concepts in range "
            f"[{min_level}, {max_level}]"
        )
        return all_concepts
    
    def _filter_by_prerequisites(
        self,
        concepts: List[Concept],
        mastered_concepts: Set[str]
    ) -> List[Concept]:
        """
        Filter concepts to those with all prerequisites satisfied.
        
        Args:
            concepts: List of candidate concepts
            mastered_concepts: Set of mastered concept IDs
            
        Returns:
            List of concepts with satisfied prerequisites
        """
        available = []
        
        for concept in concepts:
            # Get all prerequisites for this concept
            prerequisites = self.prerequisite_validator.get_prerequisites(
                concept.id,
                recursive=True
            )
            
            # Check if all prerequisites are mastered
            prerequisite_ids = {p.id for p in prerequisites}
            if prerequisite_ids.issubset(mastered_concepts):
                available.append(concept)
        
        logger.debug(
            f"Filtered to {len(available)} concepts with satisfied prerequisites "
            f"(from {len(concepts)} candidates)"
        )
        return available
    
    def _sort_by_difficulty_progression(
        self,
        concepts: List[Concept]
    ) -> List[Concept]:
        """
        Sort concepts by difficulty progression.
        
        Algorithm:
        1. Calculate difficulty score for each concept
        2. Sort by: class_level (primary), difficulty_score (secondary)
        3. This ensures progressive difficulty within each level
        
        Difficulty score is calculated as weighted sum of DNA dimensions:
        - Bloom level: 25%
        - Abstraction level: 20%
        - Computational complexity: 20%
        - Concept integration: 15%
        - Real-world context: 10%
        - Problem approach: 10%
        
        Args:
            concepts: List of concepts to sort
            
        Returns:
            Sorted list of concepts
        """
        def calculate_difficulty_score(concept: Concept) -> float:
            """Calculate overall difficulty score for a concept."""
            dna = concept.difficulty_dna
            
            # Normalize each dimension to 0-1 scale
            bloom_norm = dna.bloom_level / 6.0
            abstraction_norm = dna.abstraction_level / 5.0
            # Normalize complexity (assume max ~20 steps)
            complexity_norm = min(dna.computational_complexity / 20.0, 1.0)
            
            # Concept integration: single=0.33, multi=0.67, cross=1.0
            integration_map = {
                "single": 0.33,
                "multi-concept": 0.67,
                "cross-subject": 1.0
            }
            integration_norm = integration_map.get(
                dna.concept_integration.value,
                0.5
            )
            
            context_norm = dna.real_world_context / 5.0
            
            # Problem approach: direct=0.25, multi=0.5, proof=0.75, exploratory=1.0
            approach_map = {
                "direct-application": 0.25,
                "multi-step": 0.5,
                "proof-based": 0.75,
                "exploratory": 1.0
            }
            approach_norm = approach_map.get(
                dna.problem_solving_approach.value,
                0.5
            )
            
            # Weighted sum
            score = (
                0.25 * bloom_norm +
                0.20 * abstraction_norm +
                0.20 * complexity_norm +
                0.15 * integration_norm +
                0.10 * context_norm +
                0.10 * approach_norm
            )
            
            return score
        
        # Sort by class level first, then by difficulty score
        sorted_concepts = sorted(
            concepts,
            key=lambda c: (c.class_level, calculate_difficulty_score(c))
        )
        
        logger.debug(f"Sorted {len(sorted_concepts)} concepts by difficulty progression")
        return sorted_concepts
