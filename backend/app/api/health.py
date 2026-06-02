from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    db: str
    model_loaded: bool
    version: str

@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        db="connected",
        model_loaded=True,
        version="1.0.0"
    )
