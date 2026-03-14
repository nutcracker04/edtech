"""
TestSessionManager Service

This module provides the TestSessionManager class for managing test paper creation
and student session lifecycle.

Responsibilities:
- Generate test papers from question bank with filtering
- Track session state (in_progress, submitted, timed_out)
- Record per-question attempts with timing
- Calculate scores with negative marking
- Submit sessions and calculate ranks
- Update analytics tables

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 11.3, 12.1, 12.2, 12.3, 12.4, 12.5
"""

import logging
from typing import Optional, List, Dict, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from app.models.test_engine import Attempt
from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel
from supabase import Client

from app.models.test_engine import (
    TestPaper,
    TestPaperQuestion,
    TestSession,
    SessionStatus,
    PaperType
)
from app.models.question import QuestionType, Difficulty

logger = logging.getLogger(__name__)


class TestPaperConfig(BaseModel):
    """
    Configuration for creating a test paper.
    
    Attributes:
        title: Test paper title
        description: Optional description
        book_id: Optional book to filter questions from
        chapter_id: Optional chapter to filter questions from
        subject: Optional subject filter (Chemistry, Physics, Mathematics)
        grade_level: Optional grade level filter (7, 8, 9, 10)
        duration_minutes: Test duration in minutes
        total_marks: Total marks for the test
        question_count: Number of questions to include
        created_by: UUID of teacher/admin creating the test
        paper_type: Type of test paper (chapter_test, full_syllabus, topic_test, custom)
        difficulty_distribution: Optional dict mapping difficulty to count (e.g., {"easy": 5, "medium": 10, "hard": 5})
        answer_type_filter: Optional list of answer types to include
        negative_marking_scheme: Optional dict for negative marking (e.g., {"mcq_single": 0.25})
        is_published: Whether the test is published
    """
    title: str
    description: Optional[str] = None
    book_id: Optional[UUID] = None
    chapter_id: Optional[UUID] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    duration_minutes: int
    total_marks: Decimal
    question_count: int
    created_by: UUID
    paper_type: PaperType = PaperType.CHAPTER_TEST
    difficulty_distribution: Optional[Dict[str, int]] = None
    answer_type_filter: Optional[List[str]] = None
    negative_marking_scheme: Optional[Dict[str, Decimal]] = None
    is_published: bool = False


class TestPaperResult(BaseModel):
    """
    Result of creating a test paper.
    
    Attributes:
        success: Whether the operation succeeded
        test_paper: The created TestPaper object
        questions_added: Number of questions added to the test paper
        error: Optional error message if success=False
    """
    success: bool
    test_paper: Optional[TestPaper] = None
    questions_added: int = 0
    error: Optional[str] = None


class SessionResult(BaseModel):
    """
    Result of submitting a test session.
    
    Attributes:
        success: Whether the operation succeeded
        session_id: UUID of the submitted session
        total_marks_obtained: Total marks obtained by the student
        percentage: Percentage score
        rank: Rank among all students who took this test
        correct_count: Number of correct answers
        attempted_count: Number of attempted questions
        error: Optional error message if success=False
    """
    success: bool
    session_id: Optional[UUID] = None
    total_marks_obtained: Optional[Decimal] = None
    percentage: Optional[Decimal] = None
    rank: Optional[int] = None
    correct_count: int = 0
    attempted_count: int = 0
    error: Optional[str] = None


