"""
Concept Knowledge Graph module for mathematics education.

This module provides a sophisticated educational technology platform that models
mathematical knowledge as a directed graph structure with multi-dimensional
difficulty encoding.
"""

from .models import (
    ConceptIntegration,
    ProblemApproach,
    RelationshipType,
    QuestionType,
    DifficultyDNA,
    Concept,
    ConceptCreate,
    ConceptFilters,
    Relationship,
    RelationshipCreate,
    StudentPersona,
    Question,
)
from .encoder import DifficultyDNAEncoder, ValidationResult
from .graph_manager import ConceptGraphManager
from .prerequisite_validator import (
    PrerequisiteValidator,
    ValidationResult as PrereqValidationResult,
    ReadinessResult,
)
from .persona_engine import PersonaEngine
from .question_generator import QuestionGenerator
from .mastery_tracker import MasteryTracker, MasteryRecord
from .learning_pathway_generator import LearningPathwayGenerator, LearningPathway

__all__ = [
    "ConceptIntegration",
    "ProblemApproach",
    "RelationshipType",
    "QuestionType",
    "DifficultyDNA",
    "Concept",
    "ConceptCreate",
    "ConceptFilters",
    "Relationship",
    "RelationshipCreate",
    "StudentPersona",
    "Question",
    "DifficultyDNAEncoder",
    "ValidationResult",
    "ConceptGraphManager",
    "PrerequisiteValidator",
    "PrereqValidationResult",
    "ReadinessResult",
    "PersonaEngine",
    "QuestionGenerator",
    "MasteryTracker",
    "MasteryRecord",
    "LearningPathwayGenerator",
    "LearningPathway",
]
