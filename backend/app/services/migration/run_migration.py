#!/usr/bin/env python3
"""
Migration Orchestration Script

This script orchestrates the complete database migration from old to new schema.
It executes all migration phases in order and provides comprehensive reporting.

Usage:
    python run_migration.py [options]

Options:
    --dry-run           Run validation without making changes
    --skip-validation   Skip validation checks (not recommended)
    --rollback PATH     Rollback migration and restore from backup
    --backup-path PATH  Custom path for backup files
    --verbose           Enable verbose logging

Requirements: 1.1, 18.1, 21.1, 21.7, 22.1
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from supabase import create_client, Client

from .schema_migration_manager import SchemaMigrationManager, MigrationResult
from .data_exporter import DataExporter
from .data_migrator import DataMigrator
from .table_cleanup import TableCleanup
from .migration_validator import MigrationValidator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log')
    ]
)

logger = logging.getLogger(__name__)


@dataclass
class MigrationConfig:
    """Configuration for migration execution."""
    dry_run: bool = False
    skip_validation: bool = False
    rollback_path: Optional[str] = None
    backup_path: str = "/tmp/backups"
    verbose: bool = False
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None


@dataclass
class MigrationPhaseResult:
    """Result of a single migration phase."""
    phase_name: str
    success: bool
    duration_seconds: float
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class CompleteMigrationReport:
    """Comprehensive report of entire migration process."""
    success: bool
    started_at: datetime
    completed_at: datetime
    total_duration_seconds: float
    phases: list[MigrationPhaseResult] = field(default_factory=list)
    backup_path: Optional[str] = None
    tables_created: int = 0
    rows_migrated: int = 0
    tables_cleaned: int = 0
    validation_passed: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MigrationOrchestrator:
    """
    Orchestrates the complete database migration process.
    
    This class coordinates all migration phases:
    1. Backup existing data
    2. Create new schema
    3. Migrate data
    4. Validate migration
    5. Cleanup old tables
    
    Each phase is timed and logged. If any phase fails, the migration
    can be rolled back to the backup state.
    """
    
    def __init__(self, config: MigrationConfig):
        """
        Initialize the migration orchestrator.
        
        Args:
            config: Migration configuration
        """
        self.config = config
        self.report = CompleteMigrationReport(
            success=False,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_duration_seconds=0.0
        )
        
        # Initialize Supabase client
        self.supabase = self._init_supabase_client()
        
        # Initialize migration components
        self.schema_manager = SchemaMigrationManager(self.supabase)
        self.data_exporter = DataExporter(self.supabase, config.backup_path)
        self.data_migrator = DataMigrator(self.supabase)
        self.table_cleanup = TableCleanup(self.supabase, f"{config.backup_path}/table_backups")
        self.validator = MigrationValidator(self.supabase)
        
        # Configure logging level
        if config.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
    
    def _init_supabase_client(self) -> Client:
        """
        Initialize Supabase client from config or environment.
        
        Returns:
            Supabase client instance
        """
        import os
        
        url = self.config.supabase_url or os.getenv('SUPABASE_URL')
        key = self.config.supabase_key or os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError(
                "Supabase credentials not found. "
                "Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables "
                "or pass them via command line."
            )
        
        return create_client(url, key)
    
    def run_migration(self) -> CompleteMigrationReport:
        """
        Execute the complete migration process.
        
        Phases:
        1. Backup - Export existing data to backup files
        2. Schema Creation - Create all new tables and constraints
        3. Data Migration - Migrate data from old to new schema
        4. Validation - Verify migration integrity
        5. Cleanup - Remove old conflicting tables
        
        Each phase is executed in order. If any phase fails, the migration
        stops and can be rolled back.
        
        Returns:
            CompleteMigrationReport with detailed results
        """
        logger.info("=" * 80)
        logger.info("STARTING DATABASE MIGRATION")
        logger.info("=" * 80)
        logger.info(f"Dry run: {self.config.dry_run}")
        logger.info(f"Skip validation: {self.config.skip_validation}")
        logger.info(f"Backup path: {self.config.backup_path}")
        logger.info("")
        
        try:
            # Phase 1: Backup existing data
            if not self._execute_phase_backup():
                return self._finalize_report(success=False)
            
            # Phase 2: Create new schema
            if not self._execute_phase_schema_creation():
                return self._finalize_report(success=False)
            
            # Phase 3: Migrate data
            if not self._execute_phase_data_migration():
                return self._finalize_report(success=False)
            
            # Phase 4: Validate migration
            if not self.config.skip_validation:
                if not self._execute_phase_validation():
                    return self._finalize_report(success=False)
            else:
                logger.warning("Skipping validation (not recommended)")
                self.report.warnings.append("Validation was skipped")
            
            # Phase 5: Cleanup old tables
            if not self.config.dry_run:
                if not self._execute_phase_cleanup():
                    # Cleanup failure is not critical
                    self.report.warnings.append("Table cleanup encountered errors")
            else:
                logger.info("Dry run: Skipping table cleanup")
            
            # Migration completed successfully
            return self._finalize_report(success=True)
            
        except KeyboardInterrupt:
            logger.error("Migration interrupted by user")
            self.report.errors.append("Migration interrupted by user")
            return self._finalize_report(success=False)
        
        except Exception as e:
            logger.error(f"Migration failed with unexpected error: {str(e)}", exc_info=True)
            self.report.errors.append(f"Unexpected error: {str(e)}")
            return self._finalize_report(success=False)
    
    def _execute_phase_backup(self) -> bool:
        """
        Execute Phase 1: Backup existing data.
        
        Requirements: 21.1
        
        Returns:
            True if phase succeeded, False otherwise
        """
        phase_start = datetime.now()
        logger.info("=" * 80)
        logger.info("PHASE 1: BACKUP EXISTING DATA")
        logger.info("=" * 80)
        
        try:
            backup_result = self.schema_manager.backup_existing_data(self.config.backup_path)
            
            duration = (datetime.now() - phase_start).total_seconds()
            
            if backup_result.success:
                logger.info(f"✓ Backup completed successfully in {duration:.2f}s")
                logger.info(f"  Backup location: {backup_result.backup_path}")
                logger.info(f"  Tables backed up: {backup_result.tables_backed_up}")
                
                self.report.backup_path = backup_result.backup_path
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Backup",
                    success=True,
                    duration_seconds=duration,
                    message=f"Backed up {backup_result.tables_backed_up} tables",
                    details={
                        'backup_path': backup_result.backup_path,
                        'tables_backed_up': backup_result.tables_backed_up
                    }
                ))
                return True
            else:
                logger.error(f"✗ Backup failed: {backup_result.error}")
                self.report.errors.append(f"Backup failed: {backup_result.error}")
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Backup",
                    success=False,
                    duration_seconds=duration,
                    message=f"Backup failed: {backup_result.error}"
                ))
                return False
                
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            logger.error(f"✗ Backup phase failed: {str(e)}", exc_info=True)
            self.report.errors.append(f"Backup phase error: {str(e)}")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Backup",
                success=False,
                duration_seconds=duration,
                message=f"Error: {str(e)}"
            ))
            return False
    
    def _execute_phase_schema_creation(self) -> bool:
        """
        Execute Phase 2: Create new schema.
        
        Requirements: 1.1
        
        Returns:
            True if phase succeeded, False otherwise
        """
        phase_start = datetime.now()
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 2: CREATE NEW SCHEMA")
        logger.info("=" * 80)
        
        if self.config.dry_run:
            logger.info("Dry run: Skipping schema creation")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Schema Creation",
                success=True,
                duration_seconds=0,
                message="Skipped (dry run)"
            ))
            return True
        
        try:
            schema_result = self.schema_manager.create_new_schema()
            
            duration = (datetime.now() - phase_start).total_seconds()
            
            if schema_result.success:
                logger.info(f"✓ Schema creation completed successfully in {duration:.2f}s")
                logger.info(f"  Tables created: {schema_result.tables_created}")
                
                self.report.tables_created = schema_result.tables_created
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Schema Creation",
                    success=True,
                    duration_seconds=duration,
                    message=f"Created {schema_result.tables_created} tables",
                    details={'tables_created': schema_result.tables_created}
                ))
                return True
            else:
                logger.error(f"✗ Schema creation failed: {schema_result.error}")
                self.report.errors.append(f"Schema creation failed: {schema_result.error}")
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Schema Creation",
                    success=False,
                    duration_seconds=duration,
                    message=f"Failed: {schema_result.error}"
                ))
                return False
                
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            logger.error(f"✗ Schema creation phase failed: {str(e)}", exc_info=True)
            self.report.errors.append(f"Schema creation error: {str(e)}")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Schema Creation",
                success=False,
                duration_seconds=duration,
                message=f"Error: {str(e)}"
            ))
            return False
    
    def _execute_phase_data_migration(self) -> bool:
        """
        Execute Phase 3: Migrate data.
        
        Requirements: 21.1, 21.7
        
        Returns:
            True if phase succeeded, False otherwise
        """
        phase_start = datetime.now()
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 3: MIGRATE DATA")
        logger.info("=" * 80)
        
        if self.config.dry_run:
            logger.info("Dry run: Skipping data migration")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Data Migration",
                success=True,
                duration_seconds=0,
                message="Skipped (dry run)"
            ))
            return True
        
        try:
            migration_result = self.schema_manager.migrate_data()
            
            duration = (datetime.now() - phase_start).total_seconds()
            
            if migration_result.success:
                logger.info(f"✓ Data migration completed successfully in {duration:.2f}s")
                logger.info(f"  Records migrated: {migration_result.rows_migrated}")
                
                self.report.rows_migrated = migration_result.rows_migrated
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Data Migration",
                    success=True,
                    duration_seconds=duration,
                    message=f"Migrated {migration_result.rows_migrated} records",
                    details={'rows_migrated': migration_result.rows_migrated}
                ))
                
                # Add any migration warnings
                if migration_result.error:
                    self.report.warnings.append(f"Migration warnings: {migration_result.error}")
                
                return True
            else:
                logger.error(f"✗ Data migration failed: {migration_result.error}")
                self.report.errors.append(f"Data migration failed: {migration_result.error}")
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Data Migration",
                    success=False,
                    duration_seconds=duration,
                    message=f"Failed: {migration_result.error}"
                ))
                return False
                
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            logger.error(f"✗ Data migration phase failed: {str(e)}", exc_info=True)
            self.report.errors.append(f"Data migration error: {str(e)}")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Data Migration",
                success=False,
                duration_seconds=duration,
                message=f"Error: {str(e)}"
            ))
            return False
    
    def _execute_phase_validation(self) -> bool:
        """
        Execute Phase 4: Validate migration.
        
        Requirements: 18.1
        
        Returns:
            True if phase succeeded, False otherwise
        """
        phase_start = datetime.now()
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 4: VALIDATE MIGRATION")
        logger.info("=" * 80)
        
        try:
            validation_report = self.validator.validate_migration()
            
            duration = (datetime.now() - phase_start).total_seconds()
            
            if validation_report.success:
                logger.info(f"✓ Validation completed successfully in {duration:.2f}s")
                logger.info(f"  Tables validated: {validation_report.tables_validated}")
                logger.info(f"  Foreign keys validated: {validation_report.foreign_keys_validated}")
                
                # Log data counts
                if validation_report.data_counts:
                    logger.info("  Data counts:")
                    for table, count in sorted(validation_report.data_counts.items()):
                        if count > 0:
                            logger.info(f"    {table}: {count}")
                
                self.report.validation_passed = True
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Validation",
                    success=True,
                    duration_seconds=duration,
                    message=f"Validated {validation_report.tables_validated} tables",
                    details={
                        'tables_validated': validation_report.tables_validated,
                        'foreign_keys_validated': validation_report.foreign_keys_validated,
                        'data_counts': validation_report.data_counts
                    }
                ))
                
                # Add any validation warnings
                if validation_report.validation_warnings:
                    self.report.warnings.extend(validation_report.validation_warnings)
                
                return True
            else:
                logger.error(f"✗ Validation failed")
                self.validator.log_validation_errors(validation_report)
                
                self.report.errors.extend(validation_report.validation_errors)
                self.report.warnings.extend(validation_report.validation_warnings)
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Validation",
                    success=False,
                    duration_seconds=duration,
                    message="Validation failed",
                    details={'errors': validation_report.validation_errors}
                ))
                
                # Offer rollback
                if self.report.backup_path:
                    logger.error("")
                    logger.error("Validation failed. Consider rolling back the migration:")
                    logger.error(f"  python run_migration.py --rollback {self.report.backup_path}")
                
                return False
                
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            logger.error(f"✗ Validation phase failed: {str(e)}", exc_info=True)
            self.report.errors.append(f"Validation error: {str(e)}")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Validation",
                success=False,
                duration_seconds=duration,
                message=f"Error: {str(e)}"
            ))
            return False
    
    def _execute_phase_cleanup(self) -> bool:
        """
        Execute Phase 5: Cleanup old tables.
        
        Requirements: 22.1
        
        Returns:
            True if phase succeeded, False otherwise
        """
        phase_start = datetime.now()
        logger.info("")
        logger.info("=" * 80)
        logger.info("PHASE 5: CLEANUP OLD TABLES")
        logger.info("=" * 80)
        
        try:
            cleanup_result = self.table_cleanup.cleanup_old_tables(dry_run=False)
            
            duration = (datetime.now() - phase_start).total_seconds()
            
            if cleanup_result.success:
                logger.info(f"✓ Cleanup completed successfully in {duration:.2f}s")
                logger.info(f"  Tables identified: {cleanup_result.tables_identified}")
                logger.info(f"  Tables backed up: {cleanup_result.tables_backed_up}")
                logger.info(f"  Tables dropped: {cleanup_result.tables_dropped}")
                
                if cleanup_result.dropped_tables:
                    logger.info(f"  Dropped tables: {', '.join(cleanup_result.dropped_tables)}")
                
                self.report.tables_cleaned = cleanup_result.tables_dropped
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Cleanup",
                    success=True,
                    duration_seconds=duration,
                    message=f"Cleaned up {cleanup_result.tables_dropped} tables",
                    details={
                        'tables_identified': cleanup_result.tables_identified,
                        'tables_dropped': cleanup_result.tables_dropped,
                        'backup_path': cleanup_result.backup_path
                    }
                ))
                
                # Add any cleanup warnings
                if cleanup_result.warnings:
                    self.report.warnings.extend(cleanup_result.warnings)
                
                return True
            else:
                logger.warning(f"⚠ Cleanup completed with errors")
                for error in cleanup_result.errors:
                    logger.warning(f"  - {error}")
                
                self.report.warnings.extend(cleanup_result.errors)
                self.report.phases.append(MigrationPhaseResult(
                    phase_name="Cleanup",
                    success=False,
                    duration_seconds=duration,
                    message="Cleanup completed with errors",
                    details={'errors': cleanup_result.errors}
                ))
                
                # Cleanup errors are not critical
                return True
                
        except Exception as e:
            duration = (datetime.now() - phase_start).total_seconds()
            logger.warning(f"⚠ Cleanup phase failed: {str(e)}")
            self.report.warnings.append(f"Cleanup error: {str(e)}")
            self.report.phases.append(MigrationPhaseResult(
                phase_name="Cleanup",
                success=False,
                duration_seconds=duration,
                message=f"Error: {str(e)}"
            ))
            # Cleanup errors are not critical
            return True
    
    def _finalize_report(self, success: bool) -> CompleteMigrationReport:
        """
        Finalize the migration report.
        
        Args:
            success: Whether the migration succeeded
        
        Returns:
            Complete migration report
        """
        self.report.success = success
        self.report.completed_at = datetime.now()
        self.report.total_duration_seconds = (
            self.report.completed_at - self.report.started_at
        ).total_seconds()
        
        # Print final report
        self._print_final_report()
        
        return self.report
    
    def _print_final_report(self):
        """Print the final migration report to console."""
        logger.info("")
        logger.info("=" * 80)
        logger.info("MIGRATION REPORT")
        logger.info("=" * 80)
        logger.info(f"Status: {'✓ SUCCESS' if self.report.success else '✗ FAILED'}")
        logger.info(f"Started: {self.report.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Completed: {self.report.completed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {self.report.total_duration_seconds:.2f}s")
        logger.info("")
        
        # Phase summary
        logger.info("Phase Summary:")
        for phase in self.report.phases:
            status = "✓" if phase.success else "✗"
            logger.info(f"  {status} {phase.phase_name}: {phase.message} ({phase.duration_seconds:.2f}s)")
        logger.info("")
        
        # Statistics
        logger.info("Statistics:")
        if self.report.backup_path:
            logger.info(f"  Backup location: {self.report.backup_path}")
        logger.info(f"  Tables created: {self.report.tables_created}")
        logger.info(f"  Records migrated: {self.report.rows_migrated}")
        logger.info(f"  Tables cleaned: {self.report.tables_cleaned}")
        logger.info(f"  Validation: {'✓ PASSED' if self.report.validation_passed else '✗ FAILED'}")
        logger.info("")
        
        # Warnings
        if self.report.warnings:
            logger.info(f"Warnings ({len(self.report.warnings)}):")
            for warning in self.report.warnings:
                logger.warning(f"  ⚠ {warning}")
            logger.info("")
        
        # Errors
        if self.report.errors:
            logger.info(f"Errors ({len(self.report.errors)}):")
            for error in self.report.errors:
                logger.error(f"  ✗ {error}")
            logger.info("")
        
        logger.info("=" * 80)
        
        if self.report.success:
            logger.info("✓ Migration completed successfully!")
        else:
            logger.error("✗ Migration failed. Check errors above.")
            if self.report.backup_path:
                logger.error(f"To rollback: python run_migration.py --rollback {self.report.backup_path}")
        
        logger.info("=" * 80)
    
    def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback migration and restore from backup.
        
        Requirements: 18.5
        
        Args:
            backup_path: Path to backup directory
        
        Returns:
            True if rollback succeeded, False otherwise
        """
        logger.info("=" * 80)
        logger.info("ROLLING BACK MIGRATION")
        logger.info("=" * 80)
        logger.info(f"Backup path: {backup_path}")
        logger.info("")
        
        try:
            # Use schema manager's rollback method
            rollback_result = self.schema_manager.rollback(backup_path)
            
            if rollback_result.success:
                logger.info("✓ Rollback completed successfully")
                logger.info("Database restored to pre-migration state")
                return True
            else:
                logger.error(f"✗ Rollback failed: {rollback_result.error}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Rollback failed: {str(e)}", exc_info=True)
            return False


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description='Database Architecture Migration Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full migration
  python run_migration.py

  # Dry run (validation only)
  python run_migration.py --dry-run

  # Skip validation (not recommended)
  python run_migration.py --skip-validation

  # Custom backup path
  python run_migration.py --backup-path /path/to/backups

  # Rollback migration
  python run_migration.py --rollback /tmp/backups/pre_migration_20240315_120000

  # Verbose logging
  python run_migration.py --verbose
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run validation without making changes'
    )
    
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip validation checks (not recommended)'
    )
    
    parser.add_argument(
        '--rollback',
        type=str,
        metavar='PATH',
        help='Rollback migration and restore from backup'
    )
    
    parser.add_argument(
        '--backup-path',
        type=str,
        default='/tmp/backups',
        help='Custom path for backup files (default: /tmp/backups)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--supabase-url',
        type=str,
        help='Supabase URL (or set SUPABASE_URL env var)'
    )
    
    parser.add_argument(
        '--supabase-key',
        type=str,
        help='Supabase API key (or set SUPABASE_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = MigrationConfig(
        dry_run=args.dry_run,
        skip_validation=args.skip_validation,
        rollback_path=args.rollback,
        backup_path=args.backup_path,
        verbose=args.verbose,
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key
    )
    
    # Create orchestrator
    try:
        orchestrator = MigrationOrchestrator(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Execute rollback or migration
    if args.rollback:
        success = orchestrator.rollback_migration(args.rollback)
        sys.exit(0 if success else 1)
    else:
        report = orchestrator.run_migration()
        sys.exit(0 if report.success else 1)


if __name__ == '__main__':
    main()
