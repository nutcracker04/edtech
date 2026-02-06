"""
Question Generator for adaptive question generation using NVIDIA AI API.

This module provides the QuestionGenerator class for:
- Generating questions adapted to concept, persona, and difficulty
- Building prompts with persona and DNA constraints
- Validating generated questions against persona constraints
- Regenerating questions if constraints are violated
"""

import logging
from typing import Optional
import json
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from .models import (
    Concept,
    StudentPersona,
    Question,
    QuestionCreate,
    QuestionType,
    DifficultyDNA,
)
from .graph_manager import ConceptGraphManager
from .persona_engine import PersonaEngine
from .encoder import DifficultyDNAEncoder
from .config import concept_graph_settings

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Generator for adaptive questions using NVIDIA AI API.
    
    Handles:
    - Question generation with persona and difficulty calibration
    - Prompt engineering with concept details and constraints
    - Question validation against persona constraints
    - Regeneration on constraint violations
    """
    
    def __init__(self):
        """Initialize the QuestionGenerator."""
        if not concept_graph_settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA API key not configured. Set CONCEPT_GRAPH_NVIDIA_API_KEY in .env"
            )
        
        self.client = ChatNVIDIA(
            model=concept_graph_settings.nvidia_model,
            api_key=concept_graph_settings.nvidia_api_key,
            temperature=concept_graph_settings.nvidia_temperature,
            top_p=concept_graph_settings.nvidia_top_p,
            max_completion_tokens=concept_graph_settings.nvidia_max_tokens,
        )
        
        self.graph_manager = ConceptGraphManager()
        self.persona_engine = PersonaEngine()
        self.encoder = DifficultyDNAEncoder()
    
    def generate_question(
        self,
        concept_id: str,
        persona: StudentPersona,
        difficulty_adjustment: float = 0.0,
        question_type: QuestionType = QuestionType.MCQ
    ) -> Question:
        """
        Generate a question for a concept adapted to persona.
        
        Args:
            concept_id: ID of the concept to generate question for
            persona: Student persona with constraints
            difficulty_adjustment: Adjustment factor (-1.0 to +1.0) to modify difficulty
            question_type: Type of question to generate (MCQ/numerical/subjective)
            
        Returns:
            Generated Question object
            
        Raises:
            ValueError: If concept not found or required inputs missing
            Exception: If generation fails after max attempts
            
        Requirements: 6.1, 6.5
        """
        # Validate required inputs
        if not concept_id:
            raise ValueError("concept_id is required")
        if not persona:
            raise ValueError("persona is required")
        
        # Retrieve concept
        concept = self.graph_manager.get_concept(concept_id)
        if not concept:
            raise ValueError(f"Concept not found: {concept_id}")
        
        # Adjust difficulty DNA based on adjustment factor
        target_dna = self.encoder.adjust_difficulty(
            concept.difficulty_dna,
            difficulty_adjustment
        )
        
        # Ensure adjusted DNA fits persona constraints
        if not self.encoder.fits_persona(target_dna, persona):
            logger.warning(
                f"Adjusted DNA doesn't fit persona, using concept's original DNA"
            )
            target_dna = concept.difficulty_dna
        
        # Generate question with regeneration on failure
        question = self.regenerate_if_invalid(
            concept,
            persona,
            target_dna,
            question_type,
            max_attempts=concept_graph_settings.max_regeneration_attempts
        )
        
        return question
    
    def build_prompt(
        self,
        concept: Concept,
        persona: StudentPersona,
        target_dna: DifficultyDNA,
        question_type: QuestionType
    ) -> str:
        """
        Build NVIDIA AI API prompt with persona and difficulty constraints.
        
        Constructs a detailed prompt that includes:
        - Concept details (name, description, keywords)
        - Persona constraints (reading level, vocabulary, max steps)
        - Target difficulty DNA dimensions
        - Question type and format requirements
        
        Args:
            concept: Concept to generate question for
            persona: Student persona with constraints
            target_dna: Target difficulty DNA for the question
            question_type: Type of question to generate
            
        Returns:
            Formatted prompt string for NVIDIA AI API
            
        Requirements: 6.1, 6.5
        """
        # Build DNA description
        dna_description = self._format_dna_description(target_dna)
        
        # Build persona constraints description
        constraints_description = self._format_persona_constraints(persona)
        
        # Build question format specification
        format_spec = self._format_question_spec(question_type, persona)
        
        # Get subject name for the prompt
        subject_name = concept.subject.value.replace("-", " ").title()
        
        # Construct the prompt
        prompt = f"""You are a {subject_name} question generator for Class {persona.class_level} students.

CONCEPT INFORMATION:
- Subject: {subject_name}
- Concept: {concept.name}
- Description: {concept.description}
- Keywords: {', '.join(concept.keywords)}
- Class Level: {concept.class_level}

TARGET DIFFICULTY DNA:
{dna_description}

STUDENT PERSONA CONSTRAINTS:
{constraints_description}

QUESTION REQUIREMENTS:
1. Test understanding of {concept.name} in {subject_name}
2. Use language appropriate for Class {persona.class_level} students
3. Match the target difficulty DNA dimensions specified above
4. Require approximately {target_dna.computational_complexity} computational steps
5. Match Bloom's level {target_dna.bloom_level} cognitive complexity
6. Use {target_dna.problem_solving_approach.value} problem-solving approach
7. Question type: {question_type.value}

{format_spec}

CRITICAL CONSTRAINTS:
- Reading level must not exceed grade {persona.reading_level}
- Vocabulary must be {persona.vocabulary_complexity.value} level
- Technical terms: {persona.technical_term_usage.value} usage
- Maximum computational steps: {persona.max_steps}
- Estimated time: {persona.max_time_minutes} minutes maximum

Generate a single {subject_name} question that meets ALL requirements above. Return ONLY valid JSON in this exact format (no markdown, no code blocks):

{{
  "question_text": "The question text here",
  "question_type": "{question_type.value}",
  "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
  "correct_answer": "A",
  "explanation": "Detailed explanation of the correct answer",
  "estimated_time_minutes": {persona.max_time_minutes},
  "difficulty_dna": {{
    "bloom_level": {target_dna.bloom_level},
    "abstraction_level": {target_dna.abstraction_level},
    "computational_complexity": {target_dna.computational_complexity},
    "concept_integration": "{target_dna.concept_integration.value}",
    "real_world_context": {target_dna.real_world_context},
    "problem_solving_approach": "{target_dna.problem_solving_approach.value}"
  }}
}}

Note: 
- For MCQ questions, provide 4 options as strings. The correct_answer should be "A", "B", "C", or "D" indicating which option is correct.
- For numerical or subjective questions, set "options" to null."""
        
        return prompt
    
    def _format_dna_description(self, dna: DifficultyDNA) -> str:
        """Format difficulty DNA into human-readable description."""
        bloom_levels = {
            1: "Remember (recall facts)",
            2: "Understand (explain concepts)",
            3: "Apply (use in new situations)",
            4: "Analyze (break down and examine)",
            5: "Evaluate (make judgments)",
            6: "Create (produce new work)"
        }
        
        return f"""- Bloom's Level: {dna.bloom_level} - {bloom_levels.get(dna.bloom_level, 'Unknown')}
- Abstraction Level: {dna.abstraction_level}/5 (1=concrete, 5=highly abstract)
- Computational Complexity: {dna.computational_complexity} steps
- Concept Integration: {dna.concept_integration.value}
- Real-world Context: {dna.real_world_context}/5
- Problem-solving Approach: {dna.problem_solving_approach.value}"""
    
    def _format_persona_constraints(self, persona: StudentPersona) -> str:
        """Format persona constraints into human-readable description."""
        return f"""- Class Level: {persona.class_level}
- Cognitive Maturity: {persona.cognitive_maturity}/5
- Reading Level: Grade {persona.reading_level}
- Vocabulary: {persona.vocabulary_complexity.value}
- Technical Terms: {persona.technical_term_usage.value}
- Maximum Steps: {persona.max_steps}
- Maximum Time: {persona.max_time_minutes} minutes
- Preferred Question Types: {', '.join([qt.value for qt in persona.preferred_question_types])}"""
    
    def _format_question_spec(
        self,
        question_type: QuestionType,
        persona: StudentPersona
    ) -> str:
        """Format question type-specific requirements."""
        if question_type == QuestionType.MCQ:
            return """QUESTION FORMAT (MCQ):
- Provide 4 options (A, B, C, D)
- Exactly one correct answer
- Distractors should be plausible but clearly incorrect
- Options should be of similar length and complexity
- Avoid "all of the above" or "none of the above" options"""
        
        elif question_type == QuestionType.NUMERICAL:
            return """QUESTION FORMAT (Numerical):
- Question should require a numerical answer
- Provide the exact numerical value as correct_answer
- Include units if applicable
- Explanation should show step-by-step solution
- Set options to null"""
        
        else:  # SUBJECTIVE
            return """QUESTION FORMAT (Subjective):
