import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import setup_logging, logger
from app.api.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Application starting up", request_id="startup")
    yield
    logger.info("Application shutting down")

app = FastAPI(lifespan=lifespan, title="Resume Score Checker")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
    )
    logger.info("Request started", method=request.method, url=str(request.url))
    response = await call_next(request)
    logger.info("Request completed", status_code=response.status_code)
    return response

app.include_router(health_router, prefix="/health", tags=["health"])
