#!/usr/bin/env python3
"""
Execute Database Migration

This script runs the complete database migration process:
1. Backup existing data
2. Create new schema (if not exists)
3. Migrate data
4. Validate migration
5. Clean up old tables

Usage:
    # Dry run first (recommended)
    python execute_migration.py --dry-run
    
    # Run actual migration
    python execute_migration.py
    
    # With verbose logging
    python execute_migration.py --verbose
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from app.database import get_supabase
from app.services.migration.run_migration import MigrationOrchestrator, MigrationConfig


def main():
    parser = argparse.ArgumentParser(description='Execute database migration')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run validation without making changes')
    parser.add_argument('--skip-validation', action='store_true',
                        help='Skip validation checks (not recommended)')
    parser.add_argument('--backup-path', type=str,
                        help='Custom path for backup files')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("DATABASE MIGRATION EXECUTION")
    print("=" * 80)
    print()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    try:
        # Create migration config
        config = MigrationConfig(
            dry_run=args.dry_run,
            skip_validation=args.skip_validation,
            backup_path=args.backup_path or "/tmp/backups",
            verbose=args.verbose
        )
        
        # Create orchestrator
        orchestrator = MigrationOrchestrator(config)
        
        # Run migration
        print("🚀 Starting migration process...")
        print()
        report = orchestrator.run_migration()
        
        # Print report
        print()
        print("=" * 80)
        print("MIGRATION REPORT")
        print("=" * 80)
        print()
        print(f"Status: {'✅ SUCCESS' if report.success else '❌ FAILED'}")
        print(f"Duration: {report.total_duration_seconds:.2f} seconds")
        print()
        
        print("Phase Results:")
        for phase in report.phases:
            status = "✅" if phase.success else "❌"
            print(f"  {status} {phase.phase_name}: {phase.duration_seconds:.2f}s")
            if hasattr(phase, 'error') and phase.error:
                print(f"     Error: {phase.error}")
        print()
        
        if report.statistics:
            print("Statistics:")
            stats = {
                'Backup location': report.backup_path,
                'Tables created': report.tables_created,
                'Records migrated': report.rows_migrated,
                'Tables cleaned': report.tables_cleaned,
                'Validation': '✅ PASSED' if report.validation_passed else '❌ FAILED'
            }
            for key, value in stats.items():
                if value is not None:
                    print(f"  - {key}: {value}")
            print()
        
        if report.warnings:
            print("⚠️  Warnings:")
            for warning in report.warnings:
                print(f"  - {warning}")
            print()
        
        if report.errors:
            print("❌ Errors:")
            for error in report.errors:
                print(f"  - {error}")
            print()
        
        if report.success:
            if args.dry_run:
                print("✅ Dry run completed successfully!")
                print("   Run without --dry-run to execute the migration.")
            else:
                print("✅ Migration completed successfully!")
                print("   Your database is now using the new architecture.")
        else:
            print("❌ Migration failed. Check the errors above.")
            sys.exit(1)
        
    except Exception as e:
        print(f"❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
