import os
import re
import uuid
import pathlib
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and remove invalid characters."""
    # Strip path components
    basename = os.path.basename(filename)
    # Remove any null bytes or path separators
    clean = re.sub(r'[\0/\\:]', '', basename)
    # Replace spaces and special characters with underscores
    clean = re.sub(r'[^\w\.-]', '_', clean)
    return clean or "uploaded_file"


def validate_file(file: UploadFile) -> Tuple[str, str]:
    """Validate file extension and type. Return (original_filename, file_type)."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing"
        )
    
    clean_original = sanitize_filename(file.filename)
    ext = pathlib.Path(clean_original).suffix.lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    file_type = ext.lstrip(".")  # 'pdf' or 'docx'
    return clean_original, file_type


def save_upload_file(file: UploadFile, upload_dir: str) -> Tuple[str, str, str, int]:
    """
    Save uploaded file with a secure, unique server-side filename.
    Returns: (original_filename, server_filename, full_file_path, file_size_bytes)
    """
    original_filename, file_type = validate_file(file)
    
    # Generate unique server filename
    unique_prefix = uuid.uuid4().hex[:12]
    server_filename = f"{unique_prefix}_{original_filename}"
    
    os.makedirs(upload_dir, exist_ok=True)
    destination_path = os.path.join(upload_dir, server_filename)
    
    # Verify destination path is strictly within upload_dir (Path Traversal Protection)
    dest_abs = os.path.abspath(destination_path)
    upload_abs = os.path.abspath(upload_dir)
    if not dest_abs.startswith(upload_abs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path detected"
        )
    
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    file_size = 0
    
    with open(destination_path, "wb") as buffer:
        while chunk := file.file.read(1024 * 1024):  # 1MB chunk
            file_size += len(chunk)
            if file_size > max_bytes:
                # Remove partially written file
                buffer.close()
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds maximum allowed size of {settings.max_file_size_mb}MB"
                )
            buffer.write(chunk)
            
    if file_size == 0:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )
        
    return original_filename, server_filename, destination_path, file_size


def delete_file_from_disk(file_path: str) -> bool:
    """Safely delete file from disk if it exists."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False