class TestSessionManager:
    """
    Service for managing test paper creation and student session lifecycle.
    
    This class handles the complete test workflow: creating test papers from
    the question bank, starting student sessions, and managing session state.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the TestSessionManager.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.client = supabase_client
        logger.info("TestSessionManager initialized")
    
    def create_test_paper(self, config: TestPaperConfig) -> TestPaperResult:
        """
        Generate a test paper from the question bank with filtering.
        
        This method creates a test paper by selecting questions from the question
        bank based on the provided configuration. It supports filtering by hierarchy
        (book, chapter), difficulty, and answer type.
        
        Algorithm:
        1. Build query filters based on config (book_id, chapter_id, subject, grade_level)
        2. Apply difficulty distribution if specified
        3. Apply answer_type filter if specified
        4. Randomly select questions up to question_count
        5. Insert test_papers record
        6. Insert test_paper_questions records with sort_order and marks
        7. Return TestPaperResult with created test paper
        
        Args:
            config: TestPaperConfig with test paper parameters
        
        Returns:
            TestPaperResult with created test paper and question count
        
        Raises:
            Exception: If database operation fails
        
        Preconditions:
            - config.duration_minutes must be positive
            - config.total_marks must be positive
            - config.question_count must be positive
            - config.created_by must be a valid user UUID
        
        Postconditions:
            - One row inserted into test_papers table
            - N rows inserted into test_paper_questions table (N = config.question_count)
            - Returns TestPaperResult with success=True and test_paper populated
        
        Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
        """
        logger.info(
            f"Creating test paper: title='{config.title}', "
            f"question_count={config.question_count}, duration={config.duration_minutes}min"
        )
        
        try:
            # Step 1: Build query to select questions
            query = self.client.table("questions").select("*")
            
            # Apply hierarchy filters
            if config.book_id:
                query = query.eq("book_id", str(config.book_id))
            if config.chapter_id:
                query = query.eq("chapter_id", str(config.chapter_id))
            
            # Apply subject filter (via book join if needed)
            # For now, we'll filter in memory after fetching
            
            # Apply answer_type filter
            if config.answer_type_filter:
                query = query.in_("answer_type", config.answer_type_filter)
            
            # Execute query to get available questions
            questions_response = query.execute()
            available_questions = questions_response.data
            
            if not available_questions:
                return TestPaperResult(
                    success=False,
                    error="No questions found matching the specified criteria"
                )
            
            logger.info(f"Found {len(available_questions)} available questions")
            
            # Step 2: Apply difficulty distribution if specified
            selected_questions = []
            
            if config.difficulty_distribution:
                # Select questions by difficulty
                for difficulty, count in config.difficulty_distribution.items():
                    difficulty_questions = [
                        q for q in available_questions
                        if q["difficulty"] == difficulty
                    ]
                    
                    # Randomly select 'count' questions of this difficulty
                    import random
                    selected = random.sample(
                        difficulty_questions,
                        min(count, len(difficulty_questions))
                    )
                    selected_questions.extend(selected)
            else:
                # Randomly select questions up to question_count
                import random
                selected_questions = random.sample(
                    available_questions,
                    min(config.question_count, len(available_questions))
                )
            
            if len(selected_questions) < config.question_count:
                logger.warning(
                    f"Only {len(selected_questions)} questions available, "
                    f"requested {config.question_count}"
                )
            
            # Step 3: Insert test_papers record
            test_paper_id = uuid4()
            test_paper_data = {
                "id": str(test_paper_id),
                "title": config.title,
                "description": config.description,
                "book_id": str(config.book_id) if config.book_id else None,
                "chapter_id": str(config.chapter_id) if config.chapter_id else None,
                "subject": config.subject,
                "grade_level": config.grade_level,
                "total_marks": str(config.total_marks),
                "duration_minutes": config.duration_minutes,
                "is_published": config.is_published,
                "created_by": str(config.created_by),
                "paper_type": config.paper_type.value,
                "negative_marking_scheme": {
                    k: str(v) for k, v in config.negative_marking_scheme.items()
                } if config.negative_marking_scheme else None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            test_paper_insert = self.client.table("test_papers").insert(test_paper_data).execute()
            logger.info(f"Inserted test paper with id={test_paper_id}")
            
            # Step 4: Insert test_paper_questions records
            # Calculate marks per question (evenly distributed)
            marks_per_question = config.total_marks / len(selected_questions)
            
            # Get negative marks from scheme or default to 0
            default_negative_marks = Decimal("0")
            
            questions_added = 0
            for idx, question in enumerate(selected_questions):
                # Get negative marks for this question type
                negative_marks = default_negative_marks
                if config.negative_marking_scheme:
                    answer_type = question["answer_type"]
                    if answer_type in config.negative_marking_scheme:
                        negative_marks = config.negative_marking_scheme[answer_type]
                
                test_paper_question_data = {
                    "id": str(uuid4()),
                    "test_paper_id": str(test_paper_id),
                    "question_id": question["id"],
                    "sort_order": idx,
                    "marks": str(marks_per_question),
                    "negative_marks": str(negative_marks),
                    "section_label": None  # Can be set later if needed
                }
                
                self.client.table("test_paper_questions").insert(test_paper_question_data).execute()
                questions_added += 1
            
            logger.info(f"Inserted {questions_added} test paper questions")
            
            # Step 5: Create TestPaper object to return
            test_paper = TestPaper(
                id=test_paper_id,
                title=config.title,
                description=config.description,
                book_id=config.book_id,
                chapter_id=config.chapter_id,
                subject=config.subject,
                grade_level=config.grade_level,
                total_marks=config.total_marks,
                duration_minutes=config.duration_minutes,
                is_published=config.is_published,
                created_by=config.created_by,
                paper_type=config.paper_type,
                negative_marking_scheme=config.negative_marking_scheme,
                created_at=datetime.now(timezone.utc)
            )
            
            result = TestPaperResult(
                success=True,
                test_paper=test_paper,
                questions_added=questions_added
            )
            
            logger.info(
                f"Successfully created test paper {test_paper_id} with {questions_added} questions"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to create test paper: {e}", exc_info=True)
            return TestPaperResult(
                success=False,
                error=str(e)
            )
    
    def start_session(
        self,
        paper_id: UUID,
        student_id: UUID,
        is_practice: bool = False
    ) -> TestSession:
        """
        Create a test session for a student.
        
        This method creates a new test_sessions record with status='in_progress'
        and started_at set to the current timestamp.
        
        Algorithm:
        1. Verify test_paper exists and is published
        2. Insert test_sessions record with status='in_progress'
        3. Return TestSession object
        
        Args:
            paper_id: UUID of the test paper
            student_id: UUID of the student
            is_practice: Whether this is a practice session (default: False)
        
        Returns:
            TestSession object with session details
        
        Raises:
            Exception: If test paper doesn't exist or database operation fails
        
        Preconditions:
            - paper_id must exist in test_papers table
            - student_id must be a valid user UUID
        
        Postconditions:
            - One row inserted into test_sessions table
            - Session status is 'in_progress'
            - started_at is set to current timestamp
            - Returns valid TestSession object
        
        Requirements: 10.1, 10.2, 10.3
        """
        logger.info(
            f"Starting test session: paper_id={paper_id}, student_id={student_id}, "
            f"is_practice={is_practice}"
        )
        
        try:
            # Step 1: Verify test paper exists
            paper_query = (
                self.client.table("test_papers")
                .select("*")
                .eq("id", str(paper_id))
                .execute()
            )
            
            if not paper_query.data or len(paper_query.data) == 0:
                raise ValueError(f"Test paper {paper_id} not found")
            
            paper_data = paper_query.data[0]
            
            # Check if paper is published (unless it's a practice session)
            if not is_practice and not paper_data.get("is_published", False):
                raise ValueError(f"Test paper {paper_id} is not published")
            
            logger.info(f"Test paper '{paper_data['title']}' found and verified")
            
            # Step 2: Insert test_sessions record
            session_id = uuid4()
            started_at = datetime.now(timezone.utc)
            
            session_data = {
                "id": str(session_id),
                "test_paper_id": str(paper_id),
                "student_id": str(student_id),
                "started_at": started_at.isoformat(),
                "submitted_at": None,
                "time_taken_seconds": None,
                "status": SessionStatus.IN_PROGRESS.value,
                "total_marks_obtained": None,
                "percentage": None,
                "rank": None,
                "is_practice": is_practice,
                "created_at": started_at.isoformat()
            }
            
            session_insert = self.client.table("test_sessions").insert(session_data).execute()
            logger.info(f"Inserted test session with id={session_id}")
            
            # Step 3: Create TestSession object to return
            test_session = TestSession(
                id=session_id,
                test_paper_id=paper_id,
                student_id=student_id,
                started_at=started_at,
                submitted_at=None,
                time_taken_seconds=None,
                status=SessionStatus.IN_PROGRESS,
                total_marks_obtained=None,
                percentage=None,
                rank=None,
                is_practice=is_practice,
                created_at=started_at
            )
            
            logger.info(
                f"Successfully started test session {session_id} for student {student_id}"
            )
            
            return test_session
            
        except Exception as e:
            logger.error(f"Failed to start test session: {e}", exc_info=True)
            raise

    def record_attempt(
        self,
        session_id: UUID,
        question_id: UUID,
        test_paper_question_id: UUID,
        student_answer: Optional[str] = None,
        selected_option_ids: Optional[List[UUID]] = None,
        time_spent_seconds: Optional[int] = None,
        hint_used: bool = False,
        explanation_viewed: bool = False,
        flagged: bool = False
    ) -> "Attempt":
        """
        Record an individual attempt for a question in a test session.

        This method records a student's attempt at a specific question, including
        their answer, time spent, and any hints/explanations used. It enforces
        the unique constraint on (session_id, question_id) by using upsert logic.

        Algorithm:
        1. Verify session exists and is in 'in_progress' status
        2. Verify question exists in the test paper
        3. Determine if the attempt is actually attempted (has answer)
        4. Insert or update attempt record with unique constraint on (session_id, question_id)
        5. Return Attempt object

        Args:
            session_id: UUID of the test session
            question_id: UUID of the question being attempted
            test_paper_question_id: UUID of the test_paper_question record
            student_answer: Optional student's answer (text or option label)
            selected_option_ids: Optional list of selected option UUIDs (for MCQ)
            time_spent_seconds: Optional time spent on this question in seconds
            hint_used: Whether student used a hint (default: False)
            explanation_viewed: Whether student viewed explanation (default: False)
            flagged: Whether student flagged this question for review (default: False)

        Returns:
            Attempt object with recorded attempt details

        Raises:
            ValueError: If session doesn't exist, is not in progress, or question not in test paper
            Exception: If database operation fails

        Preconditions:
            - session_id must exist in test_sessions table
            - Session status must be 'in_progress'
            - question_id must exist in test_paper_questions for this session's test paper
            - test_paper_question_id must be valid

        Postconditions:
            - One row inserted or updated in attempts table
            - Unique constraint on (session_id, question_id) is enforced
            - Returns valid Attempt object
            - is_attempted is set to True if student_answer or selected_option_ids provided

        Requirements: 11.1, 11.2, 11.4
        """
        logger.info(
            f"Recording attempt: session_id={session_id}, question_id={question_id}, "
            f"is_attempted={bool(student_answer or selected_option_ids)}"
        )

        try:
            # Step 1: Verify session exists and is in progress
            session_query = (
                self.client.table("test_sessions")
                .select("*")
                .eq("id", str(session_id))
                .execute()
            )

            if not session_query.data or len(session_query.data) == 0:
                raise ValueError(f"Test session {session_id} not found")

            session_data = session_query.data[0]

            if session_data["status"] != SessionStatus.IN_PROGRESS.value:
                raise ValueError(
                    f"Cannot record attempt for session {session_id} with status '{session_data['status']}'. "
                    f"Session must be in 'in_progress' status."
                )

            logger.info(f"Session {session_id} verified as in progress")

            # Step 2: Verify question exists in the test paper
            test_paper_id = session_data["test_paper_id"]
            tpq_query = (
                self.client.table("test_paper_questions")
                .select("*")
                .eq("id", str(test_paper_question_id))
                .eq("test_paper_id", test_paper_id)
                .eq("question_id", str(question_id))
                .execute()
            )

            if not tpq_query.data or len(tpq_query.data) == 0:
                raise ValueError(
                    f"Question {question_id} not found in test paper for session {session_id}"
                )

            logger.info(f"Question {question_id} verified in test paper")

            # Step 3: Determine if attempt is actually attempted
            is_attempted = bool(student_answer or selected_option_ids)

            # Step 4: Insert or update attempt record (upsert to enforce unique constraint)
            attempt_id = uuid4()
            created_at = datetime.now(timezone.utc)

            attempt_data = {
                "id": str(attempt_id),
                "session_id": str(session_id),
                "question_id": str(question_id),
                "test_paper_question_id": str(test_paper_question_id),
                "student_answer": student_answer,
                "selected_option_ids": [str(oid) for oid in selected_option_ids] if selected_option_ids else None,
                "is_correct": None,  # Will be evaluated during submission
                "is_attempted": is_attempted,
                "marks_awarded": None,  # Will be calculated during submission
                "time_spent_seconds": time_spent_seconds,
                "hint_used": hint_used,
                "explanation_viewed": explanation_viewed,
                "flagged": flagged,
                "created_at": created_at.isoformat()
            }

            # Use upsert to handle unique constraint on (session_id, question_id)
            # If attempt already exists, update it; otherwise insert new
            attempt_insert = (
                self.client.table("attempts")
                .upsert(attempt_data, on_conflict="session_id,question_id")
                .execute()
            )

            logger.info(f"Recorded attempt for question {question_id} in session {session_id}")

            # Step 5: Create Attempt object to return
            from app.models.test_engine import Attempt

            attempt = Attempt(
                id=attempt_id,
                session_id=session_id,
                question_id=question_id,
                test_paper_question_id=test_paper_question_id,
                student_answer=student_answer,
                selected_option_ids=selected_option_ids,
                is_correct=None,
                is_attempted=is_attempted,
                marks_awarded=None,
                time_spent_seconds=time_spent_seconds,
                hint_used=hint_used,
                explanation_viewed=explanation_viewed,
                flagged=flagged,
                created_at=created_at
            )

            logger.info(
                f"Successfully recorded attempt for question {question_id} in session {session_id}"
            )

            return attempt

        except ValueError as ve:
            # Re-raise ValueError with original message
            logger.error(f"Validation error recording attempt: {ve}")
            raise
        except Exception as e:
            logger.error(f"Failed to record attempt: {e}", exc_info=True)
            raise


    def submit_session(self, session_id: UUID) -> "SessionResult":
        """
        Submit a test session, calculate score with negative marking, and update analytics.

        This method processes all attempts in a session, evaluates correctness by comparing
        with the answers table, calculates marks with negative marking, updates the session
        status to 'submitted', and calculates the student's rank.

        Algorithm:
        1. Fetch test paper details and marking scheme
        2. Fetch all attempts for the session
        3. For each attempt:
            a. Fetch correct answer from answers table
            b. Evaluate correctness by comparing student answer with correct answer
            c. Calculate marks_awarded: correct = +marks, incorrect = -negative_marks, unattempted = 0
            d. Update attempt record with is_correct and marks_awarded
        4. Calculate total_marks_obtained as sum of marks_awarded
        5. Calculate percentage as (total_marks_obtained / test_paper.total_marks) * 100
        6. Calculate time_taken_seconds as (current_time - started_at)
        7. Update session status to 'submitted' and set submitted_at
        8. Calculate rank by counting sessions with higher scores on same test paper
        9. Update session with rank

        Args:
            session_id: UUID of the test session to submit

        Returns:
            SessionResult with score breakdown and rank

        Raises:
            ValueError: If session doesn't exist or is not in 'in_progress' status
            Exception: If database operation fails

        Preconditions:
            - session_id must exist in test_sessions table
            - Session status must be 'in_progress'
            - All attempts for the session must be recorded

        Postconditions:
            - test_sessions.status is set to 'submitted'
            - test_sessions.submitted_at is set to current timestamp
            - test_sessions.time_taken_seconds is calculated
            - test_sessions.total_marks_obtained is calculated with negative marking
            - test_sessions.percentage is calculated
            - test_sessions.rank is calculated
            - All attempts have is_correct and marks_awarded evaluated
            - Returns SessionResult with success=True and score details

        Requirements: 10.4, 10.5, 11.3, 12.1, 12.2, 12.3, 12.4, 12.5
        """
        logger.info(f"Submitting test session: session_id={session_id}")

        try:
            # Step 1: Fetch session and verify it's in progress
            session_query = (
                self.client.table("test_sessions")
                .select("*")
                .eq("id", str(session_id))
                .execute()
            )

            if not session_query.data or len(session_query.data) == 0:
                raise ValueError(f"Test session {session_id} not found")

            session_data = session_query.data[0]

            if session_data["status"] != SessionStatus.IN_PROGRESS.value:
                raise ValueError(
                    f"Cannot submit session {session_id} with status '{session_data['status']}'. "
                    f"Session must be in 'in_progress' status."
                )

            logger.info(f"Session {session_id} verified as in progress")

            # Step 2: Fetch test paper details
            test_paper_id = session_data["test_paper_id"]
            paper_query = (
                self.client.table("test_papers")
                .select("*")
                .eq("id", test_paper_id)
                .execute()
            )

            if not paper_query.data or len(paper_query.data) == 0:
                raise ValueError(f"Test paper {test_paper_id} not found")

            paper_data = paper_query.data[0]
            total_marks = Decimal(paper_data["total_marks"])

            logger.info(f"Test paper '{paper_data['title']}' found, total_marks={total_marks}")

            # Step 3: Fetch all attempts for this session
            attempts_query = (
                self.client.table("attempts")
                .select("*")
                .eq("session_id", str(session_id))
                .execute()
            )

            attempts_data = attempts_query.data if attempts_query.data else []
            logger.info(f"Found {len(attempts_data)} attempts for session {session_id}")

            # Step 4: Process each attempt and calculate marks
            total_marks_obtained = Decimal("0")
            correct_count = 0
            attempted_count = 0

            for attempt_data in attempts_data:
                question_id = attempt_data["question_id"]
                is_attempted = attempt_data["is_attempted"]

                if is_attempted:
                    attempted_count += 1

                # Fetch correct answer from answers table
                answer_query = (
                    self.client.table("answers")
                    .select("correct_answer, correct_option_ids")
                    .eq("question_id", question_id)
                    .execute()
                )

                # Fetch marks and negative_marks from test_paper_questions
                tpq_query = (
                    self.client.table("test_paper_questions")
                    .select("marks, negative_marks")
                    .eq("test_paper_id", test_paper_id)
                    .eq("question_id", question_id)
                    .execute()
                )

                if not tpq_query.data or len(tpq_query.data) == 0:
                    logger.warning(f"Question {question_id} not found in test paper, skipping")
                    continue

                tpq_data = tpq_query.data[0]
                question_marks = Decimal(tpq_data["marks"])
                negative_marks = Decimal(tpq_data["negative_marks"])

                # Evaluate correctness and calculate marks
                is_correct = False
                marks_awarded = Decimal("0")

                if is_attempted and answer_query.data and len(answer_query.data) > 0:
                    answer_data = answer_query.data[0]
                    correct_answer = answer_data["correct_answer"]
                    correct_option_ids = answer_data.get("correct_option_ids", [])

                    # Evaluate correctness
                    student_answer = attempt_data.get("student_answer")
                    selected_option_ids = attempt_data.get("selected_option_ids", [])

                    # Compare answers
                    if student_answer:
                        # For text-based answers (integer, numerical, etc.)
                        is_correct = str(student_answer).strip().upper() == str(correct_answer).strip().upper()
                    elif selected_option_ids and correct_option_ids:
                        # For MCQ questions, compare selected option IDs
                        selected_set = set(str(oid) for oid in selected_option_ids)
                        correct_set = set(str(oid) for oid in correct_option_ids)
                        is_correct = selected_set == correct_set

                    # Calculate marks awarded
                    if is_correct:
                        marks_awarded = question_marks
                        correct_count += 1
                    else:
                        marks_awarded = -negative_marks

                # If unattempted, marks_awarded remains 0

                total_marks_obtained += marks_awarded

                # Update attempt record with is_correct and marks_awarded
                update_data = {
                    "is_correct": is_correct,
                    "marks_awarded": str(marks_awarded)
                }

                self.client.table("attempts").update(update_data).eq("id", attempt_data["id"]).execute()

                logger.debug(
                    f"Processed attempt for question {question_id}: "
                    f"is_correct={is_correct}, marks_awarded={marks_awarded}"
                )

            logger.info(
                f"Processed {len(attempts_data)} attempts: "
                f"correct={correct_count}, attempted={attempted_count}, "
                f"total_marks={total_marks_obtained}"
            )

            # Step 5: Calculate percentage
            percentage = (total_marks_obtained / total_marks * Decimal("100")) if total_marks > 0 else Decimal("0")

            # Step 6: Calculate time taken
            started_at = datetime.fromisoformat(session_data["started_at"].replace('Z', '+00:00'))
            submitted_at = datetime.now(timezone.utc)
            time_taken_seconds = int((submitted_at - started_at).total_seconds())

            # Step 7: Update session record
            session_update_data = {
                "status": SessionStatus.SUBMITTED.value,
                "submitted_at": submitted_at.isoformat(),
                "time_taken_seconds": time_taken_seconds,
                "total_marks_obtained": str(total_marks_obtained),
                "percentage": str(percentage)
            }

            self.client.table("test_sessions").update(session_update_data).eq("id", str(session_id)).execute()

            logger.info(
                f"Updated session {session_id}: status=submitted, "
                f"total_marks={total_marks_obtained}, percentage={percentage}%"
            )

            # Step 8: Calculate rank by counting sessions with higher scores
            rank_query = (
                self.client.table("test_sessions")
                .select("id", count="exact")
                .eq("test_paper_id", test_paper_id)
                .eq("status", SessionStatus.SUBMITTED.value)
                .gt("total_marks_obtained", str(total_marks_obtained))
                .execute()
            )

            # Rank is count of higher scores + 1
            rank = (rank_query.count if rank_query.count is not None else 0) + 1

            # Step 9: Update session with rank
            self.client.table("test_sessions").update({"rank": rank}).eq("id", str(session_id)).execute()

            logger.info(f"Calculated rank for session {session_id}: rank={rank}")

            # Return result
            result = SessionResult(
                success=True,
                session_id=session_id,
                total_marks_obtained=total_marks_obtained,
                percentage=percentage,
                rank=rank,
                correct_count=correct_count,
                attempted_count=attempted_count
            )

            logger.info(
                f"Successfully submitted session {session_id}: "
                f"score={total_marks_obtained}/{total_marks}, "
                f"percentage={percentage}%, rank={rank}"
            )

            return result

        except ValueError as ve:
            # Re-raise ValueError with original message
            logger.error(f"Validation error submitting session: {ve}")
            raise
        except Exception as e:
            logger.error(f"Failed to submit session: {e}", exc_info=True)
            return SessionResult(
                success=False,
                error=str(e)
            )

