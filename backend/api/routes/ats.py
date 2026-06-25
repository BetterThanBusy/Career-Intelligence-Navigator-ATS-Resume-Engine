"""
ATS API Routes
POST /api/ats/analyze
POST /api/ats/upload (PDF upload)
GET  /api/ats/history
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, validator
from typing import Optional
import structlog

from agents.ats_engine import run_ats_analysis, ATSParseError, ATSAPIError
from db.queries import save_analysis, get_user_analyses, check_usage_limit
from utils.pdf_parser import extract_text_from_pdf
from api.middleware import get_current_user

log = structlog.get_logger()
router = APIRouter()


# ─────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────

class ATSAnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str
    
    @validator("resume_text")
    def validate_resume(cls, v):
        if len(v.strip()) < 100:
            raise ValueError("Resume text too short. Please provide full resume.")
        if len(v) > 15000:
            raise ValueError("Resume text too long. Max 15,000 characters.")
        return v.strip()
    
    @validator("job_description")
    def validate_jd(cls, v):
        if len(v.strip()) < 50:
            raise ValueError("Job description too short.")
        if len(v) > 10000:
            raise ValueError("Job description too long. Max 10,000 characters.")
        return v.strip()


class ATSAnalyzeResponse(BaseModel):
    analysis_id: str
    result: dict


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@router.post("/analyze", response_model=ATSAnalyzeResponse)
async def analyze_resume_ats(
    request: ATSAnalyzeRequest,
    user=Depends(get_current_user)
):
    """
    Run ATS analysis on a resume against a job description.
    
    Requires authentication.
    Free plan: 2 analyses/month
    Pro plan: unlimited
    """
    
    # Check usage limits
    allowed, remaining = await check_usage_limit(user["id"], "ats")
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_reached",
                "message": "You've used all your free ATS analyses this month.",
                "action": "upgrade",
                "upgrade_url": "/upgrade"
            }
        )
    
    log.info("ATS analysis requested", user_id=user["id"], remaining=remaining)
    
    try:
        result = run_ats_analysis(request.resume_text, request.job_description)
    except ATSParseError as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed to parse: {e}")
    except ATSAPIError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}")
    
    # Save to database
    analysis_id = await save_analysis(
        user_id=user["id"],
        type="ats",
        resume_text=request.resume_text,
        job_description=request.job_description,
        result=result,
        tokens_used=result.get("_meta", {}).get("tokens_in", 0) + result.get("_meta", {}).get("tokens_out", 0)
    )
    
    # Remove internal meta from response
    clean_result = {k: v for k, v in result.items() if not k.startswith("_")}
    
    return ATSAnalyzeResponse(analysis_id=str(analysis_id), result=clean_result)


@router.post("/upload")
async def upload_resume_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    Upload a PDF resume and extract text for ATS analysis.
    Returns extracted text — client then calls /analyze with the text.
    """
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    if file.size and file.size > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")
    
    content = await file.read()
    
    try:
        text = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract PDF text: {e}")
    
    if len(text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. Please paste your resume as text instead."
        )
    
    return {"text": text, "char_count": len(text)}


@router.get("/history")
async def get_ats_history(
    limit: int = 10,
    user=Depends(get_current_user)
):
    """Get user's previous ATS analyses."""
    
    analyses = await get_user_analyses(user["id"], type="ats", limit=limit)
    return {"analyses": analyses}
