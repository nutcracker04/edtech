"""
Mastery Tracker for tracking student performance and calculating concept mastery.

This module provides:
- Performance recording with database persistence
- Mastery calculation based on weighted accuracy, consistency, and difficulty
- Mastery history retrieval
- Adaptive difficulty recommendations
"""

from typing import List, Optional
from datetime import datetime
import logging
from .models import PerformanceRecord, DifficultyDNA
from .database import Neo4jConnection
from .config import concept_graph_settings

logger = logging.getLogger(__name__)


class MasteryRecord:
    """
    Record of mastery status for a concept.
    
    Attributes:
        student_id: Student identifier
        concept_id: Concept identifier
        mastery_level: Mastery level (0.0 to 1.0)
        is_mastered: Whether concept is mastered
        last_updated: When mastery was last calculated
    """
    
    def __init__(
        self,
        student_id: str,
        concept_id: str,
        mastery_level: float,
        is_mastered: bool,
        last_updated: datetime
    ):
        self.student_id = student_id
        self.concept_id = concept_id
        self.mastery_level = mastery_level
        self.is_mastered = is_mastered
        self.last_updated = last_updated
    
    def to_dict(self) -> dict:
        """Convert MasteryRecord to dictionary format."""
        return {
            "student_id": self.student_id,
            "concept_id": self.concept_id,
            "mastery_level": self.mastery_level,
            "is_mastered": self.is_mastered,
            "last_updated": self.last_updated.isoformat()
        }


