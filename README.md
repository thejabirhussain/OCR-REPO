# Arabic Text Extraction & Translation System

A production-ready web application for extracting Arabic text from documents (PDF, DOCX, images) using open-source OCR engines and translating it to English while preserving document structure.

## Features

- **Multi-format Support**: PDF (text-based and scanned), DOCX, and image files (JPEG, PNG, TIFF)
- **Open-source OCR**: PaddleOCR with Arabic support and Tesseract as fallback
- **Structure Preservation**: Maintains paragraphs, headings, lists, and tables
- **High-quality Translation**: Uses Facebook NLLB-200 model for Arabic→English translation
- **Side-by-side Viewer**: Compare Arabic original and English translation
- **Multiple Export Formats**: JSON, TXT, and DOCX
- **Async Processing**: Celery-based task queue for handling large documents
- **Production-ready**: Docker Compose setup, comprehensive error handling, and monitoring

## Architecture

```
┌─────────────┐
│   Frontend  │ (React + TypeScript + Vite)
│  (Port 5173)│
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Backend   │ (FastAPI)
│  (Port 8000)│
└──────┬──────┘
       │
       ├──► PostgreSQL (Job metadata)
       ├──► Redis (Task queue)
       └──► Celery Workers (OCR + Translation)
```

## Prerequisites

- Docker & Docker Compose (v2.0+)
- 8GB+ RAM recommended (for ML models)
- 10GB+ disk space (for models and uploads)
- Git

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd OCR-POC
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration if needed
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Download ML models** (first time only):
   ```bash
   docker-compose exec backend python scripts/download_models.py
   ```

5. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

## Development Setup

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://user:password@localhost:5432/arabic_ocr
export REDIS_URL=redis://localhost:6379/0

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Start Celery worker (in another terminal)
celery -A app.tasks worker --loglevel=info
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Upload a document**: Drag and drop or select a PDF, DOCX, or image file
2. **Monitor progress**: Watch the job status update in real-time
3. **View results**: See Arabic text and English translation side-by-side
4. **Download**: Export results in JSON, TXT, or DOCX format

## API Endpoints

### `POST /api/jobs`
Upload a document for processing.

**Request**: Multipart form data with `file` field

**Response**:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "created_at": "2025-12-10T10:30:00Z"
}
```

### `GET /api/jobs/{job_id}`
Get job status and metadata.

### `GET /api/jobs/{job_id}/result`
Get extraction and translation results.

### `GET /api/jobs/{job_id}/download`
Download results in specified format (`language=ar|en`, `format=json|txt|docx`).

### `GET /api/health`
Health check endpoint.

See full API documentation at http://localhost:8000/docs

## Configuration

Key environment variables:

- `MAX_FILE_SIZE_MB`: Maximum file size (default: 50MB)
- `OCR_ENGINE`: Primary OCR engine (`paddleocr` or `tesseract`)
- `TRANSLATION_MODEL`: Hugging Face model identifier
- `JOB_TIMEOUT_MINUTES`: Maximum processing time per job

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose exec backend pytest tests/integration/
```

## Troubleshooting

### Models not loading
- Ensure models are downloaded: `docker-compose exec backend python scripts/download_models.py`
- Check disk space (models require ~5GB)

### OCR accuracy issues
- Try switching OCR engine via API parameter
- Ensure images are high resolution (300+ DPI)
- Check Arabic language pack is installed for Tesseract

### Translation quality
- Adjust `BATCH_SIZE` and `MAX_LENGTH` in environment
- Consider using larger NLLB models (requires more RAM)

### Memory issues
- Increase Docker memory limit
- Process documents sequentially (reduce worker concurrency)

## Project Structure

```
OCR-POC/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── services/ # OCR, translation, extraction
│   │   └── tasks.py  # Celery tasks
│   └── tests/        # Test suite
├── frontend/         # React frontend
│   └── src/
│       ├── components/
│       └── services/
├── docker-compose.yml
└── README.md
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please read CONTRIBUTING.md for guidelines.

## Support

For issues and questions, please open an issue on GitHub.

