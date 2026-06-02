import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repository import AsyncResumeRepository, ResumeNotFoundError
from app.api.schemas import UploadResponse, ScoreResponse, ScoreRequest
from app.services.scoring_service import ScoringService
from app.parsers.dispatcher import ParserDispatcher

router = APIRouter()

@router.post("/upload_resume", response_model=UploadResponse)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    
    content = await file.read()
    try:
        parse_result = ParserDispatcher.parse(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {str(e)}")

    repo = AsyncResumeRepository(db)
    resume = await repo.create_resume({
        "filename": file.filename,
        "file_type": file.filename.split('.')[-1] if '.' in file.filename else 'txt',
        "file_size_bytes": file.size,
        "raw_text": parse_result.text,
        "word_count": parse_result.word_count,
        "page_count": parse_result.page_count,
        "ats_flags": {
            "tables_detected": parse_result.ats_flags.tables_detected,
            "columns_detected": parse_result.ats_flags.columns_detected,
            "images_detected": parse_result.ats_flags.images_detected,
            "special_chars_ratio": parse_result.ats_flags.special_chars_ratio,
            "is_scanned_pdf": parse_result.ats_flags.is_scanned_pdf
        },
        "parsing_warnings": parse_result.warnings
    })

    return UploadResponse(
        resume_id=resume.id,
        filename=resume.filename,
        word_count=resume.word_count,
        page_count=resume.page_count,
        ats_flags=resume.ats_flags,
        preview_text=resume.raw_text[:300],
        warnings=resume.parsing_warnings or []
    )

@router.post("/score_resume/{resume_id}", response_model=ScoreResponse)
async def score_resume(
    resume_id: str,
    request: ScoreRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    repo = AsyncResumeRepository(db)
    try:
        resume = await repo.get_resume(resume_id)
    except ResumeNotFoundError:
        raise HTTPException(status_code=404, detail="Resume not found")

    scoring_service = ScoringService()
    result = await scoring_service.process(
        resume=resume,
        job_description=request.job_description,
        target_role=request.target_role
    )

    processing_time = int((time.time() - start_time) * 1000)
    
    # Save score to DB
    score_data = {
        "resume_id": resume_id,
        "overall_score": result["overall_score"],
        "ats_score": result["ats_score"],
        "content_score": result["content_score"],
        "keyword_score": result["keyword_score"],
        "semantic_score": result["semantic_score"],
        "grade": result["grade"],
        "job_description": request.job_description,
        "target_role": request.target_role,
        "feature_vector": result["feature_vector"],
        "shap_values": result["shap_values"],
        "suggestions": [s.__dict__ for s in result["suggestions"]],
        "keyword_gaps": result["keyword_gaps"],
        "waterfall_data": result["waterfall_data"],
        "processing_time_ms": processing_time
    }
    score_record = await repo.create_score(score_data)

    return ScoreResponse(
        resume_id=resume_id,
        score_id=score_record.id,
        scored_at=score_record.created_at,
        **result,
        processing_time_ms=processing_time
    )
