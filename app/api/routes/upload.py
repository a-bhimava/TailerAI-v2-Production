"""
Enhanced upload endpoint for TailerAI v2.0
Handle resume and job description file uploads with intelligent parsing
Following best practices: modular design, comprehensive error handling, logging
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, Optional
import uuid
from pathlib import Path
import tempfile
import shutil

from app.config.settings import get_settings
from app.services.file_parser import create_document_parser, FileParsingError
from app.models.schemas import UploadResponse, ParsedDocument

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Constants for better maintainability
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=UploadResponse)
async def upload_and_parse_files(
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    job_description: UploadFile = File(None, description="Optional job description file")
) -> UploadResponse:
    """
    Upload and parse resume and optional job description
    
    This endpoint follows best practices:
    - Validates file types and sizes
    - Uses secure temporary file handling
    - Provides detailed parsing results with error handling
    - Returns structured data for downstream processing
    """
    logger.info(f"Starting file upload for session")
    
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_dir = Path(settings.upload_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Created session {session_id}")
        
        # Initialize document parser
        parser = create_document_parser()
        
        # Process resume (required)
        resume_data = await _process_uploaded_file(
            file=resume,
            file_type="resume",
            session_dir=session_dir,
            parser=parser
        )
        
        # Process job description (optional)
        job_description_data = None
        if job_description and job_description.filename:
            job_description_data = await _process_uploaded_file(
                file=job_description,
                file_type="job_description",
                session_dir=session_dir,
                parser=parser
            )
        
        # Prepare response
        response = UploadResponse(
            status="success",
            session_id=session_id,
            resume=resume_data,
            job_description=job_description_data,
            message="Files uploaded and parsed successfully"
        )
        
        logger.info(f"Successfully processed upload for session {session_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload processing failed: {str(e)}"
        )


async def _process_uploaded_file(
    file: UploadFile,
    file_type: str,
    session_dir: Path,
    parser
) -> ParsedDocument:
    """
    Process a single uploaded file with validation and parsing
    Modular helper function following single responsibility principle
    """
    logger.debug(f"Processing {file_type}: {file.filename}")
    
    # Validate file
    _validate_uploaded_file(file, file_type)
    
    # Save file securely
    file_path = await _save_uploaded_file(file, file_type, session_dir)
    
    try:
        # Parse document content
        parsed_content = parser.parse_document(file_path)
        
        # Create structured response
        return ParsedDocument(
            filename=file.filename,
            file_path=str(file_path),
            file_type=file_type,
            content=parsed_content.raw_text,
            contact_info=parsed_content.contact_info,
            sections=parsed_content.sections,
            metadata=parsed_content.metadata,
            parsing_errors=parsed_content.parsing_errors
        )
        
    except FileParsingError as e:
        logger.error(f"File parsing failed for {file_type}: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse {file_type}: {str(e)}"
        )


def _validate_uploaded_file(file: UploadFile, file_type: str) -> None:
    """
    Validate uploaded file meets requirements
    Centralized validation logic for consistency
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=f"{file_type.title()} filename is required"
        )
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"{file_type.title()} file type '{file_ext}' not supported. "
                   f"Use {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"{file_type.title()} file too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )


async def _save_uploaded_file(
    file: UploadFile,
    file_type: str,
    session_dir: Path
) -> Path:
    """
    Securely save uploaded file to session directory
    Uses proper file handling with binary mode for non-text files
    """
    file_ext = Path(file.filename).suffix.lower()
    file_path = session_dir / f"{file_type}{file_ext}"
    
    try:
        # Read file content
        content = await file.read()
        
        # Save with appropriate mode (binary for PDF/DOCX, text for TXT)
        mode = 'wb' if file_ext in {'.pdf', '.docx'} else 'w'
        
        if mode == 'wb':
            with open(file_path, 'wb') as f:
                f.write(content)
        else:
            # For text files, decode and save as text
            text_content = content.decode('utf-8')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
        
        logger.debug(f"Saved {file_type} to {file_path}")
        return file_path
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid text encoding in {file_type} file"
        )
    except Exception as e:
        logger.error(f"Failed to save {file_type}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save {file_type}: {str(e)}"
        )


@router.get("/upload/{session_id}/status")
async def get_upload_status(session_id: str) -> Dict[str, Any]:
    """
    Get upload and parsing status for a session
    Enhanced with parsing status and metadata
    """
    logger.debug(f"Checking status for session {session_id}")
    
    session_dir = Path(settings.upload_dir) / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get all files in session directory
    files = list(session_dir.glob("*"))
    file_info = []
    
    for file_path in files:
        file_info.append({
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        })
    
    return {
        "session_id": session_id,
        "status": "completed" if files else "empty",
        "files_uploaded": len(files),
        "files": file_info,
        "session_dir": str(session_dir)
    }


@router.delete("/upload/{session_id}")
async def cleanup_session(session_id: str) -> Dict[str, str]:
    """
    Clean up session files (for testing and cleanup)
    Follows best practices for resource management
    """
    logger.info(f"Cleaning up session {session_id}")
    
    session_dir = Path(settings.upload_dir) / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Remove session directory and all contents
        shutil.rmtree(session_dir)
        
        logger.info(f"Successfully cleaned up session {session_id}")
        return {
            "status": "success",
            "message": f"Session {session_id} cleaned up successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )