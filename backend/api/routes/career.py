"""
Career Intelligence API Routes
POST /api/career/analyze  — full career intelligence analysis
GET  /api/career/history  — past analyses
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Optional
import structlog

from agents.resume_parser import parse_resume
from agents.market_agent import get_job_market_intelligence
from agents.gap_analyzer import analyze_skill_gap
from agents.learning_path import generate_learning_path
from db.queries import save_analysis, get_user_analyses, check_usage_limit
from api.middleware import get_current_user

log = structlog.get_logger()
router = APIRouter()


class CareerAnalyzeRequest(BaseModel):
    resume_text: str
    target_role: Optional[str] = None
    industry: Optional[str] = None
    
    # Learning constraints
    hours_per_week: int = 5
    budget: str = "free"           # free | low | any
    learning_style: str = "mixed"  # video | reading | projects | mixed
    timeline_months: int = 3
    
    @validator("resume_text")
    def validate_resume(cls, v):
        if len(v.strip()) < 100:
            raise ValueError("Resume text too short.")
        return v.strip()
    
    @validator("budget")
    def validate_budget(cls, v):
        if v not in ["free", "low", "any"]:
            raise ValueError("Budget must be 'free', 'low', or 'any'")
        return v
    
    @validator("hours_per_week")
    def validate_hours(cls, v):
        if v < 1 or v > 40:
            raise ValueError("Hours per week must be between 1 and 40")
        return v


@router.post("/analyze")
async def analyze_career(
    request: CareerAnalyzeRequest,
    user=Depends(get_current_user)
):
    """
    Run full career intelligence analysis.
    
    Chains 4 agents: resume_parser → market_agent → gap_analyzer → learning_path
    Cost: ~$0.35-0.45 per run
    Time: ~15-25 seconds
    """
    
    allowed, remaining = await check_usage_limit(user["id"], "career_gap")
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "usage_limit_reached",
                "message": "You've used your free Career Intelligence analysis this month.",
                "action": "upgrade",
                "upgrade_url": "/upgrade"
            }
        )
    
    log.info("Career analysis requested", user_id=user["id"])
    
    try:
        # Step 1: Parse resume into structured profile
        log.info("Step 1/4: Parsing resume")
        profile = parse_resume(request.resume_text)
        
        # Use target_role override if provided, otherwise use parsed current role
        role_for_market = request.target_role or profile.get("current_role", "Professional")
        
        # Step 2: Get live market intelligence
        log.info("Step 2/4: Fetching market intelligence", role=role_for_market)
        market_data = get_job_market_intelligence(
            role=role_for_market,
            skills=profile.get("skills", []),
            industry=request.industry
        )
        
        # Step 3: Analyze skill gaps
        log.info("Step 3/4: Analyzing skill gaps")
        gap_analysis = analyze_skill_gap(profile, market_data)
        
        # Step 4: Generate learning path
        log.info("Step 4/4: Generating learning path")
        learning_path = generate_learning_path(
            gap_analysis=gap_analysis,
            constraints={
                "hours_per_week": request.hours_per_week,
                "budget": request.budget,
                "learning_style": request.learning_style,
                "timeline_months": request.timeline_months
            }
        )
        
    except Exception as e:
        log.error("Career analysis failed", error=str(e), user_id=user["id"])
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    # Combine full result
    full_result = {
        "profile": {k: v for k, v in profile.items() if not k.startswith("_")},
        "market_intelligence": {k: v for k, v in market_data.items() if not k.startswith("_")},
        "gap_analysis": {k: v for k, v in gap_analysis.items() if not k.startswith("_")},
        "learning_path": {k: v for k, v in learning_path.items() if not k.startswith("_")}
    }
    
    # Calculate total tokens and cost
    total_tokens = sum([
        profile.get("_meta", {}).get("tokens_in", 0),
        profile.get("_meta", {}).get("tokens_out", 0),
        gap_analysis.get("_meta", {}).get("tokens_in", 0),
        gap_analysis.get("_meta", {}).get("tokens_out", 0),
        learning_path.get("_meta", {}).get("tokens_in", 0),
        learning_path.get("_meta", {}).get("tokens_out", 0),
    ])
    
    # Save to DB
    analysis_id = await save_analysis(
        user_id=user["id"],
        type="career_gap",
        resume_text=request.resume_text,
        target_role=role_for_market,
        result=full_result,
        tokens_used=total_tokens
    )
    
    return {
        "analysis_id": str(analysis_id),
        "result": full_result
    }


@router.get("/history")
async def get_career_history(limit: int = 10, user=Depends(get_current_user)):
    analyses = await get_user_analyses(user["id"], type="career_gap", limit=limit)
    return {"analyses": analyses}
