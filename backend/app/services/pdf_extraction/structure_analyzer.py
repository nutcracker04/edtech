"""
StructureAnalyzer component for analyzing document structure.

This module analyzes document structure to identify chapters, topics, and section types.
It implements the Structure Analysis Algorithm from the design document.
"""

import re
import json
import logging
from typing import List, Optional, Tuple
from sarvamai import SarvamAI
from dotenv import load_dotenv
load_dotenv()
try:
    from .models import (
        DocumentStructure,
        Chapter,
        Topic,
        Section,
        SectionType,
        BookMetadata
    )
    from .config import get_config
except ImportError:
    # Fallback for direct script execution
    from models import (
        DocumentStructure,
        Chapter,
        Topic,
        Section,
        SectionType,
        BookMetadata
    )
    from config import get_config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StructureAnalyzer:
    """
    Analyzes document structure to identify chapters, topics, and section types.
    
    This component parses document hierarchy (chapters → topics → sub-topics),
    identifies section boundaries using pattern matching and LLM, and classifies
    sections by type (questions, answer keys, hints, explanations).
    """
    
    def __init__(self, config=None):
        """
        Initialize StructureAnalyzer.
        
        Args:
            config: Configuration for PDF extraction. If None, loads from environment.
        """
        self.config = config or get_config()
        self.client = SarvamAI(api_subscription_key=self.config.sarvam_api_key)
        logger.info("StructureAnalyzer initialized")
    
    def analyze_document(self, markdown_content: str, metadata: BookMetadata) -> DocumentStructure:
        """
        Analyze full document and return hierarchical structure.
        
        This is the main entry point for structure analysis. It implements the
        Structure Analysis Algorithm from the design document.
        
        Preconditions:
        - markdown_content is non-empty valid markdown
        - metadata contains valid book information
        
        Postconditions:
        - Returns DocumentStructure with chapters, topics, and sections identified
        - structure_confidence >= 0.7 or raises ValueError
        - All chapters have valid page ranges
        
        Loop Invariants:
        - All identified chapters have non-overlapping page ranges
        - Chapter numbers are sequential
        
        Args:
            markdown_content: Markdown content from Document Intelligence API
            metadata: Book metadata
            
        Returns:
            DocumentStructure with complete hierarchical structure
            
        Raises:
            ValueError: If structure confidence is below threshold
        """
        logger.info("Starting document structure analysis")
        
        if not markdown_content or not markdown_content.strip():
            raise ValueError("Markdown content is empty")
        
        # Split content into pages
        pages = self._split_by_page_markers(markdown_content)
        logger.info(f"Document split into {len(pages)} pages")
        
        if len(pages) == 0:
            raise ValueError("No pages found in document")
        
        # Detect chapters
        chapters = self.detect_chapters(pages)
        logger.info(f"Detected {len(chapters)} chapters")
        
        # Calculate structure confidence
        confidence = self._calculate_structure_confidence(chapters, pages)
        logger.info(f"Structure confidence: {confidence:.2f}")
        
        # Handle low structure confidence (Error Scenario 1)
        if confidence < self.config.structure_confidence_threshold:
            structure_details = {
                "chapter_count": len(chapters),
                "topic_count": sum(len(ch.topics) for ch in chapters),
                "total_pages": len(pages),
                "chapters_with_questions": sum(
                    1 for ch in chapters
                    if any(t.questions_section for t in ch.topics)
                ),
                "chapters_with_answers": sum(
                    1 for ch in chapters
                    if any(t.answer_key_section for t in ch.topics)
                ),
            }
            logger.warning(
                "Low structure confidence: %.2f (threshold: %.2f). Details: %s",
                confidence,
                self.config.structure_confidence_threshold,
                structure_details,
            )
            raise ValueError(
                f"Low structure confidence: {confidence:.2f} "
                f"(threshold: {self.config.structure_confidence_threshold}). "
                f"Manual structure annotation may be required. "
                f"Detected: {structure_details['chapter_count']} chapters, "
                f"{structure_details['topic_count']} topics."
            )
        
        # Create document structure
        structure = DocumentStructure(
            chapters=chapters,
            metadata=metadata,
            total_pages=len(pages),
            structure_confidence=confidence
        )
        
        logger.info("Document structure analysis completed successfully")
        return structure
    
    def _split_by_page_markers(self, markdown_content: str) -> List[str]:
        """
        Split markdown content by page markers.
        
        The Sarvam AI Document Intelligence API includes page markers in the format:
        <!-- Page X --> or similar markers.
        
        Args:
            markdown_content: Full markdown content
            
        Returns:
            List of page contents
        """
        # Look for page markers in various formats
        # Common patterns: <!-- Page X -->, <!--Page X-->, [Page X], etc.
        page_pattern = r'<!--\s*[Pp]age\s+(\d+)\s*-->'
        
        # Split by page markers
        parts = re.split(page_pattern, markdown_content)
        
        # If no page markers found, treat entire content as one page
        if len(parts) <= 1:
            logger.warning("No page markers found, treating as single page")
            return [markdown_content]
        
        # Reconstruct pages (parts alternate between content and page numbers)
        pages = []
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                page_content = parts[i + 1].strip()
                if page_content:
                    pages.append(page_content)
        
        # If reconstruction failed, fall back to treating as single page
        if not pages:
            logger.warning("Page reconstruction failed, treating as single page")
            return [markdown_content]
        
        return pages
    
    def detect_chapters(self, pages: List[str]) -> List[Chapter]:
        """
        Identify chapter boundaries and titles.
        
        This method implements chapter detection using pattern matching and
        processes each chapter to extract topics and special sections.
        
        Preconditions:
        - pages is non-empty list of page contents
        
        Postconditions:
        - Returns list of Chapter objects
        - All chapters have non-overlapping page ranges
        - Chapter numbers are sequential
        
        Args:
            pages: List of page contents
            
        Returns:
            List of detected chapters
        """
        chapters = []
        
        for i, page_content in enumerate(pages):
            # Check if page starts a new chapter
            if self._is_chapter_start(page_content):
                chapter_info = self._extract_chapter_info(page_content)
                
                if chapter_info:
                    chapter_number, chapter_title = chapter_info
                    
                    # Find chapter end (returns index in pages list)
                    chapter_end_idx = self._find_chapter_end(pages, i)
                    
                    # Calculate actual page numbers (1-indexed)
                    start_page = i + 1
                    end_page = chapter_end_idx + 1
                    
                    # Extract chapter pages
                    chapter_pages = pages[i:chapter_end_idx + 1]
                    
                    # Detect topics within chapter
                    try:
                        topics = self.detect_topics(chapter_pages, Chapter(
                            chapter_number=chapter_number,
                            title=chapter_title,
                            page_range=(start_page, end_page),
                            topics=[Topic(
                                title="Temporary",
                                page_range=(start_page, end_page),
                                sub_topics=[],
                                questions_section=None,
                                answer_key_section=None
                            )],
                            hints_section=None,
                            explanations_section=None
                        ))
                    except NotImplementedError:
                        # Topic detection not yet implemented, create default topic
                        topics = [Topic(
                            title="Default Topic",
                            page_range=(start_page, end_page),
                            sub_topics=[],
                            questions_section=None,
                            answer_key_section=None
                        )]
                    
                    # Create chapter object with detected topics
                    chapter = Chapter(
                        chapter_number=chapter_number,
                        title=chapter_title,
                        page_range=(start_page, end_page),
                        topics=topics,
                        hints_section=None,
                        explanations_section=None
                    )
                    
                    # Identify special sections (hints and explanations)
                    chapter.hints_section = self._find_section(chapter_pages, 'hints', start_page)
                    chapter.explanations_section = self._find_section(chapter_pages, 'explanations', start_page)
                    
                    chapters.append(chapter)
                    logger.info(f"Detected Chapter {chapter_number}: {chapter_title} (pages {start_page}-{end_page})")
        
        return chapters
    
    def _is_chapter_start(self, page_content: str) -> bool:
        """
        Determine if page content marks the start of a new chapter.
        
        Uses pattern matching to identify chapter headings in various formats:
        - "Chapter 1: Title"
        - "CHAPTER 1 - Title"
        - "1. Title" (at start of page with large heading)
        - "Chapter One: Title"
        
        Preconditions:
        - page_content is non-empty string
        - page_content is valid markdown
        
        Postconditions:
        - Returns True if page starts a chapter, False otherwise
        - No side effects on input
        
        Args:
            page_content: Content of the page
            
        Returns:
            True if page starts a chapter, False otherwise
        """
        if not page_content or not page_content.strip():
            return False
        
        # Get first few lines (chapter headings are typically at the top)
        lines = page_content.strip().split('\n')[:10]
        first_content = '\n'.join(lines)
        
        # Pattern 1: "Chapter X" or "CHAPTER X" (with optional colon/dash and title)
        chapter_pattern1 = r'(?i)^#{1,2}\s*chapter\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)'
        
        # Pattern 2: Just a number followed by title at start (markdown heading)
        chapter_pattern2 = r'^#{1,2}\s*(\d+)\s*[:\-\.]?\s+[A-Z]'
        
        # Pattern 3: "Chapter X:" or "Chapter X -" in bold or heading
        chapter_pattern3 = r'(?i)\*\*chapter\s+(\d+)'
        
        # Check patterns
        for line in lines:
            if re.search(chapter_pattern1, line):
                return True
            if re.search(chapter_pattern2, line):
                # Additional check: title should be capitalized
                return True
            if re.search(chapter_pattern3, line):
                return True
        
        return False
    
    def _extract_chapter_info(self, page_content: str) -> Optional[Tuple[int, str]]:
        """
        Extract chapter number and title from page content.
        
        Args:
            page_content: Content of the page
            
        Returns:
            Tuple of (chapter_number, chapter_title) or None if not found
        """
        lines = page_content.strip().split('\n')[:10]
        
        # Word to number mapping for chapter numbers
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'eleven': 11, 'twelve': 12
        }
        
        for line in lines:
            # Pattern 1: "Chapter X: Title" or "Chapter X - Title"
            match = re.search(r'(?i)chapter\s+((\d+)|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*[:\-]?\s*(.+)', line)
            if match:
                chapter_num_str = match.group(1).lower()
                title = match.group(3).strip()
                
                # Convert to number
                if chapter_num_str.isdigit():
                    chapter_num = int(chapter_num_str)
                else:
                    chapter_num = word_to_num.get(chapter_num_str, 1)
                
                # Clean title (remove markdown formatting)
                title = re.sub(r'[#*_]', '', title).strip()
                
                return (chapter_num, title)
            
            # Pattern 2: "# X. Title" or "## X Title"
            match = re.search(r'^#{1,2}\s*(\d+)\s*[:\-\.]?\s+(.+)', line)
            if match:
                chapter_num = int(match.group(1))
                title = match.group(2).strip()
                title = re.sub(r'[#*_]', '', title).strip()
                return (chapter_num, title)
        
        return None
    
    def _find_chapter_end(self, pages: List[str], start_index: int) -> int:
        """
        Find the end page index for a chapter.
        
        A chapter ends when:
        1. Another chapter starts
        2. End of document is reached
        
        Args:
            pages: List of all pages
            start_index: Index where chapter starts
            
        Returns:
            Index of last page in chapter
        """
        # Look for next chapter start
        for i in range(start_index + 1, len(pages)):
            if self._is_chapter_start(pages[i]):
                return i - 1
        
        # No next chapter found, this is the last chapter
        return len(pages) - 1
    
    def _find_section(self, chapter_pages: List[str], section_type: str, start_page: int) -> Optional[Section]:
        """
        Find a special section (hints or explanations) within chapter pages.
        
        Args:
            chapter_pages: List of page contents for the chapter
            section_type: Type of section to find ('hints' or 'explanations')
            start_page: Starting page number of the chapter
            
        Returns:
            Section object if found, None otherwise
        """
        # Patterns for section headings
        if section_type == 'hints':
            patterns = [
                r'(?i)^#{1,3}\s*hints?\s*$',
                r'(?i)\*\*hints?\*\*',
                r'(?i)^hints?\s*:?\s*$'
            ]
        elif section_type == 'explanations':
            patterns = [
                r'(?i)^#{1,3}\s*(explanations?|solutions?)\s*$',
                r'(?i)\*\*(explanations?|solutions?)\*\*',
                r'(?i)^(explanations?|solutions?)\s*:?\s*$'
            ]
        else:
            return None
        
        # Search for section in chapter pages
        for page_idx, page_content in enumerate(chapter_pages):
            lines = page_content.split('\n')
            
            for line_idx, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line.strip()):
                        # Found section heading
                        # Extract content from this point to end of chapter
                        section_content = '\n'.join(lines[line_idx:])
                        
                        # Add remaining pages if any
                        if page_idx < len(chapter_pages) - 1:
                            section_content += '\n' + '\n'.join(chapter_pages[page_idx + 1:])
                        
                        section_page = start_page + page_idx
                        end_page = start_page + len(chapter_pages) - 1
                        
                        # Classify section to get confidence
                        detected_type, confidence = self.classify_section(section_content, line.strip())
                        
                        return Section(
                            section_type=SectionType.HINTS if section_type == 'hints' else SectionType.EXPLANATIONS,
                            page_range=(section_page, end_page),
                            content=section_content,
                            confidence=confidence
                        )
        
        return None
    
    def detect_topics(self, chapter_pages: List[str], chapter: Chapter) -> List[Topic]:
        """
        Identify topics within a chapter.

        This method detects topic boundaries by looking for heading patterns
        that indicate topic starts. Topics are typically marked by:
        - Level 2 headings (##)
        - Numbered sections (1.1, 1.2, etc.)
        - Bold topic titles

        Preconditions:
        - chapter_pages is non-empty list of page contents
        - chapter has valid page_range

        Postconditions:
        - Returns list of Topic objects
        - All topics have valid page ranges within chapter
        - Topics have non-overlapping page ranges

        Args:
            chapter_pages: List of page contents for the chapter
            chapter: Chapter object being processed

        Returns:
            List of detected topics
        """
        if not chapter_pages:
            logger.warning("Empty chapter pages, returning default topic")
            return [Topic(
                title="Default Topic",
                page_range=chapter.page_range,
                sub_topics=[],
                questions_section=None,
                answer_key_section=None
            )]

        topics = []
        start_page = chapter.page_range[0]

        # Combine all pages into one text for better sub-topic detection
        # But track page boundaries for page range calculation
        all_lines = []
        line_to_page = []  # Maps line index to page index

        for page_idx, page_content in enumerate(chapter_pages):
            page_lines = page_content.split('\n')
            all_lines.extend(page_lines)
            line_to_page.extend([page_idx] * len(page_lines))

        # Track topic starts: (line_index, page_index, title, sub_topics)
        topic_starts = []

        # Scan all lines for topic headings
        for line_idx, line in enumerate(all_lines):
            topic_info = self._extract_topic_info(line, all_lines, line_idx)
            if topic_info:
                title, sub_topics = topic_info
                page_idx = line_to_page[line_idx]
                topic_starts.append((line_idx, page_idx, title, sub_topics))
                logger.debug(f"Found topic at line {line_idx}, page {page_idx}: {title} with {len(sub_topics)} sub-topics")

        # If no topics found, create a default topic for the entire chapter
        if not topic_starts:
            logger.info(f"No topics detected in chapter, creating default topic")
            default_topic = Topic(
                title=chapter.title,
                page_range=chapter.page_range,
                sub_topics=[],
                questions_section=None,
                answer_key_section=None
            )

            # Try to find sections in the entire chapter
            default_topic.questions_section = self._find_questions_section(
                chapter_pages, 0, len(chapter_pages), start_page
            )
            default_topic.answer_key_section = self._find_answer_key_section(
                chapter_pages, 0, len(chapter_pages), start_page
            )

            return [default_topic]

        # Create Topic objects from detected starts
        for i, (line_idx, page_idx, title, sub_topics) in enumerate(topic_starts):
            # Determine topic end
            if i < len(topic_starts) - 1:
                # Topic ends where next topic starts
                end_page_idx = topic_starts[i + 1][1]
            else:
                # Last topic extends to end of chapter
                end_page_idx = len(chapter_pages) - 1

            # Calculate actual page numbers
            topic_start_page = start_page + page_idx
            topic_end_page = start_page + end_page_idx

            # Extract topic pages
            topic_pages = chapter_pages[page_idx:end_page_idx + 1]

            # Find questions and answer key sections within this topic
            questions_section = self._find_questions_section(
                topic_pages, 0, len(topic_pages), topic_start_page
            )
            answer_key_section = self._find_answer_key_section(
                topic_pages, 0, len(topic_pages), topic_start_page
            )

            topic = Topic(
                title=title,
                page_range=(topic_start_page, topic_end_page),
                sub_topics=sub_topics,
                questions_section=questions_section,
                answer_key_section=answer_key_section
            )

            topics.append(topic)
            logger.info(f"Detected topic: {title} (pages {topic_start_page}-{topic_end_page}) with {len(sub_topics)} sub-topics")

        return topics


    def _extract_topic_info(self, line: str, lines: List[str], line_idx: int) -> Optional[Tuple[str, List[str]]]:
        """
        Extract topic title and sub-topics from a line.

        Detects topic headings in various formats:
        - ## Topic Title (level 2 heading only)
        - **Topic Title** (bold text)
        - 1.1 Topic Title (numbered section)

        Note: Level 3 headings (###) are treated as sub-topics, not main topics.

        Args:
            line: Current line to check
            lines: All lines in the page (for context)
            line_idx: Index of current line

        Returns:
            Tuple of (title, sub_topics) or None if not a topic heading
        """
        if not line or not line.strip():
            return None

        stripped = line.strip()

        # Pattern 1: Markdown heading level 2 ONLY (##)
        # Level 3 headings (###) are sub-topics, not main topics
        heading_match = re.match(r'^(#{2})\s+(.+)$', stripped)
        if heading_match:
            title = heading_match.group(2).strip()
            # Clean markdown formatting
            title = re.sub(r'[*_]', '', title)

            # Look for sub-topics in following lines
            sub_topics = self._extract_sub_topics(lines, line_idx + 1)

            return (title, sub_topics)

        # Pattern 2: Numbered section (1.1, 1.2, etc.)
        numbered_match = re.match(r'^(\d+\.\d+)\s+(.+)$', stripped)
        if numbered_match:
            title = numbered_match.group(2).strip()
            title = re.sub(r'[*_]', '', title)

            sub_topics = self._extract_sub_topics(lines, line_idx + 1)

            return (title, sub_topics)

        # Pattern 3: Bold text that looks like a topic heading
        # Must be at start of line and followed by content
        bold_match = re.match(r'^\*\*([^*]+)\*\*\s*$', stripped)
        if bold_match:
            title = bold_match.group(1).strip()

            # Only consider it a topic if it's not too long (likely a heading, not emphasis)
            if len(title) < 100 and len(title.split()) <= 10:
                sub_topics = self._extract_sub_topics(lines, line_idx + 1)
                return (title, sub_topics)

        return None


    def _extract_sub_topics(self, lines: List[str], start_idx: int, max_lines: int = 20) -> List[str]:
        """
        Extract sub-topic titles from lines following a topic heading.

        Sub-topics are typically indicated by:
        - Level 3 headings (###)
        - Level 4 headings (####)
        - Bullet points with bold text
        - Numbered sub-sections (1.1.1, 1.1.2)

        Args:
            lines: All lines in the page
            start_idx: Index to start searching from
            max_lines: Maximum number of lines to scan

        Returns:
            List of sub-topic titles
        """
        sub_topics = []

        for i in range(start_idx, min(start_idx + max_lines, len(lines))):
            line = lines[i].strip()

            if not line:
                continue

            # Stop if we hit another level 2 topic heading
            if re.match(r'^#{2}\s+[^#]', line):
                break

            # Pattern 1: Level 3 or 4 heading (### or ####)
            heading_match = re.match(r'^#{3,4}\s+(.+)$', line)
            if heading_match:
                sub_topic = heading_match.group(1).strip()
                sub_topic = re.sub(r'[*_]', '', sub_topic)
                sub_topics.append(sub_topic)
                continue

            # Pattern 2: Bullet point with bold text
            bullet_match = re.match(r'^[-*]\s+\*\*([^*]+)\*\*', line)
            if bullet_match:
                sub_topic = bullet_match.group(1).strip()
                sub_topics.append(sub_topic)
                continue

            # Pattern 3: Numbered sub-section (1.1.1, 1.1.2)
            numbered_match = re.match(r'^(\d+\.\d+\.\d+)\s+(.+)$', line)
            if numbered_match:
                sub_topic = numbered_match.group(2).strip()
                sub_topic = re.sub(r'[*_]', '', sub_topic)
                sub_topics.append(sub_topic)
                continue

        return sub_topics


    def _find_questions_section(
        self,
        pages: List[str],
        start_idx: int,
        end_idx: int,
        start_page: int
    ) -> Optional[Section]:
        """
        Find questions section within a range of pages.

        Args:
            pages: List of page contents
            start_idx: Start index in pages list
            end_idx: End index in pages list (exclusive)
            start_page: Actual page number of start_idx

        Returns:
            Section object if found, None otherwise
        """
        # Patterns for question section headings
        patterns = [
            r'(?i)^#{1,4}\s*(practice\s+)?questions?\s*$',
            r'(?i)^#{1,4}\s*exercises?\s*$',
            r'(?i)^#{1,4}\s*problems?\s*$',
            r'(?i)\*\*(practice\s+)?questions?\*\*',
            r'(?i)\*\*exercises?\*\*',
        ]

        for page_idx in range(start_idx, min(end_idx, len(pages))):
            page_content = pages[page_idx]
            lines = page_content.split('\n')

            for line_idx, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line.strip()):
                        # Found questions section
                        section_content = '\n'.join(lines[line_idx:])

                        # Add remaining pages if any
                        if page_idx < end_idx - 1:
                            section_content += '\n' + '\n'.join(pages[page_idx + 1:end_idx])

                        section_page = start_page + page_idx
                        section_end_page = start_page + end_idx - 1

                        return Section(
                            section_type=SectionType.QUESTIONS,
                            page_range=(section_page, section_end_page),
                            content=section_content,
                            confidence=0.85
                        )

        return None

    def _find_answer_key_section(
        self,
        pages: List[str],
        start_idx: int,
        end_idx: int,
        start_page: int
    ) -> Optional[Section]:
        """
        Find answer key section within a range of pages.

        Args:
            pages: List of page contents
            start_idx: Start index in pages list
            end_idx: End index in pages list (exclusive)
            start_page: Actual page number of start_idx

        Returns:
            Section object if found, None otherwise
        """
        # Patterns for answer key section headings
        patterns = [
            r'(?i)^#{1,4}\s*answer\s+keys?\s*$',
            r'(?i)^#{1,4}\s*answers?\s*$',
            r'(?i)^#{1,4}\s*solutions?\s*$',
            r'(?i)\*\*answer\s+keys?\*\*',
            r'(?i)\*\*answers?\*\*',
            r'(?i)\*\*solutions?\*\*',
        ]

        for page_idx in range(start_idx, min(end_idx, len(pages))):
            page_content = pages[page_idx]
            lines = page_content.split('\n')

            for line_idx, line in enumerate(lines):
                for pattern in patterns:
                    if re.search(pattern, line.strip()):
                        # Found answer key section
                        section_content = '\n'.join(lines[line_idx:])

                        # Add remaining pages if any
                        if page_idx < end_idx - 1:
                            section_content += '\n' + '\n'.join(pages[page_idx + 1:end_idx])

                        section_page = start_page + page_idx
                        section_end_page = start_page + end_idx - 1

                        return Section(
                            section_type=SectionType.ANSWER_KEY,
                            page_range=(section_page, section_end_page),
                            content=section_content,
                            confidence=0.85
                        )

        return None


    
    def classify_section(self, section_content: str, context: str = "") -> Tuple[SectionType, float]:
        """
        Classify section as questions, answer_key, hints, or explanations.
        
        Uses pattern matching and LLM for classification when patterns are ambiguous.
        
        Preconditions:
        - section_content is non-empty string
        
        Postconditions:
        - Returns tuple of (SectionType, confidence_score)
        - confidence_score is between 0.0 and 1.0
        - Higher confidence indicates more certain classification
        
        Args:
            section_content: Content of the section to classify
            context: Additional context (e.g., section heading)
            
        Returns:
            Tuple of (SectionType, confidence_score)
        """
        if not section_content or not section_content.strip():
            logger.warning("Empty section content provided for classification")
            return (SectionType.QUESTIONS, 0.0)
        
        # First, try pattern-based classification using context (heading)
        if context:
            pattern_result = self._classify_by_pattern(context)
            if pattern_result:
                section_type, confidence = pattern_result
                logger.info(f"Classified section by pattern: {section_type} (confidence: {confidence:.2f})")
                return (section_type, confidence)
        
        # If context didn't help, analyze the content itself
        content_result = self._classify_by_content_patterns(section_content)
        if content_result:
            section_type, confidence = content_result
            if confidence >= 0.7:
                logger.info(f"Classified section by content patterns: {section_type} (confidence: {confidence:.2f})")
                return (section_type, confidence)
        
        # If pattern matching is ambiguous (confidence < 0.7), use LLM
        logger.info("Pattern matching ambiguous, using LLM for classification")
        llm_result = self._classify_by_llm(section_content, context)
        
        return llm_result
    
    def _classify_by_pattern(self, heading: str) -> Optional[Tuple[SectionType, float]]:
        """
        Classify section based on heading patterns.
        
        Args:
            heading: Section heading text
            
        Returns:
            Tuple of (SectionType, confidence) or None if no match
        """
        heading_lower = heading.lower().strip()
        
        # High confidence patterns for explanations (check first to avoid conflicts)
        explanations_patterns = [
            (r'\bdetailed\s+solutions?\b', 0.95),
            (r'\bworked\s+solutions?\b', 0.95),
            (r'\bsolution\s+explanations?\b', 0.95),
            (r'\bexplanations?\b', 0.95),
        ]
        
        # High confidence patterns for questions
        questions_patterns = [
            (r'\b(practice\s+)?questions?\b', 0.95),
            (r'\bexercises?\b', 0.90),
            (r'\bproblems?\b', 0.85),
            (r'\bpractice\s+problems?\b', 0.95),
        ]
        
        # High confidence patterns for answer keys
        answer_patterns = [
            (r'\banswer\s+keys?\b', 0.95),
            (r'\banswers?\b', 0.85),
            (r'\bkey\s+to\s+exercises?\b', 0.90),
        ]
        
        # High confidence patterns for hints
        hints_patterns = [
            (r'\bhints?\b', 0.95),
            (r'\btips?\b', 0.80),
            (r'\bclues?\b', 0.85),
        ]
        
        # Check explanations first (to avoid "detailed solutions" matching "solutions" as answer key)
        for pattern, confidence in explanations_patterns:
            if re.search(pattern, heading_lower):
                return (SectionType.EXPLANATIONS, confidence)
        
        # Check each pattern type
        for pattern, confidence in questions_patterns:
            if re.search(pattern, heading_lower):
                return (SectionType.QUESTIONS, confidence)
        
        for pattern, confidence in answer_patterns:
            if re.search(pattern, heading_lower):
                return (SectionType.ANSWER_KEY, confidence)
        
        for pattern, confidence in hints_patterns:
            if re.search(pattern, heading_lower):
                return (SectionType.HINTS, confidence)
        
        # Check for generic "solutions" last (lower confidence, could be either)
        if re.search(r'\bsolutions?\b', heading_lower):
            return (SectionType.ANSWER_KEY, 0.70)
        
        return None
    
    def _classify_by_content_patterns(self, content: str) -> Optional[Tuple[SectionType, float]]:
        """
        Classify section based on content patterns.
        
        Analyzes the structure and format of the content to determine section type.
        
        Args:
            content: Section content
            
        Returns:
            Tuple of (SectionType, confidence) or None if no clear match
        """
        # Take first 500 characters for analysis
        sample = content[:500].lower()
        lines = content.split('\n')[:20]  # First 20 lines
        
        # Count different patterns
        question_indicators = 0
        answer_indicators = 0
        hint_indicators = 0
        explanation_indicators = 0
        
        # Question patterns: numbered items, question marks, "find", "calculate", etc.
        question_patterns = [
            r'\?',  # Question marks
            r'\b(find|calculate|determine|prove|show|solve|evaluate|compute)\b',
            r'\b(what|why|how|when|where|which)\b',
        ]
        
        # Answer key patterns: short answers, letter answers, numerical answers
        # These are more specific to avoid false positives
        answer_patterns = [
            r'^\d+[\.\)]\s*\([a-d]\)\s*$',  # "1. (a)" format alone on line
            r'^\d+[\.\)]\s*[a-d]\)\s*$',  # "1. a)" format alone on line
            r'^\d+[\.\)]\s*[a-d]\s*$',  # "1. a" format alone on line
            r'^\d+[\.\)]\s*[-+]?\d+\.?\d*\s*$',  # "1. 42" or "1. 3.14" alone on line
            r'\bans(wer)?[:\.]?\s*\([a-d]\)',  # "Ans: (a)" or "Answer: (a)"
            r'\bans(wer)?[:\.]?\s*[a-d]\)',  # "Ans: a)" or "Answer: a)"
        ]
        
        # Hint patterns: "hint:", "tip:", shorter explanatory text
        hint_patterns = [
            r'\bhint[:\.]',
            r'\btip[:\.]',
            r'\bconsider\b',
            r'\bthink about\b',
            r'\btry\b',
        ]
        
        # Explanation patterns: "solution:", "explanation:", detailed working
        explanation_patterns = [
            r'\bsolution[:\.]',
            r'\bexplanation[:\.]',
            r'\bstep\s+\d+',
            r'\btherefore\b',
            r'\bhence\b',
            r'\bgiven\b.*\bfind\b',
        ]
        
        # Count pattern matches in lines
        for line in lines:
            line_lower = line.lower().strip()
            if not line_lower:
                continue
            
            # Check if line starts with number (common in all types)
            has_number_prefix = bool(re.match(r'^\d+[\.\)]', line_lower))
            
            # Check answer patterns first (most specific)
            matched_answer = False
            for pattern in answer_patterns:
                if re.search(pattern, line_lower):
                    answer_indicators += 2  # Weight answer patterns higher
                    matched_answer = True
                    break
            
            if matched_answer:
                continue
            
            # Check other patterns
            for pattern in question_patterns:
                if re.search(pattern, line_lower):
                    question_indicators += 1
                    break
            
            for pattern in hint_patterns:
                if re.search(pattern, line_lower):
                    hint_indicators += 1
                    break
            
            for pattern in explanation_patterns:
                if re.search(pattern, line_lower):
                    explanation_indicators += 1
                    break
        
        # Determine section type based on indicator counts
        max_indicators = max(question_indicators, answer_indicators, hint_indicators, explanation_indicators)
        
        if max_indicators == 0:
            return None
        
        # Calculate confidence based on indicator strength
        total_indicators = question_indicators + answer_indicators + hint_indicators + explanation_indicators
        
        if answer_indicators == max_indicators and answer_indicators > 0:
            confidence = min(0.6 + (answer_indicators / total_indicators) * 0.3, 0.9)
            return (SectionType.ANSWER_KEY, confidence)
        elif question_indicators == max_indicators:
            confidence = min(0.6 + (question_indicators / total_indicators) * 0.3, 0.9)
            return (SectionType.QUESTIONS, confidence)
        elif hint_indicators == max_indicators:
            confidence = min(0.6 + (hint_indicators / total_indicators) * 0.3, 0.9)
            return (SectionType.HINTS, confidence)
        elif explanation_indicators == max_indicators:
            confidence = min(0.6 + (explanation_indicators / total_indicators) * 0.3, 0.9)
            return (SectionType.EXPLANATIONS, confidence)
        
        return None
    
    def _classify_by_llm(self, content: str, context: str) -> Tuple[SectionType, float]:
        """
        Classify section using LLM when pattern matching is ambiguous.
        
        Args:
            content: Section content
            context: Section heading or context
            
        Returns:
            Tuple of (SectionType, confidence)
        """
        # Prepare content sample (limit to avoid token limits)
        content_sample = content[:1000] if len(content) > 1000 else content
        
        # Create classification prompt
        prompt = f"""Analyze the following section from a textbook and classify it into one of these types:
1. questions - Contains practice questions or exercises for students
2. answer_key - Contains answers to questions (typically short answers, letter choices, or numbers)
3. hints - Contains hints or tips to help solve questions
4. explanations - Contains detailed explanations or worked solutions

Section heading: {context if context else "Not provided"}

Section content:
{content_sample}

Respond with ONLY a JSON object in this exact format:
{{"section_type": "questions|answer_key|hints|explanations", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""
        
        try:
            # Call LLM using Sarvam AI chat completions
            response = self.client.chat.completions(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a textbook structure analyzer. Classify sections accurately based on their content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"LLM classification response: {response_text}")
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                result = json.loads(json_match.group(0))
                
                section_type_str = result.get("section_type", "questions")
                confidence = float(result.get("confidence", 0.5))
                
                # Map string to SectionType enum
                section_type_map = {
                    "questions": SectionType.QUESTIONS,
                    "answer_key": SectionType.ANSWER_KEY,
                    "hints": SectionType.HINTS,
                    "explanations": SectionType.EXPLANATIONS,
                }
                
                section_type = section_type_map.get(section_type_str, SectionType.QUESTIONS)
                
                # Ensure confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))
                
                logger.info(f"LLM classified section as {section_type} with confidence {confidence:.2f}")
                logger.debug(f"LLM reasoning: {result.get('reasoning', 'N/A')}")
                
                return (section_type, confidence)
            else:
                logger.warning("Could not parse JSON from LLM response, using default")
                return (SectionType.QUESTIONS, 0.5)
                
        except Exception as e:
            logger.error(f"Error during LLM classification: {e}")
            # Fallback to questions with low confidence
            return (SectionType.QUESTIONS, 0.5)
    
    def _calculate_structure_confidence(self, chapters: List[Chapter], pages: List[str]) -> float:
        """
        Calculate confidence score for detected structure.
        
        This implements the calculate_structure_confidence() function from the design.
        
        Preconditions:
        - chapters list may be empty
        - pages list is non-empty
        - All chapters have valid page_ranges
        
        Postconditions:
        - Returns float between 0.0 and 1.0
        - Higher score indicates better structure detection
        - Score >= 0.7 indicates acceptable structure
        - Considers: chapter count, topic count, section completeness
        
        Loop Invariants:
        - For chapter iteration: confidence score remains in [0.0, 1.0]
        
        Args:
            chapters: List of detected chapters
            pages: List of all pages
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not chapters:
            return 0.0
        
        if not pages:
            return 0.0
        
        # Component 1: Chapter detection score (0.0 to 0.4)
        # More chapters indicate better structure detection
        # Typical textbooks have 5-15 chapters
        chapter_count = len(chapters)
        if chapter_count >= 5:
            chapter_score = 0.4
        elif chapter_count >= 3:
            chapter_score = 0.3
        elif chapter_count >= 1:
            chapter_score = 0.2
        else:
            chapter_score = 0.0
        
        # Component 2: Topic detection score (0.0 to 0.3)
        # More topics indicate better structure detection
        total_topics = sum(len(chapter.topics) for chapter in chapters)
        avg_topics_per_chapter = total_topics / chapter_count if chapter_count > 0 else 0
        
        if avg_topics_per_chapter >= 3:
            topic_score = 0.3
        elif avg_topics_per_chapter >= 2:
            topic_score = 0.2
        elif avg_topics_per_chapter >= 1:
            topic_score = 0.1
        else:
            topic_score = 0.0
        
        # Component 3: Section completeness score (0.0 to 0.3)
        # Chapters with questions and answer key sections indicate better structure
        chapters_with_questions = 0
        chapters_with_answers = 0
        total_sections = 0
        
        for chapter in chapters:
            # Loop invariant: confidence score remains in [0.0, 1.0]
            has_questions = False
            has_answers = False
            
            for topic in chapter.topics:
                if topic.questions_section is not None:
                    has_questions = True
                    total_sections += 1
                if topic.answer_key_section is not None:
                    has_answers = True
                    total_sections += 1
            
            if has_questions:
                chapters_with_questions += 1
            if has_answers:
                chapters_with_answers += 1
        
        # Calculate section completeness ratio
        if chapter_count > 0:
            questions_ratio = chapters_with_questions / chapter_count
            answers_ratio = chapters_with_answers / chapter_count
            section_score = (questions_ratio * 0.15) + (answers_ratio * 0.15)
        else:
            section_score = 0.0
        
        # Combine all components
        confidence = chapter_score + topic_score + section_score
        
        # Ensure confidence is in valid range [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
