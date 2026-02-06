"""
Example usage of the Concept Knowledge Graph system.

This module demonstrates how to:
- Create concepts with difficulty DNA
- Serialize and deserialize data
- Work with different model types
"""

from app.concept_graph.models import (
    DifficultyDNA,
    Concept,
    Relationship,
    StudentPersona,
    Question,
    ConceptIntegration,
    ProblemApproach,
    RelationshipType,
    QuestionType,
    VocabularyLevel,
    TechnicalLevel,
    DifficultyConstraints,
)


def example_create_concept():
    """Example: Create a mathematical concept."""
    print("\n=== Creating a Concept ===")
    
    # Create difficulty DNA encoding
    dna = DifficultyDNA(
        bloom_level=3,  # Apply level
        abstraction_level=2,  # Moderately concrete
        computational_complexity=5,  # 5 steps
        concept_integration=ConceptIntegration.SINGLE,
        real_world_context=3,  # Moderate real-world connection
        problem_solving_approach=ProblemApproach.MULTI_STEP
    )
    
    # Create concept
    concept = Concept(
        name="Quadratic Equations",
        class_level=10,
        keywords=["algebra", "equations", "quadratic", "polynomial"],
        description="Solving quadratic equations using factorization, completing the square, and quadratic formula",
        difficulty_dna=dna
    )
    
    print(f"Created concept: {concept.name}")
    print(f"Class Level: {concept.class_level}")
    print(f"Bloom Level: {concept.difficulty_dna.bloom_level}")
    print(f"Concept ID: {concept.id}")
    
    return concept


def example_serialize_concept(concept):
    """Example: Serialize and deserialize a concept."""
    print("\n=== Serializing Concept ===")
    
    # Serialize to dict
    concept_dict = concept.to_dict()
    print(f"Serialized to dict with {len(concept_dict)} fields")
    print(f"Difficulty DNA: {concept_dict['difficulty_dna']}")
    
    # Deserialize from dict
    restored_concept = Concept.from_dict(concept_dict)
    print(f"Restored concept: {restored_concept.name}")
    print(f"IDs match: {restored_concept.id == concept.id}")
    
    return restored_concept


def example_create_relationship():
    """Example: Create a relationship between concepts."""
    print("\n=== Creating Relationships ===")
    
    # Create two concepts
    dna_basic = DifficultyDNA(
        bloom_level=2,
        abstraction_level=1,
        computational_complexity=3,
        concept_integration=ConceptIntegration.SINGLE,
        real_world_context=2,
        problem_solving_approach=ProblemApproach.DIRECT
    )
    
    concept_linear = Concept(
        name="Linear Equations",
        class_level=8,
        keywords=["algebra", "equations", "linear"],
        description="Solving linear equations in one variable",
        difficulty_dna=dna_basic
    )
    
    dna_advanced = DifficultyDNA(
        bloom_level=3,
        abstraction_level=2,
        computational_complexity=5,
        concept_integration=ConceptIntegration.SINGLE,
        real_world_context=3,
        problem_solving_approach=ProblemApproach.MULTI_STEP
    )
    
    concept_quadratic = Concept(
        name="Quadratic Equations",
        class_level=10,
        keywords=["algebra", "equations", "quadratic"],
        description="Solving quadratic equations",
        difficulty_dna=dna_advanced
    )
    
    # Create prerequisite relationship
    relationship = Relationship(
        source_id=concept_linear.id,
        target_id=concept_quadratic.id,
        relationship_type=RelationshipType.PREREQUISITE
    )
    
    print(f"Created relationship: {concept_linear.name} -> {concept_quadratic.name}")
    print(f"Relationship type: {relationship.relationship_type.value}")
    
    return relationship


def example_create_student_persona():
    """Example: Create a student persona for Class 10."""
    print("\n=== Creating Student Persona ===")
    
    # Define difficulty constraints
    constraints = DifficultyConstraints(
        max_bloom_level=4,  # Up to Analyze level
        max_abstraction_level=3,  # Moderate abstraction
        max_computational_complexity=8,  # Up to 8 steps
        allowed_concept_integration=[
            ConceptIntegration.SINGLE,
            ConceptIntegration.MULTI_CONCEPT
        ],
        max_real_world_context=4,
        allowed_problem_approaches=[
            ProblemApproach.DIRECT,
            ProblemApproach.MULTI_STEP
        ]
    )
    
    # Create persona
    persona = StudentPersona(
        class_level=10,
        cognitive_maturity=3,
        reading_level=10,
        vocabulary_complexity=VocabularyLevel.INTERMEDIATE,
        technical_term_usage=TechnicalLevel.MODERATE,
        max_steps=8,
        max_time_minutes=10,
        preferred_question_types=[
            QuestionType.MCQ,
            QuestionType.NUMERICAL
        ],
        difficulty_constraints=constraints
    )
    
    print(f"Created persona for Class {persona.class_level}")
    print(f"Reading level: Grade {persona.reading_level}")
    print(f"Max steps: {persona.max_steps}")
    print(f"Max Bloom level: {persona.difficulty_constraints.max_bloom_level}")
    
    return persona


def example_create_question():
    """Example: Create a question."""
    print("\n=== Creating Question ===")
    
    # Create difficulty DNA for question
    dna = DifficultyDNA(
        bloom_level=3,
        abstraction_level=2,
        computational_complexity=4,
        concept_integration=ConceptIntegration.SINGLE,
        real_world_context=3,
        problem_solving_approach=ProblemApproach.MULTI_STEP
    )
    
    # Create MCQ question
    question = Question(
        concept_id="quadratic-equations-id",
        question_text="Solve the equation x² - 5x + 6 = 0",
        question_type=QuestionType.MCQ,
        difficulty_dna=dna,
        options=["x = 1, 6", "x = 2, 3", "x = -2, -3", "x = 1, -6"],
        correct_answer="x = 2, 3",
        explanation="Factor the equation: (x-2)(x-3) = 0, so x = 2 or x = 3",
        estimated_time_minutes=5
    )
    
    print(f"Created question: {question.question_text}")
    print(f"Type: {question.question_type.value}")
    print(f"Options: {len(question.options)}")
    print(f"Estimated time: {question.estimated_time_minutes} minutes")
    
    return question


def run_all_examples():
    """Run all examples."""
    print("=" * 60)
    print("Concept Knowledge Graph - Usage Examples")
    print("=" * 60)
    
    # Example 1: Create concept
    concept = example_create_concept()
    
    # Example 2: Serialize/deserialize
    restored_concept = example_serialize_concept(concept)
    
    # Example 3: Create relationships
    relationship = example_create_relationship()
    
    # Example 4: Create student persona
    persona = example_create_student_persona()
    
    # Example 5: Create question
    question = example_create_question()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
