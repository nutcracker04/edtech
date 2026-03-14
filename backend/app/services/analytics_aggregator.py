"""
AnalyticsAggregator Service

This module provides the AnalyticsAggregator class for computing aggregated statistics
for questions and students.

Responsibilities:
- Aggregate attempt data into question_stats
- Calculate accuracy, avg time, skip rate
- Update question statistics after session submissions
- Handle division-by-zero cases gracefully

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from supabase import Client

from app.models.analytics import QuestionStats

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    """
    Service for computing aggregated statistics for questions and students.
    
    This class handles the aggregation of attempt data into the question_stats table,
    calculating metrics like accuracy percentage, average time, and usage counts.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the AnalyticsAggregator.
        
        Args:
            supabase_client: Supabase client for database operations
        """
        self.client = supabase_client
        logger.info("AnalyticsAggregator initialized")
    
    def update_question_stats(self, question_id: UUID) -> QuestionStats:
        """
        Update aggregated statistics for a question based on all attempts.
        
        This method aggregates data from the attempts table to calculate:
        - total_attempts: Total number of attempts for this question
        - correct_attempts: Number of correct attempts
        - accuracy_pct: Percentage of correct attempts (with division-by-zero guard)
        - avg_time_seconds: Average time spent on this question
        - skip_count: Number of times question was skipped (not attempted)
        - hint_use_count: Number of times hints were used
        - explanation_view_count: Number of times explanations were viewed
        
        The method uses an upsert operation to either insert a new question_stats
        record or update an existing one.
        
        Algorithm:
        1. Query attempts table for all attempts on this question
        2. Calculate aggregated statistics:
           - total_attempts = count of all attempts
           - correct_attempts = count where is_correct = true
           - accuracy_pct = (correct_attempts / total_attempts) * 100 with zero guard
           - avg_time_seconds = average of time_spent_seconds where not null
           - skip_count = count where is_attempted = false
           - hint_use_count = count where hint_used = true
           - explanation_view_count = count where explanation_viewed = true
        3. Upsert question_stats record with calculated values
        4. Return QuestionStats object
        
        Args:
            question_id: UUID of the question to update statistics for
        
        Returns:
            QuestionStats object with updated statistics
        
        Raises:
            Exception: If database operation fails
        
        Preconditions:
            - question_id must exist in questions table
            - Database connection is valid
        
        Postconditions:
            - question_stats record is inserted or updated for this question
            - accuracy_pct is between 0 and 100
            - All counts are non-negative
            - updated_at is set to current timestamp
            - Returns valid QuestionStats object
        
        Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
        """
        logger.info(f"Updating question stats for question_id={question_id}")
        
        try:
            # Step 1: Query all attempts for this question
            attempts_query = (
                self.client.table("attempts")
                .select("*")
                .eq("question_id", str(question_id))
                .execute()
            )
            
            attempts_data = attempts_query.data if attempts_query.data else []
            logger.info(f"Found {len(attempts_data)} attempts for question {question_id}")
            
            # Step 2: Calculate aggregated statistics
            total_attempts = len(attempts_data)
            correct_attempts = sum(1 for a in attempts_data if a.get("is_correct") is True)
            skip_count = sum(1 for a in attempts_data if a.get("is_attempted") is False)
            hint_use_count = sum(1 for a in attempts_data if a.get("hint_used") is True)
            explanation_view_count = sum(1 for a in attempts_data if a.get("explanation_viewed") is True)
            
            # Calculate accuracy_pct with division-by-zero guard
            if total_attempts > 0:
                accuracy_pct = Decimal(correct_attempts) / Decimal(total_attempts) * Decimal("100")
            else:
                accuracy_pct = Decimal("0")
            
            # Calculate avg_time_seconds (only for attempts with time_spent_seconds)
            time_values = [
                a.get("time_spent_seconds") 
                for a in attempts_data 
                if a.get("time_spent_seconds") is not None
            ]
            
            if time_values:
                avg_time_seconds = Decimal(sum(time_values)) / Decimal(len(time_values))
            else:
                avg_time_seconds = Decimal("0")
            
            logger.info(
                f"Calculated stats for question {question_id}: "
                f"total={total_attempts}, correct={correct_attempts}, "
                f"accuracy={accuracy_pct}%, avg_time={avg_time_seconds}s"
            )
            
            # Step 3: Upsert question_stats record
            updated_at = datetime.now(timezone.utc)
            
            stats_data = {
                "question_id": str(question_id),
                "total_attempts": total_attempts,
                "correct_attempts": correct_attempts,
                "accuracy_pct": str(accuracy_pct),
                "avg_time_seconds": str(avg_time_seconds),
                "skip_count": skip_count,
                "hint_use_count": hint_use_count,
                "explanation_view_count": explanation_view_count,
                "updated_at": updated_at.isoformat()
            }
            
            # Use upsert to insert or update
            stats_upsert = (
                self.client.table("question_stats")
                .upsert(stats_data, on_conflict="question_id")
                .execute()
            )
            
            logger.info(f"Successfully updated question_stats for question {question_id}")
            
            # Step 4: Create QuestionStats object to return
            question_stats = QuestionStats(
                question_id=question_id,
                total_attempts=total_attempts,
                correct_attempts=correct_attempts,
                accuracy_pct=accuracy_pct,
                avg_time_seconds=avg_time_seconds,
                skip_count=skip_count,
                hint_use_count=hint_use_count,
                explanation_view_count=explanation_view_count,
                most_common_wrong_answer=None,  # Not calculated in this method
                discrimination_index=None,  # Not calculated in this method
                updated_at=updated_at
            )
            
            return question_stats
            
        except Exception as e:
            logger.error(f"Failed to update question stats for {question_id}: {e}", exc_info=True)
            raise

    def update_student_mastery(self, student_id: UUID, session_id: UUID) -> list:
        """
        Update student mastery levels for all topics covered in a completed session.

        This method aggregates attempt data from a session to update the student's
        mastery level for each topic. It calculates:
        - questions_attempted: Total questions attempted for each topic
        - questions_correct: Number of correct answers for each topic
        - accuracy_pct: Percentage of correct answers
        - mastery_level: Determined by accuracy_pct and questions_attempted
        - last_attempted_at: Timestamp of the session
        - streak_days: Consecutive days of practice (calculated based on activity)

        Mastery Level Calculation Rules:
        - not_started: 0 questions attempted
        - learning: accuracy < 50%
        - developing: 50% <= accuracy < 70%
        - proficient: 70% <= accuracy < 85%
        - mastered: accuracy >= 85%

        Algorithm:
        1. Query all attempts for the session
        2. Group attempts by topic_id
        3. For each topic:
           a. Calculate questions_attempted and questions_correct
           b. Calculate accuracy_pct
           c. Determine mastery_level based on accuracy and attempts
           d. Calculate streak_days based on consecutive activity
           e. Upsert student_topic_mastery record
        4. Return list of updated mastery records

        Args:
            student_id: UUID of the student
            session_id: UUID of the completed test session

        Returns:
            List of StudentTopicMastery objects that were updated

        Raises:
            Exception: If database operation fails

        Preconditions:
            - student_id must be valid
            - session_id must exist in test_sessions table
            - Session must be completed (status = 'submitted')
            - Database connection is valid

        Postconditions:
            - student_topic_mastery records are inserted or updated for each topic
            - accuracy_pct is between 0 and 100
            - mastery_level follows deterministic rules
            - last_attempted_at is set to current timestamp
            - All counts are non-negative
            - Returns list of StudentTopicMastery objects

        Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
        """
        from app.models.analytics import StudentTopicMastery, MasteryLevel
        from uuid import uuid4

        logger.info(f"Updating student mastery for student_id={student_id}, session_id={session_id}")

        try:
            # Step 1: Query all attempts for this session with question details
            attempts_query = (
                self.client.table("attempts")
                .select("*, questions!inner(topic_id, chapter_id, book_id)")
                .eq("session_id", str(session_id))
                .execute()
            )

            attempts_data = attempts_query.data if attempts_query.data else []
            logger.info(f"Found {len(attempts_data)} attempts for session {session_id}")

            if not attempts_data:
                logger.warning(f"No attempts found for session {session_id}")
                return []

            # Step 2: Group attempts by topic_id
            topic_attempts = {}
            for attempt in attempts_data:
                # Extract question data from the join
                question_data = attempt.get("questions")
                if not question_data:
                    logger.warning(f"Attempt {attempt.get('id')} has no question data, skipping")
                    continue

                topic_id = question_data.get("topic_id")
                chapter_id = question_data.get("chapter_id")
                book_id = question_data.get("book_id")

                if not topic_id:
                    logger.warning(f"Attempt {attempt.get('id')} has no topic_id, skipping")
                    continue

                if topic_id not in topic_attempts:
                    topic_attempts[topic_id] = {
                        "chapter_id": chapter_id,
                        "book_id": book_id,
                        "attempts": []
                    }

                topic_attempts[topic_id]["attempts"].append(attempt)

            logger.info(f"Grouped attempts into {len(topic_attempts)} topics")

            # Step 3: Process each topic and update mastery
            updated_masteries = []
            current_time = datetime.now(timezone.utc)

            for topic_id, topic_data in topic_attempts.items():
                attempts = topic_data["attempts"]
                chapter_id = topic_data["chapter_id"]
                book_id = topic_data["book_id"]

                # Calculate statistics for this topic
                attempted_count = sum(1 for a in attempts if a.get("is_attempted") is True)
                correct_count = sum(1 for a in attempts if a.get("is_correct") is True)

                # Fetch existing mastery record if it exists
                existing_mastery_query = (
                    self.client.table("student_topic_mastery")
                    .select("*")
                    .eq("student_id", str(student_id))
                    .eq("topic_id", str(topic_id))
                    .execute()
                )

                existing_mastery = existing_mastery_query.data[0] if existing_mastery_query.data else None

                # Calculate cumulative statistics
                if existing_mastery:
                    total_attempted = existing_mastery.get("questions_attempted", 0) + attempted_count
                    total_correct = existing_mastery.get("questions_correct", 0) + correct_count
                    mastery_id = existing_mastery.get("id")
                else:
                    total_attempted = attempted_count
                    total_correct = correct_count
                    mastery_id = str(uuid4())

                # Calculate accuracy_pct with division-by-zero guard
                if total_attempted > 0:
                    accuracy_pct = Decimal(total_correct) / Decimal(total_attempted) * Decimal("100")
                else:
                    accuracy_pct = Decimal("0")

                # Determine mastery_level based on accuracy and attempts
                if total_attempted == 0:
                    mastery_level = MasteryLevel.NOT_STARTED
                elif accuracy_pct < 50:
                    mastery_level = MasteryLevel.LEARNING
                elif accuracy_pct < 70:
                    mastery_level = MasteryLevel.DEVELOPING
                elif accuracy_pct < 85:
                    mastery_level = MasteryLevel.PROFICIENT
                else:
                    mastery_level = MasteryLevel.MASTERED

                # Calculate streak_days
                streak_days = self._calculate_streak_days(student_id, existing_mastery)

                logger.info(
                    f"Topic {topic_id}: attempted={total_attempted}, correct={total_correct}, "
                    f"accuracy={accuracy_pct}%, mastery={mastery_level.value}, streak={streak_days}"
                )

                # Prepare mastery data for upsert
                mastery_data = {
                    "id": mastery_id,
                    "student_id": str(student_id),
                    "topic_id": str(topic_id),
                    "chapter_id": str(chapter_id),
                    "book_id": str(book_id),
                    "questions_attempted": total_attempted,
                    "questions_correct": total_correct,
                    "accuracy_pct": str(accuracy_pct),
                    "mastery_level": mastery_level.value,
                    "last_attempted_at": current_time.isoformat(),
                    "streak_days": streak_days
                }

                # Upsert student_topic_mastery record
                mastery_upsert = (
                    self.client.table("student_topic_mastery")
                    .upsert(mastery_data, on_conflict="student_id,topic_id")
                    .execute()
                )

                logger.info(f"Successfully updated mastery for student {student_id}, topic {topic_id}")

                # Create StudentTopicMastery object for return
                mastery_obj = StudentTopicMastery(
                    id=UUID(mastery_id),
                    student_id=student_id,
                    topic_id=UUID(topic_id),
                    chapter_id=UUID(chapter_id),
                    book_id=UUID(book_id),
                    questions_attempted=total_attempted,
                    questions_correct=total_correct,
                    accuracy_pct=accuracy_pct,
                    mastery_level=mastery_level,
                    last_attempted_at=current_time,
                    streak_days=streak_days
                )

                updated_masteries.append(mastery_obj)

            logger.info(f"Updated mastery for {len(updated_masteries)} topics")
            return updated_masteries

        except Exception as e:
            logger.error(f"Failed to update student mastery for student {student_id}, session {session_id}: {e}", exc_info=True)
            raise

    def _calculate_streak_days(self, student_id: UUID, existing_mastery: Optional[dict]) -> int:
        """
        Calculate streak days for a student's topic mastery.

        Streak is calculated based on consecutive days of activity. If the student
        practiced yesterday, increment the streak. If they practiced today for the
        first time, start a new streak of 1. Otherwise, reset to 1.

        Args:
            student_id: UUID of the student
            existing_mastery: Existing mastery record (if any)

        Returns:
            Updated streak_days count
        """
        from datetime import date, timedelta

        try:
            # Get current streak from existing mastery
            current_streak = existing_mastery.get("streak_days", 0) if existing_mastery else 0
            last_attempted = existing_mastery.get("last_attempted_at") if existing_mastery else None

            if not last_attempted:
                # First time practicing this topic
                return 1

            # Parse last_attempted_at
            if isinstance(last_attempted, str):
                last_attempted_dt = datetime.fromisoformat(last_attempted.replace('Z', '+00:00'))
            else:
                last_attempted_dt = last_attempted

            last_attempted_date = last_attempted_dt.date()
            today = date.today()

            # Calculate days since last attempt
            days_since = (today - last_attempted_date).days

            if days_since == 0:
                # Same day, keep current streak
                return current_streak if current_streak > 0 else 1
            elif days_since == 1:
                # Consecutive day, increment streak
                return current_streak + 1
            else:
                # Streak broken, start new streak
                return 1

        except Exception as e:
            logger.warning(f"Failed to calculate streak days: {e}")
            return 1


    def update_daily_activity(self, student_id: UUID, session_id: UUID) -> 'DailyActivity':
        """
        Update or insert daily activity record for a student's completed session.

        This method aggregates session data to update the daily_activity table:
        - sessions_count: Incremented by 1 for each completed session
        - questions_attempted: Incremented by number of attempted questions
        - questions_correct: Incremented by number of correct answers
        - time_spent_minutes: Incremented by session duration in minutes

        The method uses an upsert operation to either insert a new daily_activity
        record or update an existing one for the current date.

        Algorithm:
        1. Query the test_sessions table to get session timing information
        2. Query all attempts for the session to count attempted and correct questions
        3. Calculate time_spent_minutes from session duration
        4. Fetch existing daily_activity record for today (if exists)
        5. Calculate new cumulative values
        6. Upsert daily_activity record with updated values
        7. Return DailyActivity object

        Args:
            student_id: UUID of the student
            session_id: UUID of the completed test session

        Returns:
            DailyActivity object with updated statistics

        Raises:
            Exception: If database operation fails

        Preconditions:
            - student_id must be valid
            - session_id must exist in test_sessions table
            - Session must be completed (status = 'submitted')
            - Database connection is valid

        Postconditions:
            - daily_activity record is inserted or updated for current date
            - sessions_count is incremented by 1
            - questions_attempted is incremented by number of attempted questions
            - questions_correct is incremented by number of correct answers
            - time_spent_minutes is incremented by session duration
            - All counts are non-negative
            - Returns valid DailyActivity object

        Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
        """
        from app.models.analytics import DailyActivity
        from datetime import date
        from uuid import uuid4

        logger.info(f"Updating daily activity for student_id={student_id}, session_id={session_id}")

        try:
            # Step 1: Query session to get timing information
            session_query = (
                self.client.table("test_sessions")
                .select("time_taken_seconds, submitted_at")
                .eq("id", str(session_id))
                .execute()
            )

            if not session_query.data:
                logger.error(f"Session {session_id} not found")
                raise ValueError(f"Session {session_id} not found")

            session_data = session_query.data[0]
            time_taken_seconds = session_data.get("time_taken_seconds", 0) or 0

            # Convert seconds to minutes (round up)
            time_spent_minutes = (time_taken_seconds + 59) // 60  # Round up to nearest minute

            logger.info(f"Session duration: {time_taken_seconds}s ({time_spent_minutes} minutes)")

            # Step 2: Query all attempts for this session
            attempts_query = (
                self.client.table("attempts")
                .select("is_attempted, is_correct")
                .eq("session_id", str(session_id))
                .execute()
            )

            attempts_data = attempts_query.data if attempts_query.data else []
            logger.info(f"Found {len(attempts_data)} attempts for session {session_id}")

            # Calculate statistics for this session
            questions_attempted = sum(1 for a in attempts_data if a.get("is_attempted") is True)
            questions_correct = sum(1 for a in attempts_data if a.get("is_correct") is True)

            logger.info(
                f"Session stats: attempted={questions_attempted}, correct={questions_correct}, "
                f"time={time_spent_minutes} minutes"
            )

            # Step 3: Get current date
            today = date.today()

            # Step 4: Fetch existing daily_activity record for today
            existing_activity_query = (
                self.client.table("daily_activity")
                .select("*")
                .eq("student_id", str(student_id))
                .eq("activity_date", today.isoformat())
                .execute()
            )

            existing_activity = existing_activity_query.data[0] if existing_activity_query.data else None

            # Step 5: Calculate cumulative values
            if existing_activity:
                activity_id = existing_activity.get("id")
                sessions_count = existing_activity.get("sessions_count", 0) + 1
                total_questions_attempted = existing_activity.get("questions_attempted", 0) + questions_attempted
                total_questions_correct = existing_activity.get("questions_correct", 0) + questions_correct
                total_time_spent_minutes = existing_activity.get("time_spent_minutes", 0) + time_spent_minutes
                logger.info(f"Updating existing daily_activity record {activity_id}")
            else:
                activity_id = str(uuid4())
                sessions_count = 1
                total_questions_attempted = questions_attempted
                total_questions_correct = questions_correct
                total_time_spent_minutes = time_spent_minutes
                logger.info(f"Creating new daily_activity record {activity_id}")

            # Step 6: Prepare activity data for upsert
            activity_data = {
                "id": activity_id,
                "student_id": str(student_id),
                "activity_date": today.isoformat(),
                "sessions_count": sessions_count,
                "questions_attempted": total_questions_attempted,
                "questions_correct": total_questions_correct,
                "time_spent_minutes": total_time_spent_minutes
            }

            # Upsert daily_activity record
            activity_upsert = (
                self.client.table("daily_activity")
                .upsert(activity_data, on_conflict="student_id,activity_date")
                .execute()
            )

            logger.info(
                f"Successfully updated daily_activity for student {student_id} on {today}: "
                f"sessions={sessions_count}, attempted={total_questions_attempted}, "
                f"correct={total_questions_correct}, time={total_time_spent_minutes}min"
            )

            # Step 7: Create DailyActivity object to return
            daily_activity = DailyActivity(
                id=UUID(activity_id),
                student_id=student_id,
                activity_date=today,
                sessions_count=sessions_count,
                questions_attempted=total_questions_attempted,
                questions_correct=total_questions_correct,
                time_spent_minutes=total_time_spent_minutes
            )

            return daily_activity

        except Exception as e:
            logger.error(f"Failed to update daily activity for student {student_id}, session {session_id}: {e}", exc_info=True)
            raise

    def calculate_discrimination_index(self, question_id: UUID) -> float:
        """
        Calculate psychometric discrimination index for a question.

        The discrimination index compares the performance of top-performing students
        versus bottom-performing students on a specific question. It measures how well
        a question differentiates between high and low achievers.

        Algorithm:
        1. Query all students who have attempted this question
        2. Calculate overall performance for each student (across all their test sessions)
        3. Identify top 27% and bottom 27% of students by overall performance
        4. Calculate percentage of correct answers for top 27% on this question
        5. Calculate percentage of correct answers for bottom 27% on this question
        6. Discrimination index = top_correct_pct - bottom_correct_pct

        Interpretation:
        - Positive value (0 to 1): Good discrimination - top students answer correctly more often
        - Negative value (-1 to 0): Poor discrimination - bottom students answer correctly more often
        - Value near 0: No discrimination - question doesn't differentiate between groups
        - Ideal range: 0.3 to 0.7 indicates good discrimination

        Args:
            question_id: UUID of the question to calculate discrimination index for

        Returns:
            Float between -1.0 and 1.0 representing the discrimination index

        Raises:
            Exception: If database operation fails

        Preconditions:
            - question_id must exist in questions table
            - At least 30 attempts exist for the question (minimum sample size)
            - Students have overall performance scores available
            - Database connection is valid

        Postconditions:
            - Returns float between -1.0 and 1.0
            - question_stats.discrimination_index is updated
            - No other data is modified

        Requirements: 13.1, 13.5
        """
        logger.info(f"Calculating discrimination index for question_id={question_id}")

        try:
            # Step 1: Query all attempts for this question with session information
            attempts_query = (
                self.client.table("attempts")
                .select("session_id, is_correct, test_sessions!inner(student_id)")
                .eq("question_id", str(question_id))
                .execute()
            )

            attempts_data = attempts_query.data if attempts_query.data else []
            logger.info(f"Found {len(attempts_data)} attempts for question {question_id}")

            # Check minimum sample size
            if len(attempts_data) < 30:
                logger.warning(
                    f"Insufficient attempts ({len(attempts_data)}) for discrimination index calculation. "
                    f"Minimum 30 required."
                )
                return 0.0

            # Step 2: Extract student IDs and their attempts on this question
            student_ids = set()
            question_attempts_by_student = {}

            for attempt in attempts_data:
                # Extract student_id from the nested test_sessions structure
                test_session = attempt.get("test_sessions")
                if not test_session:
                    continue

                student_id = test_session.get("student_id")
                if not student_id:
                    continue

                student_ids.add(student_id)

                is_correct = attempt.get("is_correct")

                if student_id not in question_attempts_by_student:
                    question_attempts_by_student[student_id] = []

                question_attempts_by_student[student_id].append(is_correct)

            if len(student_ids) < 10:
                logger.warning(
                    f"Insufficient unique students ({len(student_ids)}) for discrimination index. "
                    f"Minimum 10 required."
                )
                return 0.0

            # Step 3: Calculate overall performance for each student across ALL their sessions
            # Query test_sessions to get overall performance metrics
            student_performance = []

            for student_id in student_ids:
                # Query all completed sessions for this student
                sessions_query = (
                    self.client.table("test_sessions")
                    .select("percentage")
                    .eq("student_id", str(student_id))
                    .eq("status", "submitted")
                    .execute()
                )

                sessions = sessions_query.data if sessions_query.data else []

                if not sessions:
                    # If no completed sessions, skip this student
                    continue

                # Calculate average percentage across all sessions as overall performance
                percentages = [
                    float(s.get("percentage", 0)) 
                    for s in sessions 
                    if s.get("percentage") is not None
                ]

                if percentages:
                    overall_performance = sum(percentages) / len(percentages)
                    student_performance.append({
                        "student_id": student_id,
                        "overall_performance": overall_performance,
                        "question_attempts": question_attempts_by_student.get(student_id, [])
                    })

            if len(student_performance) < 10:
                logger.warning(
                    f"Insufficient students with completed sessions ({len(student_performance)}). "
                    f"Minimum 10 required."
                )
                return 0.0

            # Step 4: Sort students by overall performance
            student_performance.sort(key=lambda x: x["overall_performance"], reverse=True)

            # Step 5: Identify top 27% and bottom 27%
            total_students = len(student_performance)
            top_27_count = max(1, int(total_students * 0.27))
            bottom_27_count = max(1, int(total_students * 0.27))

            top_students = student_performance[:top_27_count]
            bottom_students = student_performance[-bottom_27_count:]

            logger.info(
                f"Analyzing {total_students} students: "
                f"top 27% = {top_27_count} students, bottom 27% = {bottom_27_count} students"
            )

            # Step 6: Calculate correct percentage for top 27% on this question
            top_correct = 0
            top_total = 0
            for student in top_students:
                for is_correct in student["question_attempts"]:
                    top_total += 1
                    if is_correct:
                        top_correct += 1

            top_correct_pct = (top_correct / top_total) if top_total > 0 else 0.0

            # Step 7: Calculate correct percentage for bottom 27% on this question
            bottom_correct = 0
            bottom_total = 0
            for student in bottom_students:
                for is_correct in student["question_attempts"]:
                    bottom_total += 1
                    if is_correct:
                        bottom_correct += 1

            bottom_correct_pct = (bottom_correct / bottom_total) if bottom_total > 0 else 0.0

            # Step 8: Calculate discrimination index
            discrimination_index = top_correct_pct - bottom_correct_pct

            logger.info(
                f"Discrimination index for question {question_id}: {discrimination_index:.3f} "
                f"(top: {top_correct_pct:.2%}, bottom: {bottom_correct_pct:.2%})"
            )

            # Step 9: Update question_stats with discrimination_index
            updated_at = datetime.now(timezone.utc)

            update_data = {
                "question_id": str(question_id),
                "discrimination_index": str(Decimal(str(discrimination_index))),
                "updated_at": updated_at.isoformat()
            }

            # Use upsert to update discrimination_index
            self.client.table("question_stats").upsert(
                update_data,
                on_conflict="question_id"
            ).execute()

            logger.info(f"Updated discrimination_index in question_stats for question {question_id}")

            # Ensure return value is between -1.0 and 1.0
            return max(-1.0, min(1.0, discrimination_index))

        except Exception as e:
            logger.error(
                f"Failed to calculate discrimination index for question {question_id}: {e}",
                exc_info=True
            )
            raise