class MasteryTracker:
    """
    Track student performance and calculate concept mastery.
    
    This class manages:
    - Recording student performance on questions
    - Calculating mastery levels based on performance history
    - Determining mastery status
    - Recommending difficulty adjustments
    - Maintaining mastery history
    """
    
    def __init__(self):
        """Initialize MasteryTracker with database connections."""
        self.neo4j_driver = Neo4jConnection.get_driver()
    
    def record_performance(self, record: PerformanceRecord) -> None:
        """
        Record a student's performance on a question.
        
        This method:
        1. Persists the performance record to Neo4j
        2. Invalidates cached mastery data for the student/concept
        3. Logs the performance recording
        
        Args:
            record: PerformanceRecord containing student performance data
            
        Raises:
            Exception: If database persistence fails
        """
        try:
            with self.neo4j_driver.session(database=concept_graph_settings.neo4j_database) as session:
                # Create performance record node
                query = """
                CREATE (p:PerformanceRecord {
                    student_id: $student_id,
                    concept_id: $concept_id,
                    is_correct: $is_correct,
                    time_taken_seconds: $time_taken_seconds,
                    timestamp: datetime($timestamp),
                    bloom_level: $bloom_level,
                    abstraction_level: $abstraction_level,
                    computational_complexity: $computational_complexity,
                    concept_integration: $concept_integration,
                    real_world_context: $real_world_context,
                    problem_solving_approach: $problem_solving_approach
                })
                RETURN p
                """
                
                session.run(
                    query,
                    student_id=record.student_id,
                    concept_id=record.concept_id,
                    is_correct=record.is_correct,
                    time_taken_seconds=record.time_taken_seconds,
                    timestamp=record.timestamp.isoformat(),
                    bloom_level=record.question_difficulty.bloom_level,
                    abstraction_level=record.question_difficulty.abstraction_level,
                    computational_complexity=record.question_difficulty.computational_complexity,
                    concept_integration=record.question_difficulty.concept_integration.value,
                    real_world_context=record.question_difficulty.real_world_context,
                    problem_solving_approach=record.question_difficulty.problem_solving_approach.value
                )
                
                logger.info(
                    f"Recorded performance for student {record.student_id} "
                    f"on concept {record.concept_id}: "
                    f"correct={record.is_correct}, time={record.time_taken_seconds}s"
                )
            
        except Exception as e:
            logger.error(f"Failed to record performance: {e}")
            raise
    
    def get_mastery_history(self, student_id: str) -> List[MasteryRecord]:
        """
        Get complete mastery history for a student.
        
        This method:
        1. Retrieves all concepts the student has attempted
        2. Calculates current mastery level for each concept
        3. Returns list of mastery records
        
        Args:
            student_id: Student identifier
            
        Returns:
            List of MasteryRecord objects for all attempted concepts
        """
        try:
            with self.neo4j_driver.session(database=concept_graph_settings.neo4j_database) as session:
                # Get all concepts the student has attempted
                query = """
                MATCH (p:PerformanceRecord {student_id: $student_id})
                RETURN DISTINCT p.concept_id as concept_id
                """
                
                result = session.run(query, student_id=student_id)
                concept_ids = [record["concept_id"] for record in result]
            
            # Calculate mastery for each concept
            mastery_records = []
            for concept_id in concept_ids:
                mastery_level = self.calculate_mastery(student_id, concept_id)
                is_mastered = self.is_mastered(student_id, concept_id)
                
                mastery_records.append(
                    MasteryRecord(
                        student_id=student_id,
                        concept_id=concept_id,
                        mastery_level=mastery_level,
                        is_mastered=is_mastered,
                        last_updated=datetime.utcnow()
                    )
                )
            
            logger.info(f"Retrieved mastery history for student {student_id}: {len(mastery_records)} concepts")
            return mastery_records
            
        except Exception as e:
            logger.error(f"Failed to get mastery history: {e}")
            raise
    
    def calculate_mastery(self, student_id: str, concept_id: str) -> float:
        """
        Calculate mastery level (0.0 to 1.0) for a concept.
        
        Algorithm:
        1. Get recent performance records (up to 10)
        2. Calculate weighted accuracy (recent attempts weighted higher)
        3. Add consistency bonus (reward consistent correct answers)
        4. Add difficulty bonus (reward mastery at higher difficulty)
        5. Return capped mastery score (0.0 to 1.0)
        
        Args:
            student_id: Student identifier
            concept_id: Concept identifier
            
        Returns:
            Mastery level from 0.0 (no mastery) to 1.0 (full mastery)
        """
        try:
            with self.neo4j_driver.session(database=concept_graph_settings.neo4j_database) as session:
                # Get recent performance records (up to 10, most recent first)
                query = """
                MATCH (p:PerformanceRecord {student_id: $student_id, concept_id: $concept_id})
                RETURN p.is_correct as is_correct,
                       p.bloom_level as bloom_level,
                       p.abstraction_level as abstraction_level,
                       p.computational_complexity as computational_complexity
                ORDER BY p.timestamp DESC
                LIMIT 10
                """
                
                result = session.run(query, student_id=student_id, concept_id=concept_id)
                records = list(result)
            
            if len(records) < 3:
                # Insufficient data for mastery calculation
                return 0.0
            
            # Weighted accuracy (recent attempts weighted higher)
            # Weights sum to 1.0, with more weight on recent attempts
            weights = [0.15, 0.15, 0.15, 0.15, 0.10, 0.10, 0.10, 0.05, 0.03, 0.02]
            accuracy_score = sum(
                w * (1.0 if r["is_correct"] else 0.0)
                for w, r in zip(weights, records)
            )
            
            # Consistency bonus (reward consistent correct answers in recent 5)
            recent_5 = records[:min(5, len(records))]
            consistency = sum(1.0 if r["is_correct"] else 0.0 for r in recent_5) / len(recent_5)
            consistency_bonus = 0.1 if consistency >= 0.8 else 0.0
            
            # Difficulty bonus (reward mastery at higher difficulty)
            # Calculate average difficulty score from bloom and abstraction levels
            avg_bloom = sum(r["bloom_level"] for r in records) / len(records)
            avg_abstraction = sum(r["abstraction_level"] for r in records) / len(records)
            avg_difficulty = (avg_bloom / 6.0 + avg_abstraction / 5.0) / 2.0
            difficulty_bonus = min(0.1, avg_difficulty * 0.1)
            
            # Calculate final mastery score
            mastery = min(1.0, accuracy_score + consistency_bonus + difficulty_bonus)
            
            logger.debug(
                f"Calculated mastery for student {student_id}, concept {concept_id}: "
                f"{mastery:.3f} (accuracy={accuracy_score:.3f}, "
                f"consistency_bonus={consistency_bonus:.3f}, "
                f"difficulty_bonus={difficulty_bonus:.3f})"
            )
            
            return mastery
            
        except Exception as e:
            logger.error(f"Failed to calculate mastery: {e}")
            raise
    
    def is_mastered(self, student_id: str, concept_id: str, threshold: float = 0.8) -> bool:
        """
        Check if concept is mastered above threshold.
        
        Args:
            student_id: Student identifier
            concept_id: Concept identifier
            threshold: Mastery threshold (default: 0.8)
            
        Returns:
            True if mastery level >= threshold, False otherwise
        """
        mastery = self.calculate_mastery(student_id, concept_id)
        return mastery >= threshold
    
    def recommend_difficulty_adjustment(self, student_id: str, concept_id: str) -> float:
        """
        Recommend difficulty adjustment based on recent performance.
        
        Algorithm:
        1. Get recent 5 performance records
        2. Calculate accuracy rate
        3. Return positive adjustment for high accuracy (>= 0.8)
        4. Return negative adjustment for low accuracy (<= 0.4)
        5. Return zero adjustment for moderate accuracy
        
        Args:
            student_id: Student identifier
            concept_id: Concept identifier
            
        Returns:
            Difficulty adjustment factor (-1.0 to +1.0)
            - Positive: increase difficulty
            - Negative: decrease difficulty
            - Zero: maintain current difficulty
        """
        try:
            with self.neo4j_driver.session(database=concept_graph_settings.neo4j_database) as session:
                # Get recent 5 performance records
                query = """
                MATCH (p:PerformanceRecord {student_id: $student_id, concept_id: $concept_id})
                RETURN p.is_correct as is_correct
                ORDER BY p.timestamp DESC
                LIMIT 5
                """
                
                result = session.run(query, student_id=student_id, concept_id=concept_id)
                records = list(result)
            
            if len(records) < 3:
                # Insufficient data, maintain current difficulty
                return 0.0
            
            # Calculate accuracy rate
            accuracy = sum(1.0 if r["is_correct"] else 0.0 for r in records) / len(records)
            
            # Determine adjustment based on accuracy
            if accuracy >= 0.8:
                # High accuracy: increase difficulty
                adjustment = 0.5
            elif accuracy <= 0.4:
                # Low accuracy: decrease difficulty
                adjustment = -0.5
            else:
                # Moderate accuracy: maintain difficulty
                adjustment = 0.0
            
            logger.debug(
                f"Recommended difficulty adjustment for student {student_id}, "
                f"concept {concept_id}: {adjustment:+.2f} (accuracy={accuracy:.2f})"
            )
            
            return adjustment
            
        except Exception as e:
            logger.error(f"Failed to recommend difficulty adjustment: {e}")
            raise