- Question should require written explanation or proof
- Provide a model answer as correct_answer
- Explanation should include key points to cover
- Set options to null
- Question should test deeper understanding"""
    
    def validate_generated_question(
        self,
        question: Question,
        persona: StudentPersona
    ) -> dict:
        """
        Validate generated question against persona constraints.
        
        Checks:
        - Question text reading level and vocabulary
        - Difficulty DNA fits persona constraints
        - Estimated time within persona limits
        - Question type is preferred by persona
        
        Args:
            question: Generated question to validate
            persona: Student persona with constraints
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "errors": list of error messages,
                "warnings": list of warning messages
            }
            
        Requirements: 6.6
        """
        errors = []
        warnings = []
        
        # Validate question text against persona
        text_validation = self.persona_engine.validate_question(
            question.question_text,
            persona
        )
        
        if not text_validation["valid"]:
            errors.extend(text_validation["errors"])
        
        # Validate difficulty DNA fits persona constraints
        if not self.encoder.fits_persona(question.difficulty_dna, persona):
            errors.append(
                "Question difficulty DNA exceeds persona constraints"
            )
        
        # Validate estimated time
        if question.estimated_time_minutes > persona.max_time_minutes:
            errors.append(
                f"Estimated time ({question.estimated_time_minutes} min) exceeds "
                f"persona limit ({persona.max_time_minutes} min)"
            )
        
        # Check if question type is preferred (warning only)
        if question.question_type not in persona.preferred_question_types:
            warnings.append(
                f"Question type {question.question_type.value} not in persona's "
                f"preferred types: {[qt.value for qt in persona.preferred_question_types]}"
            )
        
        # Validate MCQ has options
        if question.question_type == QuestionType.MCQ:
            if not question.options or len(question.options) < 2:
                errors.append("MCQ question must have at least 2 options")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def regenerate_if_invalid(
        self,
        concept: Concept,
        persona: StudentPersona,
        target_dna: DifficultyDNA,
        question_type: QuestionType,
        max_attempts: int = 3
    ) -> Question:
        """
        Generate question with regeneration on constraint violation.
        
        Attempts to generate a valid question up to max_attempts times.
        If all attempts fail, raises an exception with details.
        
        Args:
            concept: Concept to generate question for
            persona: Student persona with constraints
            target_dna: Target difficulty DNA
            question_type: Type of question to generate
            max_attempts: Maximum number of generation attempts
            
        Returns:
            Valid Question object
            
        Raises:
            Exception: If all attempts fail to generate valid question
            
        Requirements: 6.7
        """
        last_errors = []
        
        for attempt in range(1, max_attempts + 1):
            logger.info(
                f"Question generation attempt {attempt}/{max_attempts} for concept {concept.id}"
            )
            
            try:
                # Build prompt
                prompt = self.build_prompt(concept, persona, target_dna, question_type)
                
                # Call NVIDIA AI API with streaming
                full_response = ""
                for chunk in self.client.stream(
                    [{"role": "user", "content": prompt}],
                    chat_template_kwargs={"thinking": True}
                ):
                    if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
                        # Optionally log reasoning content
                        pass
                    full_response += chunk.content
                
                # Extract content
                content = full_response.strip()
                
                # Remove markdown code blocks if present
                if content.startswith("```json"):
                    content = content.replace("```json\n", "").replace("```", "")
                elif content.startswith("```"):
                    content = content.replace("```\n", "").replace("```", "")
                
                # Parse JSON response
                question_data = json.loads(content)
                
                # Create Question object
                question = Question(
                    concept_id=concept.id,
                    question_text=question_data["question_text"],
                    question_type=QuestionType(question_data["question_type"]),
                    difficulty_dna=DifficultyDNA.from_dict(question_data["difficulty_dna"]),
                    options=question_data.get("options"),
                    correct_answer=question_data["correct_answer"],
                    explanation=question_data["explanation"],
                    estimated_time_minutes=question_data["estimated_time_minutes"]
                )
                
                # Validate generated question
                validation = self.validate_generated_question(question, persona)
                
                if validation["valid"]:
                    logger.info(
                        f"Successfully generated valid question on attempt {attempt}"
                    )
                    if validation["warnings"]:
                        logger.warning(
                            f"Question has warnings: {', '.join(validation['warnings'])}"
                        )
                    return question
                else:
                    last_errors = validation["errors"]
                    logger.warning(
                        f"Attempt {attempt} generated invalid question: "
                        f"{', '.join(validation['errors'])}"
                    )
                    
                    # If not last attempt, continue to next iteration
                    if attempt < max_attempts:
                        continue
                
            except json.JSONDecodeError as e:
                last_errors = [f"Failed to parse NVIDIA AI API response as JSON: {str(e)}"]
                logger.error(f"Attempt {attempt} JSON parse error: {str(e)}")
                if attempt < max_attempts:
                    continue
            
            except Exception as e:
                last_errors = [f"Question generation error: {str(e)}"]
                logger.error(f"Attempt {attempt} generation error: {str(e)}")
                if attempt < max_attempts:
                    continue
        
        # All attempts failed
        error_msg = (
            f"Failed to generate valid question after {max_attempts} attempts. "
            f"Last errors: {', '.join(last_errors)}"
        )
        logger.error(error_msg)
        raise Exception(error_msg)
