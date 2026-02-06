"""
Concept Graph Manager for CRUD operations on concepts and relationships.

This module provides the ConceptGraphManager class which handles:
- Creating and retrieving concepts from Neo4j
- Querying concepts by filters (class level, keywords, difficulty)
- Creating relationships between concepts
"""

from typing import Optional, List
from datetime import datetime
import json
import logging
from neo4j import Session

from .models import (
    Concept,
    ConceptCreate,
    ConceptFilters,
    Relationship,
    RelationshipCreate,
    RelationshipType,
    DifficultyDNA,
)
from .database import Neo4jConnection
from .config import concept_graph_settings

logger = logging.getLogger(__name__)


class ConceptGraphManager:
    """
    Manager for concept graph operations with Neo4j.
    
    Handles CRUD operations for concepts and relationships.
    """
    
    def __init__(self):
        """Initialize the ConceptGraphManager."""
        self.driver = Neo4jConnection.get_driver()
    
    def create_concept(self, concept_create: ConceptCreate) -> Concept:
        """
        Create a new concept node in the graph database.
        
        Args:
            concept_create: ConceptCreate model with concept data
            
        Returns:
            Created Concept with generated ID and timestamps
            
        Raises:
            ValueError: If validation fails
            Exception: If database operation fails
        """
        # Create Concept with generated ID and timestamps
        concept = Concept(
            name=concept_create.name,
            subject=concept_create.subject,
            class_level=concept_create.class_level,
            keywords=concept_create.keywords,
            description=concept_create.description,
            difficulty_dna=concept_create.difficulty_dna,
        )
        
        # Store in Neo4j
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            result = session.execute_write(self._create_concept_tx, concept)
        
        logger.info(f"Created concept: {concept.id} - {concept.name}")
        return result
    
    @staticmethod
    def _create_concept_tx(tx, concept: Concept) -> Concept:
        """Transaction function to create a concept node."""
        query = """
        CREATE (c:Concept {
            id: $id,
            name: $name,
            subject: $subject,
            class_level: $class_level,
            keywords: $keywords,
            description: $description,
            bloom_level: $bloom_level,
            abstraction_level: $abstraction_level,
            computational_complexity: $computational_complexity,
            concept_integration: $concept_integration,
            real_world_context: $real_world_context,
            problem_solving_approach: $problem_solving_approach,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at)
        })
        RETURN c
        """
        
        result = tx.run(
            query,
            id=concept.id,
            name=concept.name,
            subject=concept.subject.value,
            class_level=concept.class_level,
            keywords=concept.keywords,
            description=concept.description,
            bloom_level=concept.difficulty_dna.bloom_level,
            abstraction_level=concept.difficulty_dna.abstraction_level,
            computational_complexity=concept.difficulty_dna.computational_complexity,
            concept_integration=concept.difficulty_dna.concept_integration.value,
            real_world_context=concept.difficulty_dna.real_world_context,
            problem_solving_approach=concept.difficulty_dna.problem_solving_approach.value,
            created_at=concept.created_at.isoformat(),
            updated_at=concept.updated_at.isoformat(),
        )
        
        record = result.single()
        if record is None:
            raise Exception("Failed to create concept")
        
        return concept
    
    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """
        Retrieve a concept by its unique identifier.
        
        Queries Neo4j for the concept.
        
        Args:
            concept_id: Unique concept identifier
            
        Returns:
            Concept if found, None otherwise
        """
        # Query Neo4j
        logger.debug(f"Querying Neo4j for concept: {concept_id}")
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            concept = session.execute_read(self._get_concept_tx, concept_id)
        
        return concept
    
    @staticmethod
    def _get_concept_tx(tx, concept_id: str) -> Optional[Concept]:
        """Transaction function to retrieve a concept by ID."""
        query = """
        MATCH (c:Concept {id: $id})
        RETURN c
        """
        
        result = tx.run(query, id=concept_id)
        record = result.single()
        
        if record is None:
            return None
        
        node = record["c"]
        
        # Reconstruct Concept from Neo4j node
        difficulty_dna = DifficultyDNA.from_dict({
            "bloom_level": node["bloom_level"],
            "abstraction_level": node["abstraction_level"],
            "computational_complexity": node["computational_complexity"],
            "concept_integration": node["concept_integration"],
            "real_world_context": node["real_world_context"],
            "problem_solving_approach": node["problem_solving_approach"],
        })
        
        concept = Concept(
            id=node["id"],
            name=node["name"],
            subject=node["subject"],
            class_level=node["class_level"],
            keywords=node["keywords"],
            description=node["description"],
            difficulty_dna=difficulty_dna,
            created_at=node["created_at"].to_native(),
            updated_at=node["updated_at"].to_native(),
        )
        
        return concept
    
    def query_concepts(self, filters: ConceptFilters) -> List[Concept]:
        """
        Query concepts by filters (class level, keywords, difficulty dimensions).
        
        Args:
            filters: ConceptFilters with optional filter criteria
            
        Returns:
            List of matching concepts
        """
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            concepts = session.execute_read(self._query_concepts_tx, filters)
        
        logger.info(f"Query returned {len(concepts)} concepts")
        return concepts
    
    @staticmethod
    def _query_concepts_tx(tx, filters: ConceptFilters) -> List[Concept]:
        """Transaction function to query concepts with filters."""
        # Build dynamic query based on filters
        where_clauses = []
        params = {}
        
        if filters.subject is not None:
            where_clauses.append("c.subject = $subject")
            params["subject"] = filters.subject.value
        
        if filters.class_level is not None:
            where_clauses.append("c.class_level = $class_level")
            params["class_level"] = filters.class_level
        
        if filters.keyword is not None:
            # Fuzzy keyword matching - check if keyword is in the keywords list
            where_clauses.append("ANY(k IN c.keywords WHERE k CONTAINS $keyword)")
            params["keyword"] = filters.keyword
        
        if filters.min_bloom_level is not None:
            where_clauses.append("c.bloom_level >= $min_bloom_level")
            params["min_bloom_level"] = filters.min_bloom_level
        
        if filters.max_bloom_level is not None:
            where_clauses.append("c.bloom_level <= $max_bloom_level")
            params["max_bloom_level"] = filters.max_bloom_level
        
        if filters.min_abstraction_level is not None:
            where_clauses.append("c.abstraction_level >= $min_abstraction_level")
            params["min_abstraction_level"] = filters.min_abstraction_level
        
        if filters.max_abstraction_level is not None:
            where_clauses.append("c.abstraction_level <= $max_abstraction_level")
            params["max_abstraction_level"] = filters.max_abstraction_level
        
        if filters.min_computational_complexity is not None:
            where_clauses.append("c.computational_complexity >= $min_computational_complexity")
            params["min_computational_complexity"] = filters.min_computational_complexity
        
        if filters.max_computational_complexity is not None:
            where_clauses.append("c.computational_complexity <= $max_computational_complexity")
            params["max_computational_complexity"] = filters.max_computational_complexity
        
        if filters.min_real_world_context is not None:
            where_clauses.append("c.real_world_context >= $min_real_world_context")
            params["min_real_world_context"] = filters.min_real_world_context
        
        if filters.max_real_world_context is not None:
            where_clauses.append("c.real_world_context <= $max_real_world_context")
            params["max_real_world_context"] = filters.max_real_world_context
        
        if filters.concept_integration is not None:
            where_clauses.append("c.concept_integration = $concept_integration")
            params["concept_integration"] = filters.concept_integration.value
        
        if filters.problem_solving_approach is not None:
            where_clauses.append("c.problem_solving_approach = $problem_solving_approach")
            params["problem_solving_approach"] = filters.problem_solving_approach.value
        
        # Build query
        query = "MATCH (c:Concept)"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " RETURN c"
        
        result = tx.run(query, **params)
        
        concepts = []
        for record in result:
            node = record["c"]
            
            difficulty_dna = DifficultyDNA.from_dict({
                "bloom_level": node["bloom_level"],
                "abstraction_level": node["abstraction_level"],
                "computational_complexity": node["computational_complexity"],
                "concept_integration": node["concept_integration"],
                "real_world_context": node["real_world_context"],
                "problem_solving_approach": node["problem_solving_approach"],
            })
            
            concept = Concept(
                id=node["id"],
                name=node["name"],
                subject=node["subject"],
                class_level=node["class_level"],
                keywords=node["keywords"],
                description=node["description"],
                difficulty_dna=difficulty_dna,
                created_at=node["created_at"].to_native(),
                updated_at=node["updated_at"].to_native(),
            )
            concepts.append(concept)
        
        return concepts
    
    def detect_cycle(self, source_id: str, target_id: str) -> bool:
        """
        Detect if adding an edge from source to target would create a cycle.
        
        Uses depth-first search to check if there's already a path from
        target to source. If such a path exists, adding source->target
        would create a cycle.
        
        Args:
            source_id: Source concept ID for proposed edge
            target_id: Target concept ID for proposed edge
            
        Returns:
            True if adding the edge would create a cycle, False otherwise
        """
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            return session.execute_read(self._detect_cycle_tx, source_id, target_id)
    
    @staticmethod
    def _detect_cycle_tx(tx, source_id: str, target_id: str) -> bool:
        """
        Transaction function to detect cycles using DFS.
        
        Checks if there's a path from target to source. If yes, adding
        source->target would create a cycle.
        """
        # Use Neo4j's path matching to check if a path exists from target to source
        # We check all relationship types that form prerequisite chains
        query = """
        MATCH (target:Concept {id: $target_id})
        MATCH (source:Concept {id: $source_id})
        MATCH path = (target)-[:PREREQUISITE|BUILDS_UPON*]->(source)
        RETURN count(path) > 0 AS cycle_exists
        """
        
        result = tx.run(query, source_id=source_id, target_id=target_id)
        record = result.single()
        
        if record is None:
            return False
        
        return record["cycle_exists"]
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType
    ) -> Relationship:
        """
        Create a relationship between two concepts.
        
        Args:
            source_id: Source concept ID
            target_id: Target concept ID
            rel_type: Type of relationship
            
        Returns:
            Created Relationship
            
        Raises:
            ValueError: If concepts don't exist or relationship would create cycle
        """
        # Verify both concepts exist
        source = self.get_concept(source_id)
        if source is None:
            raise ValueError(f"Source concept not found: {source_id}")
        
        target = self.get_concept(target_id)
        if target is None:
            raise ValueError(f"Target concept not found: {target_id}")
        
        # Check for cycles before creating the relationship
        if self.detect_cycle(source_id, target_id):
            raise ValueError(
                f"Cannot create relationship: would create a cycle. "
                f"A path already exists from {target_id} to {source_id}"
            )
        
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
        )
        
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            session.execute_write(self._create_relationship_tx, relationship)
        
        logger.info(
            f"Created {rel_type.value} relationship: {source_id} -> {target_id}"
        )
        
        # Invalidate prerequisite cache
        self._invalidate_prerequisite_cache(source_id)
        self._invalidate_prerequisite_cache(target_id)
        
        return relationship
    
    @staticmethod
    def _create_relationship_tx(tx, relationship: Relationship):
        """Transaction function to create a relationship."""
        # Map relationship type to Neo4j relationship type
        rel_type_map = {
            RelationshipType.PREREQUISITE: "PREREQUISITE",
            RelationshipType.BUILDS_UPON: "BUILDS_UPON",
            RelationshipType.APPLIES_TO: "APPLIES_TO",
        }
        
        neo4j_rel_type = rel_type_map[relationship.relationship_type]
        
        query = f"""
        MATCH (source:Concept {{id: $source_id}})
        MATCH (target:Concept {{id: $target_id}})
        CREATE (source)-[r:{neo4j_rel_type} {{
            created_at: datetime($created_at)
        }}]->(target)
        RETURN r
        """
        
        result = tx.run(
            query,
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            created_at=relationship.created_at.isoformat(),
        )
        
        record = result.single()
        if record is None:
            raise Exception("Failed to create relationship")
    
    def get_prerequisites(
        self,
        concept_id: str,
        recursive: bool = True,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Concept]:
        """
        Get all prerequisite concepts for a given concept.
        
        By default, includes both PREREQUISITE and BUILDS_UPON relationships.
        Can be filtered to specific relationship types.
        
        Args:
            concept_id: Concept ID to get prerequisites for
            recursive: If True, get all transitive prerequisites
            relationship_types: Optional list of relationship types to filter by.
                              Defaults to [PREREQUISITE, BUILDS_UPON] if not specified.
            
        Returns:
            List of prerequisite concepts
        """
        # Default to PREREQUISITE and BUILDS_UPON if not specified
        if relationship_types is None:
            relationship_types = [RelationshipType.PREREQUISITE, RelationshipType.BUILDS_UPON]
        
        # Query Neo4j
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            prerequisites = session.execute_read(
                self._get_prerequisites_tx,
                concept_id,
                recursive,
                relationship_types
            )
        
        return prerequisites
    
    @staticmethod
    def _get_prerequisites_tx(
        tx,
        concept_id: str,
        recursive: bool,
        relationship_types: List[RelationshipType]
    ) -> List[Concept]:
        """Transaction function to get prerequisites with relationship type filtering."""
        # Map relationship types to Neo4j relationship names
        rel_type_map = {
            RelationshipType.PREREQUISITE: "PREREQUISITE",
            RelationshipType.BUILDS_UPON: "BUILDS_UPON",
            RelationshipType.APPLIES_TO: "APPLIES_TO",
        }
        
        # Build relationship type filter for Cypher query
        neo4j_rel_types = [rel_type_map[rt] for rt in relationship_types]
        rel_types_str = "|".join(neo4j_rel_types)
        
        if recursive:
            # Get all transitive prerequisites with filtered relationship types
            query = f"""
            MATCH (c:Concept {{id: $concept_id}})
            MATCH (prereq:Concept)-[:{rel_types_str}*]->(c)
            RETURN DISTINCT prereq
            """
        else:
            # Get only direct prerequisites with filtered relationship types
            query = f"""
            MATCH (c:Concept {{id: $concept_id}})
            MATCH (prereq:Concept)-[:{rel_types_str}]->(c)
            RETURN prereq
            """
        
        result = tx.run(query, concept_id=concept_id)
        
        prerequisites = []
        for record in result:
            node = record["prereq"]
            
            difficulty_dna = DifficultyDNA.from_dict({
                "bloom_level": node["bloom_level"],
                "abstraction_level": node["abstraction_level"],
                "computational_complexity": node["computational_complexity"],
                "concept_integration": node["concept_integration"],
                "real_world_context": node["real_world_context"],
                "problem_solving_approach": node["problem_solving_approach"],
            })
            
            concept = Concept(
                id=node["id"],
                name=node["name"],
                subject=node["subject"],
                class_level=node["class_level"],
                keywords=node["keywords"],
                description=node["description"],
                difficulty_dna=difficulty_dna,
                created_at=node["created_at"].to_native(),
                updated_at=node["updated_at"].to_native(),
            )
            prerequisites.append(concept)
        
        return prerequisites
    
    def get_dependents(
        self,
        concept_id: str,
        relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Concept]:
        """
        Get all concepts that depend on this concept (reverse prerequisites).
        
        By default, includes both PREREQUISITE and BUILDS_UPON relationships.
        Can be filtered to specific relationship types.
        
        Args:
            concept_id: Concept ID to get dependents for
            relationship_types: Optional list of relationship types to filter by.
                              Defaults to [PREREQUISITE, BUILDS_UPON] if not specified.
            
        Returns:
            List of dependent concepts
        """
        # Default to PREREQUISITE and BUILDS_UPON if not specified
        if relationship_types is None:
            relationship_types = [RelationshipType.PREREQUISITE, RelationshipType.BUILDS_UPON]
        
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            dependents = session.execute_read(
                self._get_dependents_tx,
                concept_id,
                relationship_types
            )
        
        return dependents
    
    @staticmethod
    def _get_dependents_tx(
        tx,
        concept_id: str,
        relationship_types: List[RelationshipType]
    ) -> List[Concept]:
        """Transaction function to get dependent concepts with relationship type filtering."""
        # Map relationship types to Neo4j relationship names
        rel_type_map = {
            RelationshipType.PREREQUISITE: "PREREQUISITE",
            RelationshipType.BUILDS_UPON: "BUILDS_UPON",
            RelationshipType.APPLIES_TO: "APPLIES_TO",
        }
        
        # Build relationship type filter for Cypher query
        neo4j_rel_types = [rel_type_map[rt] for rt in relationship_types]
        rel_types_str = "|".join(neo4j_rel_types)
        
        query = f"""
        MATCH (c:Concept {{id: $concept_id}})
        MATCH (c)-[:{rel_types_str}]->(dependent:Concept)
        RETURN DISTINCT dependent
        """
        
        result = tx.run(query, concept_id=concept_id)
        
        dependents = []
        for record in result:
            node = record["dependent"]
            
            difficulty_dna = DifficultyDNA.from_dict({
                "bloom_level": node["bloom_level"],
                "abstraction_level": node["abstraction_level"],
                "computational_complexity": node["computational_complexity"],
                "concept_integration": node["concept_integration"],
                "real_world_context": node["real_world_context"],
                "problem_solving_approach": node["problem_solving_approach"],
            })
            
            concept = Concept(
                id=node["id"],
                name=node["name"],
                subject=node["subject"],
                class_level=node["class_level"],
                keywords=node["keywords"],
                description=node["description"],
                difficulty_dna=difficulty_dna,
                created_at=node["created_at"].to_native(),
                updated_at=node["updated_at"].to_native(),
            )
            dependents.append(concept)
        
        return dependents
    
    def export_graph(self) -> dict:
        """
        Export entire graph to JSON format.
        
        Exports all concepts and relationships in the graph to a JSON-serializable
        dictionary format suitable for backup, versioning, or transfer.
        
        Returns:
            Dictionary containing:
                - concepts: List of all concept dictionaries
                - relationships: List of all relationship dictionaries
                - metadata: Export metadata (timestamp, version, concept count)
                
        Raises:
            Exception: If database operation fails
        """
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            concepts = session.execute_read(self._export_concepts_tx)
            relationships = session.execute_read(self._export_relationships_tx)
        
        export_data = {
            "concepts": [c.to_dict() for c in concepts],
            "relationships": [r.to_dict() for r in relationships],
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "concept_count": len(concepts),
                "relationship_count": len(relationships),
            }
        }
        
        logger.info(
            f"Exported graph: {len(concepts)} concepts, {len(relationships)} relationships"
        )
        
        return export_data
    
    @staticmethod
    def _export_concepts_tx(tx) -> List[Concept]:
        """Transaction function to export all concepts."""
        query = """
        MATCH (c:Concept)
        RETURN c
        ORDER BY c.created_at
        """
        
        result = tx.run(query)
        
        concepts = []
        for record in result:
            node = record["c"]
            
            difficulty_dna = DifficultyDNA.from_dict({
                "bloom_level": node["bloom_level"],
                "abstraction_level": node["abstraction_level"],
                "computational_complexity": node["computational_complexity"],
                "concept_integration": node["concept_integration"],
                "real_world_context": node["real_world_context"],
                "problem_solving_approach": node["problem_solving_approach"],
            })
            
            concept = Concept(
                id=node["id"],
                name=node["name"],
                subject=node["subject"],
                class_level=node["class_level"],
                keywords=node["keywords"],
                description=node["description"],
                difficulty_dna=difficulty_dna,
                created_at=node["created_at"].to_native(),
                updated_at=node["updated_at"].to_native(),
            )
            concepts.append(concept)
        
        return concepts
    
    @staticmethod
    def _export_relationships_tx(tx) -> List[Relationship]:
        """Transaction function to export all relationships."""
        query = """
        MATCH (source:Concept)-[r]->(target:Concept)
        WHERE type(r) IN ['PREREQUISITE', 'BUILDS_UPON', 'APPLIES_TO']
        RETURN source.id AS source_id, target.id AS target_id, 
               type(r) AS rel_type, r.created_at AS created_at
        ORDER BY r.created_at
        """
        
        result = tx.run(query)
        
        relationships = []
        for record in result:
            # Map Neo4j relationship type to RelationshipType enum
            rel_type_map = {
                "PREREQUISITE": RelationshipType.PREREQUISITE,
                "BUILDS_UPON": RelationshipType.BUILDS_UPON,
                "APPLIES_TO": RelationshipType.APPLIES_TO,
            }
            
            relationship = Relationship(
                source_id=record["source_id"],
                target_id=record["target_id"],
                relationship_type=rel_type_map[record["rel_type"]],
                created_at=record["created_at"].to_native(),
            )
            relationships.append(relationship)
        
        return relationships
    
    def import_graph(self, graph_data: dict) -> dict:
        """
        Import graph from JSON format with validation.
        
        Validates the imported data structure, checks for cycles, validates
        all concepts and relationships, and imports them into the database.
        The import is atomic - either all data is imported or none is.
        
        Args:
            graph_data: Dictionary containing:
                - concepts: List of concept dictionaries
                - relationships: List of relationship dictionaries
                - metadata: Optional metadata
                
        Returns:
            Dictionary containing import results:
                - success: Boolean indicating success
                - concepts_imported: Number of concepts imported
                - relationships_imported: Number of relationships imported
                - errors: List of validation errors (if any)
                
        Raises:
            ValueError: If validation fails or data contains cycles/invalid data
            Exception: If database operation fails
        """
        # Validate data structure
        validation_errors = self._validate_import_data(graph_data)
        if validation_errors:
            error_msg = f"Import validation failed: {', '.join(validation_errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Parse concepts and relationships
        try:
            concepts = [
                Concept.from_dict(c_dict) 
                for c_dict in graph_data["concepts"]
            ]
            relationships = [
                Relationship.from_dict(r_dict) 
                for r_dict in graph_data["relationships"]
            ]
        except Exception as e:
            error_msg = f"Failed to parse import data: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate concept IDs exist for all relationships
        concept_ids = {c.id for c in concepts}
        for rel in relationships:
            if rel.source_id not in concept_ids:
                raise ValueError(
                    f"Relationship references non-existent source concept: {rel.source_id}"
                )
            if rel.target_id not in concept_ids:
                raise ValueError(
                    f"Relationship references non-existent target concept: {rel.target_id}"
                )
        
        # Check for cycles in the relationship graph
        cycle_check_result = self._check_import_for_cycles(concepts, relationships)
        if not cycle_check_result["valid"]:
            error_msg = (
                f"Import data contains cycles: {cycle_check_result['cycle_description']}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Import data in a transaction
        with self.driver.session(database=concept_graph_settings.neo4j_database) as session:
            result = session.execute_write(
                self._import_graph_tx,
                concepts,
                relationships
            )
        
        logger.info(
            f"Imported graph: {len(concepts)} concepts, {len(relationships)} relationships"
        )
        
        return {
            "success": True,
            "concepts_imported": len(concepts),
            "relationships_imported": len(relationships),
            "errors": []
        }
    
    def _validate_import_data(self, graph_data: dict) -> List[str]:
        """
        Validate the structure of import data.
        
        Args:
            graph_data: Dictionary to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required top-level keys
        if "concepts" not in graph_data:
            errors.append("Missing 'concepts' key in import data")
        elif not isinstance(graph_data["concepts"], list):
            errors.append("'concepts' must be a list")
        
        if "relationships" not in graph_data:
            errors.append("Missing 'relationships' key in import data")
        elif not isinstance(graph_data["relationships"], list):
            errors.append("'relationships' must be a list")
        
        # If basic structure is invalid, return early
        if errors:
            return errors
        
        # Validate each concept has required fields
        for i, concept_dict in enumerate(graph_data["concepts"]):
            if not isinstance(concept_dict, dict):
                errors.append(f"Concept at index {i} is not a dictionary")
                continue
            
            required_fields = [
                "id", "name", "class_level", "keywords", 
                "description", "difficulty_dna"
            ]
            for field in required_fields:
                if field not in concept_dict:
                    errors.append(f"Concept at index {i} missing required field: {field}")
        
        # Validate each relationship has required fields
        for i, rel_dict in enumerate(graph_data["relationships"]):
            if not isinstance(rel_dict, dict):
                errors.append(f"Relationship at index {i} is not a dictionary")
                continue
            
            required_fields = ["source_id", "target_id", "relationship_type"]
            for field in required_fields:
                if field not in rel_dict:
                    errors.append(
                        f"Relationship at index {i} missing required field: {field}"
                    )
        
        return errors
    
    def _check_import_for_cycles(
        self,
        concepts: List[Concept],
        relationships: List[Relationship]
    ) -> dict:
        """
        Check if the import data contains cycles.
        
        Uses depth-first search to detect cycles in the relationship graph.
        Only checks PREREQUISITE and BUILDS_UPON relationships as these
        form the dependency chain.
        
        Args:
            concepts: List of concepts to import
            relationships: List of relationships to import
            
        Returns:
            Dictionary with:
                - valid: Boolean indicating if graph is acyclic
                - cycle_description: Description of cycle if found
        """
        # Build adjacency list for prerequisite relationships
        graph = {c.id: [] for c in concepts}
        
        for rel in relationships:
            # Only check prerequisite-type relationships for cycles
            if rel.relationship_type in [
                RelationshipType.PREREQUISITE,
                RelationshipType.BUILDS_UPON
            ]:
                graph[rel.source_id].append(rel.target_id)
        
        # DFS-based cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {c.id: WHITE for c in concepts}
        parent = {c.id: None for c in concepts}
        
        def dfs_visit(node_id: str) -> Optional[List[str]]:
            """
            Visit a node in DFS. Returns cycle path if found, None otherwise.
            """
            color[node_id] = GRAY
            
            for neighbor_id in graph[node_id]:
                if color[neighbor_id] == GRAY:
                    # Back edge found - cycle detected
                    # Reconstruct cycle path
                    cycle = [neighbor_id, node_id]
                    current = node_id
                    while parent[current] != neighbor_id and parent[current] is not None:
                        current = parent[current]
                        cycle.insert(1, current)
                    return cycle
                
                if color[neighbor_id] == WHITE:
                    parent[neighbor_id] = node_id
                    cycle = dfs_visit(neighbor_id)
                    if cycle:
                        return cycle
            
            color[node_id] = BLACK
            return None
        
        # Check all components
        for concept in concepts:
            if color[concept.id] == WHITE:
                cycle = dfs_visit(concept.id)
                if cycle:
                    # Find concept names for better error message
                    concept_map = {c.id: c.name for c in concepts}
                    cycle_names = [concept_map.get(cid, cid) for cid in cycle]
                    return {
                        "valid": False,
                        "cycle_description": " -> ".join(cycle_names)
                    }
        
        return {"valid": True, "cycle_description": None}
    
    @staticmethod
    def _import_graph_tx(tx, concepts: List[Concept], relationships: List[Relationship]):
        """
        Transaction function to import concepts and relationships.
        
        This is an atomic operation - either all data is imported or none is.
        """
        # First, create all concepts
        for concept in concepts:
            query = """
            MERGE (c:Concept {id: $id})
            SET c.name = $name,
                c.class_level = $class_level,
                c.keywords = $keywords,
                c.description = $description,
                c.bloom_level = $bloom_level,
                c.abstraction_level = $abstraction_level,
                c.computational_complexity = $computational_complexity,
                c.concept_integration = $concept_integration,
                c.real_world_context = $real_world_context,
                c.problem_solving_approach = $problem_solving_approach,
                c.created_at = datetime($created_at),
                c.updated_at = datetime($updated_at)
            """
            
            tx.run(
                query,
                id=concept.id,
                name=concept.name,
                class_level=concept.class_level,
                keywords=concept.keywords,
                description=concept.description,
                bloom_level=concept.difficulty_dna.bloom_level,
                abstraction_level=concept.difficulty_dna.abstraction_level,
                computational_complexity=concept.difficulty_dna.computational_complexity,
                concept_integration=concept.difficulty_dna.concept_integration.value,
                real_world_context=concept.difficulty_dna.real_world_context,
                problem_solving_approach=concept.difficulty_dna.problem_solving_approach.value,
                created_at=concept.created_at.isoformat(),
                updated_at=concept.updated_at.isoformat(),
            )
        
        # Then, create all relationships
        rel_type_map = {
            RelationshipType.PREREQUISITE: "PREREQUISITE",
            RelationshipType.BUILDS_UPON: "BUILDS_UPON",
            RelationshipType.APPLIES_TO: "APPLIES_TO",
        }
        
        for rel in relationships:
            neo4j_rel_type = rel_type_map[rel.relationship_type]
            
            # Use MERGE to avoid duplicate relationships
            query = f"""
            MATCH (source:Concept {{id: $source_id}})
            MATCH (target:Concept {{id: $target_id}})
            MERGE (source)-[r:{neo4j_rel_type}]->(target)
            SET r.created_at = datetime($created_at)
            """
            
            tx.run(
                query,
                source_id=rel.source_id,
                target_id=rel.target_id,
                created_at=rel.created_at.isoformat(),
            )
    
