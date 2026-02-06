"""
Database connection management for Neo4j.

This module provides connection managers and initialization for:
- Neo4j graph database
"""

from neo4j import GraphDatabase, Driver
from typing import Optional
from .config import concept_graph_settings
import logging

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j database connection manager."""
    
    _driver: Optional[Driver] = None
    
    @classmethod
    def get_driver(cls) -> Driver:
        """Get or create Neo4j driver instance."""
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                concept_graph_settings.neo4j_uri,
                auth=(
                    concept_graph_settings.neo4j_user,
                    concept_graph_settings.neo4j_password
                )
            )
            logger.info("Neo4j driver initialized")
        return cls._driver
    
    @classmethod
    def close(cls):
        """Close Neo4j driver connection."""
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None
            logger.info("Neo4j driver closed")
    
    @classmethod
    def verify_connectivity(cls) -> bool:
        """Verify Neo4j connection is working."""
        try:
            driver = cls.get_driver()
            driver.verify_connectivity()
            logger.info("Neo4j connectivity verified")
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False
    
    @classmethod
    def initialize_schema(cls):
        """Initialize Neo4j schema with indexes and constraints."""
        driver = cls.get_driver()
        
        with driver.session(database=concept_graph_settings.neo4j_database) as session:
            # Create uniqueness constraint on concept ID
            try:
                session.run(
                    "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS "
                    "FOR (c:Concept) REQUIRE c.id IS UNIQUE"
                )
                logger.info("Created uniqueness constraint on Concept.id")
            except Exception as e:
                logger.warning(f"Constraint creation skipped: {e}")
            
            # Create indexes for efficient querying
            indexes = [
                "CREATE INDEX concept_subject IF NOT EXISTS FOR (c:Concept) ON (c.subject)",
                "CREATE INDEX concept_class_level IF NOT EXISTS FOR (c:Concept) ON (c.class_level)",
                "CREATE INDEX concept_bloom_level IF NOT EXISTS FOR (c:Concept) ON (c.bloom_level)",
                "CREATE INDEX concept_abstraction_level IF NOT EXISTS FOR (c:Concept) ON (c.abstraction_level)",
                "CREATE INDEX concept_computational_complexity IF NOT EXISTS FOR (c:Concept) ON (c.computational_complexity)",
                "CREATE INDEX concept_real_world_context IF NOT EXISTS FOR (c:Concept) ON (c.real_world_context)",
                "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
            ]
            
            for index_query in indexes:
                try:
                    session.run(index_query)
                    logger.info(f"Created index: {index_query}")
                except Exception as e:
                    logger.warning(f"Index creation skipped: {e}")


def initialize_databases():
    """Initialize Neo4j connection and schema."""
    logger.info("Initializing database...")
    
    # Verify Neo4j connectivity
    if not Neo4jConnection.verify_connectivity():
        logger.error("Failed to connect to Neo4j")
        raise ConnectionError("Neo4j connection failed")
    
    # Initialize Neo4j schema
    Neo4jConnection.initialize_schema()
    
    logger.info("Database initialized successfully")


def close_databases():
    """Close all database connections."""
    logger.info("Closing database connections...")
    Neo4jConnection.close()
    logger.info("Database connections closed")
