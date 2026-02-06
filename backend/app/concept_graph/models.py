"""
Core data models for the Concept Knowledge Graph system.

This module defines Pydantic models for all core entities including:
- Enums for categorical values
- DifficultyDNA for multi-dimensional difficulty encoding
- Concept for mathematical concept nodes
- Relationship for concept dependencies
- StudentPersona for class-level profiles
- Question for generated questions
"""

from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4


class ConceptIntegration(str, Enum):
    """Enum for concept integration complexity."""
    SINGLE = "single"
    MULTI_CONCEPT = "multi-concept"
    CROSS_SUBJECT = "cross-subject"


class Subject(str, Enum):
    """Enum for academic subjects."""
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ECONOMICS = "economics"
    POLITICAL_SCIENCE = "political-science"
    ENGLISH = "english"
    HINDI = "hindi"
    SANSKRIT = "sanskrit"
    COMPUTER_SCIENCE = "computer-science"
    ACCOUNTANCY = "accountancy"
    BUSINESS_STUDIES = "business-studies"


class ProblemApproach(str, Enum):
    """Enum for problem-solving approach types."""
    DIRECT = "direct-application"
    MULTI_STEP = "multi-step"
    PROOF = "proof-based"
    EXPLORATORY = "exploratory"


class RelationshipType(str, Enum):
    """Enum for relationship types between concepts."""
    PREREQUISITE = "prerequisite"
    BUILDS_UPON = "builds-upon"
    APPLIES_TO = "applies-to"


class QuestionType(str, Enum):
    """Enum for question types."""
    MCQ = "mcq"
    NUMERICAL = "numerical"
    SUBJECTIVE = "subjective"


class VocabularyLevel(str, Enum):
    """Enum for vocabulary complexity levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TechnicalLevel(str, Enum):
    """Enum for technical term usage levels."""
    MINIMAL = "minimal"
    MODERATE = "moderate"
    EXTENSIVE = "extensive"


class DifficultyDNA(BaseModel):
    """
    Multi-dimensional difficulty encoding for mathematical concepts.
    
    Attributes:
        bloom_level: Bloom's taxonomy level (1-6)
        abstraction_level: Abstraction level (1-5)
        computational_complexity: Number of computational steps (positive integer)
        concept_integration: Integration complexity (single/multi/cross-subject)
        real_world_context: Real-world context level (1-5)
        problem_solving_approach: Problem-solving approach type
    """
    bloom_level: int = Field(..., ge=1, le=6, description="Bloom's taxonomy level (1-6)")
    abstraction_level: int = Field(..., ge=1, le=5, description="Abstraction level (1-5)")
    computational_complexity: int = Field(..., gt=0, description="Number of computational steps")
    concept_integration: ConceptIntegration = Field(..., description="Integration complexity")
    real_world_context: int = Field(..., ge=1, le=5, description="Real-world context level (1-5)")
    problem_solving_approach: ProblemApproach = Field(..., description="Problem-solving approach")

    def to_dict(self) -> dict:
        """Convert DifficultyDNA to dictionary format."""
        return {
            "bloom_level": self.bloom_level,
            "abstraction_level": self.abstraction_level,
            "computational_complexity": self.computational_complexity,
            "concept_integration": self.concept_integration.value,
            "real_world_context": self.real_world_context,
            "problem_solving_approach": self.problem_solving_approach.value
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DifficultyDNA":
        """Create DifficultyDNA from dictionary format."""
        return cls(
            bloom_level=data["bloom_level"],
            abstraction_level=data["abstraction_level"],
            computational_complexity=data["computational_complexity"],
            concept_integration=ConceptIntegration(data["concept_integration"]),
            real_world_context=data["real_world_context"],
            problem_solving_approach=ProblemApproach(data["problem_solving_approach"])
        )


class ConceptBase(BaseModel):
    """Base model for Concept with common fields."""
    name: str = Field(..., min_length=1, description="Concept name")
    subject: Subject = Field(..., description="Academic subject")
    class_level: int = Field(..., ge=8, le=12, description="Class level (8-12)")
    keywords: List[str] = Field(..., min_length=1, description="Related keywords")
    description: str = Field(..., min_length=1, description="Concept description")
    difficulty_dna: DifficultyDNA = Field(..., description="Multi-dimensional difficulty encoding")


class ConceptCreate(ConceptBase):
    """Model for creating a new concept."""
    pass


class Concept(ConceptBase):
    """
    Concept node in the knowledge graph.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Concept name
        subject: Academic subject
        class_level: Class level (8-12)
        keywords: List of related keywords
        description: Concept description
        difficulty_dna: Multi-dimensional difficulty encoding
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    def to_dict(self) -> dict:
        """Convert Concept to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject.value,
            "class_level": self.class_level,
            "keywords": self.keywords,
            "description": self.description,
            "difficulty_dna": self.difficulty_dna.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Concept":
        """Create Concept from dictionary format."""
        return cls(
            id=data["id"],
            name=data["name"],
            subject=Subject(data["subject"]),
            class_level=data["class_level"],
            keywords=data["keywords"],
            description=data["description"],
            difficulty_dna=DifficultyDNA.from_dict(data["difficulty_dna"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


class RelationshipCreate(BaseModel):
    """Model for creating a new relationship."""
    source_id: Optional[str] = Field(default=None, description="Source concept ID (optional, can be provided in URL path)")
    target_id: str = Field(..., description="Target concept ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")


class Relationship(BaseModel):
    """
    Relationship between concepts in the knowledge graph.
    
    Attributes:
        source_id: Source concept ID
        target_id: Target concept ID
        relationship_type: Type of relationship
        created_at: Creation timestamp
    """
    source_id: str = Field(..., description="Source concept ID")
    target_id: str = Field(..., description="Target concept ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    def to_dict(self) -> dict:
        """Convert Relationship to dictionary format."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type.value,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        """Create Relationship from dictionary format."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relationship_type=RelationshipType(data["relationship_type"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )


