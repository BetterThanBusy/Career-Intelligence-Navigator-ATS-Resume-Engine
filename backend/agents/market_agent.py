"""
Market Intelligence Agent
Uses Perplexity's online search model to pull LIVE job market data.
This is what separates us from static career tools — real-time data.

Cost: ~$0.05-0.10 per query (Perplexity)
"""

import json
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
import structlog

log = structlog.get_logger()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

MARKET_SCHEMA = {
    "in_demand_skills": ["top 8 skills appearing most in current job postings for this role"],
    "skills_at_risk": ["skills likely to be automated or devalued in 2-3 years"],
    "salary_range": {
        "low": "integer USD annual",
        "mid": "integer USD annual", 
        "high": "integer USD annual",
        "currency": "USD"
    },
    "target_job_titles": ["5 specific job titles to apply for based on current profile"],
    "growing_adjacent_roles": ["3 roles this person could pivot to with upskilling"],
    "top_certifications": ["most valued certifications for this role right now"],
    "market_summary": "2-3 sentence summary of current market conditions for this role",
    "hiring_trend": "growing | stable | declining",
    "data_freshness": "date string of when this data was retrieved"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
def get_job_market_intelligence(role: str, skills: list, industry: str = None) -> dict:
    """
    Fetch real-time job market intelligence for a given role.
    
    Args:
        role: Current job title (e.g. "Marketing Manager")
        skills: List of current skills to contextualize the search
        industry: Optional industry to narrow the search
        
    Returns:
        Live market intelligence dict with citations
    """
    
    log.info("Fetching market intelligence", role=role, industry=industry)
    
    skills_context = ", ".join(skills[:8]) if skills else "general skills"
    industry_context = f"in the {industry} industry" if industry else "across industries"
    
    query = f"""
    For a {role} professional {industry_context} with skills in {skills_context}:
    
    Provide a current job market analysis (June 2026) including:
    1. Top 8 in-demand skills appearing most in job postings right now
    2. Skills at risk of automation or becoming obsolete in 2-3 years
    3. Current salary ranges (low/mid/high annual USD)
    4. Top 5 specific job titles to target for career growth
    5. 3 adjacent roles they could pivot to with 3-6 months upskilling
    6. Most valued certifications for this role
    7. Overall hiring trend: growing, stable, or declining
    
    Base your answer on current job postings, LinkedIn data, Glassdoor, 
    Indeed, and recent industry reports. Be specific with numbers.
    
    Return ONLY valid JSON matching this schema:
    {json.dumps(MARKET_SCHEMA, indent=2)}
    
    Return only JSON. No markdown. No explanation.
    """
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-sonar-large-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "You are a career market intelligence analyst. Return only valid JSON. Be specific and data-driven."
            },
            {
                "role": "user", 
                "content": query
            }
        ],
        "temperature": 0.1,      # Low temp for factual consistency
        "return_citations": True,
        "return_related_questions": False
    }
    
    response = requests.post(PERPLEXITY_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    raw = data["choices"][0]["message"]["content"].strip()
    
    # Strip markdown
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    result = json.loads(raw.strip())
    result["data_freshness"] = datetime.utcnow().isoformat()
    
    # Store citations if available
    if "citations" in data:
        result["_citations"] = data["citations"]
    
    log.info("Market intelligence fetched",
             role=role,
             hiring_trend=result.get("hiring_trend"),
             in_demand_count=len(result.get("in_demand_skills", [])))
    
    return result
