-- Migration: 003_migration_helpers.sql
-- Description: Helper functions for schema migration manager
-- Author: Database Architecture Migration
-- Date: 2024

-- ============================================================================
-- HELPER FUNCTIONS FOR MIGRATION MANAGER
-- ============================================================================

-- Function: exec_sql
-- Executes arbitrary SQL statements (admin only)
-- Used by SchemaMigrationManager for schema creation and rollback
CREATE OR REPLACE FUNCTION exec_sql(sql TEXT)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql;
    RETURN 'SQL executed successfully';
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$;

-- Function: get_tables
-- Returns list of all tables in the public schema
-- Used by SchemaMigrationManager for validation
CREATE OR REPLACE FUNCTION get_tables()
RETURNS TABLE(table_name TEXT)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    SELECT tablename::TEXT
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename;
END;
$$;

-- Function: check_foreign_keys
-- Validates all foreign key constraints in the database
-- Returns list of invalid foreign keys (empty if all valid)
CREATE OR REPLACE FUNCTION check_foreign_keys()
RETURNS TABLE(
    constraint_name TEXT,
    table_name TEXT,
    error_message TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    fk_record RECORD;
    check_sql TEXT;
    invalid_count INTEGER;
BEGIN
    -- Loop through all foreign key constraints
    FOR fk_record IN
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
    LOOP
        -- Check if there are any orphaned foreign key references
        check_sql := format(
            'SELECT COUNT(*) FROM %I t1 
             LEFT JOIN %I t2 ON t1.%I = t2.%I 
             WHERE t1.%I IS NOT NULL AND t2.%I IS NULL',
            fk_record.table_name,
            fk_record.foreign_table_name,
            fk_record.column_name,
            fk_record.foreign_column_name,
            fk_record.column_name,
            fk_record.foreign_column_name
        );
        
        EXECUTE check_sql INTO invalid_count;
        
        IF invalid_count > 0 THEN
            constraint_name := fk_record.constraint_name;
            table_name := fk_record.table_name;
            error_message := format(
                'Found %s orphaned references in %s.%s',
                invalid_count,
                fk_record.table_name,
                fk_record.column_name
            );
            RETURN NEXT;
        END IF;
    END LOOP;
    
    RETURN;
END;
$$;

-- Function: get_table_row_counts
-- Returns row counts for all tables
-- Used for migration validation
CREATE OR REPLACE FUNCTION get_table_row_counts()
RETURNS TABLE(
    table_name TEXT,
    row_count BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    tbl RECORD;
    count_sql TEXT;
    cnt BIGINT;
BEGIN
    FOR tbl IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    LOOP
        count_sql := format('SELECT COUNT(*) FROM %I', tbl.tablename);
        EXECUTE count_sql INTO cnt;
        
        table_name := tbl.tablename;
        row_count := cnt;
        RETURN NEXT;
    END LOOP;
    
    RETURN;
END;
$$;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION exec_sql(TEXT) IS 'Executes arbitrary SQL statements for migration operations';
COMMENT ON FUNCTION get_tables() IS 'Returns list of all tables in the public schema';
COMMENT ON FUNCTION check_foreign_keys() IS 'Validates all foreign key constraints and returns any violations';
COMMENT ON FUNCTION get_table_row_counts() IS 'Returns row counts for all tables for validation purposes';

-- ============================================================================
-- END OF MIGRATION HELPERS
-- ============================================================================
