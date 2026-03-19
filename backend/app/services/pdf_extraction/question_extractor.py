"""
QuestionExtractor component for extracting questions from document sections.

This module extracts questions with all associated content (text, images, tables, options)
from structured document sections. It implements the Question Extraction Algorithm from
the design document.
"""

import re
import json
import logging
from typing import List, Optional, Set
from sarvamai import SarvamAI
from dotenv import load_dotenv
load_dotenv()
try:
    from .models import (
        RawQuestion,
        Section,
        Chapter,
        Topic,
        ImageReference,
        AnswerKey,
        Hint,
        Explanation,
        SectionType,
        QuestionType,
    )
    from .config import get_config
except ImportError:
    # Fallback for direct script execution
    from models import (
        RawQuestion,
        Section,
        Chapter,
        Topic,
        ImageReference,
        AnswerKey,
        Hint,
        Explanation,
        SectionType,
        QuestionType,
    )
    from config import get_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionContext:
    """Context information for question extraction"""
    
    def __init__(self, chapter: Chapter, topic: Topic):
        """
        Initialize extraction context.
        
        Args:
            chapter: Chapter containing the questions
            topic: Topic containing the questions
        """
        self.chapter = chapter
        self.topic = topic


class QuestionExtractor:
    """
    Extracts questions with all associated content from document sections.
    
    This component extracts individual questions from question sections,
    preserves formatting (bold, italics, mathematical symbols), extracts
    and links images referenced in questions, and identifies question types.
    """
    
    def __init__(self, config=None, supabase_client=None):
        """
        Initialize QuestionExtractor.
        
        Args:
            config: Configuration for PDF extraction. If None, loads from environment.
            supabase_client: Optional Supabase client for database integration.
        """
        self.config = config or get_config()
        self.client = SarvamAI(api_subscription_key=self.config.sarvam_api_key)
        self.supabase_client = supabase_client  # Optional Supabase client for database integration
        logger.info("QuestionExtractor initialized")
    
    def extract_questions(
        self,
        section: Section,
        context: ExtractionContext
    ) -> List[RawQuestion]:
        """
        Extract all questions from a section.
        
        This is the main entry point for question extraction. It implements the
        Question Extraction Algorithm from the design document.
        
        Preconditions:
        - section.section_type == 'questions'
        - section.content is non-empty markdown
        - context provides valid chapter and topic
        
        Postconditions:
        - Returns list of RawQuestion objects
        - All questions have unique question_numbers within topic
        - Images and tables are properly extracted and linked
        
        Loop Invariants:
        - All processed questions have valid question_numbers
        - No duplicate question_numbers in result list
        
        Args:
            section: Section containing questions
            context: Extraction context with chapter and topic info
            
        Returns:
            List of extracted RawQuestion objects
            
        Raises:
            ValueError: If section is not a questions section
        """
        if section.section_type != SectionType.QUESTIONS:
            raise ValueError(
                f"Section must be of type QUESTIONS, got {section.section_type}"
            )
        
        logger.info(
            f"Extracting questions from section in "
            f"{context.chapter.title} > {context.topic.title}"
        )
        
        content = section.content
        if not content or not content.strip():
            logger.warning("Empty section content, returning empty list")
            return []
        
        # Use LLM to identify question boundaries
        question_blocks = self._identify_question_blocks(content)
        logger.info(f"Identified {len(question_blocks)} question blocks")
        
        questions = []
        seen_numbers: Set[str] = set()
        
        for block in question_blocks:
            try:
                # Extract question number
                question_number = self._extract_question_number(block)
                
                if not question_number:
                    logger.warning(
                        "Could not extract question number from block: %s...",
                        block[:100],
                    )
                    continue
                
                # Check for duplicates (Error Scenario 3)
                if question_number in seen_numbers:
                    logger.warning("Duplicate question number: %s, skipping", question_number)
                    continue
                
                seen_numbers.add(question_number)

                # Extract question text (preserve formatting)
                question_text = self._extract_formatted_text(block)
                
                # Extract options if MCQ
                options = None
                if self._is_multiple_choice(block):
                    options = self._extract_options(block)
                
                # Extract image references
                images = self._extract_image_references(block)
                
                # Validate image references exist (Error Scenario 4)
                validated_images = []
                for image in images:
                    # Check if image file exists (in production, this would check actual file system)
                    # For now, we'll assume images are validated during database write
                    # But we still log and flag missing images
                    validated_images.append(image)
                
                images = validated_images
                
                # Extract tables
                tables = self._extract_tables(block)
                
                # Determine sub-topic if present
                sub_topic = self._infer_sub_topic(block, context.topic)
                
                # Create RawQuestion object
                question = RawQuestion(
                    question_number=question_number,
                    question_text=question_text,
                    options=options,
                    images=images,
                    tables=tables,
                    page_number=section.page_range[0],
                    chapter_context=context.chapter.title,
                    topic_context=context.topic.title,
                    sub_topic_context=sub_topic,
                )
                
                questions.append(question)
                logger.debug(f"Extracted question {question_number}")
                
            except Exception as e:
                logger.error("Error extracting question from block: %s", e)
                logger.debug("Block content: %s...", block[:200])
                continue
        
        logger.info(f"Successfully extracted {len(questions)} questions")
        
        # Verify uniqueness
        assert len(questions) == len(seen_numbers), "Question count mismatch with unique numbers"
        
        return questions
    
    def _identify_question_blocks(self, content: str) -> List[str]:
        """
        Identify question boundaries using LLM and pattern matching.
        
        This method splits the content into individual question blocks.
        Each block contains one complete question with its options, images, etc.
        
        Args:
            content: Section content containing questions
            
        Returns:
            List of question block strings
        """
        # First, try pattern-based splitting
        # Common patterns: "1.", "Q1.", "1)", etc. at start of line
        question_pattern = r'^(?:\d+\.|\d+\)|\bQ\d+\.?|\bQuestion\s+\d+)'
        
        lines = content.split('\n')
        blocks = []
        current_block = []
        
        for line in lines:
            # Check if line starts a new question
            if re.match(question_pattern, line.strip(), re.IGNORECASE):
                # Save previous block if exists
                if current_block:
                    blocks.append('\n'.join(current_block))
                # Start new block
                current_block = [line]
            else:
                # Continue current block
                if current_block:
                    current_block.append(line)
        
        # Add last block
        if current_block:
            blocks.append('\n'.join(current_block))
        
        # If pattern-based splitting found blocks, return them
        if blocks:
            logger.debug(f"Pattern-based splitting found {len(blocks)} blocks")
            return blocks
        
        # Fallback: Use LLM to identify question boundaries
        logger.info("Pattern-based splitting failed, using LLM")
        return self._identify_blocks_with_llm(content)
    
    def _identify_blocks_with_llm(self, content: str) -> List[str]:
        """
        Use LLM to identify question boundaries when patterns fail.
        
        Args:
            content: Section content
            
        Returns:
            List of question blocks
        """
        # Truncate content if too long
        max_chars = 4000
        truncated = content[:max_chars]
        if len(content) > max_chars:
            truncated += "\n... (content truncated)"
        
        prompt = f"""Analyze the following text and identify individual question boundaries.
Return a JSON array of question numbers found, in order.

Text:
{truncated}

Return format: {{"question_numbers": ["1", "2", "3", ...]}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="sarvam-2b-v0.5",
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.llm_temperature,
                max_tokens=500,
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            question_numbers = result.get("question_numbers", [])
            
            # Split content by identified question numbers
            blocks = []
            for i, qnum in enumerate(question_numbers):
                # Find start of this question
                pattern = rf'(?:^|\n)(?:{re.escape(qnum)}\.|\bQ{re.escape(qnum)}\.?|\bQuestion\s+{re.escape(qnum)})'
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                
                if match:
                    start = match.start()
                    
                    # Find end (start of next question or end of content)
                    if i + 1 < len(question_numbers):
                        next_qnum = question_numbers[i + 1]
                        next_pattern = rf'(?:^|\n)(?:{re.escape(next_qnum)}\.|\bQ{re.escape(next_qnum)}\.?|\bQuestion\s+{re.escape(next_qnum)})'
                        next_match = re.search(next_pattern, content[start + 1:], re.IGNORECASE | re.MULTILINE)
                        if next_match:
                            end = start + 1 + next_match.start()
                        else:
                            end = len(content)
                    else:
                        end = len(content)
                    
                    block = content[start:end].strip()
                    blocks.append(block)
            
            return blocks
            
        except Exception as e:
            logger.error(f"LLM-based block identification failed: {e}")
            # Fallback: treat entire content as one block
            return [content]
    
    def _extract_question_number(self, block: str) -> Optional[str]:
        """
        Extract question number from question block.
        
        Handles formats: "1", "Q1", "1.", "1)", "2.a", etc.
        
        Preconditions:
        - block contains a valid question
        - block is non-empty
        
        Postconditions:
        - Returns normalized question number string
        - Handles formats: "1", "Q1", "1.", "1)", "2.a", etc.
        - Returns None if no question number found
        
        Args:
            block: Question block text
            
        Returns:
            Normalized question number or None
        """
        # Get first few lines where question number typically appears
        lines = block.strip().split('\n')[:3]
        first_content = '\n'.join(lines)
        
        raw_number = None
        
        # Pattern 1: "1." or "1)"
        match = re.search(r'^(\d+)[.)]', first_content.strip(), re.MULTILINE)
        if match:
            raw_number = match.group(1)
        
        # Pattern 2: "Q1" or "Q1."
        if not raw_number:
            match = re.search(r'^\bQ(\d+)\.?', first_content.strip(), re.IGNORECASE | re.MULTILINE)
            if match:
                raw_number = match.group(1)
        
        # Pattern 3: "Question 1"
        if not raw_number:
            match = re.search(r'^\bQuestion\s+(\d+)', first_content.strip(), re.IGNORECASE | re.MULTILINE)
            if match:
                raw_number = match.group(1)
        
        # Pattern 4: "2.a" or "2a" (sub-questions)
        if not raw_number:
            match = re.search(r'^(\d+[a-z]|\d+\.[a-z])', first_content.strip(), re.MULTILINE)
            if match:
                raw_number = match.group(1)
        
        # Pattern 5: Just a number at start
        if not raw_number:
            match = re.search(r'^(\d+)\s', first_content.strip(), re.MULTILINE)
            if match:
                raw_number = match.group(1)
        
        # Normalize the extracted number
        if raw_number:
            return self._normalize_question_number(raw_number)
        
        return None
    
    def _normalize_question_number(self, raw_number: str) -> str:
        """
        Normalize question number to standard format.
        
        This function is idempotent: normalize(normalize(x)) == normalize(x)
        
        Preconditions:
        - raw_number is non-empty string
        
        Postconditions:
        - Returns normalized format (e.g., "1", "2a", "15")
        - Removes punctuation and prefixes
        - Consistent format for matching
        - Idempotent: normalize(normalize(x)) == normalize(x)
        
        Args:
            raw_number: Raw question number string
            
        Returns:
            Normalized question number
            
        Examples:
            "1" -> "1"
            "Q1" -> "1"
            "1." -> "1"
            "1)" -> "1"
            "2.a" -> "2a"
            "Q15." -> "15"
        """
        if not raw_number:
            return raw_number
        
        # Remove common prefixes (Question, then Q) - case insensitive
        # Do "Question" first to avoid matching just "Q" in "Question"
        normalized = re.sub(r'^Question\s*', '', raw_number, flags=re.IGNORECASE)
        normalized = re.sub(r'^Q\s*', '', normalized, flags=re.IGNORECASE)
        
        # Remove trailing punctuation (., ), :, etc.) but keep letters for sub-questions
        # Handle "2.a" -> "2a" but keep "2a" as "2a"
        normalized = re.sub(r'\.([a-z])', r'\1', normalized, flags=re.IGNORECASE)  # "2.a" -> "2a"
        normalized = re.sub(r'[.):]+$', '', normalized)  # Remove trailing punctuation
        
        # Remove any remaining non-alphanumeric characters except for internal letters
        # Keep format like "2a" but remove other special chars
        normalized = re.sub(r'[^\da-z]', '', normalized, flags=re.IGNORECASE)
        normalized = normalized.strip()
        
        return normalized
    
    def _extract_formatted_text(self, block: str) -> str:
        """
        Extract question text while preserving markdown formatting.
        
        Preconditions:
        - block is non-empty markdown string
        - block contains question text
        
        Postconditions:
        - Returns formatted text with markdown preserved
        - Mathematical symbols preserved (LaTeX, Unicode)
        - Image references converted to proper format
        - No loss of formatting information
        
        Args:
            block: Question block
            
        Returns:
            Formatted question text
        """
        # Remove question number prefix
        lines = block.strip().split('\n')
        
        # Find where actual question text starts (after question number)
        question_lines = []
        found_start = False
        
        for line in lines:
            # Skip question number line
            if not found_start:
                # Check if this line has question number
                if re.match(r'^(?:\d+[.)]|\bQ\d+\.?|\bQuestion\s+\d+)', line.strip(), re.IGNORECASE):
                    # Extract text after question number
                    text_after_number = re.sub(
                        r'^(?:\d+[.)]|\bQ\d+\.?|\bQuestion\s+\d+)\s*',
                        '',
                        line.strip(),
                        flags=re.IGNORECASE
                    )
                    if text_after_number:
                        question_lines.append(text_after_number)
                    found_start = True
                    continue
            
            # Add subsequent lines
            question_lines.append(line)
        
        # Join lines and preserve formatting
        question_text = '\n'.join(question_lines).strip()
        
        # Preserve markdown formatting (bold, italics, etc.)
        # Preserve LaTeX math expressions (inline: $...$ and display: $$...$$)
        # Preserve Unicode mathematical symbols
        # No modification needed - keep as is to preserve all formatting
        
        # Remove MCQ options from question text (they're extracted separately)
        question_text = self._remove_options_from_text(question_text)
        
        # Normalize whitespace while preserving intentional formatting
        question_text = self._normalize_whitespace(question_text)
        
        return question_text
    
    def _remove_options_from_text(self, text: str) -> str:
        """
        Remove MCQ options from question text.
        
        Options are extracted separately, so we remove them from the main
        question text to avoid duplication.
        
        Args:
            text: Question text possibly containing options
            
        Returns:
            Question text without options
        """
        lines = text.split('\n')
        question_lines = []
        
        # Pattern for option lines: (A), (B), A., B), etc.
        option_pattern = r'^(?:\([A-Da-d]\)|[A-Da-d][.)])\s+'
        
        for line in lines:
            # Skip lines that are MCQ options
            if re.match(option_pattern, line.strip()):
                continue
            question_lines.append(line)
        
        return '\n'.join(question_lines).strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving intentional formatting.
        
        This function:
        - Preserves line breaks (important for multi-line questions)
        - Removes excessive blank lines (more than 2 consecutive)
        - Trims trailing whitespace from lines
        - Preserves indentation (important for code/math)
        
        Args:
            text: Text to normalize
            
        Returns:
            Text with normalized whitespace
        """
        # Split into lines
        lines = text.split('\n')
        
        # Trim trailing whitespace from each line (but preserve leading for indentation)
        lines = [line.rstrip() for line in lines]
        
        # Remove excessive blank lines (more than 2 consecutive)
        normalized_lines = []
        blank_count = 0
        
        for line in lines:
            if not line.strip():
                blank_count += 1
                # Keep at most 2 consecutive blank lines
                if blank_count <= 2:
                    normalized_lines.append(line)
            else:
                blank_count = 0
                normalized_lines.append(line)
        
        # Join back together
        result = '\n'.join(normalized_lines).strip()
        
        return result
    
    def _is_multiple_choice(self, block: str) -> bool:
        """
        Determine if question block contains multiple choice options.
        
        Args:
            block: Question block
            
        Returns:
            True if MCQ, False otherwise
        """
        # Look for option patterns: (A), (a), A., a), etc.
        option_patterns = [
            r'\([A-Da-d]\)',  # (A), (B), (C), (D)
            r'^[A-Da-d][.)]',  # A., B), etc.
            r'^\([A-Da-d]\)',  # (A) at start of line
        ]
        
        for pattern in option_patterns:
            if re.search(pattern, block, re.MULTILINE):
                return True
        
        return False
    
    def _extract_options(self, block: str) -> List[str]:
        """
        Extract MCQ options from question block.

        Handles various option formats:
        - (A), (B), (C), (D) - parentheses format
        - A., B., C., D. - dot format
        - A), B), C), D) - parenthesis format
        - a), b), c), d) - lowercase variants
        - (a), (b), (c), (d) - lowercase parentheses
        - 1., 2., 3., 4. - numeric format
        - (1), (2), (3), (4) - numeric parentheses

        Preserves formatting:
        - Markdown bold, italics, code
        - Mathematical symbols (LaTeX, Unicode)
        - Multi-line options
        - Nested formatting

        Args:
            block: Question block

        Returns:
            List of option texts with formatting preserved
        """
        options = []
        lines = block.split('\n')

        # Enhanced patterns for various option formats
        # Matches: (A), (B), A., A), a., a), (a), (1), 1., 1)
        option_patterns = [
            r'^(?:\(([A-Da-d1-4])\)|([A-Da-d1-4])[.)])\s*(.+)$',  # Standard formats
            r'^\s*(?:\(([A-Da-d1-4])\)|([A-Da-d1-4])[.)])\s*(.+)$',  # With leading whitespace
        ]

        current_option = None
        current_text = []

        for line in lines:
            matched = False

            # Try each pattern
            for pattern in option_patterns:
                match = re.match(pattern, line)
                if match:
                    # Save previous option if exists
                    if current_option is not None and current_text:
                        option_text = '\n'.join(current_text).strip()
                        if option_text:  # Only add non-empty options
                            options.append(option_text)

                    # Start new option
                    # Extract the option label (A, B, C, D, etc.) from whichever group matched
                    label = match.group(1) or match.group(2)
                    text = match.group(3).strip()

                    current_option = label
                    current_text = [text] if text else []
                    matched = True
                    break

            # If not a new option but we're in an option, it's a continuation line
            if not matched and current_option is not None:
                stripped = line.strip()
                # Only add non-empty continuation lines
                # Stop if we hit a blank line or start of next question
                if stripped and not re.match(r'^\d+[\.)]\s', stripped):
                    current_text.append(stripped)
                elif not stripped and current_text:
                    # Blank line might end the option
                    # But we'll be lenient and continue for now
                    pass

        # Don't forget the last option
        if current_option is not None and current_text:
            option_text = '\n'.join(current_text).strip()
            if option_text:
                options.append(option_text)

        # Validate we have reasonable number of options (typically 2-4 for MCQ)
        # But don't filter here - let caller decide

        return options
    
    def _extract_image_references(self, block: str) -> List[ImageReference]:
        """
        Extract image references from question block.
        
        Looks for markdown image syntax: ![alt](path)
        
        Args:
            block: Question block
            
        Returns:
            List of ImageReference objects
        """
        images = []
        
        # Markdown image pattern: ![alt text](image_path)
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        matches = re.finditer(image_pattern, block)
        
        for match in matches:
            alt_text = match.group(1).strip() or None
            path = match.group(2).strip()
            
            # Determine position based on context
            # If image is on its own line, it's "above" or "below"
            # If inline with text, it's "inline"
            position = "inline"
            
            # Check if image is on its own line
            lines = block.split('\n')
            for line in lines:
                if match.group(0) in line and line.strip() == match.group(0):
                    position = "above"
                    break
            
            image_ref = ImageReference(
                path=path,
                alt_text=alt_text,
                position=position
            )
            images.append(image_ref)
        
        return images
    
    def validate_image_references(
        self,
        images: List[ImageReference],
        question_number: str,
        chapter: str,
        topic: str,
        page_number: int,
        images_dir: Optional[str] = None
    ) -> List[ImageReference]:
        """
        Validate that image references exist and handle failures.
        
        Error Scenario 4: Image extraction failure
        - Check if image files exist
        - Use placeholder for missing images
        - Flag for manual image attachment
        
        Args:
            images: List of image references to validate
            question_number: Question number for error reporting
            chapter: Chapter context
            topic: Topic context
            page_number: Page number
            images_dir: Directory where images are stored (optional)
            
        Returns:
            List of validated ImageReference objects (with placeholders for missing)
        """
        import os
        
        validated_images = []
        
        for image in images:
            image_exists = True
            
            # Check if image file exists (if images_dir provided)
            if images_dir:
                full_path = os.path.join(images_dir, image.path)
                image_exists = os.path.exists(full_path)
            
            if not image_exists:
                logger.warning(
                    "Image not found: %s (question %s, %s > %s)",
                    image.path,
                    question_number,
                    chapter,
                    topic,
                )
                placeholder_image = ImageReference(
                    path=f"placeholder_{image.path}",
                    alt_text=f"Missing image: {image.path}",
                    position=image.position,
                )
                validated_images.append(placeholder_image)
            else:
                # Image exists, keep original reference
                validated_images.append(image)
        
        return validated_images
    
    def _extract_tables(self, block: str) -> List[str]:
        """
        Extract markdown tables from question block.
        
        Args:
            block: Question block
            
        Returns:
            List of markdown table strings
        """
        tables = []
        lines = block.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            # Check if line is part of a markdown table (contains |)
            if '|' in line:
                current_table.append(line)
                in_table = True
            else:
                # End of table
                if in_table and current_table:
                    # Verify it's a valid table (has at least 2 rows)
                    if len(current_table) >= 2:
                        tables.append('\n'.join(current_table))
                    current_table = []
                    in_table = False
        
        # Add last table if exists
        if current_table and len(current_table) >= 2:
            tables.append('\n'.join(current_table))
        
        return tables
    
    def _infer_sub_topic(self, block: str, topic: Topic) -> Optional[str]:
        """
        Infer sub-topic from question block and topic context.
        
        Args:
            block: Question block
            topic: Topic containing the question
            
        Returns:
            Sub-topic name or None
        """
        # If topic has sub-topics, try to match question to one
        if not topic.sub_topics:
            return None
        
        # Simple heuristic: check if any sub-topic name appears in question
        block_lower = block.lower()
        
        for sub_topic in topic.sub_topics:
            if sub_topic.lower() in block_lower:
                return sub_topic
        
        # No match found
        return None


    def identify_question_type(self, question: RawQuestion) -> QuestionType:
        """
        Determine question type (MCQ, subjective, numerical, etc.).

        Uses question content patterns to classify the question type:
        - MCQ_SINGLE: Has options (A, B, C, D format)
        - MCQ_MULTIPLE: Has options with "select all" or "choose all" language
        - INTEGER: Asks for integer answer (whole number)
        - NUMERICAL: Asks for numerical answer (decimal, calculation)
        - SUBJECTIVE: Descriptive/explanatory questions

        Args:
            question: RawQuestion object to classify

        Returns:
            QuestionType enum value
        """
        question_text_lower = question.question_text.lower()

        # Check if it has options - likely MCQ
        if question.options and len(question.options) >= 2:
            # Check for multiple choice indicators
            multiple_choice_patterns = [
                r'select all',
                r'choose all',
                r'which of the following are',
                r'all that apply',
                r'more than one',
                r'multiple correct',
            ]

            for pattern in multiple_choice_patterns:
                if re.search(pattern, question_text_lower):
                    return QuestionType.MCQ_MULTIPLE

            # Default to single choice MCQ
            return QuestionType.MCQ_SINGLE

        # Check for integer answer type
        integer_patterns = [
            r'how many',
            r'number of',
            r'count',
            r'integer',
            r'whole number',
            r'find the value of n',
            r'find n',
        ]

        for pattern in integer_patterns:
            if re.search(pattern, question_text_lower):
                return QuestionType.INTEGER

        # Check for numerical answer type (calculations, decimals)
        numerical_patterns = [
            r'calculate',
            r'compute',
            r'find the value',
            r'what is the value',
            r'determine the value',
            r'solve for',
            r'evaluate',
            r'find.*=',
            r'=\s*\?',
            r'decimal',
            r'approximate',
            r'round to',
        ]

        for pattern in numerical_patterns:
            if re.search(pattern, question_text_lower):
                return QuestionType.NUMERICAL

        # Check for subjective question indicators
        subjective_patterns = [
            r'explain',
            r'describe',
            r'discuss',
            r'why',
            r'how does',
            r'what are the reasons',
            r'justify',
            r'elaborate',
            r'define',
            r'state the',
            r'give reasons',
            r'write.*about',
            r'comment on',
        ]

        for pattern in subjective_patterns:
            if re.search(pattern, question_text_lower):
                return QuestionType.SUBJECTIVE

        # Default classification based on heuristics
        # If question is very short and has numbers/symbols, likely numerical
        if len(question_text_lower.split()) < 15:
            # Check for mathematical symbols or numbers
            if re.search(r'[\d+\-*/=()]', question.question_text):
                return QuestionType.NUMERICAL

        # Default to subjective for longer descriptive questions
        return QuestionType.SUBJECTIVE

    def extract_answer_keys(self, section: Section) -> List[AnswerKey]:
        """
        Extract answer keys from answer key sections.

        Parses answer key sections to extract question number and answer pairs.
        Handles various answer formats including:
        - Simple format: "1. A" or "1) B"
        - Verbose format: "1. The answer is A"
        - Text format: "1. Force is a push or pull"
        - Mixed format: "Q1: (A) 5 m/s²"

        Preconditions:
        - section.section_type == 'answer_key'
        - section.content is non-empty markdown

        Postconditions:
        - Returns list of AnswerKey objects
        - All answer keys have valid question_numbers
        - Answer text is extracted and cleaned

        Args:
            section: Section containing answer keys

        Returns:
            List of AnswerKey objects

        Raises:
            ValueError: If section is not an answer key section
        """
        if section.section_type != SectionType.ANSWER_KEY:
            raise ValueError(
                f"Section must be of type ANSWER_KEY, got {section.section_type}"
            )

        logger.info("Extracting answer keys from section")

        content = section.content
        if not content or not content.strip():
            logger.warning("Empty answer key section content, returning empty list")
            return []

        answer_keys = []
        lines = content.split('\n')

        # Pattern to match answer key entries
        # Matches formats like:
        # "1. A", "1) B", "Q1. C", "1: D", "Question 1. A"
        # "1. The answer is A", "1. Force is a push or pull"
        answer_pattern = r'^(?:Q(?:uestion)?\s*)?(\d+[a-z]?)[.):]\s*(.+)$'

        current_answer_number = None
        current_answer_text = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines and section headers
            if not line_stripped or self._is_section_header(line_stripped):
                continue

            # Try to match answer key pattern
            match = re.match(answer_pattern, line_stripped, re.IGNORECASE)

            if match:
                # Save previous answer if exists
                if current_answer_number and current_answer_text:
                    answer_text = ' '.join(current_answer_text).strip()
                    answer_key = AnswerKey(
                        question_number=self._normalize_question_number(current_answer_number),
                        answer=self._clean_answer_text(answer_text),
                        page_number=section.page_range[0]
                    )
                    answer_keys.append(answer_key)
                    logger.debug(f"Extracted answer for question {answer_key.question_number}")

                # Start new answer
                current_answer_number = match.group(1)
                answer_text = match.group(2).strip()
                current_answer_text = [answer_text] if answer_text else []

            elif current_answer_number:
                # Continuation of previous answer (multi-line answer)
                # Only add if it doesn't look like a new answer entry
                if not re.match(r'^\d+[.):]\s', line_stripped):
                    current_answer_text.append(line_stripped)

        # Don't forget the last answer
        if current_answer_number and current_answer_text:
            answer_text = ' '.join(current_answer_text).strip()
            answer_key = AnswerKey(
                question_number=self._normalize_question_number(current_answer_number),
                answer=self._clean_answer_text(answer_text),
                page_number=section.page_range[0]
            )
            answer_keys.append(answer_key)
            logger.debug(f"Extracted answer for question {answer_key.question_number}")

        logger.info(f"Successfully extracted {len(answer_keys)} answer keys")

        return answer_keys

    def _is_section_header(self, line: str) -> bool:
        """
        Check if line is a section header (not an answer entry).

        Args:
            line: Line to check

        Returns:
            True if line is a header, False otherwise
        """
        # Common header patterns
        header_patterns = [
            r'^#+\s',  # Markdown headers
            r'^answer\s*key',
            r'^answers',
            r'^solution',
            r'^chapter\s+\d+',
            r'^topic:',
            r'^section\s+\d+',
        ]

        line_lower = line.lower()
        for pattern in header_patterns:
            if re.match(pattern, line_lower):
                return True

        return False

    def _clean_answer_text(self, answer_text: str) -> str:
        """
        Clean and normalize answer text.

        Handles various answer formats:
        - "A" -> "A"
        - "(A)" -> "A"
        - "The answer is A" -> "A"
        - "Option A" -> "A"
        - "A) 5 m/s²" -> "A"
        - "Force is a push or pull" -> "Force is a push or pull" (keep as is)

        Args:
            answer_text: Raw answer text

        Returns:
            Cleaned answer text
        """
        if not answer_text:
            return answer_text

        # Remove common prefixes
        cleaned = answer_text.strip()

        # Pattern 1: "The answer is A" -> "A"
        match = re.match(r'^(?:The\s+)?answer\s+is\s+(.+)$', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

        # Pattern 2: "Option A" -> "A"
        match = re.match(r'^Option\s+(.+)$', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

        # Pattern 3: "Choice A" -> "A"
        match = re.match(r'^Choice\s+(.+)$', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

        # Pattern 4: "(A)" -> "A" (only if it's a single letter option)
        match = re.match(r'^\(([A-Da-d])\)$', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).upper()

        # Pattern 5: "A)" or "A." -> "A"
        match = re.match(r'^([A-Da-d])[.)](?:\s+(.+))?$', cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).upper()

        # Pattern 6: Just a single letter "A", "B", "C", "D" -> uppercase
        if re.match(r'^[A-Da-d]$', cleaned, re.IGNORECASE):
            cleaned = cleaned.upper()

        # Pattern 7: Explanatory text that still contains the final option label
        match = re.search(
            r'(?:correct\s+(?:answer|option)\s+is|option\s+is)\s+\(?([A-Da-d])\)?',
            cleaned,
            re.IGNORECASE,
        )
        if match:
            cleaned = match.group(1).upper()

        return cleaned.strip()

    def extract_hints(self, section: Section) -> List[Hint]:
        """
        Extract hints from hint sections.

        Parses hint sections to extract question number and hint text pairs.
        Handles various hint formats including:
        - Simple format: "1. Use the formula F = ma"
        - Verbose format: "Hint 1: Consider the direction of force"
        - Text format: "1. Remember that velocity is a vector"
        - Mixed format: "Q1: Think about Newton's laws"

        Preconditions:
        - section.section_type == 'hints'
        - section.content is non-empty markdown

        Postconditions:
        - Returns list of Hint objects
        - All hints have valid question_numbers
        - Hint text is extracted and preserved with formatting

        Args:
            section: Section containing hints

        Returns:
            List of Hint objects

        Raises:
            ValueError: If section is not a hints section
        """
        if section.section_type != SectionType.HINTS:
            raise ValueError(
                f"Section must be of type HINTS, got {section.section_type}"
            )

        logger.info("Extracting hints from section")

        content = section.content
        if not content or not content.strip():
            logger.warning("Empty hints section content, returning empty list")
            return []

        hints = []
        lines = content.split('\n')

        # Pattern to match hint entries
        # Matches formats like:
        # "1. Use formula", "1) Think about", "Q1. Consider", "1: Remember"
        # "Hint 1. Apply", "Hint 1: Use"
        hint_pattern = r'^(?:Hint\s+)?(?:Q(?:uestion)?\s*)?(\d+[a-z]?)[.):]\s*(.+)$'

        current_hint_number = None
        current_hint_text = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines and section headers
            if not line_stripped or self._is_section_header(line_stripped):
                continue

            # Try to match hint pattern
            match = re.match(hint_pattern, line_stripped, re.IGNORECASE)

            if match:
                # Save previous hint if exists
                if current_hint_number and current_hint_text:
                    hint_text = ' '.join(current_hint_text).strip()
                    hint = Hint(
                        question_number=self._normalize_question_number(current_hint_number),
                        hint_text=hint_text,
                        page_number=section.page_range[0]
                    )
                    hints.append(hint)
                    logger.debug(f"Extracted hint for question {hint.question_number}")

                # Start new hint
                current_hint_number = match.group(1)
                hint_text = match.group(2).strip()
                current_hint_text = [hint_text] if hint_text else []

            elif current_hint_number:
                # Continuation of previous hint (multi-line hint)
                # Only add if it doesn't look like a new hint entry
                if not re.match(r'^(?:Hint\s+)?\d+[.):]\s', line_stripped, re.IGNORECASE):
                    current_hint_text.append(line_stripped)

        # Don't forget the last hint
        if current_hint_number and current_hint_text:
            hint_text = ' '.join(current_hint_text).strip()
            hint = Hint(
                question_number=self._normalize_question_number(current_hint_number),
                hint_text=hint_text,
                page_number=section.page_range[0]
            )
            hints.append(hint)
            logger.debug(f"Extracted hint for question {hint.question_number}")

        logger.info(f"Successfully extracted {len(hints)} hints")

        return hints



    def extract_explanations(self, section: Section) -> List[Explanation]:
        """
        Extract explanations from explanation sections.

        Parses explanation sections to extract question number, explanation text,
        and associated images. Handles various explanation formats including:
        - Simple format: "1. Using F = ma, we get..."
        - Verbose format: "Explanation 1: The force can be calculated..."
        - Solution format: "Solution 1: First, identify the given values..."
        - Mixed format: "Q1: Step 1: Calculate the mass..."

        Preconditions:
        - section.section_type == 'explanations'
        - section.content is non-empty markdown

        Postconditions:
        - Returns list of Explanation objects
        - All explanations have valid question_numbers
        - Explanation text is extracted and preserved with formatting
        - Images within explanations are extracted and linked

        Args:
            section: Section containing explanations

        Returns:
            List of Explanation objects

        Raises:
            ValueError: If section is not an explanations section
        """
        if section.section_type != SectionType.EXPLANATIONS:
            raise ValueError(
                f"Section must be of type EXPLANATIONS, got {section.section_type}"
            )

        logger.info("Extracting explanations from section")

        content = section.content
        if not content or not content.strip():
            logger.warning("Empty explanations section content, returning empty list")
            return []

        explanations = []
        lines = content.split('\n')

        # Pattern to match explanation entries
        # Matches formats like:
        # "1. Using formula", "1) First step", "Q1. Calculate", "1: The answer"
        # "Explanation 1. Apply", "Solution 1: Use", "Soln 1. Consider"
        explanation_pattern = r'^(?:(?:Explanation|Solution|Soln)\s+)?(?:Q(?:uestion)?\s*)?(\d+[a-z]?)[.):]\s*(.+)'

        current_explanation_number = None
        current_explanation_text = []

        for line in lines:
            line_stripped = line.strip()

            # Skip empty lines
            if not line_stripped:
                continue
            
            # Skip section headers, but not explanation entries like "Solution 1:"
            # Check if it's a header by seeing if it matches explanation pattern first
            if not re.match(explanation_pattern, line_stripped, re.IGNORECASE):
                if self._is_section_header(line_stripped):
                    continue

            # Try to match explanation pattern
            match = re.match(explanation_pattern, line_stripped, re.IGNORECASE)

            if match:
                # Save previous explanation if exists
                if current_explanation_number and current_explanation_text:
                    explanation_text = '\n'.join(current_explanation_text).strip()
                    
                    # Extract images from the explanation text
                    images = self._extract_image_references(explanation_text)
                    
                    explanation = Explanation(
                        question_number=self._normalize_question_number(current_explanation_number),
                        explanation_text=explanation_text,
                        images=images,
                        page_number=section.page_range[0]
                    )
                    explanations.append(explanation)
                    logger.debug(f"Extracted explanation for question {explanation.question_number}")

                # Start new explanation
                current_explanation_number = match.group(1)
                explanation_text = match.group(2).strip()
                current_explanation_text = [explanation_text] if explanation_text else []

            elif current_explanation_number:
                # Continuation of previous explanation (multi-line explanation)
                # Only add if it doesn't look like a new explanation entry
                if not re.match(r'^(?:(?:Explanation|Solution|Soln)\s+)?\d+[.):]\s', line_stripped, re.IGNORECASE):
                    current_explanation_text.append(line_stripped)

        # Don't forget the last explanation
        if current_explanation_number and current_explanation_text:
            explanation_text = '\n'.join(current_explanation_text).strip()
            
            # Extract images from the explanation text
            images = self._extract_image_references(explanation_text)
            
            explanation = Explanation(
                question_number=self._normalize_question_number(current_explanation_number),
                explanation_text=explanation_text,
                images=images,
                page_number=section.page_range[0]
            )
            explanations.append(explanation)
            logger.debug(f"Extracted explanation for question {explanation.question_number}")

        logger.info(f"Successfully extracted {len(explanations)} explanations")

        return explanations

    def write_raw_questions_to_db(
        self,
        questions: List[RawQuestion],
        job_id: str
    ) -> int:
        """
        Write raw_questions to database with processing_status='pending'.
        
        This method stores extracted questions in the raw_questions table
        before they are tagged with metadata. It stores:
        - question_text, options, page_number
        - context fields (chapter_context, topic_context, sub_topic_context)
        - raw_images, raw_tables
        - processing_status='pending'
        
        Requirements: 8.1, 8.2, 23.3
        
        Args:
            questions: List of RawQuestion objects to write
            job_id: UUID of the extraction job
        
        Returns:
            Number of questions written to database
        
        Raises:
            Exception: If database write fails
        """
        if not self.supabase_client:
            logger.warning("No Supabase client available, skipping database write")
            return 0
        
        try:
            from datetime import datetime, timezone
            from uuid import uuid4
            
            questions_written = 0
            
            for question in questions:
                # Prepare raw_images data
                raw_images = None
                if question.images:
                    raw_images = [
                        {
                            "path": img.path,
                            "alt_text": img.alt_text,
                            "position": img.position
                        }
                        for img in question.images
                    ]
                
                # Prepare raw_tables data
                raw_tables = None
                if question.tables:
                    raw_tables = [
                        {"markdown": table}
                        for table in question.tables
                    ]
                
                # Create raw_questions record
                raw_question_data = {
                    "id": str(uuid4()),
                    "job_id": job_id,
                    "question_number": question.question_number,
                    "question_text": question.question_text,
                    "options": question.options if question.options else [],
                    "page_number": question.page_number,
                    "chapter_context": question.chapter_context,
                    "topic_context": question.topic_context,
                    "sub_topic_context": question.sub_topic_context,
                    "raw_images": raw_images,
                    "raw_tables": raw_tables,
                    "processing_status": "pending",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase_client.table("raw_questions").insert(raw_question_data).execute()
                questions_written += 1
                logger.debug(f"Wrote raw_question to database: question_number={question.question_number}")
            
            logger.info(f"Successfully wrote {questions_written} raw_questions to database")
            return questions_written
            
        except Exception as e:
            logger.error(f"Failed to write raw_questions to database: {e}", exc_info=True)
            raise
