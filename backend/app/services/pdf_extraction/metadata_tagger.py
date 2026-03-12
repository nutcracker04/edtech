"""
MetadataTagger component for applying hierarchical metadata to questions.

This module enriches LinkedQuestion objects with hierarchical metadata extracted
from the document structure and context. It implements Design Component 5.
"""

import logging
from typing import Optional

try:
    from .models import (
        LinkedQuestion,
        TaggedQuestion,
        BookMetadata,
        DocumentStructure,
        DifficultyLevel,
        QuestionType,
        Option,
    )
except ImportError:
    # Fallback for direct script execution
    from models import (
        LinkedQuestion,
        TaggedQuestion,
        BookMetadata,
        DocumentStructure,
        DifficultyLevel,
        QuestionType,
        Option,
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentContext:
    """
    Context information about the document structure for metadata tagging.
    
    This class provides the hierarchical context needed to tag questions with
    proper metadata (subject, chapter, topic, etc.).
    """
    
    def __init__(self, structure: DocumentStructure):
        """
        Initialize DocumentContext from DocumentStructure.
        
        Args:
            structure: DocumentStructure containing book metadata and hierarchy
        """
        self.structure = structure
        self.metadata = structure.metadata
        
        # Create lookup maps for efficient access
        self._chapter_map = {
            chapter.title: chapter for chapter in structure.chapters
        }
        
        self._topic_map = {}
        for chapter in structure.chapters:
            for topic in chapter.topics:
                # Key: (chapter_title, topic_title)
                self._topic_map[(chapter.title, topic.title)] = topic
    
    def get_chapter(self, chapter_title: str):
        """Get chapter by title."""
        return self._chapter_map.get(chapter_title)
    
    def get_topic(self, chapter_title: str, topic_title: str):
        """Get topic by chapter and topic title."""
        return self._topic_map.get((chapter_title, topic_title))


class MetadataTagger:
    """
    Applies hierarchical metadata tags to questions.
    
    This component enriches LinkedQuestion objects with complete metadata including:
    - Hierarchical structure (subject → chapter → topic → sub_topic)
    - Difficulty level inference
    - Content-based tags
    - Metadata validation
    
    Implements Design Component 5.
    """
    
    def __init__(self, config=None):
        """
        Initialize MetadataTagger.
        
        Args:
            config: Optional configuration object
        """
        try:
            from .document_processor import get_config
        except ImportError:
            from document_processor import get_config
        
        self.config = config or get_config()
        logger.info("MetadataTagger initialized")
    
    def apply_metadata(
        self,
        question: LinkedQuestion,
        context: DocumentContext
    ) -> TaggedQuestion:
        """
        Apply all metadata tags to a question.
        
        This method enriches a LinkedQuestion with complete hierarchical metadata
        extracted from the document context. It applies:
        - Subject, chapter, topic, sub_topic hierarchy
        - Grade level information
        - Question type classification
        - Difficulty level (placeholder for now)
        - Content tags (placeholder for now)
        
        Preconditions:
        - question is a valid LinkedQuestion
        - context contains valid DocumentStructure
        - question.raw_question has chapter_context and topic_context
        
        Postconditions:
        - Returns TaggedQuestion with all required metadata fields populated
        - All metadata fields are non-null (Property 7)
        - Metadata is validated for completeness
        
        Args:
            question: LinkedQuestion object to enrich
            context: DocumentContext with structure information
            
        Returns:
            TaggedQuestion with complete metadata
            
        Raises:
            ValueError: If required metadata cannot be extracted
        """
        raw_q = question.raw_question
        
        logger.debug(f"Applying metadata to question {raw_q.question_number}")
        
        # Extract hierarchical metadata from context
        chapter = context.get_chapter(raw_q.chapter_context)
        if not chapter:
            raise ValueError(
                f"Chapter '{raw_q.chapter_context}' not found in document structure"
            )
        
        topic = context.get_topic(raw_q.chapter_context, raw_q.topic_context)
        if not topic:
            raise ValueError(
                f"Topic '{raw_q.topic_context}' not found in chapter '{raw_q.chapter_context}'"
            )
        
        # Generate IDs for hierarchical entities
        subject_id = self._generate_subject_id(context.metadata.subject)
        chapter_id = self._generate_chapter_id(chapter.chapter_number)
        topic_id = self._generate_topic_id(chapter.chapter_number, raw_q.topic_context)
        
        # Determine question type
        answer_type = self._identify_question_type(question)
        
        # Convert options to Option objects
        options = []
        if raw_q.options:
            for i, opt_text in enumerate(raw_q.options):
                label = chr(65 + i)  # A, B, C, D, ...
                options.append(Option(text=opt_text, label=label))
        
        # Determine correct answer
        correct_answer = question.answer_key or ""
        
        # Extract image URLs (placeholder - will be populated by DatabaseWriter)
        images = [img.path for img in raw_q.images]
        
        # Create TaggedQuestion with placeholder difficulty
        tagged = TaggedQuestion(
            question=raw_q.question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=question.explanation,
            hint=question.hint,
            difficulty=DifficultyLevel.MEDIUM,  # Temporary - will be inferred below
            topic=raw_q.topic_context,
            topic_id=topic_id,
            chapter=raw_q.chapter_context,
            chapter_id=chapter_id,
            subject=context.metadata.subject,
            subject_id=subject_id,
            grade_level=[context.metadata.grade_level],
            tags=[],  # Temporary - will be extracted below
            source=context.metadata.title,
            answer_type=answer_type,
            images=images,
            tables=raw_q.tables,
            sub_topic=raw_q.sub_topic_context,
        )
        
        # Infer difficulty level based on question content
        tagged.difficulty = self.infer_difficulty(tagged)
        
        # Extract content-based tags
        tagged.tags = self.extract_tags(tagged)
        
        # Validate metadata completeness (Property 7)
        self._validate_metadata_completeness(tagged)
        
        logger.debug(
            f"Metadata applied to question {raw_q.question_number}: "
            f"{tagged.subject} > {tagged.chapter} > {tagged.topic}"
        )
        
        return tagged
    
    def _identify_question_type(self, question: LinkedQuestion) -> QuestionType:
        """
        Identify the type of question based on its content.
        
        Determines whether the question is:
        - MCQ (single or multiple choice)
        - Integer answer
        - Numerical answer
        - Subjective
        
        Args:
            question: LinkedQuestion to classify
            
        Returns:
            QuestionType enum value
        """
        raw_q = question.raw_question
        
        # If has options, it's MCQ
        if raw_q.options:
            # For now, assume single choice
            # Could be enhanced to detect multiple choice based on answer format
            return QuestionType.MCQ_SINGLE
        
        # Check answer key for type hints
        if question.answer_key:
            answer = question.answer_key.strip().lower()
            
            # Check if answer is an integer
            try:
                int(answer)
                return QuestionType.INTEGER
            except ValueError:
                pass
            
            # Check if answer is numerical (float)
            try:
                float(answer)
                return QuestionType.NUMERICAL
            except ValueError:
                pass
        
        # Default to subjective
        return QuestionType.SUBJECTIVE
    def infer_difficulty(self, question: TaggedQuestion) -> DifficultyLevel:
        """
        Infer difficulty level from question content.

        Analyzes the question text, options, and other content to determine
        the difficulty level. Uses heuristics based on:
        - Question length and complexity
        - Presence of mathematical symbols or formulas
        - Number of concepts involved
        - Cognitive level (recall vs. application vs. analysis)

        Args:
            question: TaggedQuestion to analyze

        Returns:
            DifficultyLevel enum value (EASY, MEDIUM, or HARD)
        """
        question_text = question.question.lower()

        # Initialize difficulty score (0-100)
        difficulty_score = 50  # Start at medium

        # Factor 1: Question length
        # Longer questions tend to be more complex
        word_count = len(question_text.split())
        if word_count < 15:
            difficulty_score -= 10
        elif word_count > 40:
            difficulty_score += 15
        elif word_count > 25:
            difficulty_score += 5

        # Factor 2: Cognitive level indicators
        # Easy: recall, identify, define, list, name
        easy_keywords = ['what is', 'define', 'list', 'name', 'identify', 'state', 'recall']
        # Medium: explain, describe, compare, calculate
        medium_keywords = ['explain', 'describe', 'compare', 'calculate', 'find', 'determine', 'show']
        # Hard: analyze, evaluate, derive, prove, justify
        hard_keywords = ['analyze', 'evaluate', 'derive', 'prove', 'justify', 'critique', 'assess', 'synthesize']

        if any(keyword in question_text for keyword in easy_keywords):
            difficulty_score -= 15
        elif any(keyword in question_text for keyword in hard_keywords):
            difficulty_score += 20
        elif any(keyword in question_text for keyword in medium_keywords):
            difficulty_score += 5

        # Factor 3: Mathematical complexity
        # Check for mathematical symbols and formulas
        math_indicators = ['∫', '∑', '∂', '√', '²', '³', 'dx', 'dy', 'sin', 'cos', 'tan', 'log', 'ln']
        math_count = sum(1 for indicator in math_indicators if indicator in question.question)
        if math_count > 3:
            difficulty_score += 15
        elif math_count > 1:
            difficulty_score += 5

        # Factor 4: Multiple concepts
        # Questions with "and", "or", multiple parts tend to be harder
        if ' and ' in question_text and ' or ' in question_text:
            difficulty_score += 10
        elif question_text.count(' and ') > 2:
            difficulty_score += 10

        # Factor 5: Presence of images/tables
        # Visual aids can indicate complexity
        if len(question.images) > 1:
            difficulty_score += 10
        elif len(question.images) == 1:
            difficulty_score += 5

        if len(question.tables) > 0:
            difficulty_score += 10

        # Factor 6: Question type
        # Subjective questions tend to be harder than MCQs
        if question.answer_type == QuestionType.SUBJECTIVE:
            difficulty_score += 10
        elif question.answer_type == QuestionType.MCQ_SINGLE:
            difficulty_score -= 5

        # Factor 7: Number of MCQ options
        # More options can indicate complexity
        if len(question.options) > 4:
            difficulty_score += 5

        # Factor 8: Presence of explanation/hint
        # Questions needing detailed explanations tend to be harder
        if question.explanation and len(question.explanation) > 200:
            difficulty_score += 10

        # Factor 9: Sub-topic specificity
        # Questions with specific sub-topics tend to be more advanced
        if question.sub_topic:
            difficulty_score += 5

        # Classify based on final score
        if difficulty_score < 40:
            return DifficultyLevel.EASY
        elif difficulty_score > 65:
            return DifficultyLevel.HARD
        else:
            return DifficultyLevel.MEDIUM
    
    def extract_tags(self, question: TaggedQuestion) -> list[str]:
        """
        Extract relevant tags from question content.
        
        Analyzes the question text, options, and metadata to generate relevant
        content-based tags that help categorize and search questions. Tags include:
        - Subject-specific concepts and keywords
        - Question characteristics (e.g., "calculation", "conceptual", "diagram-based")
        - Content types (e.g., "has-image", "has-table", "multi-step")
        - Cognitive levels (e.g., "recall", "application", "analysis")
        
        Args:
            question: TaggedQuestion to extract tags from
            
        Returns:
            List of relevant tag strings
        """
        tags = set()  # Use set to avoid duplicates
        
        question_text = question.question.lower()
        
        # 1. Add subject-specific concept tags
        # Physics concepts
        physics_concepts = {
            'force': ['force', 'newton', 'push', 'pull'],
            'motion': ['motion', 'velocity', 'acceleration', 'speed', 'displacement'],
            'energy': ['energy', 'kinetic', 'potential', 'work', 'power'],
            'gravity': ['gravity', 'gravitational', 'weight'],
            'friction': ['friction', 'resistance'],
            'pressure': ['pressure', 'pascal', 'atmospheric'],
            'heat': ['heat', 'temperature', 'thermal', 'calorimetry'],
            'light': ['light', 'reflection', 'refraction', 'optics', 'lens', 'mirror'],
            'sound': ['sound', 'wave', 'frequency', 'amplitude', 'acoustics'],
            'electricity': ['electric', 'current', 'voltage', 'resistance', 'circuit', 'ohm'],
            'magnetism': ['magnet', 'magnetic', 'field', 'electromagnetic'],
            'mechanics': ['mechanics', 'dynamics', 'kinematics', 'statics'],
        }
        
        # Chemistry concepts
        chemistry_concepts = {
            'atom': ['atom', 'atomic', 'molecule', 'molecular'],
            'element': ['element', 'periodic', 'compound'],
            'reaction': ['reaction', 'chemical', 'reactant', 'product'],
            'acid-base': ['acid', 'base', 'ph', 'alkaline', 'neutral'],
            'oxidation': ['oxidation', 'reduction', 'redox'],
            'bonding': ['bond', 'ionic', 'covalent', 'metallic'],
            'organic': ['organic', 'hydrocarbon', 'alkane', 'alkene'],
            'solution': ['solution', 'solvent', 'solute', 'concentration'],
        }
        
        # Mathematics concepts
        math_concepts = {
            'algebra': ['equation', 'variable', 'expression', 'polynomial'],
            'geometry': ['triangle', 'circle', 'angle', 'area', 'volume', 'perimeter'],
            'trigonometry': ['sin', 'cos', 'tan', 'trigonometry'],
            'calculus': ['derivative', 'integral', 'differentiation', 'integration'],
            'statistics': ['mean', 'median', 'mode', 'probability', 'statistics'],
        }
        
        # Select concept dictionary based on subject
        if question.subject.lower() == 'physics':
            concept_dict = physics_concepts
        elif question.subject.lower() == 'chemistry':
            concept_dict = chemistry_concepts
        elif question.subject.lower() == 'mathematics':
            concept_dict = math_concepts
        else:
            concept_dict = {}
        
        # Add matching concept tags
        for tag, keywords in concept_dict.items():
            if any(keyword in question_text for keyword in keywords):
                tags.add(tag)
        
        # 2. Add question characteristic tags
        
        # Calculation-based questions
        calculation_indicators = ['calculate', 'compute', 'find', 'determine', 'solve']
        if any(indicator in question_text for indicator in calculation_indicators):
            tags.add('calculation')
        
        # Conceptual questions
        conceptual_indicators = ['explain', 'describe', 'what is', 'define', 'why']
        if any(indicator in question_text for indicator in conceptual_indicators):
            tags.add('conceptual')
        
        # Comparison questions
        if 'compare' in question_text or 'difference between' in question_text:
            tags.add('comparison')
        
        # Application questions
        application_indicators = ['apply', 'use', 'demonstrate', 'show how']
        if any(indicator in question_text for indicator in application_indicators):
            tags.add('application')
        
        # Derivation/proof questions
        if 'derive' in question_text or 'prove' in question_text:
            tags.add('derivation')
        
        # Analysis questions
        if 'analyze' in question_text or 'analyse' in question_text:
            tags.add('analysis')
        
        # 3. Add content type tags
        
        # Has images
        if len(question.images) > 0:
            tags.add('has-image')
            if len(question.images) > 1:
                tags.add('multiple-images')
        
        # Has tables
        if len(question.tables) > 0:
            tags.add('has-table')
        
        # Multi-step (indicated by multiple "and" or "step" keyword)
        if question_text.count(' and ') >= 2 or 'step' in question_text or (
            'calculate' in question_text and 'determine' in question_text
        ) or (
            'calculate' in question_text and 'derive' in question_text
        ):
            tags.add('multi-step')
        
        # Has formula/equation
        math_symbols = ['=', '∫', '∑', '∂', '√', '²', '³', 'dx', 'dy']
        if any(symbol in question.question for symbol in math_symbols):
            tags.add('formula')
        
        # 4. Add cognitive level tags based on Bloom's taxonomy
        
        # Remember/Recall
        recall_keywords = ['list', 'name', 'identify', 'state', 'recall', 'what is']
        if any(keyword in question_text for keyword in recall_keywords):
            tags.add('recall')
        
        # Understand
        understand_keywords = ['explain', 'describe', 'summarize', 'interpret']
        if any(keyword in question_text for keyword in understand_keywords):
            tags.add('understand')
        
        # Apply
        apply_keywords = ['calculate', 'solve', 'use', 'apply', 'demonstrate']
        if any(keyword in question_text for keyword in apply_keywords):
            tags.add('apply')
        
        # Analyze
        analyze_keywords = ['analyze', 'compare', 'contrast', 'examine']
        if any(keyword in question_text for keyword in analyze_keywords):
            tags.add('analyze')
        
        # Evaluate
        evaluate_keywords = ['evaluate', 'assess', 'justify', 'critique']
        if any(keyword in question_text for keyword in evaluate_keywords):
            tags.add('evaluate')
        
        # Create
        create_keywords = ['design', 'construct', 'develop', 'formulate']
        if any(keyword in question_text for keyword in create_keywords):
            tags.add('create')
        
        # 5. Add question type tags
        if question.answer_type == QuestionType.MCQ_SINGLE:
            tags.add('mcq')
        elif question.answer_type == QuestionType.MCQ_MULTIPLE:
            tags.add('mcq-multiple')
        elif question.answer_type == QuestionType.SUBJECTIVE:
            tags.add('subjective')
        elif question.answer_type == QuestionType.INTEGER:
            tags.add('integer-answer')
        elif question.answer_type == QuestionType.NUMERICAL:
            tags.add('numerical-answer')
        
        # 6. Add difficulty-based tags
        tags.add(f'difficulty-{question.difficulty.value}')
        
        # 7. Add sub-topic as tag if present
        if question.sub_topic:
            # Normalize sub-topic to tag format
            sub_topic_tag = question.sub_topic.lower().replace(' ', '-')
            tags.add(sub_topic_tag)
        
        # 8. Add support material tags
        if question.hint:
            tags.add('has-hint')
        
        if question.explanation:
            tags.add('has-explanation')
        
        # Convert set to sorted list for consistent output
        return sorted(list(tags))
    
    def _generate_subject_id(self, subject: str) -> str:
        """
        Generate a consistent ID for a subject.
        
        Args:
            subject: Subject name (e.g., "Physics", "Chemistry")
            
        Returns:
            Subject ID (e.g., "physics", "chemistry")
        """
        return subject.lower()
    
    def _generate_chapter_id(self, chapter_number: int) -> str:
        """
        Generate a consistent ID for a chapter.
        
        Args:
            chapter_number: Chapter number
            
        Returns:
            Chapter ID (e.g., "chapter_1", "chapter_2")
        """
        return f"chapter_{chapter_number}"
    
    def _generate_topic_id(self, chapter_number: int, topic_title: str) -> str:
        """
        Generate a consistent ID for a topic.
        
        Args:
            chapter_number: Chapter number
            topic_title: Topic title
            
        Returns:
            Topic ID (e.g., "chapter_1_topic_forces")
        """
        # Normalize topic title to ID format
        topic_slug = topic_title.lower()
        topic_slug = topic_slug.replace(" ", "_")
        # Remove special characters
        topic_slug = "".join(c for c in topic_slug if c.isalnum() or c == "_")
        
        return f"chapter_{chapter_number}_topic_{topic_slug}"
    
    def _validate_metadata_completeness(self, question: TaggedQuestion) -> None:
        """
        Validate that all required metadata fields are populated.
        
        Implements Property 7: Metadata Completeness
        
        Args:
            question: TaggedQuestion to validate
            
        Raises:
            ValueError: If any required metadata field is missing
        """
        # Check all required fields are non-null
        required_fields = {
            'subject': question.subject,
            'chapter': question.chapter,
            'topic': question.topic,
            'grade_level': question.grade_level,
        }
        
        for field_name, field_value in required_fields.items():
            if field_value is None:
                raise ValueError(
                    f"Required metadata field '{field_name}' is None for question"
                )
        
        # Check grade_level is non-empty list
        if not question.grade_level or len(question.grade_level) == 0:
            raise ValueError("grade_level must be a non-empty list")
        
        logger.debug("Metadata completeness validation passed")
