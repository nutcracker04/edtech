from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import (
    upload_router,
    tests_router,
    analysis_router,
    performance_router,
    auth_router,
    repository_router,
    ai_router,
    pyq_router
)

# Create FastAPI app
app = FastAPI(
    title="EdTech Platform API",
    description="Backend API for EdTech platform with OCR test upload, adaptive testing, and performance analytics",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(tests_router)
app.include_router(analysis_router)
app.include_router(performance_router)
app.include_router(repository_router)
app.include_router(pyq_router) # Added pyq_router
app.include_router(ai_router)


@app.get("/")
async def root():
    """
    Root endpoint - API health check.
    """
    return {
        "message": "EdTech Platform API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "database": "connected",
        "ocr": "ready"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
