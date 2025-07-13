"""
Generation endpoint for TailerAI v2.0
Generate LaTeX-based resume PDFs
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
from pathlib import Path
import subprocess
import os

from app.config.settings import get_settings

router = APIRouter()
settings = get_settings()

@router.post("/generate/{session_id}")
async def generate_resume(session_id: str) -> Dict[str, Any]:
    """Generate LaTeX resume PDF"""
    
    session_dir = Path(settings.upload_dir) / session_id
    output_dir = Path(settings.output_dir) / session_id
    
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # TODO: Implement actual LaTeX generation
        # For now, copy the template and return a placeholder
        
        template_path = Path(settings.latex_template_dir) / settings.default_template
        output_tex = output_dir / "generated_resume.tex"
        output_pdf = output_dir / "generated_resume.pdf"
        
        # Copy template as starting point
        import shutil
        shutil.copy(template_path, output_tex)
        
        # For now, just return success without actually compiling LaTeX
        # TODO: Add LaTeX compilation when pdflatex is available
        
        return {
            "session_id": session_id,
            "status": "generated",
            "tex_file": str(output_tex),
            "pdf_file": str(output_pdf) if output_pdf.exists() else None,
            "template_used": settings.default_template,
            "message": "Resume generated successfully (LaTeX compilation pending)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/generate/{session_id}/download")
async def download_resume(session_id: str):
    """Download generated resume PDF"""
    
    output_dir = Path(settings.output_dir) / session_id
    pdf_file = output_dir / "generated_resume.pdf"
    
    if not pdf_file.exists():
        # Try TEX file if PDF doesn't exist
        tex_file = output_dir / "generated_resume.tex"
        if tex_file.exists():
            return FileResponse(
                tex_file,
                media_type="application/x-tex",
                filename=f"resume_{session_id}.tex"
            )
        raise HTTPException(status_code=404, detail="Generated resume not found")
    
    return FileResponse(
        pdf_file,
        media_type="application/pdf",
        filename=f"resume_{session_id}.pdf"
    )

@router.get("/generate/{session_id}/status")
async def get_generation_status(session_id: str) -> Dict[str, Any]:
    """Get generation status for a session"""
    
    output_dir = Path(settings.output_dir) / session_id
    
    if not output_dir.exists():
        return {
            "session_id": session_id,
            "status": "not_started",
            "message": "Generation not started"
        }
    
    files = list(output_dir.glob("*"))
    
    return {
        "session_id": session_id,
        "status": "completed" if files else "in_progress",
        "files_generated": len(files),
        "files": [f.name for f in files]
    }