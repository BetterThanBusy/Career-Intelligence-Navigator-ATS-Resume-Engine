"""
Gap Analyzer Agent
Combines user profile + market intelligence → actionable gap analysis.
This is the core IP of Career Intelligence Navigator.

Cost: ~$0.10 per analysis (Claude Sonnet 4.6)
"""

import json
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

log = structlog.get_logger()
client = anthropic.Anthropic()

GAP_SCHEMA = {
    "gap_score": "integer 0-100. Higher = bigger gap. 0-30 = strong, 31-60 = moderate, 61-100 = significant",
    "critical_gaps": [
        {
            "skill": "specific skill name",
            "urgency": "high | medium | low",
            "reason": "why this gap matters and market demand evidence",
            "time_to_learn": "estimated weeks to reach competency"
        }
    ],
    "strengths_to_leverage": ["existing skills that are highly valued in the market right now"],
    "automation_risk_score": "integer 0-100. Higher = higher risk. Based on skills overlap with automatable tasks",
    "automation_risk_breakdown": ["specific tasks or skills at automation risk"],
    "recommended_pivot": {
        "target_role": "specific job title",
        "rationale": "why this is the optimal next move",
        "time_to_qualify": "X months",
        "salary_upside": "estimated % salary increase"
    },
    "quick_wins": ["3-5 skills or certifications achievable in 30 days or less"],
    "six_month_plan": [
        {
            "month": "1",
            "focus": "primary learning focus",
            "goal": "measurable milestone"
        }
    ],
    "competitive_advantage": "what makes this person uniquely valuable if they close the gaps"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def analyze_skill_gap(user_profile: dict, market_data: dict) -> dict:
    """
    Analyze the gap between a user's current profile and market demands.
    
    Args:
        user_profile: Output from resume_parser
        market_data: Output from market_agent
        
    Returns:
        Comprehensive gap analysis dict
    """
    
    log.info("Running gap analysis",
             role=user_profile.get("current_role"),
             years_exp=user_profile.get("years_experience"))
    
    # Remove internal meta fields before sending to Claude
    clean_profile = {k: v for k, v in user_profile.items() if not k.startswith("_")}
    clean_market = {k: v for k, v in market_data.items() if not k.startswith("_")}
    
    prompt = f"""You are a senior career strategist who has helped 10,000+ professionals navigate career transitions.

Analyze the gap between this professional's current profile and what the market demands.
Be honest, specific, and strategic. Do not sugarcoat gaps — professionals need accurate intelligence.

USER PROFILE:
{json.dumps(clean_profile, indent=2)}

LIVE MARKET INTELLIGENCE:
{json.dumps(clean_market, indent=2)}

Return ONLY valid JSON matching this schema:
{json.dumps(GAP_SCHEMA, indent=2)}

Analysis rules:
- gap_score: Compare user skills[] vs market in_demand_skills[]. Weight by urgency and frequency
- automation_risk_score: Compare user skills[] vs market skills_at_risk[]. Higher overlap = higher risk
- critical_gaps: Only include gaps that meaningfully affect career trajectory. Max 6.
- recommended_pivot: Must be realistic given current experience level
- quick_wins: Must be genuinely achievable in 30 days (free certifications count)
- six_month_plan: 6 entries, one per month, ordered by priority

Return only the JSON. No markdown. No explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw.strip())
    result["_meta"] = {
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "model": "claude-sonnet-4-6"
    }
    
    log.info("Gap analysis complete",
             gap_score=result.get("gap_score"),
             automation_risk=result.get("automation_risk_score"),
             critical_gaps_count=len(result.get("critical_gaps", [])))
    
    return result
