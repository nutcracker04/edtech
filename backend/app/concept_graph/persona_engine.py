"""
PersonaEngine for managing student persona profiles.

This module provides:
- Persona profile management for Class 8-12 and JEE mode
- Persona retrieval and validation
- Question validation against persona constraints
"""

import json
import logging
import re
from typing import Optional
from .models import (
    StudentPersona,
    DifficultyConstraints,
    VocabularyLevel,
    TechnicalLevel,
    QuestionType,
    ConceptIntegration,
    ProblemApproach,
)

logger = logging.getLogger(__name__)


class PersonaEngine:
    """
    Engine for managing student persona profiles.
    
    Handles:
    - Loading persona profiles in memory
    - Retrieving personas by class level
    - Validating content against persona constraints
    """
    
    def __init__(self):
        """Initialize the PersonaEngine."""
        self.personas = {}
        self._initialize_personas()
    
    def _initialize_personas(self):
        """Initialize persona profiles in memory."""
        personas = self._get_default_personas()
        
        for persona in personas:
            self.personas[persona.class_level] = persona
            logger.info(f"Initialized persona for class level {persona.class_level}")
    
    def _get_default_personas(self) -> list[StudentPersona]:
        """
        Get default persona profiles for Class 8-12 and JEE mode.
        
        Returns:
            List of StudentPersona objects with predefined profiles
        """
        personas = []
        
        # Class 8: Concrete thinking, basic vocabulary, max 3-4 steps, 5-minute questions
        personas.append(StudentPersona(
            class_level=8,
            cognitive_maturity=2,
            reading_level=8,
            vocabulary_complexity=VocabularyLevel.BASIC,
            technical_term_usage=TechnicalLevel.MINIMAL,
            max_steps=4,
            max_time_minutes=5,
            preferred_question_types=[QuestionType.MCQ, QuestionType.NUMERICAL],
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=3,  # Up to Apply
                max_abstraction_level=2,  # Concrete
                max_computational_complexity=4,
                allowed_concept_integration=[ConceptIntegration.SINGLE],
                max_real_world_context=3,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP]
            )
        ))
        
        # Class 9: Developing abstraction, intermediate vocabulary, max 5-6 steps, 7-minute questions
        personas.append(StudentPersona(
            class_level=9,
            cognitive_maturity=3,
            reading_level=9,
            vocabulary_complexity=VocabularyLevel.INTERMEDIATE,
            technical_term_usage=TechnicalLevel.MINIMAL,
            max_steps=6,
            max_time_minutes=7,
            preferred_question_types=[QuestionType.MCQ, QuestionType.NUMERICAL, QuestionType.SUBJECTIVE],
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=4,  # Up to Analyze
                max_abstraction_level=3,
                max_computational_complexity=6,
                allowed_concept_integration=[ConceptIntegration.SINGLE, ConceptIntegration.MULTI_CONCEPT],
                max_real_world_context=3,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP]
            )
        ))
        
        # Class 10: Board exam focus, formal terminology, max 6-8 steps, 10-minute questions
        personas.append(StudentPersona(
            class_level=10,
            cognitive_maturity=3,
            reading_level=10,
            vocabulary_complexity=VocabularyLevel.INTERMEDIATE,
            technical_term_usage=TechnicalLevel.MODERATE,
            max_steps=8,
            max_time_minutes=10,
            preferred_question_types=[QuestionType.MCQ, QuestionType.NUMERICAL, QuestionType.SUBJECTIVE],
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=4,  # Up to Analyze
                max_abstraction_level=3,
                max_computational_complexity=8,
                allowed_concept_integration=[ConceptIntegration.SINGLE, ConceptIntegration.MULTI_CONCEPT],
                max_real_world_context=4,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP, ProblemApproach.PROOF]
            )
        ))
        
        # Class 11: Advanced abstraction, technical vocabulary, max 8-10 steps, 12-minute questions
        personas.append(StudentPersona(
            class_level=11,
            cognitive_maturity=4,
            reading_level=11,
            vocabulary_complexity=VocabularyLevel.ADVANCED,
            technical_term_usage=TechnicalLevel.MODERATE,
            max_steps=10,
            max_time_minutes=12,
            preferred_question_types=[QuestionType.MCQ, QuestionType.NUMERICAL, QuestionType.SUBJECTIVE],
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=5,  # Up to Evaluate
                max_abstraction_level=4,
                max_computational_complexity=10,
                allowed_concept_integration=[ConceptIntegration.SINGLE, ConceptIntegration.MULTI_CONCEPT, ConceptIntegration.CROSS_SUBJECT],
                max_real_world_context=4,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP, ProblemApproach.PROOF, ProblemApproach.EXPLORATORY]
            )
        ))
        
        # Class 12: Pre-university level, extensive technical terms, max 10-12 steps, 15-minute questions
        personas.append(StudentPersona(
            class_level=12,
            cognitive_maturity=5,
            reading_level=12,
            vocabulary_complexity=VocabularyLevel.ADVANCED,
            technical_term_usage=TechnicalLevel.EXTENSIVE,
            max_steps=12,
            max_time_minutes=15,
            preferred_question_types=[QuestionType.MCQ, QuestionType.NUMERICAL, QuestionType.SUBJECTIVE],
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=6,  # Up to Create
                max_abstraction_level=5,
                max_computational_complexity=12,
                allowed_concept_integration=[ConceptIntegration.SINGLE, ConceptIntegration.MULTI_CONCEPT, ConceptIntegration.CROSS_SUBJECT],
                max_real_world_context=5,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP, ProblemApproach.PROOF, ProblemApproach.EXPLORATORY]
            )
        ))
        
        # JEE Mode: Competitive exam constraints, complex multi-concept integration, max 15 steps, 3-minute MCQs
        # Using class_level 13 to represent JEE mode (beyond Class 12)
        personas.append(StudentPersona(
            class_level=13,  # Special value for JEE mode
            cognitive_maturity=5,
            reading_level=12,
            vocabulary_complexity=VocabularyLevel.ADVANCED,
            technical_term_usage=TechnicalLevel.EXTENSIVE,
            max_steps=15,
            max_time_minutes=3,  # JEE questions need to be solved quickly
            preferred_question_types=[QuestionType.MCQ],  # JEE is primarily MCQ
            difficulty_constraints=DifficultyConstraints(
                max_bloom_level=6,  # Up to Create
                max_abstraction_level=5,
                max_computational_complexity=15,
                allowed_concept_integration=[ConceptIntegration.SINGLE, ConceptIntegration.MULTI_CONCEPT, ConceptIntegration.CROSS_SUBJECT],
                max_real_world_context=5,
                allowed_problem_approaches=[ProblemApproach.DIRECT, ProblemApproach.MULTI_STEP, ProblemApproach.PROOF, ProblemApproach.EXPLORATORY]
            )
        ))
        
        return personas
    
    def get_persona(self, class_level: int) -> Optional[StudentPersona]:
        """
        Retrieve persona profile for a class level.
        
        Args:
            class_level: Class level (8-12) or 13 for JEE mode
            
        Returns:
            StudentPersona object if found, None otherwise
            
        Raises:
            ValueError: If class_level is invalid
        """
        if class_level < 8 or class_level > 13:
            raise ValueError(f"Invalid class level: {class_level}. Must be between 8 and 13 (13 for JEE mode)")
        
        persona = self.personas.get(class_level)
        
        if persona:
            logger.debug(f"Retrieved persona for class level {class_level}")
            return persona
        else:
            logger.warning(f"Persona for class level {class_level} not found")
            return None
    
    def reload_personas(self):
        """
        Reload all persona profiles from defaults.
        
        This will overwrite any existing personas in memory with default values.
        """
        personas = self._get_default_personas()
        
        for persona in personas:
            self.personas[persona.class_level] = persona
            logger.info(f"Reloaded persona for class level {persona.class_level}")
    
    def update_persona(self, persona: StudentPersona):
        """
        Update a persona profile in Redis.
        
        Args:
            persona: StudentPersona object to update
        """
        self.personas[persona.class_level] = persona
        logger.info(f"Updated persona for class level {persona.class_level}")
    
    def delete_persona(self, class_level: int):
        """
        Delete a persona profile from memory.
        
        Args:
            class_level: Class level of the persona to delete
        """
        if class_level in self.personas:
            del self.personas[class_level]
            logger.info(f"Deleted persona for class level {class_level}")
        else:
            logger.warning(f"Persona for class level {class_level} not found")
    
    def calculate_reading_level(self, text: str) -> float:
        """
        Calculate Flesch-Kincaid reading level of text.
        
        The Flesch-Kincaid Grade Level formula:
        0.39 * (total words / total sentences) + 11.8 * (total syllables / total words) - 15.59
        
        Args:
            text: Text to analyze
            
        Returns:
            Flesch-Kincaid grade level (e.g., 8.5 means 8th-9th grade level)
        """
        if not text or not text.strip():
            return 0.0
        
        # Count sentences (split by . ! ?)
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s for s in sentences if s.strip()]
        total_sentences = len(sentences) if sentences else 1
        
        # Count words (split by whitespace)
        words = text.split()
        words = [w for w in words if w.strip()]
        total_words = len(words)
        
        if total_words == 0:
            return 0.0
        
        # Count syllables
        total_syllables = sum(self._count_syllables(word) for word in words)
        
        # Calculate Flesch-Kincaid Grade Level
        avg_words_per_sentence = total_words / total_sentences
        avg_syllables_per_word = total_syllables / total_words
        
        grade_level = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59
        
        # Ensure non-negative result
        return max(0.0, grade_level)
    
    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word using a simple heuristic.
        
        Args:
            word: Word to count syllables in
            
        Returns:
            Estimated syllable count
        """
        # Remove non-alphabetic characters and convert to lowercase
        word = re.sub(r'[^a-zA-Z]', '', word).lower()
        
        if not word:
            return 0
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent 'e' at the end
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        # Every word has at least one syllable
        return max(1, syllable_count)
    
    def check_vocabulary(self, text: str, persona: StudentPersona) -> bool:
        """
        Check if vocabulary matches persona level.
        
        This method checks vocabulary complexity by:
        1. Calculating the reading level of the text
        2. Comparing it against the persona's reading level
        3. Checking for overly complex words based on persona vocabulary level
        
        Args:
            text: Text to check
            persona: Student persona with vocabulary constraints
            
        Returns:
            True if vocabulary is appropriate for persona, False otherwise
        """
        if not text or not text.strip():
            return True
        
        # Calculate reading level
        reading_level = self.calculate_reading_level(text)
        
        # Allow some tolerance (±1 grade level)
        max_allowed_reading_level = persona.reading_level + 1
        
        if reading_level > max_allowed_reading_level:
            logger.debug(f"Text reading level {reading_level:.1f} exceeds persona limit {max_allowed_reading_level}")
            return False
        
        # Check for overly complex words based on vocabulary level
        words = text.split()
        complex_word_threshold = self._get_complex_word_threshold(persona.vocabulary_complexity)
        
        complex_word_count = 0
        for word in words:
            # Remove punctuation for syllable counting
            clean_word = re.sub(r'[^a-zA-Z]', '', word)
            if clean_word:
                syllables = self._count_syllables(clean_word)
                if syllables >= complex_word_threshold:
                    complex_word_count += 1
        
        # Allow up to 20% complex words for basic, 30% for intermediate, 40% for advanced
        max_complex_ratio = {
            VocabularyLevel.BASIC: 0.20,
            VocabularyLevel.INTERMEDIATE: 0.30,
            VocabularyLevel.ADVANCED: 0.40
        }
        
        if len(words) > 0:
            complex_ratio = complex_word_count / len(words)
            allowed_ratio = max_complex_ratio.get(persona.vocabulary_complexity, 0.30)
            
            if complex_ratio > allowed_ratio:
                logger.debug(f"Complex word ratio {complex_ratio:.2f} exceeds limit {allowed_ratio:.2f}")
                return False
        
        return True
    
    def _get_complex_word_threshold(self, vocabulary_level: VocabularyLevel) -> int:
        """
        Get syllable threshold for complex words based on vocabulary level.
        
        Args:
            vocabulary_level: Vocabulary complexity level
            
        Returns:
            Syllable count threshold (words with this many or more syllables are "complex")
        """
        thresholds = {
            VocabularyLevel.BASIC: 3,        # 3+ syllables is complex for basic
            VocabularyLevel.INTERMEDIATE: 4,  # 4+ syllables is complex for intermediate
            VocabularyLevel.ADVANCED: 5       # 5+ syllables is complex for advanced
        }
        return thresholds.get(vocabulary_level, 4)
    
    def validate_question(self, question_text: str, persona: StudentPersona) -> dict:
        """
        Validate question text against all persona constraints.
        
        This method performs comprehensive validation including:
        1. Reading level check
        2. Vocabulary complexity check
        3. Text length appropriateness
        
        Args:
            question_text: Question text to validate
            persona: Student persona with constraints
            
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "reading_level": float,
                "reading_level_ok": bool,
                "vocabulary_ok": bool,
                "errors": list of error messages
            }
        """
        result = {
            "valid": True,
            "reading_level": 0.0,
            "reading_level_ok": True,
            "vocabulary_ok": True,
            "errors": []
        }
        
        if not question_text or not question_text.strip():
            result["valid"] = False
            result["errors"].append("Question text is empty")
            return result
        
        # Check reading level
        reading_level = self.calculate_reading_level(question_text)
        result["reading_level"] = reading_level
        
        max_allowed_reading_level = persona.reading_level + 1
        if reading_level > max_allowed_reading_level:
            result["valid"] = False
            result["reading_level_ok"] = False
            result["errors"].append(
                f"Reading level {reading_level:.1f} exceeds persona limit {max_allowed_reading_level}"
            )
        
        # Check vocabulary
        vocabulary_ok = self.check_vocabulary(question_text, persona)
        result["vocabulary_ok"] = vocabulary_ok
        
        if not vocabulary_ok:
            result["valid"] = False
            result["errors"].append(
                f"Vocabulary complexity exceeds {persona.vocabulary_complexity.value} level"
            )
        
        # Check text length (very long questions may be inappropriate)
        word_count = len(question_text.split())
        max_words = persona.max_time_minutes * 50  # Rough estimate: 50 words per minute reading
        
        if word_count > max_words:
            result["valid"] = False
            result["errors"].append(
                f"Question length ({word_count} words) exceeds recommended maximum ({max_words} words)"
            )
        
        return result
