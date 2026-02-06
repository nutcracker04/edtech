"""
Configuration for Concept Knowledge Graph system.

This module provides configuration for:
- Neo4j graph database connection
- Claude API integration
"""

from pydantic_settings import BaseSettings
from typing import Optional


class ConceptGraphSettings(BaseSettings):
    """Settings for Concept Knowledge Graph system."""
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    
    # NVIDIA AI API Configuration
    nvidia_api_key: str = ""
    nvidia_model: str = ""
    nvidia_max_tokens: int = 16384
    nvidia_temperature: float = 1.0
    nvidia_top_p: float = 1.0
    
    # Question Generation Configuration
    max_regeneration_attempts: int = 3
    
    # Mastery Tracking Configuration
    mastery_threshold: float = 0.8
    mastery_history_limit: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = "CONCEPT_GRAPH_"
        extra = "ignore"  # Ignore extra fields from .env


concept_graph_settings = ConceptGraphSettings()
