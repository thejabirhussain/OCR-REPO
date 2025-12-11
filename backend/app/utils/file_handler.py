"""File handling utilities for uploads and downloads."""

import hashlib
import mimetypes
import shutil
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from app.config import get_settings

settings = get_settings()


def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return Path(filename).suffix.lower()


def is_allowed_file_type(filename: str) -> bool:
    """Check if file type is allowed."""
    ext = get_file_extension(filename)
    return ext in settings.allowed_file_extensions


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename for storage."""
    ext = get_file_extension(original_filename)
    unique_id = str(uuid4())
    return f"{unique_id}{ext}"


def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[Path, str]:
    """
    Save uploaded file to disk.

    Returns:
        Tuple of (file_path, unique_filename)
    """
    unique_filename = generate_unique_filename(original_filename)
    file_path = settings.upload_dir / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path, unique_filename


def get_file_mime_type(filename: str) -> str:
    """Get MIME type for file."""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def delete_file(file_path: Path) -> bool:
    """Delete a file safely."""
    try:
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size


def ensure_directory_exists(directory: Path) -> None:
    """Ensure directory exists, create if not."""
    directory.mkdir(parents=True, exist_ok=True)




