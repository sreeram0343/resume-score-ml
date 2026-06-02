import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.health import router as health_router
from app.api.routes.resume import router as resume_router
from app.api.middleware import setup_middleware
from app.db.cleanup import cleanup_expired_resumes

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application starting up", env=settings.env)
    
    # Download spacy model if missing
    try:
        import spacy
        spacy.load("en_core_web_sm")
    except:
        import os
        os.system("python -m spacy download en_core_web_sm")

    yield
    logger.info("Application shutting down")

app = FastAPI(
    lifespan=lifespan, 
    title="Resume Score Checker API v1",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

setup_middleware(app)

app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(resume_router, prefix="/api/v1/resume", tags=["resume"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
