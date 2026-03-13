"""
RelationshipLinker component for linking questions to answers, hints, and explanations.

This module links questions to their answer keys, hints, and explanations across
document sections. It implements the Relationship Linking Algorithm from the design document.
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple

try:
    from .models import (
        RawQuestion,
        LinkedQuestion,
        AnswerKey,
        Hint,
        Explanation,
    )
except ImportError:
    # Fallback for direct script execution
    from models import (
        RawQuestion,
        LinkedQuestion,
        AnswerKey,
        Hint,
        Explanation,
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelationshipLinker:
    """
    Links questions to their answer keys, hints, and explanations.
    
    This component matches questions to answer keys using question numbers/identifiers,
    links questions to hints from chapter-end sections, and links questions to
    explanations from chapter-end sections. It handles missing or ambiguous links
    and validates link consistency.
    """
    
    def __init__(self, config=None):
        """
        Initialize RelationshipLinker.

        Args:
            config: Optional configuration object with sarvam_api_key
        """
        try:
            from .document_processor import get_config
        except ImportError:
            from document_processor import get_config

        self.config = config or get_config()

        # Import SarvamAI client
        try:
            from sarvamai import SarvamAI
            self.client = SarvamAI(api_subscription_key=self.config.sarvam_api_key)
        except ImportError:
            logger.warning("sarvamai package not installed, fuzzy matching will be disabled")
            self.client = None

        logger.info("RelationshipLinker initialized")
    
    def link_answers(
        self,
        questions: List[RawQuestion],
        answer_keys: List[AnswerKey]
    ) -> List[LinkedQuestion]:
        """
        Link questions to their answer keys.
        
        This method implements exact question number matching with O(1) lookup
        using dictionaries. It calculates link confidence scores for each match.
        
        Preconditions:
        - questions list is non-empty
        - All lists contain items with valid question_numbers
        - question_numbers follow consistent format
        
        Postconditions:
        - Returns LinkedQuestion objects with answer relationships established
        - All MCQ questions have answer_key linked (or confidence < 1.0)
        - link_confidence scores calculated for all links
        
        Loop Invariants:
        - All processed questions maintain their original data
        - Link confidence scores remain between 0.0 and 1.0
        
        Args:
            questions: List of RawQuestion objects to link
            answer_keys: List of AnswerKey objects to link from
            
        Returns:
            List of LinkedQuestion objects with answer keys linked
            
        Raises:
            ValueError: If questions list is empty
        """
        if not questions:
            raise ValueError("Questions list cannot be empty")
        
        logger.info(
            f"Linking {len(questions)} questions to {len(answer_keys)} answer keys"
        )
        
        # Create lookup dictionary for O(1) access
        # Key: normalized question number, Value: AnswerKey object
        answer_map: Dict[str, AnswerKey] = {}
        for answer in answer_keys:
            normalized_num = self._normalize_question_number(answer.question_number)
            answer_map[normalized_num] = answer
        
        logger.debug(f"Created answer lookup map with {len(answer_map)} entries")
        
        linked_questions = []
        exact_matches = 0
        fuzzy_matches = 0
        no_matches = 0
        
        for question in questions:
            # Normalize question number for matching
            qnum = self._normalize_question_number(question.question_number)
            
            # Attempt exact match
            answer_key = None
            answer_confidence = 0.0
            
            if qnum in answer_map:
                # Exact match found
                answer_key = answer_map[qnum].answer
                answer_confidence = 1.0
                exact_matches += 1
                logger.debug(f"Exact match for question {question.question_number}")
            else:
                # Try fuzzy matching
                answer_key, answer_confidence = self._fuzzy_match_answer(question, answer_keys)
                
                if answer_key and answer_confidence >= 0.7:
                    fuzzy_matches += 1
                    logger.debug(
                        f"Fuzzy match for question {question.question_number} "
                        f"(confidence: {answer_confidence})"
                    )
                else:
                    no_matches += 1
                    logger.warning(
                        "No answer key found for question %s (chapter: %s, topic: %s)",
                        question.question_number,
                        question.chapter_context,
                        question.topic_context,
                    )
            
            # Create LinkedQuestion object
            linked = LinkedQuestion(
                raw_question=question,
                answer_key=answer_key,
                hint=None,  # Will be linked in link_hints()
                explanation=None,  # Will be linked in link_explanations()
                link_confidence={
                    'answer': answer_confidence,
                }
            )
            
            linked_questions.append(linked)
        
        logger.info(
            f"Linking complete: {exact_matches} exact matches, "
            f"{fuzzy_matches} fuzzy matches, "
            f"{no_matches} no matches"
        )
        
        # Log warning for MCQ questions without answers
        mcq_without_answers = [
            q for q in linked_questions
            if q.raw_question.options is not None and q.answer_key is None
        ]
        if mcq_without_answers:
            logger.warning(
                f"{len(mcq_without_answers)} MCQ questions have no answer keys"
            )
        
        return linked_questions

    def link_hints(
        self,
        questions: List[LinkedQuestion],
        hints: List[Hint]
    ) -> List[LinkedQuestion]:
        """
        Link questions to their hints.

        This method implements exact question number matching with O(1) lookup
        using dictionaries. It calculates link confidence scores for each match.
        Similar to link_answers(), it uses exact matching first, then falls back
        to fuzzy matching when needed.

        Preconditions:
        - questions list is non-empty
        - All lists contain items with valid question_numbers
        - question_numbers follow consistent format

        Postconditions:
        - Returns LinkedQuestion objects with hint relationships established
        - link_confidence scores calculated for all hint links

        Loop Invariants:
        - All processed questions maintain their original data
        - Link confidence scores remain between 0.0 and 1.0

        Args:
            questions: List of LinkedQuestion objects to link
            hints: List of Hint objects to link from

        Returns:
            List of LinkedQuestion objects with hints linked

        Raises:
            ValueError: If questions list is empty
        """
        if not questions:
            raise ValueError("Questions list cannot be empty")

        logger.info(
            f"Linking {len(questions)} questions to {len(hints)} hints"
        )

        # Create lookup dictionary for O(1) access
        # Key: normalized question number, Value: Hint object
        hint_map: Dict[str, Hint] = {}
        for hint in hints:
            normalized_num = self._normalize_question_number(hint.question_number)
            hint_map[normalized_num] = hint

        logger.debug(f"Created hint lookup map with {len(hint_map)} entries")

        linked_questions = []
        exact_matches = 0
        fuzzy_matches = 0
        no_matches = 0

        for question in questions:
            # Normalize question number for matching
            qnum = self._normalize_question_number(question.raw_question.question_number)

            # Attempt exact match
            hint = None
            hint_confidence = 0.0

            if qnum in hint_map:
                # Exact match found
                hint = hint_map[qnum].hint_text
                hint_confidence = 1.0
                exact_matches += 1
                logger.debug(f"Exact match for question {question.raw_question.question_number}")
            else:
                # Try fuzzy matching
                hint, hint_confidence = self._fuzzy_match_hint(question.raw_question, hints)

                if hint and hint_confidence >= 0.7:
                    fuzzy_matches += 1
                    logger.debug(
                        f"Fuzzy match for question {question.raw_question.question_number} "
                        f"(confidence: {hint_confidence})"
                    )
                else:
                    # No match found
                    no_matches += 1
                    logger.debug(f"No hint found for question {question.raw_question.question_number}")

            # Update LinkedQuestion object with hint
            question.hint = hint
            question.link_confidence['hint'] = hint_confidence

            linked_questions.append(question)

        logger.info(
            f"Hint linking complete: {exact_matches} exact matches, "
            f"{fuzzy_matches} fuzzy matches, "
            f"{no_matches} no matches"
        )

        return linked_questions

    def link_explanations(
        self,
        questions: List[LinkedQuestion],
        explanations: List[Explanation]
    ) -> List[LinkedQuestion]:
        """
        Link questions to their explanations.

        This method implements exact question number matching with O(1) lookup
        using dictionaries. It calculates link confidence scores for each match.
        Similar to link_answers() and link_hints(), it uses exact matching first,
        then falls back to fuzzy matching when needed.

        Preconditions:
        - questions list is non-empty
        - All lists contain items with valid question_numbers
        - question_numbers follow consistent format

        Postconditions:
        - Returns LinkedQuestion objects with explanation relationships established
        - link_confidence scores calculated for all explanation links

        Loop Invariants:
        - All processed questions maintain their original data
        - Link confidence scores remain between 0.0 and 1.0

        Args:
            questions: List of LinkedQuestion objects to link
            explanations: List of Explanation objects to link from

        Returns:
            List of LinkedQuestion objects with explanations linked

        Raises:
            ValueError: If questions list is empty
        """
        if not questions:
            raise ValueError("Questions list cannot be empty")

        logger.info(
            f"Linking {len(questions)} questions to {len(explanations)} explanations"
        )

        # Create lookup dictionary for O(1) access
        # Key: normalized question number, Value: Explanation object
        explanation_map: Dict[str, Explanation] = {}
        for explanation in explanations:
            normalized_num = self._normalize_question_number(explanation.question_number)
            explanation_map[normalized_num] = explanation

        logger.debug(f"Created explanation lookup map with {len(explanation_map)} entries")

        linked_questions = []
        exact_matches = 0
        fuzzy_matches = 0
        no_matches = 0

        for question in questions:
            # Normalize question number for matching
            qnum = self._normalize_question_number(question.raw_question.question_number)

            # Attempt exact match
            explanation = None
            explanation_confidence = 0.0

            if qnum in explanation_map:
                # Exact match found
                explanation = explanation_map[qnum].explanation_text
                explanation_confidence = 1.0
                exact_matches += 1
                logger.debug(f"Exact match for question {question.raw_question.question_number}")
            else:
                # Try fuzzy matching
                explanation, explanation_confidence = self._fuzzy_match_explanation(
                    question.raw_question, explanations
                )

                if explanation and explanation_confidence >= 0.7:
                    fuzzy_matches += 1
                    logger.debug(
                        f"Fuzzy match for question {question.raw_question.question_number} "
                        f"(confidence: {explanation_confidence})"
                    )
                else:
                    # No match found
                    no_matches += 1
                    logger.debug(
                        f"No explanation found for question {question.raw_question.question_number}"
                    )

            # Update LinkedQuestion object with explanation
            question.explanation = explanation
            question.link_confidence['explanation'] = explanation_confidence

            linked_questions.append(question)

        logger.info(
            f"Explanation linking complete: {exact_matches} exact matches, "
            f"{fuzzy_matches} fuzzy matches, "
            f"{no_matches} no matches"
        )

        return linked_questions
    
    def validate_links(
            self,
            questions: List[LinkedQuestion]
        ) -> Dict[str, any]:
            """
            Validate the quality of links between questions and their answers/hints/explanations.

            This method implements link validation as specified in Design Component 4.
            It validates that MCQ questions have answer keys (Property 2) and flags
            low confidence links for manual review (Property 6).

            Preconditions:
            - questions list is non-empty
            - All questions have link_confidence scores

            Postconditions:
            - Returns validation report with statistics and flagged questions
            - All MCQ questions without answers are flagged
            - All links with confidence < 0.7 are flagged

            Args:
                questions: List of LinkedQuestion objects to validate

            Returns:
                Dictionary containing:
                - 'total_questions': Total number of questions validated
                - 'mcq_without_answers': List of MCQ questions missing answer keys
                - 'low_confidence_answers': List of questions with low answer confidence
                - 'low_confidence_hints': List of questions with low hint confidence
                - 'low_confidence_explanations': List of questions with low explanation confidence
                - 'validation_passed': Boolean indicating if all critical validations passed

            Raises:
                ValueError: If questions list is empty
            """
            if not questions:
                raise ValueError("Questions list cannot be empty")

            logger.info(f"Validating links for {len(questions)} questions")

            # Track validation issues
            mcq_without_answers = []
            low_confidence_answers = []
            low_confidence_hints = []
            low_confidence_explanations = []

            confidence_threshold = 0.7

            for question in questions:
                qnum = question.raw_question.question_number

                # Property 2: Validate MCQ questions have answer keys
                if question.raw_question.options is not None:
                    if question.answer_key is None:
                        mcq_without_answers.append({
                            'question_number': qnum,
                            'question_text': question.raw_question.question_text[:100],
                            'chapter': question.raw_question.chapter_context,
                            'topic': question.raw_question.topic_context,
                        })
                        logger.warning(
                            f"MCQ question {qnum} missing answer key "
                            f"(Chapter: {question.raw_question.chapter_context}, "
                            f"Topic: {question.raw_question.topic_context})"
                        )

                # Property 6: Flag low confidence links for review
                answer_confidence = question.link_confidence.get('answer', 0.0)
                if 0.0 < answer_confidence < confidence_threshold:
                    low_confidence_answers.append({
                        'question_number': qnum,
                        'confidence': answer_confidence,
                        'answer_key': question.answer_key,
                        'question_text': question.raw_question.question_text[:100],
                    })
                    logger.warning(
                        f"Question {qnum} has low answer confidence: {answer_confidence}"
                    )

                hint_confidence = question.link_confidence.get('hint', 0.0)
                if 0.0 < hint_confidence < confidence_threshold:
                    low_confidence_hints.append({
                        'question_number': qnum,
                        'confidence': hint_confidence,
                        'hint': question.hint[:100] if question.hint else None,
                    })
                    logger.debug(
                        f"Question {qnum} has low hint confidence: {hint_confidence}"
                    )

                explanation_confidence = question.link_confidence.get('explanation', 0.0)
                if 0.0 < explanation_confidence < confidence_threshold:
                    low_confidence_explanations.append({
                        'question_number': qnum,
                        'confidence': explanation_confidence,
                        'explanation': question.explanation[:100] if question.explanation else None,
                    })
                    logger.debug(
                        f"Question {qnum} has low explanation confidence: {explanation_confidence}"
                    )

            # Determine if validation passed (critical issues only)
            validation_passed = len(mcq_without_answers) == 0

            # Create validation report
            report = {
                'total_questions': len(questions),
                'mcq_without_answers': mcq_without_answers,
                'low_confidence_answers': low_confidence_answers,
                'low_confidence_hints': low_confidence_hints,
                'low_confidence_explanations': low_confidence_explanations,
                'validation_passed': validation_passed,
            }

            # Log summary
            logger.info(
                f"Validation complete: "
                f"{len(mcq_without_answers)} MCQs without answers, "
                f"{len(low_confidence_answers)} low confidence answers, "
                f"{len(low_confidence_hints)} low confidence hints, "
                f"{len(low_confidence_explanations)} low confidence explanations"
            )

            if not validation_passed:
                logger.error(
                    f"Validation FAILED: {len(mcq_without_answers)} MCQ questions missing answer keys"
                )
            else:
                logger.info("Validation PASSED: All critical checks passed")

            return report
    
    def resolve_ambiguous_links(
            self,
            question: RawQuestion,
            candidates: List[any],
            link_type: str = 'answer'
        ) -> Tuple[Optional[any], float]:
            """
            Resolve ambiguous question-to-content links using LLM.

            This method uses the Sarvam AI LLM to intelligently resolve cases where
            multiple candidates might match a question, or when the best match is unclear.
            It provides detailed reasoning for the match decision.

            Preconditions:
            - question has valid question_text
            - candidates list is non-empty
            - link_type is one of: 'answer', 'hint', 'explanation'

            Postconditions:
            - Returns (matched_item, confidence) tuple
            - confidence is between 0.0 and 1.0
            - Returns (None, 0.0) if no reliable match found

            Args:
                question: RawQuestion object to match
                candidates: List of candidate objects (AnswerKey, Hint, or Explanation)
                link_type: Type of link to resolve ('answer', 'hint', or 'explanation')

            Returns:
                Tuple of (matched_item, confidence_score)
                Returns (None, 0.0) if no match found or confidence below threshold

            Raises:
                ValueError: If link_type is not valid
            """
            if link_type not in ['answer', 'hint', 'explanation']:
                raise ValueError(f"Invalid link_type: {link_type}. Must be 'answer', 'hint', or 'explanation'")

            if not self.client:
                logger.warning("LLM client not available, cannot resolve ambiguous links")
                return (None, 0.0)

            if not candidates:
                return (None, 0.0)

            logger.info(
                f"Resolving ambiguous {link_type} link for question {question.question_number} "
                f"with {len(candidates)} candidates"
            )

            # Truncate question text for prompt
            question_text = question.question_text[:400]
            if len(question.question_text) > 400:
                question_text += "..."

            # Format candidates based on type
            candidate_list = []
            for i, candidate in enumerate(candidates[:10]):  # Limit to 10 candidates
                if link_type == 'answer':
                    candidate_list.append(
                        f"  {i+1}. Question Number: {candidate.question_number}, "
                        f"Answer: {candidate.answer}"
                    )
                elif link_type == 'hint':
                    hint_preview = candidate.hint_text[:150]
                    if len(candidate.hint_text) > 150:
                        hint_preview += "..."
                    candidate_list.append(
                        f"  {i+1}. Question Number: {candidate.question_number}, "
                        f"Hint: {hint_preview}"
                    )
                elif link_type == 'explanation':
                    explanation_preview = candidate.explanation_text[:150]
                    if len(candidate.explanation_text) > 150:
                        explanation_preview += "..."
                    candidate_list.append(
                        f"  {i+1}. Question Number: {candidate.question_number}, "
                        f"Explanation: {explanation_preview}"
                    )

            candidates_text = "\n".join(candidate_list)

            prompt = f"""You are resolving an ambiguous link between a question and its {link_type}. Multiple candidates are available and you need to determine the best match.

    Question Number: {question.question_number}
    Question Text: {question_text}
    Chapter Context: {question.chapter_context}
    Topic Context: {question.topic_context}

    Candidate {link_type.capitalize()}s:
    {candidates_text}

    Task: Determine which candidate is the best match for this question.

    Return a JSON object with:
    - "candidate_index": the 1-based index of the best matching candidate (or null if no good match)
    - "confidence": a number between 0.0 and 1.0 indicating match confidence
    - "reasoning": brief explanation of why this candidate was chosen

    Consider:
    1. Question number similarity and format variations
    2. Context alignment (chapter/topic)
    3. Content relevance (does the {link_type} make sense for this question?)
    4. Only return confidence >= 0.7 for reliable matches

    Format: {{"candidate_index": 1, "confidence": 0.95, "reasoning": "Question numbers match and context aligns"}}
    """

            try:
                response = self.client.chat.completions.create(
                    model="sarvam-2b-v0.5",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # Low temperature for consistent matching
                    max_tokens=300,
                )

                result_text = response.choices[0].message.content.strip()

                # Parse JSON response
                result = json.loads(result_text)

                candidate_index = result.get("candidate_index")
                confidence = float(result.get("confidence", 0.0))
                reasoning = result.get("reasoning", "No reasoning provided")

                # Validate confidence is in valid range
                confidence = max(0.0, min(1.0, confidence))

                # Apply confidence threshold
                if confidence < 0.7:
                    logger.info(
                        f"Ambiguous link resolution for question {question.question_number} "
                        f"below threshold: {confidence}. Reasoning: {reasoning}"
                    )
                    return (None, 0.0)

                # Get the matched candidate
                if candidate_index and 1 <= candidate_index <= len(candidates):
                    matched_candidate = candidates[candidate_index - 1]
                    logger.info(
                        f"Resolved ambiguous {link_type} link for question {question.question_number} "
                        f"-> candidate {candidate_index} (confidence: {confidence}). "
                        f"Reasoning: {reasoning}"
                    )
                    return (matched_candidate, confidence)

                return (None, 0.0)

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response for ambiguous link resolution: {e}")
                logger.debug(f"Response text: {result_text}")
                return (None, 0.0)
            except Exception as e:
                logger.error(
                    f"Ambiguous link resolution failed for question {question.question_number}: {e}"
                )
                return (None, 0.0)



    
    def _normalize_question_number(self, raw_number: str) -> str:
        """
        Normalize question number to standard format for matching.
        
        This function is idempotent: normalize(normalize(x)) == normalize(x)
        
        Removes common prefixes (Question, Q) and punctuation to create
        a consistent format for matching across questions and answer keys.
        
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
            "Question 5" -> "5"
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
    
    def _fuzzy_match_answer(
        self,
        question: RawQuestion,
        answers: List[AnswerKey]
    ) -> Tuple[Optional[str], float]:
        """
        Use LLM to match question to answer when direct match fails.
        
        This method implements the Fuzzy Matching Algorithm from the design document.
        It uses the Sarvam AI LLM to intelligently match questions to answer keys
        based on content similarity and context when exact question number matching fails.
        
        Preconditions:
        - question has valid question_text
        - answers list is non-empty
        
        Postconditions:
        - Returns (answer, confidence) tuple
        - confidence is between 0.0 and 1.0
        - Returns (None, 0.0) if no match found or confidence < 0.7
        
        Args:
            question: RawQuestion object to match
            answers: List of AnswerKey objects to match from
            
        Returns:
            Tuple of (answer_text, confidence_score)
            Returns (None, 0.0) if no match found or confidence below threshold
        """
        if not self.client:
            logger.warning("LLM client not available, fuzzy matching disabled")
            return (None, 0.0)
        
        if not answers:
            return (None, 0.0)
        
        # Truncate question text for prompt
        question_text = question.question_text[:300]
        if len(question.question_text) > 300:
            question_text += "..."
        
        # Format available answer keys for prompt
        answer_list = []
        for i, answer in enumerate(answers[:20]):  # Limit to 20 answers to avoid token limits
            answer_list.append(
                f"  - Question Number: {answer.question_number}, Answer: {answer.answer}"
            )
        answer_keys_text = "\n".join(answer_list)
        
        prompt = f"""You are matching a question to its answer key. The question number format may differ between the question and answer key.

Question Number: {question.question_number}
Question Text: {question_text}
Chapter Context: {question.chapter_context}
Topic Context: {question.topic_context}

Available Answer Keys:
{answer_keys_text}

Task: Determine which answer key matches this question based on question number similarity and context.

Return a JSON object with:
- "question_number": the matching answer key's question number (or null if no match)
- "confidence": a number between 0.0 and 1.0 indicating match confidence

Consider:
1. Question number similarity (e.g., "1a" might match "1.a" or "Q1a")
2. Context alignment (chapter/topic)
3. Only return confidence >= 0.7 for reliable matches

Format: {{"question_number": "X", "confidence": 0.95}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="sarvam-2b-v0.5",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=200,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            result = json.loads(result_text)
            
            matched_qnum = result.get("question_number")
            confidence = float(result.get("confidence", 0.0))
            
            # Validate confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            # Apply confidence threshold
            if confidence < 0.7:
                logger.debug(
                    f"Fuzzy match for question {question.question_number} "
                    f"below threshold: {confidence}"
                )
                return (None, 0.0)
            
            # Find the matched answer
            if matched_qnum:
                for answer in answers:
                    if answer.question_number == matched_qnum:
                        logger.info(
                            f"Fuzzy match found for question {question.question_number} "
                            f"-> {matched_qnum} (confidence: {confidence})"
                        )
                        return (answer.answer, confidence)
            
            return (None, 0.0)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for fuzzy matching: {e}")
            logger.debug(f"Response text: {result_text}")
            return (None, 0.0)
        except Exception as e:
            logger.error(f"Fuzzy matching failed for question {question.question_number}: {e}")
            return (None, 0.0)
    
    def _fuzzy_match_hint(
        self,
        question: RawQuestion,
        hints: List[Hint]
    ) -> Tuple[Optional[str], float]:
        """
        Use LLM to match question to hint when direct match fails.

        This method implements the Fuzzy Matching Algorithm from the design document.
        It uses the Sarvam AI LLM to intelligently match questions to hints
        based on content similarity and context when exact question number matching fails.

        Preconditions:
        - question has valid question_text
        - hints list is non-empty

        Postconditions:
        - Returns (hint, confidence) tuple
        - confidence is between 0.0 and 1.0
        - Returns (None, 0.0) if no match found or confidence < 0.7

        Args:
            question: RawQuestion object to match
            hints: List of Hint objects to match from

        Returns:
            Tuple of (hint_text, confidence_score)
            Returns (None, 0.0) if no match found or confidence below threshold
        """
        if not self.client:
            logger.warning("LLM client not available, fuzzy matching disabled")
            return (None, 0.0)

        if not hints:
            return (None, 0.0)

        # Truncate question text for prompt
        question_text = question.question_text[:300]
        if len(question.question_text) > 300:
            question_text += "..."

        # Format available hints for prompt
        hint_list = []
        for i, hint in enumerate(hints[:20]):  # Limit to 20 hints to avoid token limits
            hint_preview = hint.hint_text[:100]
            if len(hint.hint_text) > 100:
                hint_preview += "..."
            hint_list.append(
                f"  - Question Number: {hint.question_number}, Hint: {hint_preview}"
            )
        hints_text = "\n".join(hint_list)

        prompt = f"""You are matching a question to its hint. The question number format may differ between the question and hint.

