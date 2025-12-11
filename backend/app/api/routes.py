"""API route handlers."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Job, JobStatus
from app.schemas import (
    HealthResponse,
    JobCreateResponse,
    JobListResponse,
    JobResponse,
    JobResultResponse,
    JobStats,
    ProcessingStages,
)
from app.tasks import process_document_task
from app.utils.file_handler import (
    is_allowed_file_type,
    save_uploaded_file,
)
from app.services.docx_generator import (
    generate_docx_from_document,
    generate_txt_from_document,
)
from app.schemas import StructuredDocument

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    # Check database
    db_status = "connected"
    try:
        db.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"

    # Check Redis (skip if using in-memory broker)
    if settings.celery_broker_url.startswith("memory://"):
        redis_status = "not_configured"
    else:
        redis_status = "connected"
        try:
            import redis

            r = redis.from_url(settings.redis_url)
            r.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = "disconnected"

    # Check models (simplified - just check if they can be loaded)
    models_status = {}
    try:
        # Check PaddleOCR
        from app.services.ocr import _get_paddleocr

        _get_paddleocr()
        models_status["paddleocr"] = "loaded"
    except Exception:
        models_status["paddleocr"] = "not_loaded"

    try:
        # Check translation model
        from app.services.translate import _load_translation_model

        _load_translation_model()
        models_status["nllb"] = "loaded"
    except Exception:
        models_status["nllb"] = "not_loaded"

    overall_status = "healthy" if db_status == "connected" and redis_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        models=models_status,
        timestamp=datetime.utcnow(),
    )


@router.post("/jobs", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    file: UploadFile = File(...),
    source_language: str = Query(default="ar", description="Source language code"),
    target_language: str = Query(default="en", description="Target language code"),
    preserve_layout: bool = Query(default=True, description="Preserve document layout"),
    ocr_engine: str = Query(
        default="paddleocr",
        description="OCR engine: paddleocr, tesseract, ensemble",
    ),
    translation_model: str = Query(
        default="facebook/nllb-200-3.3B",
        description="Translation model identifier",
    ),
    db: Session = Depends(get_db),
):
    """Create a new job for document processing."""
    # Validate file type
    if not is_allowed_file_type(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.allowed_file_extensions)}",
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size
    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum of {settings.max_file_size_mb}MB",
        )

    # Save file
    try:
        file_path, unique_filename = save_uploaded_file(file_content, file.filename)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file",
        )

    # Determine file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext == ".pdf":
        file_type = "pdf"
    elif file_ext == ".docx":
        file_type = "docx"
    else:
        file_type = "image"

    # Create job record
    job = Job(
        status=JobStatus.QUEUED,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_type,
        config={
            "source_language": source_language,
            "target_language": target_language,
            "preserve_layout": preserve_layout,
            "ocr_engine": ocr_engine,
            "translation_model": translation_model,
        },
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue processing task. For local in-memory broker, run synchronously.
    try:
        if settings.celery_broker_url.startswith("memory://"):
            process_document_task.apply(args=[str(job.id)])
        else:
            process_document_task.delay(str(job.id))
        logger.info(f"Job {job.id} queued for processing")
    except Exception as e:
        logger.error(f"Error enqueueing job {job.id}: {e}")
        job.status = JobStatus.FAILED
        job.error_message = f"Failed to enqueue task: {str(e)}"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue processing task",
        )

    return JobCreateResponse(
        job_id=str(job.id),
        status=job.status.value,
        created_at=job.created_at,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get job status and metadata."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    stats = None
    if job.stats:
        stats = JobStats(**job.stats)

    processing_stages = ProcessingStages(
        extraction=job.extraction_stage.value,
        ocr=job.ocr_stage.value,
        translation=job.translation_stage.value,
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        original_filename=job.original_filename,
        created_at=job.created_at,
        updated_at=job.updated_at,
        stats=stats,
        error_message=job.error_message,
        processing_stages=processing_stages,
    )


@router.get("/jobs/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str, db: Session = Depends(get_db)):
    """Get job results (Arabic and English structured documents)."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status.value}",
        )

    arabic_doc = None
    english_doc = None

    if job.arabic_json:
        arabic_doc = StructuredDocument(**job.arabic_json)
    if job.english_json:
        english_doc = StructuredDocument(**job.english_json)

    return JobResultResponse(
        job_id=str(job.id),
        arabic=arabic_doc,
        english=english_doc,
    )


@router.get("/jobs/{job_id}/download")
async def download_job_result(
    job_id: str,
    language: str = Query(..., description="Language: ar or en"),
    format: str = Query(default="json", description="Format: json, txt, or docx"),
    db: Session = Depends(get_db),
):
    """Download job result in specified format."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status.value}",
        )

    # Get document
    if language == "ar":
        doc_data = job.arabic_json
        lang_suffix = "arabic"
    elif language == "en":
        doc_data = job.english_json
        lang_suffix = "english"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be 'ar' or 'en'",
        )

    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{language.upper()} document not found",
        )

    document = StructuredDocument(**doc_data)

    # Generate file based on format
    output_dir = Path(settings.upload_dir) / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)

    if format == "json":
        import json

        output_path = output_dir / f"{job_id}_{lang_suffix}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(document.dict(), f, ensure_ascii=False, indent=2)
        return FileResponse(
            output_path,
            media_type="application/json",
            filename=f"{job.original_filename}_{lang_suffix}.json",
        )

    elif format == "txt":
        output_path = output_dir / f"{job_id}_{lang_suffix}.txt"
        generate_txt_from_document(document, output_path)
        return FileResponse(
            output_path,
            media_type="text/plain",
            filename=f"{job.original_filename}_{lang_suffix}.txt",
        )

    elif format == "docx":
        output_path = output_dir / f"{job_id}_{lang_suffix}.docx"
        generate_docx_from_document(document, output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{job.original_filename}_{lang_suffix}.docx",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'json', 'txt', or 'docx'",
        )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """List all jobs with pagination."""
    query = db.query(Job)

    # Apply status filter
    if status_filter:
        try:
            status_enum = JobStatus(status_filter)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    # Get total count
    total = query.count()

    # Apply pagination
    jobs = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # Convert to response format
    job_responses = []
    for job in jobs:
        stats = None
        if job.stats:
            stats = JobStats(**job.stats)

        processing_stages = ProcessingStages(
            extraction=job.extraction_stage.value,
            ocr=job.ocr_stage.value,
            translation=job.translation_stage.value,
        )

        job_responses.append(
            JobResponse(
                job_id=str(job.id),
                status=job.status.value,
                original_filename=job.original_filename,
                created_at=job.created_at,
                updated_at=job.updated_at,
                stats=stats,
                error_message=job.error_message,
                processing_stages=processing_stages,
            )
        )

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its associated files."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Delete associated files
    file_path = Path(job.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete job record
    db.delete(job)
    db.commit()

    return None



