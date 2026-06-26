import json
import os
import requests
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"

def get_job_market_intelligence(role: str, skills: list, industry: str = None) -> dict:

    print(f"Fetching market intelligence for: {role}")
    print(f"Perplexity key present: {bool(PERPLEXITY_API_KEY)}")

    skills_context = ", ".join(skills[:8]) if skills else "general skills"

    query = f"""For a {role} professional with skills in {skills_context}, provide a job market analysis.

Return ONLY valid JSON:
{{
    "in_demand_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
    "skills_at_risk": ["risk1", "risk2"],
    "salary_range": {{
        "low": 80000,
        "mid": 110000,
        "high": 150000,
        "currency": "USD"
    }},
    "target_job_titles": ["title1", "title2", "title3"],
    "growing_adjacent_roles": ["role1", "role2"],
    "top_certifications": ["cert1", "cert2"],
    "market_summary": "brief market summary here",
    "hiring_trend": "growing",
    "data_freshness": "2026-06-26"
}}

Return only JSON. No markdown."""

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }

    try:
        print("Calling Perplexity API")
        response = requests.post(
            PERPLEXITY_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"Perplexity status: {response.status_code}")
        print(f"Perplexity response: {response.text[:500]}")
        response.raise_for_status()

        data = response.json()
        raw = data["choices"][0]["message"]["content"].strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())
        result["data_freshness"] = datetime.utcnow().isoformat()
        return result

    except Exception as e:
        print(f"Perplexity error: {type(e).__name__}: {str(e)}")
        raise Exception(f"Market agent failed: {type(e).__name__}: {str(e)}")
