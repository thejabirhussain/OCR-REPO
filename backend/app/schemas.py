"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    OCR = "ocr"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingStage(str, Enum):
    """Processing stage enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Layout Schema Definitions
class TableMetadata(BaseModel):
    """Table cell metadata."""

    row: Optional[int] = None
    col: Optional[int] = None
    table_id: Optional[str] = None


class BlockMetadata(BaseModel):
    """Block metadata."""

    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2]
    is_heading: bool = False
    heading_level: Optional[int] = None
    list_level: Optional[int] = None
    table: Optional[TableMetadata] = None
    confidence: Optional[float] = None


class Block(BaseModel):
    """Text block in document."""

    block_id: str
    type: str = Field(..., description="Type: paragraph, heading, table_cell, list_item")
    metadata: BlockMetadata
    text: str


class Page(BaseModel):
    """Page in document."""

    page_index: int
    blocks: List[Block]


class DocumentMetadata(BaseModel):
    """Document-level metadata."""

    source_filename: str
    total_pages: int
    extraction_timestamp: str
    ocr_engine: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class StructuredDocument(BaseModel):
    """Structured document representation."""

    document_id: str
    language: str  # "ar" or "en"
    pages: List[Page]
    metadata: DocumentMetadata


# API Request/Response Schemas
class JobCreateRequest(BaseModel):
    """Job creation request schema."""

    source_language: str = Field(default="ar", description="Source language code")
    target_language: str = Field(default="en", description="Target language code")
    preserve_layout: bool = Field(default=True, description="Preserve document layout")
    ocr_engine: str = Field(
        default="paddleocr",
        description="OCR engine: paddleocr, tesseract, ensemble",
    )
    translation_model: str = Field(
        default="facebook/nllb-200-3.3B",
        description="Translation model identifier",
    )


class JobCreateResponse(BaseModel):
    """Job creation response schema."""

    job_id: str
    status: str
    created_at: datetime


class JobStats(BaseModel):
    """Job statistics."""

    total_pages: Optional[int] = None
    total_blocks: Optional[int] = None
    total_characters_arabic: Optional[int] = None
    total_characters_english: Optional[int] = None


class ProcessingStages(BaseModel):
    """Processing stages status."""

    extraction: str
    ocr: str
    translation: str


class JobResponse(BaseModel):
    """Job status response schema."""

    job_id: str
    status: str
    original_filename: str
    created_at: datetime
    updated_at: datetime
    stats: Optional[JobStats] = None
    error_message: Optional[str] = None
    processing_stages: ProcessingStages


class JobResultResponse(BaseModel):
    """Job result response schema."""

    job_id: str
    arabic: Optional[StructuredDocument] = None
    english: Optional[StructuredDocument] = None


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    database: str
    redis: str
    models: Dict[str, str]
    timestamp: datetime


class JobListResponse(BaseModel):
    """Job list response schema."""

    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int




