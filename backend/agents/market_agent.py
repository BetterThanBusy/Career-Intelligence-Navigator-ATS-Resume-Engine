import json
import os
import re
import requests
import anthropic
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def extract_json_from_text(text: str) -> dict:
    """
    Robustly extract JSON from any response —
    handles markdown fences, prose wrapping, partial JSON.
    """
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue

    # Find JSON object using regex
    pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid JSON found in response: {text[:300]}")


def get_job_market_intelligence(role: str, skills: list, industry: str = None) -> dict:

    print(f"Fetching market intelligence for: {role}")

    skills_context = ", ".join(skills[:8]) if skills else "general skills"
    industry_context = f"in {industry}" if industry else "across industries"

    query = f"""Analyze the 2026 job market for a {role} professional {industry_context} with skills in {skills_context}.

Return ONLY a raw JSON object with NO markdown, NO explanation, NO text before or after.
The response must start with {{ and end with }}.

Required format:
{{
    "in_demand_skills": ["skill1", "skill2", "skill3", "skill4", "skill5", "skill6", "skill7", "skill8"],
    "skills_at_risk": ["risk_skill1", "risk_skill2", "risk_skill3"],
    "salary_range": {{
        "low": 100000,
        "mid": 140000,
        "high": 200000,
        "currency": "USD"
    }},
    "target_job_titles": ["title1", "title2", "title3", "title4", "title5"],
    "growing_adjacent_roles": ["role1", "role2", "role3"],
    "top_certifications": ["cert1", "cert2", "cert3"],
    "market_summary": "2-3 sentence summary of current market conditions for this role in 2026",
    "hiring_trend": "growing"
}}"""

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are a job market analyst. Return only raw JSON objects. Never use markdown. Never add explanation. Start response with { and end with }."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "temperature": 0.1
    }

    # Try Perplexity first
    try:
        print("Calling Perplexity API")
        response = requests.post(
            PERPLEXITY_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"Perplexity status: {response.status_code}")

        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        print(f"Perplexity raw response: {raw[:200]}")

        result = extract_json_from_text(raw)
        result["data_freshness"] = datetime.utcnow().isoformat()
        result["source"] = "perplexity"
        print(f"Perplexity success, hiring trend: {result.get('hiring_trend')}")
        return result

    except Exception as e:
        print(f"Perplexity failed: {type(e).__name__}: {str(e)}")
        print("Falling back to Claude for market intelligence")

    # Fallback to Claude if Perplexity fails
    try:
        fallback_prompt = f"""You are a job market analyst. Analyze the 2026 job market for a {role} with skills in {skills_context}.

Return ONLY valid JSON, no markdown, no explanation:
{{
    "in_demand_skills": ["list 8 most in-demand skills for this role in 2026"],
    "skills_at_risk": ["list 3 skills at risk of automation"],
    "salary_range": {{
        "low": 0,
        "mid": 0,
        "high": 0,
        "currency": "USD"
    }},
    "target_job_titles": ["list 5 relevant job titles"],
    "growing_adjacent_roles": ["list 3 adjacent roles"],
    "top_certifications": ["list 3 top certifications"],
    "market_summary": "2-3 sentence market summary",
    "hiring_trend": "growing or stable or declining"
}}

Fill all values specifically for {role}. Return only JSON."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": fallback_prompt}]
        )

        raw = response.content[0].text.strip()
        result = extract_json_from_text(raw)
        result["data_freshness"] = datetime.utcnow().isoformat()
        result["source"] = "claude_fallback"
        print(f"Claude fallback success, hiring trend: {result.get('hiring_trend')}")
        return result

    except Exception as e:
        print(f"Claude fallback also failed: {type(e).__name__}: {str(e)}")
        raise Exception(f"Market intelligence failed on both Perplexity and Claude: {str(e)}")