Question Number: {question.question_number}
Question Text: {question_text}
Chapter Context: {question.chapter_context}
Topic Context: {question.topic_context}

Available Hints:
{hints_text}

Task: Determine which hint matches this question based on question number similarity and context.

Return a JSON object with:
- "question_number": the matching hint's question number (or null if no match)
- "confidence": a number between 0.0 and 1.0 indicating match confidence

Consider:
1. Question number similarity (e.g., "1a" might match "1.a" or "Q1a")
2. Context alignment (chapter/topic)
3. Only return confidence >= 0.7 for reliable matches

Format: {{"question_number": "X", "confidence": 0.95}}
"""

        try:
            response = self.client.chat.completions.create(
                model="sarvam-2b-v0.5",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=200,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            result = json.loads(result_text)

            matched_qnum = result.get("question_number")
            confidence = float(result.get("confidence", 0.0))

            # Validate confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))

            # Apply confidence threshold
            if confidence < 0.7:
                logger.debug(
                    f"Fuzzy match for question {question.question_number} "
                    f"below threshold: {confidence}"
                )
                return (None, 0.0)

            # Find the matched hint
            if matched_qnum:
                for hint in hints:
                    if hint.question_number == matched_qnum:
                        logger.info(
                            f"Fuzzy match found for question {question.question_number} "
                            f"-> {matched_qnum} (confidence: {confidence})"
                        )
                        return (hint.hint_text, confidence)

            return (None, 0.0)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for fuzzy matching: {e}")
            logger.debug(f"Response text: {result_text}")
            return (None, 0.0)
        except Exception as e:
            logger.error(f"Fuzzy matching failed for question {question.question_number}: {e}")
            return (None, 0.0)
    
    def _fuzzy_match_explanation(
        self,
        question: RawQuestion,
        explanations: List[Explanation]
    ) -> Tuple[Optional[str], float]:
        """
        Use LLM to match question to explanation when direct match fails.

        This method implements the Fuzzy Matching Algorithm from the design document.
        It uses the Sarvam AI LLM to intelligently match questions to explanations
        based on content similarity and context when exact question number matching fails.

        Preconditions:
        - question has valid question_text
        - explanations list is non-empty

        Postconditions:
        - Returns (explanation, confidence) tuple
        - confidence is between 0.0 and 1.0
        - Returns (None, 0.0) if no match found or confidence < 0.7

        Args:
            question: RawQuestion object to match
            explanations: List of Explanation objects to match from

        Returns:
            Tuple of (explanation_text, confidence_score)
            Returns (None, 0.0) if no match found or confidence below threshold
        """
        if not self.client:
            logger.warning("LLM client not available, fuzzy matching disabled")
            return (None, 0.0)

        if not explanations:
            return (None, 0.0)

        # Truncate question text for prompt
        question_text = question.question_text[:300]
        if len(question.question_text) > 300:
            question_text += "..."

        # Format available explanations for prompt
        explanation_list = []
        for i, explanation in enumerate(explanations[:20]):  # Limit to 20 explanations to avoid token limits
            explanation_preview = explanation.explanation_text[:100]
            if len(explanation.explanation_text) > 100:
                explanation_preview += "..."
            explanation_list.append(
                f"  - Question Number: {explanation.question_number}, Explanation: {explanation_preview}"
            )
        explanations_text = "\n".join(explanation_list)

        prompt = f"""You are matching a question to its explanation. The question number format may differ between the question and explanation.

