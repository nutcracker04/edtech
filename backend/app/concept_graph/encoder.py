"""
Difficulty DNA Encoder for validating and comparing difficulty encodings.

This module provides the DifficultyDNAEncoder class for:
- Validating difficulty DNA dimensions
- Comparing difficulty DNA encodings
- Checking persona constraints
- Adjusting difficulty levels
"""

from typing import List, Optional
from .models import DifficultyDNA, StudentPersona, ConceptIntegration, ProblemApproach
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    
    def __bool__(self):
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


class DifficultyDNAEncoder:
    """
    Encoder for validating and comparing Difficulty DNA encodings.
    
    This class provides methods to:
    - Validate that all DNA dimensions are within acceptable ranges
    - Compare two DNA encodings to calculate relative difficulty
    - Check if a DNA fits within persona constraints
    - Adjust DNA difficulty by a factor
    """
    
    # Valid ranges for each dimension
    BLOOM_LEVEL_RANGE = (1, 6)
    ABSTRACTION_LEVEL_RANGE = (1, 5)
    COMPUTATIONAL_COMPLEXITY_MIN = 1
    REAL_WORLD_CONTEXT_RANGE = (1, 5)
    
    @classmethod
    def validate(cls, dna: DifficultyDNA) -> ValidationResult:
        """
        Validate all dimensions of a DifficultyDNA encoding.
        
        Args:
            dna: The DifficultyDNA instance to validate
            
        Returns:
            ValidationResult with is_valid flag and list of error messages
            
        Requirements: 2.8
        """
        errors = []
        
        # Validate bloom_level (1-6)
        if not (cls.BLOOM_LEVEL_RANGE[0] <= dna.bloom_level <= cls.BLOOM_LEVEL_RANGE[1]):
            errors.append(
                f"bloom_level must be between {cls.BLOOM_LEVEL_RANGE[0]} and {cls.BLOOM_LEVEL_RANGE[1]}, "
                f"got {dna.bloom_level}"
            )
        
        # Validate abstraction_level (1-5)
        if not (cls.ABSTRACTION_LEVEL_RANGE[0] <= dna.abstraction_level <= cls.ABSTRACTION_LEVEL_RANGE[1]):
            errors.append(
                f"abstraction_level must be between {cls.ABSTRACTION_LEVEL_RANGE[0]} and {cls.ABSTRACTION_LEVEL_RANGE[1]}, "
                f"got {dna.abstraction_level}"
            )
        
        # Validate computational_complexity (positive integer)
        if dna.computational_complexity < cls.COMPUTATIONAL_COMPLEXITY_MIN:
            errors.append(
                f"computational_complexity must be at least {cls.COMPUTATIONAL_COMPLEXITY_MIN}, "
                f"got {dna.computational_complexity}"
            )
        
        # Validate real_world_context (1-5)
        if not (cls.REAL_WORLD_CONTEXT_RANGE[0] <= dna.real_world_context <= cls.REAL_WORLD_CONTEXT_RANGE[1]):
            errors.append(
                f"real_world_context must be between {cls.REAL_WORLD_CONTEXT_RANGE[0]} and {cls.REAL_WORLD_CONTEXT_RANGE[1]}, "
                f"got {dna.real_world_context}"
            )
        
        # Validate concept_integration (enum - should always be valid if using the enum)
        if not isinstance(dna.concept_integration, ConceptIntegration):
            errors.append(
                f"concept_integration must be a valid ConceptIntegration enum value, "
                f"got {type(dna.concept_integration).__name__}"
            )
        
        # Validate problem_solving_approach (enum - should always be valid if using the enum)
        if not isinstance(dna.problem_solving_approach, ProblemApproach):
            errors.append(
                f"problem_solving_approach must be a valid ProblemApproach enum value, "
                f"got {type(dna.problem_solving_approach).__name__}"
            )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @classmethod
    def compare(cls, dna1: DifficultyDNA, dna2: DifficultyDNA) -> float:
        """
        Calculate relative difficulty score between two DNA encodings.
        
        Uses weighted sum of normalized dimension differences:
        - Bloom level: 0.25
        - Abstraction: 0.20
        - Complexity: 0.20
        - Integration: 0.15
        - Context: 0.10
        - Approach: 0.10
        
        Args:
            dna1: First DifficultyDNA instance
            dna2: Second DifficultyDNA instance
            
        Returns:
            Float score from 0.0 (identical) to 1.0 (maximally different)
            
        Requirements: 2.9
        """
        # Normalize and calculate differences for each dimension
        
        # Bloom level (1-6) - weight 0.25
        bloom_diff = abs(dna1.bloom_level - dna2.bloom_level) / 5.0
        
        # Abstraction level (1-5) - weight 0.20
        abstraction_diff = abs(dna1.abstraction_level - dna2.abstraction_level) / 4.0
        
        # Computational complexity - normalize to reasonable range (1-50) - weight 0.20
        max_complexity = 50.0
        complexity_diff = abs(dna1.computational_complexity - dna2.computational_complexity) / max_complexity
        complexity_diff = min(complexity_diff, 1.0)  # Cap at 1.0
        
        # Concept integration (categorical) - weight 0.15
        integration_values = {
            ConceptIntegration.SINGLE: 0,
            ConceptIntegration.MULTI_CONCEPT: 1,
            ConceptIntegration.CROSS_SUBJECT: 2
        }
        integration_diff = abs(
            integration_values[dna1.concept_integration] - 
            integration_values[dna2.concept_integration]
        ) / 2.0
        
        # Real-world context (1-5) - weight 0.10
        context_diff = abs(dna1.real_world_context - dna2.real_world_context) / 4.0
        
        # Problem-solving approach (categorical) - weight 0.10
        approach_values = {
            ProblemApproach.DIRECT: 0,
            ProblemApproach.MULTI_STEP: 1,
            ProblemApproach.PROOF: 2,
            ProblemApproach.EXPLORATORY: 3
        }
        approach_diff = abs(
            approach_values[dna1.problem_solving_approach] - 
            approach_values[dna2.problem_solving_approach]
        ) / 3.0
        
        # Calculate weighted sum
        distance = (
            0.25 * bloom_diff +
            0.20 * abstraction_diff +
            0.20 * complexity_diff +
            0.15 * integration_diff +
            0.10 * context_diff +
            0.10 * approach_diff
        )
        
        return distance
    
    @classmethod
    def fits_persona(cls, dna: DifficultyDNA, persona: StudentPersona) -> bool:
        """
        Check if difficulty DNA fits within persona constraints.
        
        Args:
            dna: DifficultyDNA instance to check
            persona: StudentPersona with constraints
            
        Returns:
            True if DNA fits within all persona constraints, False otherwise
            
        Requirements: 5.6
        """
        constraints = persona.difficulty_constraints
        
        # Check Bloom level
        if dna.bloom_level > constraints.max_bloom_level:
            return False
        
        # Check abstraction level
        if dna.abstraction_level > constraints.max_abstraction_level:
            return False
        
        # Check computational complexity
        if dna.computational_complexity > constraints.max_computational_complexity:
            return False
        
        # Check concept integration
        if dna.concept_integration not in constraints.allowed_concept_integration:
            return False
        
        # Check real-world context
        if dna.real_world_context > constraints.max_real_world_context:
            return False
        
        # Check problem-solving approach
        if dna.problem_solving_approach not in constraints.allowed_problem_approaches:
            return False
        
        return True
    
    @classmethod
    def adjust_difficulty(cls, dna: DifficultyDNA, adjustment: float) -> DifficultyDNA:
        """
        Adjust difficulty DNA by a factor while maintaining validity.
        
        Args:
            dna: Original DifficultyDNA instance
            adjustment: Adjustment factor from -1.0 (decrease) to +1.0 (increase)
            
        Returns:
            New DifficultyDNA instance with adjusted difficulty
            
        Requirements: 5.6
        """
        # Clamp adjustment to valid range
        adjustment = max(-1.0, min(1.0, adjustment))
        
        # Adjust bloom level
        bloom_adjustment = int(round(adjustment * 2))  # Max change of ±2 levels
        new_bloom = max(
            cls.BLOOM_LEVEL_RANGE[0],
            min(cls.BLOOM_LEVEL_RANGE[1], dna.bloom_level + bloom_adjustment)
        )
        
        # Adjust abstraction level
        abstraction_adjustment = int(round(adjustment * 1.5))  # Max change of ±1-2 levels
        new_abstraction = max(
            cls.ABSTRACTION_LEVEL_RANGE[0],
            min(cls.ABSTRACTION_LEVEL_RANGE[1], dna.abstraction_level + abstraction_adjustment)
        )
        
        # Adjust computational complexity
        complexity_adjustment = int(round(adjustment * dna.computational_complexity * 0.3))
        new_complexity = max(
            cls.COMPUTATIONAL_COMPLEXITY_MIN,
            dna.computational_complexity + complexity_adjustment
        )
        
        # Adjust real-world context
        context_adjustment = int(round(adjustment * 1))  # Max change of ±1 level
        new_context = max(
            cls.REAL_WORLD_CONTEXT_RANGE[0],
            min(cls.REAL_WORLD_CONTEXT_RANGE[1], dna.real_world_context + context_adjustment)
        )
        
        # For categorical values, keep them the same or upgrade/downgrade if possible
        new_integration = dna.concept_integration
        if adjustment > 0.5:
            # Increase integration complexity
            if dna.concept_integration == ConceptIntegration.SINGLE:
                new_integration = ConceptIntegration.MULTI_CONCEPT
            elif dna.concept_integration == ConceptIntegration.MULTI_CONCEPT:
                new_integration = ConceptIntegration.CROSS_SUBJECT
        elif adjustment < -0.5:
            # Decrease integration complexity
            if dna.concept_integration == ConceptIntegration.CROSS_SUBJECT:
                new_integration = ConceptIntegration.MULTI_CONCEPT
            elif dna.concept_integration == ConceptIntegration.MULTI_CONCEPT:
                new_integration = ConceptIntegration.SINGLE
        
        new_approach = dna.problem_solving_approach
        if adjustment > 0.5:
            # Increase approach complexity
            if dna.problem_solving_approach == ProblemApproach.DIRECT:
                new_approach = ProblemApproach.MULTI_STEP
            elif dna.problem_solving_approach == ProblemApproach.MULTI_STEP:
                new_approach = ProblemApproach.PROOF
            elif dna.problem_solving_approach == ProblemApproach.PROOF:
                new_approach = ProblemApproach.EXPLORATORY
        elif adjustment < -0.5:
            # Decrease approach complexity
            if dna.problem_solving_approach == ProblemApproach.EXPLORATORY:
                new_approach = ProblemApproach.PROOF
            elif dna.problem_solving_approach == ProblemApproach.PROOF:
                new_approach = ProblemApproach.MULTI_STEP
            elif dna.problem_solving_approach == ProblemApproach.MULTI_STEP:
                new_approach = ProblemApproach.DIRECT
        
        return DifficultyDNA(
            bloom_level=new_bloom,
            abstraction_level=new_abstraction,
            computational_complexity=new_complexity,
            concept_integration=new_integration,
            real_world_context=new_context,
            problem_solving_approach=new_approach
        )
