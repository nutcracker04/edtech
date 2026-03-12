"""
Configuration for PDF extraction service.

This module manages configuration settings and API credentials for the extraction pipeline.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import  load_dotenv
load_dotenv()

class PDFExtractionConfig(BaseSettings):
    """Configuration settings for PDF extraction service"""
    
    # Sarvam AI API Configuration
    sarvam_api_key: str = Field(..., description="Sarvam AI API key")
    sarvam_base_url: str = Field(
        default="https://api.sarvam.ai/v1",
        description="Sarvam AI API base URL"
    )
    sarvam_timeout: int = Field(
        default=300,
        description="API request timeout in seconds"
    )
    
    # Document Intelligence API Configuration
    doc_intelligence_model: str = Field(
        default="sarvam-doc-intelligence-v1",
        description="Document Intelligence model name"
    )
    
    # Processing Configuration
    max_pdf_size_mb: int = Field(
        default=100,
        description="Maximum PDF file size in MB"
    )
    max_pages_per_job: int = Field(
        default=10,
        description="Maximum number of PDF pages to send per extraction job"
    )
    structure_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum structure confidence for processing"
    )
    link_confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum link confidence for automatic linking"
    )
    
    # Image Storage Configuration
    image_storage_path: str = Field(
        default="backend/data/extracted_images",
        description="Path for storing extracted images"
    )
    image_compression_quality: int = Field(
        default=85,
        ge=1,
        le=100,
        description="JPEG compression quality (1-100)"
    )
    
    # Performance Configuration
    max_concurrent_pages: int = Field(
        default=5,
        description="Maximum number of pages to process concurrently"
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable caching of structure analysis results"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache time-to-live in seconds"
    )
    
    # LLM Configuration for fuzzy matching
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM calls"
    )
    llm_max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for LLM responses"
    )
    
    # Retry Configuration
    max_retries: int = Field(
        default=3,
        description="Maximum number of API retry attempts"
    )
    retry_delay_seconds: int = Field(
        default=2,
        description="Initial delay between retries in seconds"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "PDF_EXTRACTION_"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


def get_config() -> PDFExtractionConfig:
    """
    Get PDF extraction configuration.
    
    Returns:
        PDFExtractionConfig: Configuration instance
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Check for API key in environment
    api_key = os.getenv("SARVAM_API_KEY") or os.getenv("PDF_EXTRACTION_SARVAM_API_KEY")
    
    if not api_key:
        raise ValueError(
            "SARVAM_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
    
    # Create config with API key
    config_dict = {"sarvam_api_key": api_key}
    
    # Add other environment variables if present
    for key in [
        "sarvam_base_url",
        "sarvam_timeout",
        "doc_intelligence_model",
        "max_pdf_size_mb",
        "max_pages_per_job",
        "structure_confidence_threshold",
        "link_confidence_threshold",
        "image_storage_path",
        "image_compression_quality",
        "max_concurrent_pages",
        "enable_caching",
        "cache_ttl_seconds",
        "llm_temperature",
        "llm_max_tokens",
        "max_retries",
        "retry_delay_seconds",
    ]:
        env_key = f"PDF_EXTRACTION_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value is not None:
            config_dict[key] = env_value
    
    return PDFExtractionConfig(**config_dict)


# Global config instance
_config: Optional[PDFExtractionConfig] = None


def init_config() -> PDFExtractionConfig:
    """
    Initialize global configuration instance.
    
    Returns:
        PDFExtractionConfig: Initialized configuration
    """
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_current_config() -> PDFExtractionConfig:
    """
    Get current configuration instance.
    
    Returns:
        PDFExtractionConfig: Current configuration
        
    Raises:
        RuntimeError: If configuration not initialized
    """
    if _config is None:
        raise RuntimeError(
            "Configuration not initialized. Call init_config() first."
        )
    return _config
