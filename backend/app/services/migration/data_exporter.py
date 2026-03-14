"""
Data Exporter Service

Exports existing data from old models to JSON backup files before migration.
Creates comprehensive backups to prevent data loss during migration.

Requirements: 21.1
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel
from supabase import Client

logger = logging.getLogger(__name__)


class ExportResult(BaseModel):
    """Result of a data export operation."""
    success: bool
    backup_path: str
    tables_exported: int = 0
    total_records: int = 0
    error: Optional[str] = None
    timestamp: datetime


class DataExporter:
    """
    Exports existing data from old models to JSON backup files.
    
    This service creates comprehensive backups before migration to ensure
    no data is lost during the migration process. Backups are stored in
    timestamped directories for easy identification and restoration.
    """
    
    def __init__(self, supabase_client: Client, backup_base_path: str = "/tmp/backups"):
        """
        Initialize the data exporter.
        
        Args:
            supabase_client: Supabase client for database operations
            backup_base_path: Base directory for backup files
        """
        self.client = supabase_client
        self.backup_base_path = Path(backup_base_path)
        
    def export_all_data(self) -> ExportResult:
        """
        Export all existing data from old models to JSON backup files.
        
        Creates a timestamped backup directory and exports:
        - Test data (test_papers, test_sessions, attempts)
        - Question data (questions, options, answers, metadata)
        - User preferences and analytics data
        - Extraction job data
        
        Preconditions:
            - Database connection is valid
            - backup_base_path directory exists or can be created
        
        Postconditions:
            - Backup directory created with timestamp
            - All table data exported to JSON files
            - Returns ExportResult with success status and counts
        
        Returns:
            ExportResult with export status and statistics
        """
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_base_path / f"pre_migration_{timestamp_str}"
        
        logger.info(f"Starting data export to {backup_path}")
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            tables_exported = 0
            total_records = 0
            
            # Export test data
            test_count = self._export_test_data(backup_path)
            if test_count > 0:
                tables_exported += 1
                total_records += test_count
                logger.info(f"Exported {test_count} test records")
            
            # Export question data
            question_count = self._export_question_data(backup_path)
            if question_count > 0:
                tables_exported += 1
                total_records += question_count
                logger.info(f"Exported {question_count} question records")
            
            # Export user preferences
            user_count = self._export_user_data(backup_path)
            if user_count > 0:
                tables_exported += 1
                total_records += user_count
                logger.info(f"Exported {user_count} user records")
            
            # Export analytics data
            analytics_count = self._export_analytics_data(backup_path)
            if analytics_count > 0:
                tables_exported += 1
                total_records += analytics_count
                logger.info(f"Exported {analytics_count} analytics records")
            
            # Export extraction job data
            extraction_count = self._export_extraction_data(backup_path)
            if extraction_count > 0:
                tables_exported += 1
                total_records += extraction_count
                logger.info(f"Exported {extraction_count} extraction records")
            
            # Create export manifest
            manifest = {
                "export_timestamp": timestamp.isoformat(),
                "tables_exported": tables_exported,
                "total_records": total_records,
                "backup_path": str(backup_path),
                "tables": {
                    "test_data": test_count,
                    "question_data": question_count,
                    "user_data": user_count,
                    "analytics_data": analytics_count,
                    "extraction_data": extraction_count
                }
            }
            
            manifest_path = backup_path / "export_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2, default=str)
            
            logger.info(f"Data export completed successfully: {tables_exported} tables, {total_records} records")
            
            return ExportResult(
                success=True,
                backup_path=str(backup_path),
                tables_exported=tables_exported,
                total_records=total_records,
                timestamp=timestamp
            )
            
        except Exception as e:
            error_msg = f"Data export failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ExportResult(
                success=False,
                backup_path=str(backup_path),
                error=error_msg,
                timestamp=timestamp
            )
    
    def _export_test_data(self, backup_path: Path) -> int:
        """
        Export test-related data to JSON files.
        
        Exports:
        - test_papers
        - test_sessions
        - attempts
        
        Args:
            backup_path: Directory to store backup files
        
        Returns:
            Number of records exported
        """
        total_records = 0
        
        try:
            # Export test_papers
            test_papers = self._export_table('test_papers', backup_path)
            total_records += len(test_papers)
            
            # Export test_sessions
            test_sessions = self._export_table('test_sessions', backup_path)
            total_records += len(test_sessions)
            
            # Export attempts
            attempts = self._export_table('attempts', backup_path)
            total_records += len(attempts)
            
        except Exception as e:
            logger.warning(f"Error exporting test data: {e}")
        
        return total_records
    
    def _export_question_data(self, backup_path: Path) -> int:
        """
        Export question-related data to JSON files.
        
        Exports:
        - books, chapters, topics (hierarchy)
        - questions
        - options
        - answers
        - question_images
        - question_tables
        - question_tags
        - hints
        - explanations
        
        Args:
            backup_path: Directory to store backup files
        
        Returns:
            Number of records exported
        """
        total_records = 0
        
        try:
            # Export hierarchy
            books = self._export_table('books', backup_path)
            total_records += len(books)
            
            chapters = self._export_table('chapters', backup_path)
            total_records += len(chapters)
            
            topics = self._export_table('topics', backup_path)
            total_records += len(topics)
            
            # Export questions and metadata
            questions = self._export_table('questions', backup_path)
            total_records += len(questions)
            
            options = self._export_table('options', backup_path)
            total_records += len(options)
            
            answers = self._export_table('answers', backup_path)
            total_records += len(answers)
            
            question_images = self._export_table('question_images', backup_path)
            total_records += len(question_images)
            
            question_tables = self._export_table('question_tables', backup_path)
            total_records += len(question_tables)
            
            question_tags = self._export_table('question_tags', backup_path)
            total_records += len(question_tags)
            
            hints = self._export_table('hints', backup_path)
            total_records += len(hints)
            
            explanations = self._export_table('explanations', backup_path)
            total_records += len(explanations)
            
        except Exception as e:
            logger.warning(f"Error exporting question data: {e}")
        
        return total_records
    
    def _export_user_data(self, backup_path: Path) -> int:
        """
        Export user-related data to JSON files.
        
        Note: User authentication data is managed by Supabase Auth and
        doesn't need to be exported. This exports user preferences and
        profile data stored in user_metadata.
        
        Args:
            backup_path: Directory to store backup files
        
        Returns:
            Number of records exported
        """
        total_records = 0
        
        try:
            # Export user preferences if stored in a separate table
            # For now, user data is in Supabase Auth, so we skip this
            logger.info("User data is managed by Supabase Auth, skipping export")
            
        except Exception as e:
            logger.warning(f"Error exporting user data: {e}")
        
        return total_records
    
    def _export_analytics_data(self, backup_path: Path) -> int:
        """
        Export analytics-related data to JSON files.
        
        Exports:
        - question_stats
        - student_topic_mastery
        - daily_activity
        
        Args:
            backup_path: Directory to store backup files
        
        Returns:
            Number of records exported
        """
        total_records = 0
        
        try:
            # Export question_stats
            question_stats = self._export_table('question_stats', backup_path)
            total_records += len(question_stats)
            
            # Export student_topic_mastery
            mastery = self._export_table('student_topic_mastery', backup_path)
            total_records += len(mastery)
            
            # Export daily_activity
            daily_activity = self._export_table('daily_activity', backup_path)
            total_records += len(daily_activity)
            
        except Exception as e:
            logger.warning(f"Error exporting analytics data: {e}")
        
        return total_records
    
    def _export_extraction_data(self, backup_path: Path) -> int:
        """
        Export extraction pipeline data to JSON files.
        
        Exports:
        - extraction_jobs
        - extraction_pages
        - extraction_blocks
        - raw_questions
        
        Args:
            backup_path: Directory to store backup files
        
        Returns:
            Number of records exported
        """
        total_records = 0
        
        try:
            # Export extraction_jobs
            jobs = self._export_table('extraction_jobs', backup_path)
            total_records += len(jobs)
            
            # Export extraction_pages
            pages = self._export_table('extraction_pages', backup_path)
            total_records += len(pages)
            
            # Export extraction_blocks
            blocks = self._export_table('extraction_blocks', backup_path)
            total_records += len(blocks)
            
            # Export raw_questions
            raw_questions = self._export_table('raw_questions', backup_path)
            total_records += len(raw_questions)
            
        except Exception as e:
            logger.warning(f"Error exporting extraction data: {e}")
        
        return total_records
    
    def _export_table(self, table_name: str, backup_path: Path) -> List[Dict[str, Any]]:
        """
        Export a single table to a JSON file.
        
        Args:
            table_name: Name of the table to export
            backup_path: Directory to store backup file
        
        Returns:
            List of records exported
        """
        try:
            # Query all data from table
            response = self.client.table(table_name).select("*").execute()
            
            if not response.data:
                logger.info(f"Table {table_name} is empty, skipping export")
                return []
            
            # Write to JSON file
            output_file = backup_path / f"{table_name}.json"
            with open(output_file, 'w') as f:
                json.dump(response.data, f, indent=2, default=str)
            
            logger.debug(f"Exported {len(response.data)} records from {table_name}")
            return response.data
            
        except Exception as e:
            logger.warning(f"Could not export table {table_name}: {e}")
            return []
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore data from a backup directory.
        
        This is a utility method for disaster recovery. It reads JSON files
        from a backup directory and restores them to the database.
        
        Args:
            backup_path: Path to backup directory
        
        Returns:
            True if restoration succeeded, False otherwise
        """
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            logger.error(f"Backup directory does not exist: {backup_path}")
            return False
        
        try:
            # Read manifest
            manifest_path = backup_dir / "export_manifest.json"
            if not manifest_path.exists():
                logger.error(f"Backup manifest not found: {manifest_path}")
                return False
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            logger.info(f"Restoring from backup: {manifest['export_timestamp']}")
            
            # Restore each table
            for json_file in backup_dir.glob("*.json"):
                if json_file.name == "export_manifest.json":
                    continue
                
                table_name = json_file.stem
                
                with open(json_file, 'r') as f:
                    records = json.load(f)
                
                if not records:
                    continue
                
                # Insert records into table
                try:
                    self.client.table(table_name).insert(records).execute()
                    logger.info(f"Restored {len(records)} records to {table_name}")
                except Exception as e:
                    logger.error(f"Failed to restore {table_name}: {e}")
            
            logger.info("Backup restoration completed")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}", exc_info=True)
            return False