Question Number: {question.question_number}
Question Text: {question_text}
Chapter Context: {question.chapter_context}
Topic Context: {question.topic_context}

Available Explanations:
{explanations_text}

Task: Determine which explanation matches this question based on question number similarity and context.

Return a JSON object with:
- "question_number": the matching explanation's question number (or null if no match)
- "confidence": a number between 0.0 and 1.0 indicating match confidence

Consider:
1. Question number similarity (e.g., "1a" might match "1.a" or "Q1a")
2. Context alignment (chapter/topic)
3. Only return confidence >= 0.7 for reliable matches

Format: {{"question_number": "X", "confidence": 0.95}}
"""

        try:
            response = self.client.chat.completions.create(
                model="sarvam-2b-v0.5",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Low temperature for consistent matching
                max_tokens=200,
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            result = json.loads(result_text)

            matched_qnum = result.get("question_number")
            confidence = float(result.get("confidence", 0.0))

            # Validate confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))

            # Apply confidence threshold
            if confidence < 0.7:
                logger.debug(
                    f"Fuzzy match for question {question.question_number} "
                    f"below threshold: {confidence}"
                )
                return (None, 0.0)

            # Find the matched explanation
            if matched_qnum:
                for explanation in explanations:
                    if explanation.question_number == matched_qnum:
                        logger.info(
                            f"Fuzzy match found for question {question.question_number} "
                            f"-> {matched_qnum} (confidence: {confidence})"
                        )
                        return (explanation.explanation_text, confidence)

            return (None, 0.0)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response for fuzzy matching: {e}")
            logger.debug(f"Response text: {result_text}")
            return (None, 0.0)
        except Exception as e:
            logger.error(f"Fuzzy matching failed for question {question.question_number}: {e}")
            return (None, 0.0)


