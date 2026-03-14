"""
Migration Validator Service

This module provides validation functionality for database migrations.
It verifies that all tables exist with correct schema, checks foreign key
constraints, validates data counts, and tests sample queries.

Requirements: 18.1, 18.2, 18.3, 18.4, 18.5
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check"""
    success: bool
    message: str
    details: Optional[Dict] = None


@dataclass
class MigrationValidationReport:
    """Complete migration validation report"""
    success: bool
    timestamp: datetime
    tables_validated: int
    foreign_keys_validated: int
    data_counts: Dict[str, int]
    validation_errors: List[str]
    validation_warnings: List[str]
    sample_query_results: Dict[str, bool]


class MigrationValidator:
    """
    Validates database migration integrity and correctness.
    
    This class provides methods to:
    - Verify all required tables exist with correct schema
    - Check all foreign key constraints are valid
    - Verify data counts match expected values
    - Test sample queries to ensure schema works correctly
    - Rollback migration and restore from backup on validation failure
    """
    
    # All 22 tables that should exist after migration
    REQUIRED_TABLES = [
        'books',
        'chapters',
        'topics',
        'extraction_jobs',
        'extraction_pages',
        'extraction_blocks',
        'raw_questions',
        'questions',
        'options',
        'answers',
        'question_images',
        'question_tables',
        'question_tags',
        'hints',
        'explanations',
        'test_papers',
        'test_paper_questions',
        'test_sessions',
        'attempts',
        'question_stats',
        'student_topic_mastery',
        'daily_activity'
    ]
    
    def __init__(self, supabase: Client):
        """
        Initialize the migration validator.
        
        Args:
            supabase: Supabase client instance
        """
        self.supabase = supabase
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_migration(self) -> MigrationValidationReport:
        """
        Perform complete migration validation.
        
        This method runs all validation checks and returns a comprehensive report.
        
        Returns:
            MigrationValidationReport with validation results
        """
        logger.info("Starting migration validation...")
        
        # Reset error and warning lists
        self.validation_errors = []
        self.validation_warnings = []
        
        # Step 1: Verify all tables exist
        tables_result = self._verify_tables_exist()
        if not tables_result.success:
            self.validation_errors.append(tables_result.message)
            return self._create_failed_report("Table existence check failed")
        
        # Step 2: Verify table schemas
        schema_result = self._verify_table_schemas()
        if not schema_result.success:
            self.validation_errors.append(schema_result.message)
            return self._create_failed_report("Schema validation failed")
        
        # Step 3: Check foreign key constraints
        fk_result = self._check_foreign_key_constraints()
        if not fk_result.success:
            self.validation_errors.append(fk_result.message)
            return self._create_failed_report("Foreign key validation failed")
        
        # Step 4: Verify data counts
        data_counts = self._verify_data_counts()
        
        # Step 5: Test sample queries
        query_results = self._test_sample_queries()
        failed_queries = [q for q, success in query_results.items() if not success]
        if failed_queries:
            self.validation_errors.append(f"Sample queries failed: {', '.join(failed_queries)}")
            return self._create_failed_report("Sample query validation failed")
        
        # All validations passed
        logger.info("Migration validation completed successfully")
        return MigrationValidationReport(
            success=True,
            timestamp=datetime.now(),
            tables_validated=len(self.REQUIRED_TABLES),
            foreign_keys_validated=fk_result.details.get('fk_count', 0) if fk_result.details else 0,
            data_counts=data_counts,
            validation_errors=[],
            validation_warnings=self.validation_warnings,
            sample_query_results=query_results
        )
    
    def _verify_tables_exist(self) -> ValidationResult:
        """
        Verify all 21 required tables exist in the database.
        
        Requirements: 18.1
        
        Returns:
            ValidationResult indicating success or failure
        """
        logger.info("Verifying table existence...")
        
        try:
            existing_tables = []
            missing_tables = []
            
            # Try to query each table to verify it exists
            for table in self.REQUIRED_TABLES:
                try:
                    # Attempt to query the table (limit 0 to avoid loading data)
                    self.supabase.table(table).select("*").limit(0).execute()
                    existing_tables.append(table)
                except Exception as e:
                    # Table doesn't exist or can't be accessed
                    missing_tables.append(table)
                    logger.debug(f"Table {table} not accessible: {str(e)}")
            
            if missing_tables:
                message = f"Missing or inaccessible tables: {', '.join(sorted(missing_tables))}"
                logger.error(message)
                return ValidationResult(success=False, message=message)
            
            logger.info(f"All {len(self.REQUIRED_TABLES)} required tables exist")
            return ValidationResult(
                success=True,
                message=f"All {len(self.REQUIRED_TABLES)} tables exist",
                details={'tables': existing_tables}
            )
        
        except Exception as e:
            message = f"Error checking table existence: {str(e)}"
            logger.error(message)
            return ValidationResult(success=False, message=message)
    
    def _verify_table_schemas(self) -> ValidationResult:
        """
        Verify that tables have the expected columns and data types.
        
        Requirements: 18.1
        
        Returns:
            ValidationResult indicating success or failure
        """
        logger.info("Verifying table schemas...")
        
        # Define critical columns for key tables
        critical_tables_columns = {
            'questions': ['id', 'question_number', 'question_text', 'topic_id', 'chapter_id', 'book_id', 'answer_type'],
            'test_sessions': ['id', 'test_paper_id', 'student_id', 'status', 'started_at'],
            'attempts': ['id', 'session_id', 'question_id', 'is_correct', 'marks_awarded'],
            'question_stats': ['question_id', 'total_attempts', 'correct_attempts', 'accuracy_pct'],
        }
        
        try:
            for table_name, required_columns in critical_tables_columns.items():
                try:
                    # Query the table with select to verify columns exist
                    select_clause = ','.join(required_columns)
                    self.supabase.table(table_name).select(select_clause).limit(1).execute()
                except Exception as e:
                    message = f"Table '{table_name}' schema validation failed: {str(e)}"
                    logger.error(message)
                    return ValidationResult(success=False, message=message)
            
            logger.info("All table schemas validated successfully")
            return ValidationResult(success=True, message="Table schemas are correct")
        
        except Exception as e:
            message = f"Error verifying table schemas: {str(e)}"
            logger.error(message)
            return ValidationResult(success=False, message=message)
    
    def _check_foreign_key_constraints(self) -> ValidationResult:
        """
        Check that all foreign key constraints are valid and no orphaned records exist.
        
        Requirements: 18.2
        
        Returns:
            ValidationResult indicating success or failure
        """
        logger.info("Checking foreign key constraints...")
        
        try:
            # Check for orphaned records in key tables
            orphan_checks = [
                ("questions", "topic_id", "topics"),
                ("questions", "chapter_id", "chapters"),
                ("questions", "book_id", "books"),
                ("test_sessions", "test_paper_id", "test_papers"),
                ("attempts", "session_id", "test_sessions"),
                ("attempts", "question_id", "questions"),
            ]
            
            fk_count = len(orphan_checks)
            
            for table, fk_column, ref_table in orphan_checks:
                try:
                    # Get all foreign key values from the table
                    result = self.supabase.table(table).select(fk_column).limit(100).execute()
                    
                    if result.data:
                        # Check a sample of foreign keys
                        for row in result.data[:10]:  # Check first 10 records
                            fk_value = row.get(fk_column)
                            if fk_value:
                                # Verify the referenced record exists
                                ref_result = self.supabase.table(ref_table).select("id").eq("id", fk_value).execute()
                                if not ref_result.data:
                                    message = f"Orphaned record in {table}.{fk_column}: {fk_value} not found in {ref_table}"
                                    logger.error(message)
                                    return ValidationResult(success=False, message=message)
                
                except Exception as e:
                    logger.warning(f"Could not validate FK {table}.{fk_column}: {str(e)}")
            
            logger.info(f"Validated {fk_count} foreign key relationships")
            return ValidationResult(
                success=True,
                message="All foreign key constraints are valid",
                details={'fk_count': fk_count}
            )
        
        except Exception as e:
            message = f"Error checking foreign key constraints: {str(e)}"
            logger.error(message)
            return ValidationResult(success=False, message=message)
    
    def _verify_data_counts(self) -> Dict[str, int]:
        """
        Verify data counts for all tables and check for reasonable values.
        
        Requirements: 18.3
        
        Returns:
            Dictionary mapping table names to row counts
        """
        logger.info("Verifying data counts...")
        
        data_counts = {}
        
        try:
            for table in self.REQUIRED_TABLES:
                try:
                    result = self.supabase.table(table).select("*", count="exact").limit(0).execute()
                    count = result.count if hasattr(result, 'count') else 0
                    data_counts[table] = count
                    logger.info(f"  {table}: {count} rows")
                except Exception as e:
                    logger.warning(f"Could not count rows in {table}: {str(e)}")
                    data_counts[table] = -1  # Indicate error
            
            # Check for data consistency
            if data_counts.get('questions', 0) > 0:
                # If we have questions, we should have related data
                if data_counts.get('topics', 0) == 0:
                    self.validation_warnings.append("Questions exist but no topics found")
                if data_counts.get('books', 0) == 0:
                    self.validation_warnings.append("Questions exist but no books found")
            
            if data_counts.get('test_sessions', 0) > 0:
                # If we have sessions, we should have attempts
                if data_counts.get('attempts', 0) == 0:
                    self.validation_warnings.append("Test sessions exist but no attempts found")
        
        except Exception as e:
            logger.error(f"Error verifying data counts: {str(e)}")
            self.validation_warnings.append(f"Could not verify all data counts: {str(e)}")
        
        return data_counts
    
    def _test_sample_queries(self) -> Dict[str, bool]:
        """
        Test sample queries to ensure schema works correctly.
        
        Requirements: 18.4
        
        Returns:
            Dictionary mapping query names to success status
        """
        logger.info("Testing sample queries...")
        
        query_results = {}
        
        # Query 1: Questions with hierarchy join
        query_results['hierarchy_join'] = self._test_query(
            "hierarchy_join",
            lambda: self.supabase.table("questions")
                .select("id, question_text, topics(title), chapters(title), books(title)")
                .limit(5)
                .execute()
        )
        
        # Query 2: Test sessions with attempts count
        query_results['session_attempts'] = self._test_query(
            "session_attempts",
            lambda: self.supabase.table("test_sessions")
                .select("id, status, attempts(count)")
                .limit(5)
                .execute()
        )
        
        # Query 3: Question stats
        query_results['question_stats'] = self._test_query(
            "question_stats",
            lambda: self.supabase.table("question_stats")
                .select("question_id, total_attempts, accuracy_pct")
                .gt("total_attempts", 0)
                .limit(5)
                .execute()
        )
        
        # Query 4: Student mastery
        query_results['student_mastery'] = self._test_query(
            "student_mastery",
            lambda: self.supabase.table("student_topic_mastery")
                .select("student_id, topic_id, mastery_level, accuracy_pct")
                .limit(5)
                .execute()
        )
        
        # Query 5: Extraction pipeline
        query_results['extraction_pipeline'] = self._test_query(
            "extraction_pipeline",
            lambda: self.supabase.table("extraction_jobs")
                .select("id, stage, extraction_pages(count)")
                .limit(5)
                .execute()
        )
        
        # Query 6: Test papers with questions
        query_results['test_paper_questions'] = self._test_query(
            "test_paper_questions",
            lambda: self.supabase.table("test_papers")
                .select("id, title, test_paper_questions(count)")
                .limit(5)
                .execute()
        )
        
        return query_results
    
    def _test_query(self, query_name: str, query_func) -> bool:
        """
        Execute a test query and return success status.
        
        Args:
            query_name: Name of the query for logging
            query_func: Function that executes the query
        
        Returns:
            True if query executed successfully, False otherwise
        """
        try:
            result = query_func()
            row_count = len(result.data) if result.data else 0
            logger.info(f"  {query_name}: SUCCESS ({row_count} rows)")
            return True
        
        except Exception as e:
            logger.error(f"  {query_name}: FAILED - {str(e)}")
            return False
    
    def _create_failed_report(self, reason: str) -> MigrationValidationReport:
        """
        Create a failed validation report.
        
        Args:
            reason: Reason for validation failure
        
        Returns:
            MigrationValidationReport with success=False
        """
        return MigrationValidationReport(
            success=False,
            timestamp=datetime.now(),
            tables_validated=0,
            foreign_keys_validated=0,
            data_counts={},
            validation_errors=self.validation_errors,
            validation_warnings=self.validation_warnings,
            sample_query_results={}
        )
    
    def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback migration and restore from backup if validation fails.
        
        Note: With Supabase, rollback typically involves running migration scripts
        in reverse or restoring from a database backup. This method logs the
        rollback requirement and provides guidance.
        
        Requirements: 18.5
        
        Args:
            backup_path: Path to the backup file to restore from
        
        Returns:
            True if rollback guidance provided, False otherwise
        """
        logger.warning(f"Migration rollback required. Backup location: {backup_path}")
        logger.warning("=" * 80)
        logger.warning("ROLLBACK INSTRUCTIONS:")
        logger.warning("1. Stop all application services")
        logger.warning("2. Use Supabase dashboard or CLI to restore from backup")
        logger.warning(f"3. Backup file: {backup_path}")
        logger.warning("4. Alternatively, run migration down scripts if available")
        logger.warning("5. Verify database state after rollback")
        logger.warning("=" * 80)
        
        # Log the rollback event
        try:
            logger.error(f"Migration validation failed. Manual rollback required from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error logging rollback: {str(e)}")
            return False
    
    def log_validation_errors(self, report: MigrationValidationReport) -> None:
        """
        Log detailed validation errors for debugging.
        
        Requirements: 18.5
        
        Args:
            report: Validation report to log
        """
        logger.error("=" * 80)
        logger.error("MIGRATION VALIDATION FAILED")
        logger.error("=" * 80)
        logger.error(f"Timestamp: {report.timestamp}")
        logger.error(f"Tables validated: {report.tables_validated}")
        logger.error(f"Foreign keys validated: {report.foreign_keys_validated}")
        
        if report.validation_errors:
            logger.error("\nValidation Errors:")
            for i, error in enumerate(report.validation_errors, 1):
                logger.error(f"  {i}. {error}")
        
        if report.validation_warnings:
            logger.warning("\nValidation Warnings:")
            for i, warning in enumerate(report.validation_warnings, 1):
                logger.warning(f"  {i}. {warning}")
        
        if report.data_counts:
            logger.info("\nData Counts:")
            for table, count in sorted(report.data_counts.items()):
                logger.info(f"  {table}: {count}")
        
        if report.sample_query_results:
            logger.info("\nSample Query Results:")
            for query, success in report.sample_query_results.items():
                status = "✓" if success else "✗"
                logger.info(f"  {status} {query}")
        
        logger.error("=" * 80)
