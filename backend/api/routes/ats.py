from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, validator
from typing import Optional

from agents.ats_engine import run_ats_analysis
from db.queries import save_analysis, get_user_analyses, check_usage_limit
from api.middleware import get_current_user

router = APIRouter()


class ATSAnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str

    @validator("resume_text")
    def validate_resume(cls, v):
        if len(v.strip()) < 50:
            raise ValueError("Resume text too short.")
        return v.strip()

    @validator("job_description")
    def validate_jd(cls, v):
        if len(v.strip()) < 20:
            raise ValueError("Job description too short.")
        return v.strip()


@router.post("/analyze")
async def analyze_resume_ats(
    request: ATSAnalyzeRequest,
    user=Depends(get_current_user)
):
    print(f"ATS analysis requested by user: {user['id']}")

    allowed, remaining = await check_usage_limit(user["id"], "ats")
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_reached",
                "message": "Upgrade to Pro for unlimited analyses.",
                "upgrade_url": "/upgrade"
            }
        )

    try:
        result = run_ats_analysis(request.resume_text, request.job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    analysis_id = await save_analysis(
        user_id=user["id"],
        type="ats",
        resume_text=request.resume_text,
        job_description=request.job_description,
        result=result
    )

    clean_result = {k: v for k, v in result.items() if not k.startswith("_")}

    return {"analysis_id": str(analysis_id), "result": clean_result}


@router.get("/history")
async def get_ats_history(
    limit: int = 10,
    user=Depends(get_current_user)
):
    analyses = await get_user_analyses(user["id"], type="ats", limit=limit)
    return {"analyses": analyses}
