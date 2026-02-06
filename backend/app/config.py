from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str
    
    # Storage
    storage_bucket_test_papers: str = "test-papers"
    storage_bucket_response_sheets: str = "response-sheets"
    
    # CORS
    cors_origins: str = "http://localhost:5173"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # OCR
    tesseract_cmd: str = "/usr/bin/tesseract"
    tesseract_lang: str = "eng"
    
    # AI
    groq_api_key: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env (e.g., concept_graph settings)
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