class DifficultyConstraints(BaseModel):
    """Difficulty constraints for a student persona."""
    max_bloom_level: int = Field(..., ge=1, le=6, description="Maximum Bloom's level")
    max_abstraction_level: int = Field(..., ge=1, le=5, description="Maximum abstraction level")
    max_computational_complexity: int = Field(..., gt=0, description="Maximum computational steps")
    allowed_concept_integration: List[ConceptIntegration] = Field(..., description="Allowed integration types")
    max_real_world_context: int = Field(..., ge=1, le=5, description="Maximum real-world context level")
    allowed_problem_approaches: List[ProblemApproach] = Field(..., description="Allowed problem approaches")


class StudentPersona(BaseModel):
    """
    Student persona profile for a specific class level.
    
    Attributes:
        class_level: Class level (8-12, or 13 for JEE mode)
        cognitive_maturity: Cognitive maturity level (1-5)
        reading_level: Flesch-Kincaid grade level
        vocabulary_complexity: Vocabulary complexity level
        technical_term_usage: Technical term usage level
        max_steps: Maximum computational steps
        max_time_minutes: Maximum time per question
        preferred_question_types: Preferred question types
        difficulty_constraints: Difficulty constraints
    """
    class_level: int = Field(..., ge=8, le=13, description="Class level (8-12, or 13 for JEE mode)")
    cognitive_maturity: int = Field(..., ge=1, le=5, description="Cognitive maturity level (1-5)")
    reading_level: int = Field(..., ge=8, le=16, description="Flesch-Kincaid grade level")
    vocabulary_complexity: VocabularyLevel = Field(..., description="Vocabulary complexity level")
    technical_term_usage: TechnicalLevel = Field(..., description="Technical term usage level")
    max_steps: int = Field(..., gt=0, description="Maximum computational steps")
    max_time_minutes: int = Field(..., gt=0, description="Maximum time per question")
    preferred_question_types: List[QuestionType] = Field(..., description="Preferred question types")
    difficulty_constraints: DifficultyConstraints = Field(..., description="Difficulty constraints")

    def to_dict(self) -> dict:
        """Convert StudentPersona to dictionary format."""
        return {
            "class_level": self.class_level,
            "cognitive_maturity": self.cognitive_maturity,
            "reading_level": self.reading_level,
            "vocabulary_complexity": self.vocabulary_complexity.value,
            "technical_term_usage": self.technical_term_usage.value,
            "max_steps": self.max_steps,
            "max_time_minutes": self.max_time_minutes,
            "preferred_question_types": [qt.value for qt in self.preferred_question_types],
            "difficulty_constraints": self.difficulty_constraints.model_dump()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StudentPersona":
        """Create StudentPersona from dictionary format."""
        return cls(
            class_level=data["class_level"],
            cognitive_maturity=data["cognitive_maturity"],
            reading_level=data["reading_level"],
            vocabulary_complexity=VocabularyLevel(data["vocabulary_complexity"]),
            technical_term_usage=TechnicalLevel(data["technical_term_usage"]),
            max_steps=data["max_steps"],
            max_time_minutes=data["max_time_minutes"],
            preferred_question_types=[QuestionType(qt) for qt in data["preferred_question_types"]],
            difficulty_constraints=DifficultyConstraints(**data["difficulty_constraints"])
        )


class QuestionBase(BaseModel):
    """Base model for Question with common fields."""
    concept_id: str = Field(..., description="Associated concept ID")
    question_text: str = Field(..., min_length=1, description="Question text")
    question_type: QuestionType = Field(..., description="Question type")
    difficulty_dna: DifficultyDNA = Field(..., description="Question difficulty encoding")
    options: Optional[List[str]] = Field(None, description="Options for MCQ")
    correct_answer: str = Field(..., min_length=1, description="Correct answer")
    explanation: str = Field(..., min_length=1, description="Answer explanation")
    estimated_time_minutes: int = Field(..., gt=0, description="Estimated time in minutes")


class QuestionCreate(QuestionBase):
    """Model for creating a new question."""
    pass


class Question(QuestionBase):
    """
    Generated question for a mathematical concept.
    
    Attributes:
        id: Unique identifier (UUID)
        concept_id: Associated concept ID
        question_text: Question text
        question_type: Question type (MCQ/numerical/subjective)
        difficulty_dna: Question difficulty encoding
        options: Options for MCQ (optional)
        correct_answer: Correct answer
        explanation: Answer explanation
        estimated_time_minutes: Estimated time in minutes
        created_at: Creation timestamp
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        """Validate that MCQ questions have options."""
        if info.data.get('question_type') == QuestionType.MCQ and not v:
            raise ValueError("MCQ questions must have options")
        return v

    def to_dict(self) -> dict:
        """Convert Question to dictionary format."""
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "difficulty_dna": self.difficulty_dna.to_dict(),
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "estimated_time_minutes": self.estimated_time_minutes,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Question":
        """Create Question from dictionary format."""
        return cls(
            id=data["id"],
            concept_id=data["concept_id"],
            question_text=data["question_text"],
            question_type=QuestionType(data["question_type"]),
            difficulty_dna=DifficultyDNA.from_dict(data["difficulty_dna"]),
            options=data.get("options"),
            correct_answer=data["correct_answer"],
            explanation=data["explanation"],
            estimated_time_minutes=data["estimated_time_minutes"],
            created_at=datetime.fromisoformat(data["created_at"])
        )


class PerformanceRecord(BaseModel):
    """
    Record of student performance on a question.
    
    Attributes:
        student_id: Student identifier
        concept_id: Associated concept ID
        question_difficulty: Difficulty of the question
        is_correct: Whether the answer was correct
        time_taken_seconds: Time taken in seconds
        timestamp: When the performance was recorded
    """
    student_id: str = Field(..., description="Student identifier")
    concept_id: str = Field(..., description="Associated concept ID")
    question_difficulty: DifficultyDNA = Field(..., description="Question difficulty")
    is_correct: bool = Field(..., description="Whether answer was correct")
    time_taken_seconds: int = Field(..., gt=0, description="Time taken in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Performance timestamp")


class ConceptFilters(BaseModel):
    """Filters for querying concepts."""
    subject: Optional[Subject] = Field(None, description="Filter by subject")
    class_level: Optional[int] = Field(None, ge=8, le=12, description="Filter by class level")
    keyword: Optional[str] = Field(None, description="Filter by keyword (fuzzy match)")
    min_bloom_level: Optional[int] = Field(None, ge=1, le=6, description="Minimum Bloom's level")
    max_bloom_level: Optional[int] = Field(None, ge=1, le=6, description="Maximum Bloom's level")
    min_abstraction_level: Optional[int] = Field(None, ge=1, le=5, description="Minimum abstraction level")
    max_abstraction_level: Optional[int] = Field(None, ge=1, le=5, description="Maximum abstraction level")
    min_computational_complexity: Optional[int] = Field(None, gt=0, description="Minimum computational complexity")
    max_computational_complexity: Optional[int] = Field(None, gt=0, description="Maximum computational complexity")
    min_real_world_context: Optional[int] = Field(None, ge=1, le=5, description="Minimum real-world context level")
    max_real_world_context: Optional[int] = Field(None, ge=1, le=5, description="Maximum real-world context level")
    concept_integration: Optional[ConceptIntegration] = Field(None, description="Filter by concept integration type")
    problem_solving_approach: Optional[ProblemApproach] = Field(None, description="Filter by problem-solving approach")
